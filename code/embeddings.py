"""Transformer un texte en vecteur avec un modele d'embedding local (fastembed). FOURNI.

    python embeddings.py              # demonstration : trois phrases, leurs similarites
    python embeddings.py mpnet

Le modele est telecharge UNE fois (dans ~/.cache/fastembed), puis tout tourne hors ligne,
sans cle et sans quota. Les vecteurs des passages sont gardes dans data/index/.
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

MODELES = {
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",   # 220 Mo, 384 dimensions
    "mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",    # 1 Go, 768 dimensions
}
DOSSIER_INDEX = Path("../data/index")
DOSSIER_MODELES = Path.home() / ".cache" / "fastembed"   # sinon fastembed utilise /tmp, vide au redemarrage
_charges = {}


def _modele(nom):
    if nom not in MODELES:
        raise ValueError(f"modele inconnu : {nom} (choix : {', '.join(MODELES)})")
    if nom not in _charges:
        from fastembed import TextEmbedding
        print(f"chargement de {MODELES[nom]} (telechargement la premiere fois)...")
        _charges[nom] = TextEmbedding(MODELES[nom], cache_dir=str(DOSSIER_MODELES))
    return _charges[nom]


def encoder(textes, nom="minilm"):
    """Une ligne par texte ; chaque vecteur est ramene a une longueur de 1."""
    vecteurs = np.array(list(_modele(nom).embed(list(textes))), dtype=np.float32)
    return vecteurs / np.linalg.norm(vecteurs, axis=1, keepdims=True)


def charger_passages(chemin="../data/passages.csv"):
    with open(chemin, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def texte_a_indexer(passage):
    """Le titre aide beaucoup : il resume la section en quelques mots."""
    return f"{passage['titre']}. {passage['texte']}"


def index_passages(passages, nom="minilm"):
    """Les vecteurs de tous les passages, calcules une fois puis relus sur disque."""
    textes = [texte_a_indexer(p) for p in passages]
    empreinte = hashlib.md5("\n".join(textes).encode("utf-8")).hexdigest()[:8]
    cache = DOSSIER_INDEX / f"{nom}_{empreinte}.npy"
    if cache.exists():
        return np.load(cache)
    vecteurs = encoder(textes, nom)
    DOSSIER_INDEX.mkdir(parents=True, exist_ok=True)
    np.save(cache, vecteurs)
    return vecteurs


if __name__ == "__main__":
    nom = sys.argv[1] if len(sys.argv) > 1 else "minilm"
    phrases = ["Je n'arrive plus à me connecter à mon compte",
               "Mon mot de passe ne fonctionne plus",
               "Combien coûte l'offre Premium ?"]
    v = encoder(phrases, nom)
    print(f"un vecteur = {v.shape[1]} nombres, par exemple : {np.round(v[0][:5], 3)} ...")
    print("\nsimilarite cosinus (1 = meme sens, 0 = sans rapport)")
    for i in range(3):
        for j in range(i + 1, 3):
            print(f"  {float(v[i] @ v[j]):.2f}   « {phrases[i]} »  /  « {phrases[j]} »")
