"""Retrouver les passages les plus proches d'une question.

    python recherche.py "Je ne peux plus me connecter"
    python recherche.py "Je ne peux plus me connecter" mpnet 5
"""
import sys

import numpy as np

from embeddings import charger_passages, encoder, index_passages


# ---------------------------------------------------------------- a ecrire
def chercher(vecteur_question, index, k=3):
    """Renvoie (positions, scores) des k passages les plus proches, du meilleur au moins bon.

    index : une ligne par passage ; tous les vecteurs ont une longueur de 1,
    donc le produit scalaire EST la similarite cosinus.
    """
    scores = index @ vecteur_question            # un score par passage
    positions = np.argsort(scores)[::-1][:k]     # tri decroissant, k premiers
    return positions.tolist(), scores[positions].tolist()


# ---------------------------------------------------------------- fourni
def rechercher(question, passages, index, modele="minilm", k=3):
    """La question en clair -> les k passages, avec leur score."""
    q = encoder([question], modele)[0]
    positions, scores = chercher(q, index, k)
    return [dict(passages[i], score=round(s, 3)) for i, s in zip(positions, scores)]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage : python recherche.py "question" [minilm|mpnet] [k]')
    modele = sys.argv[2] if len(sys.argv) > 2 else "minilm"
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    passages = charger_passages()
    for p in rechercher(sys.argv[1], passages, index_passages(passages, modele), modele, k):
        print(f"{p['id']}  {p['score']:.3f}  {p['titre']}  ({p['source']})")
