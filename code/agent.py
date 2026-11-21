"""L'agent : un LLM qui decide quels outils appeler, et une boucle qui les execute.

    python agent.py "Client C1003 : internet coupe 4 jours, combien vais-je recuperer ?"
    python agent.py "..." openai/gpt-oss-20b
"""
import json
import os
import sys
import time

from groq import Groq, RateLimitError

from outils import SCHEMAS, executer_outil

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
MODELE = "qwen/qwen3.8-27b"
TOKENS_PAR_MINUTE = 8000

CONSIGNE_AGENT = """Tu es l'agent du service client de l'operateur Fibrelune. Date du jour : 15 novembre 2026.
- Utilise les outils pour obtenir les informations. N'invente jamais un montant, une date
  ou un numero de client.
- Si la demande concerne un client et que son numero manque, demande-le sans appeler d'outil.
- Ne communique jamais les informations d'un autre client que celui qui ecrit.
- Si la demande sort du service client Fibrelune, dis-le poliment, sans appeler d'outil.
- Reponds en francais, en trois phrases au plus, avec les chiffres exacts renvoyes par les outils."""


# ---------------------------------------------------------------- fourni
def appel_llm(messages, schemas, modele=MODELE):
    """Un appel au modele avec la liste des outils. Attend ensuite le temps qu'il faut
    pour rester sous 8 000 tokens par minute : un appel de 1 500 tokens -> ~11 s."""
    for tentative in range(4):
        try:
            reponse = client.chat.completions.create(
                model=modele, messages=messages, tools=schemas,
                tool_choice="auto", temperature=0.0)
            break
        except RateLimitError:
            attente = 20 * (tentative + 1)
            print(f"\n  quota atteint, pause de {attente} s")
            time.sleep(attente)
    else:
        raise RuntimeError("quota toujours atteint apres 4 tentatives")
    time.sleep(max(2.0, reponse.usage.total_tokens / TOKENS_PAR_MINUTE * 60))
    return reponse


def message_assistant(msg):
    """Le message du modele, remis sous forme de dictionnaire pour l'historique."""
    d = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        d["tool_calls"] = [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name, "arguments": c.function.arguments}}
                           for c in msg.tool_calls]
    return d


# ---------------------------------------------------------------- a ecrire
def executer_agent(demande, modele=MODELE, schemas=SCHEMAS, max_tours=5):
    messages = [{"role": "system", "content": CONSIGNE_AGENT},
                {"role": "user", "content": demande}]
    appels = []
    for tour in range(1, max_tours + 1):
        msg = appel_llm(messages, schemas, modele).choices[0].message
        if not msg.tool_calls:
            return {"reponse": msg.content or "", "appels": appels,
                    "tours": tour, "abandon": False}
        messages.append(message_assistant(msg))
        for appel in msg.tool_calls:
            try:
                arguments = json.loads(appel.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            resultat = executer_outil(appel.function.name, arguments)
            appels.append({"outil": appel.function.name,
                           "arguments": arguments, "resultat": resultat})
            messages.append({"role": "tool", "tool_call_id": appel.id,
                             "content": json.dumps(resultat, ensure_ascii=False)})
    return {"reponse": "", "appels": appels, "tours": max_tours, "abandon": True}



if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage : python agent.py "demande du client" [modele]')
    r = executer_agent(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else MODELE)
    for a in r["appels"]:
        print(f"  outil  {a['outil']}({json.dumps(a['arguments'], ensure_ascii=False)})")
        print(f"         -> {json.dumps(a['resultat'], ensure_ascii=False)[:120]}")
    print(f"\n{r['reponse']}\n({r['tours']} tours{', ABANDON' if r['abandon'] else ''})")
