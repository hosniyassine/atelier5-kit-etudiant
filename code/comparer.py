"""Toutes vos evaluations d'agent cote a cote. FOURNI.

    python comparer.py
"""
import glob
import json

resumes = []
for chemin in sorted(glob.glob("resultats/agent__*.json")):
    with open(chemin, encoding="utf-8") as f:
        resumes.append(json.load(f))
if not resumes:
    raise SystemExit("aucun resultat : lancez d'abord evaluer_agent.py")
print(f"{'agent':<30}{'reussite':>9}{'outils':>8}{'justes':>8}{'appels':>8}"
      f"{'tickets':>9}{'duree':>8}")
for r in sorted(resumes, key=lambda x: -x["reussite"]):
    print(f"{r['etiquette']:<30}{r['reussite']:>9.2f}{r['outils_corrects']:>8.2f}"
          f"{r['reponses_justes']:>8.2f}{r['appels_moyens']:>8}{r['tickets_non_demandes']:>9}"
          f"{r['duree_moyenne_s']:>7}s")
print("\n1 demande sur 20 = 5 points : deux demandes d'ecart ne prouvent rien.")
