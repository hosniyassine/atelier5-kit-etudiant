"""Les mesures de l'atelier : la recherche (Recall@k, MRR) et la reponse (faits attendus).

Pour une question, la recherche renvoie une liste ordonnee de passages : ["P19", "P18", "P22"].
On connait le ou les passages attendus : ["P18"].

  Recall@k : la part des questions dont un passage attendu est dans les k premiers.
  MRR      : la moyenne de 1 / rang du premier passage attendu (0 s'il est absent).
             rang 1 -> 1 ; rang 2 -> 0,5 ; rang 3 -> 0,33. Il recompense le bon classement.
"""
import re


# ---------------------------------------------------------------- a ecrire
def recall_at_k(attendus, trouves, k):
    """attendus : liste de listes d'ids ; trouves : liste de listes ordonnees d'ids."""
    touches = sum(1 for a, t in zip(attendus, trouves) if set(a) & set(t[:k]))
    return touches / len(attendus)


def mrr(attendus, trouves):
    total = 0.0
    for a, t in zip(attendus, trouves):
        for rang, pid in enumerate(t, start=1):
            if pid in a:
                total += 1 / rang
                break
    return total / len(attendus)


# ---------------------------------------------------------------- fourni
def normaliser(texte):
    """Meme idee qu'a l'atelier 3 : comparer la forme, pas la typographie."""
    texte = texte.lower().replace("’", "'")
    texte = texte.replace("€", " euros ").replace("%", " pour cent ")
    texte = re.sub(r"(\d)([a-zà-ÿ])", r"\1 \2", texte)      # 24h -> 24 h
    texte = re.sub(r"[^\w\s]", " ", texte)                  # ponctuation, apostrophes
    return " ".join(texte.split())


def fait_present(fait, reponse):
    """Un fait peut avoir plusieurs formes acceptees, separees par | ."""
    reponse = f" {normaliser(reponse)} "
    return any(f" {normaliser(forme)} " in reponse for forme in fait.split("|"))


def faits_presents(faits, reponse):
    """faits : "48 heures|48 h;trentieme|1/30" -> True si TOUS les faits sont presents."""
    return all(fait_present(f, reponse) for f in faits.split(";") if f.strip())
