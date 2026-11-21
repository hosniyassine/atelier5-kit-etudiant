# Atelier 5 — Agir : un agent et ses outils

    python -m pip install groq numpy fastembed
    export GROQ_API_KEY=gsk_votre_cle
    cd code
    python outils.py                 # les 5 outils, sans LLM

## Contenu

    data/clients.json       8 clients fictifs (date du jour fixée au 15/11/2026)
    data/taches.csv         20 demandes annotées
    data/passages.csv       les procédures de l'atelier 4 (pour chercher_procedure)

    code/outils.py          fourni — 5 outils et 4 descriptions ; À COMPLÉTER : SCHEMA_COMPENSATION
    code/agent.py           À COMPLÉTER : executer_agent() (appel_llm et message_assistant fournis)
    code/diagnostic.py      À COMPLÉTER : diagnostic()
    code/evaluer_agent.py   fourni — les 20 demandes, mesures, cache
    code/comparer.py        fourni
    code/embeddings.py, recherche.py, metriques.py   repris de l'atelier 4
    code/test_schema.py, test_diagnostic.py          sans quota

## Ordre

    étape 1  python test_schema.py
    étape 2  python agent.py "Client C1003. Internet coupé 4 jours. Combien vais-je récupérer ?"
    étape 3  python evaluer_agent.py qwen/qwen3.8-27b
    étape 4  python test_diagnostic.py && python diagnostic.py qwen3.8-27b__precises
    étape 5  python evaluer_agent.py openai/gpt-oss-20b
    étape 6  python evaluer_agent.py qwen/qwen3.8-27b vagues
             python comparer.py
