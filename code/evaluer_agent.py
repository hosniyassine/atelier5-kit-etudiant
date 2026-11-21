"""Evalue l'agent sur les 20 demandes de data/taches.csv. FOURNI.

    python evaluer_agent.py qwen/qwen3.8-27b
    python evaluer_agent.py openai/gpt-oss-20b
    python evaluer_agent.py qwen/qwen3.8-27b vagues     # descriptions d'outils reduites

Les executions sont gardees en cache dans data/agent/ : relancer ne coute rien.
"""
import csv
import json
import sys
import time
from pathlib import Path

from agent import executer_agent
from metriques import faits_presents
from outils import SCHEMAS, SCHEMAS_VAGUES


def charger_taches(chemin="../data/taches.csv"):
    with open(chemin, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(modele, variante="precises"):
    schemas = SCHEMAS_VAGUES if variante == "vagues" else SCHEMAS
    etiquette = f"{modele.split('/')[-1]}__{variante}"
    fichier_cache = Path("../data/agent") / f"{etiquette}.json"
    cache = json.loads(fichier_cache.read_text(encoding="utf-8")) if fichier_cache.exists() else {}
    taches = charger_taches()
    runs = []
    for i, t in enumerate(taches, 1):
        if t["id"] not in cache:
            debut = time.time()
            r = executer_agent(t["demande"], modele, schemas)
            r["duree_s"] = round(time.time() - debut, 1)
            cache[t["id"]] = r
            fichier_cache.parent.mkdir(exist_ok=True)
            fichier_cache.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        runs.append(cache[t["id"]])
        print(f"\r{i}/{len(taches)} demandes", end="", flush=True)
    print()

    attendus = [set(filter(None, t["outils_attendus"].split("|"))) for t in taches]
    appeles = [[a["outil"] for a in r["appels"]] for r in runs]
    # consulter la fiche du client qui ecrit est tolere (lecture seule, sans effet)
    tolere = [{"consulter_client"} if t["consultation_toleree"] == "1" else set() for t in taches]
    outils_ok = [set(ap) - (tol - at) == at for ap, at, tol in zip(appeles, attendus, tolere)]
    justes = [not r["abandon"] and (faits_presents(t["faits"], r["reponse"]) if t["faits"] else True)
              for t, r in zip(taches, runs)]
    reussites = [o and j for o, j in zip(outils_ok, justes)]
    non_demandes = sum(1 for ap, at in zip(appeles, attendus) if "creer_ticket" in ap and "creer_ticket" not in at)
    n = len(taches)
    resume = {
        "etiquette": etiquette, "modele": modele, "variante": variante,
        "reussite": sum(reussites) / n, "outils_corrects": sum(outils_ok) / n,
        "reponses_justes": sum(justes) / n,
        "appels_moyens": round(sum(len(a) for a in appeles) / n, 2),
        "tickets_non_demandes": non_demandes, "abandons": sum(r["abandon"] for r in runs),
        "duree_moyenne_s": round(sum(r["duree_s"] for r in runs) / n, 1),
        "ids": [t["id"] for t in taches], "outils_ok": outils_ok, "justes": justes,
        "appeles": appeles, "attendus": [sorted(a) for a in attendus],
        "reponses": [r["reponse"] for r in runs],
    }
    print(f"\n=== agent {etiquette} ===")
    print(f"taches reussies       : {resume['reussite']:.3f}  ({sum(reussites)}/{n})")
    print(f"bons outils           : {resume['outils_corrects']:.3f}")
    print(f"reponses justes       : {resume['reponses_justes']:.3f}")
    print(f"appels par demande    : {resume['appels_moyens']}")
    print(f"tickets non demandes  : {non_demandes}      abandons : {resume['abandons']}")
    print(f"duree par demande     : {resume['duree_moyenne_s']} s (pauses de quota comprises)")
    print("\nDemandes ratees")
    for t, ap, at, o, j, r in zip(taches, appeles, attendus, outils_ok, justes, runs):
        if not (o and j):
            print(f"  {t['id']}  attendu {sorted(at) or '-'}  appele {ap or '-'}")
            print(f"        reponse : {r['reponse'][:100]}")
    Path("resultats").mkdir(exist_ok=True)
    chemin = Path("resultats") / f"agent__{etiquette}.json"
    chemin.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nresultat enregistre dans {chemin}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "precises")
