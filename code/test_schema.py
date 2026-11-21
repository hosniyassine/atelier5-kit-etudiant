"""Verifie votre description de calculer_compensation, sans reseau ni quota.

    python test_schema.py
"""
from outils import SCHEMA_COMPENSATION, calculer_compensation

if not SCHEMA_COMPENSATION:
    raise SystemExit("SCHEMA_COMPENSATION n'est pas encore ecrit (etape 1)")
f = SCHEMA_COMPENSATION.get("function", {}) if SCHEMA_COMPENSATION else {}
p = f.get("parameters", {})
props = p.get("properties", {})
verifs = [
    ("type = function", SCHEMA_COMPENSATION.get("type") == "function"),
    ("nom identique a la fonction Python", f.get("name") == calculer_compensation.__name__),
    ("description d'au moins une phrase (> 40 caracteres)", len(f.get("description", "")) > 40),
    ("parametres numero_client et jours_coupure", set(props) == {"numero_client", "jours_coupure"}),
    ("jours_coupure est un integer", props.get("jours_coupure", {}).get("type") == "integer"),
    ("les deux parametres sont obligatoires (required)",
     set(p.get("required", [])) == {"numero_client", "jours_coupure"}),
]
for nom, ok in verifs:
    if not ok:
        print(f"ECHEC  {nom}")
print(f"{sum(ok for _, ok in verifs)}/{len(verifs)} verifications reussies")
