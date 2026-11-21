"""Pourquoi une demande a-t-elle echoue ? Le choix des outils, ou la reponse finale ?

    python diagnostic.py qwen3.8-27b__precises

Sans appel reseau : on relit resultats/agent__<etiquette>.json.
"""
import json
import sys


# ---------------------------------------------------------------- a ecrire
def diagnostic(outils_ok, justes):
    """Range chaque demande dans une des quatre cases et renvoie leurs positions.

      "ok"        : bons outils, reponse juste
      "redaction" : bons outils, reponse fausse   <- le modele a mal lu ou mal recopie le resultat
      "outils"    : mauvais outils, reponse fausse <- descriptions d'outils, consigne, modele
      "detour"    : mauvais outils, reponse juste  <- appel en trop ou en moins, sans degat visible
    """
    cases = {"ok": [], "redaction": [], "outils": [], "detour": []}
    for i, (bons_outils, juste) in enumerate(zip(outils_ok, justes)):
        if bons_outils and juste:
            cases["ok"].append(i)
        elif bons_outils and not juste:
            cases["redaction"].append(i)
        elif not bons_outils and juste:
            cases["detour"].append(i)
        else:
            cases["outils"].append(i)
    return cases


# ---------------------------------------------------------------- fourni
def afficher(r):
    cases = diagnostic(r["outils_ok"], r["justes"])
    print(f"\n{r['etiquette']} : {len(r['ids'])} demandes")
    print(f"\n{'':<17}{'reponse juste':>15}{'reponse fausse':>16}")
    print(f"{'bons outils':<17}{len(cases['ok']):>15}{len(cases['redaction']):>16}")
    print(f"{'mauvais outils':<17}{len(cases['detour']):>15}{len(cases['outils']):>16}")
    for nom in ("outils", "detour", "redaction"):
        if cases[nom]:
            print(f"\n{nom} :")
        for i in cases[nom]:
            print(f"  {r['ids'][i]}  attendu {r['attendus'][i] or '-'}  appele {r['appeles'][i] or '-'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage : python diagnostic.py qwen3.8-27b__precises")
    with open(f"resultats/agent__{sys.argv[1]}.json", encoding="utf-8") as f:
        afficher(json.load(f))