"""Verifie diagnostic(), sans reseau ni quota.

    python test_diagnostic.py
"""
from diagnostic import diagnostic

outils_ok = [True, True, False, False, True]
justes    = [True, False, False, True, True]
try:
    cases = diagnostic(outils_ok, justes)
except NotImplementedError as e:
    raise SystemExit(str(e))
attendu = {"ok": [0, 4], "redaction": [1], "outils": [2], "detour": [3]}
ok = 0
for cle, pos in attendu.items():
    if sorted(cases.get(cle, [])) == pos:
        ok += 1
    else:
        print(f"ECHEC  case {cle!r} : attendu {pos}, obtenu {cases.get(cle)}")
print(f"{ok}/4 cases correctes")
