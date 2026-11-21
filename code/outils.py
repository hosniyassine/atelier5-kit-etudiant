"""Les outils de l'agent : des fonctions Python ordinaires, et leur description JSON Schema.

    python outils.py        # essaie chaque outil a la main, sans LLM

Le modele ne lance JAMAIS ces fonctions lui-meme : il demande « appelle tel outil avec
tels arguments », et c'est NOTRE code qui l'execute puis lui renvoie le resultat.
"""
import csv
import json
import re
from datetime import date
from pathlib import Path

DATA = Path("../data")
DATE_DU_JOUR = date(2026, 11, 15)          # fixee pour que les resultats soient reproductibles
CATEGORIES = ["facturation", "technique", "compte", "commercial"]
CLIENTS = json.loads((DATA / "clients.json").read_text(encoding="utf-8"))
TICKETS_CREES = []


def euros(x):
    return f"{x:.2f}".replace(".", ",") + " euros"


def _client(numero_client):
    numero_client = str(numero_client).strip().upper()
    if numero_client not in CLIENTS:
        return None, {"erreur": f"client {numero_client} introuvable"}
    return CLIENTS[numero_client], None


# ---------------------------------------------------------------- les 5 outils (fournis)
def consulter_client(numero_client):
    c, erreur = _client(numero_client)
    if erreur:
        return erreur
    return {"offre": c["offre"], "prix_mensuel": euros(c["prix_mensuel"]),
            "date_souscription": c["date_souscription"], "fin_engagement": c["fin_engagement"],
            "statut_ligne": c["statut_ligne"],
            "factures_impayees": [dict(f, montant=euros(f["montant"])) for f in c["factures_impayees"]]}


def calculer_frais_resiliation(numero_client):
    c, erreur = _client(numero_client)
    if erreur:
        return erreur
    souscription = date.fromisoformat(c["date_souscription"])
    fin = date.fromisoformat(c["fin_engagement"])
    if (DATE_DU_JOUR - souscription).days <= 14:
        return {"frais": euros(0), "motif": "droit de rétractation (moins de 14 jours)"}
    if DATE_DU_JOUR < fin:
        return {"frais": euros(49), "motif": f"engagement en cours jusqu'au {fin.isoformat()}"}
    return {"frais": euros(0), "motif": "engagement terminé"}


def calculer_compensation(numero_client, jours_coupure):
    c, erreur = _client(numero_client)
    if erreur:
        return erreur
    jours = int(jours_coupure)
    if jours < 1:
        return {"erreur": "jours_coupure doit etre au moins 1"}
    if jours * 24 <= 48:
        return {"compensation": euros(0), "motif": "coupure de 48 heures ou moins : pas de compensation"}
    return {"compensation": euros(round(jours * c["prix_mensuel"] / 30, 2)),
            "motif": f"{jours} jours x 1/30 de {euros(c['prix_mensuel'])}, deduit de la prochaine facture"}


def chercher_procedure(question):
    """La recherche de l'atelier 4 : les 2 passages les plus proches de la question."""
    with open(DATA / "passages.csv", encoding="utf-8") as f:
        passages = list(csv.DictReader(f))
    try:
        from embeddings import index_passages
        from recherche import rechercher
        trouves = rechercher(question, passages, index_passages(passages), k=2)
    except Exception:                          # fastembed ou modele absent : recherche par mots
        print("  (modele d'embedding indisponible : recherche par mots en commun)")
        mots = set(re.findall(r"\w{4,}", question.lower()))
        trouves = sorted(passages, key=lambda p: -len(mots & set(re.findall(r"\w{4,}", p["texte"].lower()))))[:2]
    return {"passages": [{"id": p["id"], "titre": p["titre"], "texte": p["texte"]} for p in trouves]}


def creer_ticket(numero_client, categorie, resume):
    c, erreur = _client(numero_client)
    if erreur:
        return erreur
    if categorie not in CATEGORIES:
        return {"erreur": f"categorie {categorie!r} inconnue : {', '.join(CATEGORIES)}"}
    numero = f"TK-{5001 + len(TICKETS_CREES)}"
    TICKETS_CREES.append({"numero": numero, "client": numero_client, "categorie": categorie,
                          "resume": resume})
    return {"ticket": numero, "statut": "créé", "delai_reponse": "48 heures"}


OUTILS = {f.__name__: f for f in (consulter_client, calculer_frais_resiliation,
                                  calculer_compensation, chercher_procedure, creer_ticket)}


def executer_outil(nom, arguments):
    """Lance l'outil demande par le modele. Une erreur devient un resultat, pas un plantage."""
    if nom not in OUTILS:
        return {"erreur": f"outil {nom!r} inconnu"}
    try:
        return OUTILS[nom](**arguments)
    except (TypeError, ValueError) as e:       # argument manquant, en trop, ou de mauvais type
        return {"erreur": f"arguments invalides pour {nom} : {e}"}


# ---------------------------------------------------------------- les descriptions
def schema(nom, description, proprietes, obligatoires):
    return {"type": "function", "function": {
        "name": nom, "description": description,
        "parameters": {"type": "object", "properties": proprietes, "required": obligatoires}}}


CLIENT = {"type": "string", "description": "Numéro client, de la forme C suivi de 4 chiffres, par exemple C1001"}

# ---- etape 1 : la description de calculer_compensation
SCHEMA_COMPENSATION = schema(
    "calculer_compensation",
    "Calcule le montant compensé à un client après une coupure de service, "
    "selon la règle Fibrelune (rien sous 48 heures). À utiliser quand le client "
    "signale une panne et demande ce qu'il récupère.",
    {"numero_client": CLIENT,
     "jours_coupure": {"type": "integer", "minimum": 1,
                       "description": "Nombre de jours complets sans service"}},
    ["numero_client", "jours_coupure"])

SCHEMAS = [
    schema("consulter_client",
           "Renvoie la fiche d'un client : offre, prix, dates d'engagement, état de la ligne, "
           "factures impayées. À utiliser pour toute question sur le contrat ou le compte d'un client précis.",
           {"numero_client": CLIENT}, ["numero_client"]),
    schema("calculer_frais_resiliation",
           "Calcule les frais si le client résilie aujourd'hui (engagement, droit de rétractation). "
           "À utiliser pour toute question sur le coût d'une résiliation ou d'une annulation.",
           {"numero_client": CLIENT}, ["numero_client"]),
    SCHEMA_COMPENSATION,
    schema("chercher_procedure",
           "Cherche dans les procédures Fibrelune les passages qui répondent à une question "
           "générale (règles, délais, offres), sans rapport avec un client précis.",
           {"question": {"type": "string", "description": "La question, reformulée en une phrase"}},
           ["question"]),
    schema("creer_ticket",
           "Crée un ticket pour le service concerné. À utiliser UNIQUEMENT si le client demande "
           "explicitement d'ouvrir un ticket ou de transmettre sa demande.",
           {"numero_client": CLIENT,
            "categorie": {"type": "string", "enum": CATEGORIES},
            "resume": {"type": "string", "description": "Le problème en une phrase"}},
           ["numero_client", "categorie", "resume"]),
]

# Variante de l'etape 6 : memes outils, descriptions reduites a quelques mots
SCHEMAS_VAGUES = [
    schema(s["function"]["name"], s["function"]["name"].replace("_", " "),
           {k: {"type": v["type"]} for k, v in s["function"]["parameters"]["properties"].items()},
           s["function"]["parameters"]["required"])
    for s in SCHEMAS
]


if __name__ == "__main__":
    print(consulter_client("C1005"))
    print(calculer_frais_resiliation("C1001"))
    print(calculer_compensation("C1003", 4))
    print(executer_outil("calculer_compensation", {"numero_client": "C1003"}))
    print(creer_ticket("C1003", "technique", "La box ne s'allume plus"))
    print(json.dumps(SCHEMA_COMPENSATION, ensure_ascii=False, indent=2))