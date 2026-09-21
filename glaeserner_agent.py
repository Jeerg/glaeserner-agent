# -*- coding: utf-8 -*-
"""
Glaeserner Agent - ein Mini-Agent zum ZUSCHAUEN.
Sie tippen im Terminal eine Frage; der Agent laeuft die Schleife und druckt
ALLES aus: jeden Gedanken, jeden Werkzeugaufruf, jede Beobachtung, jede Runde.

Lehrbeispiel fuer "Agentic AI" (Kap 2.2). Bewusst klein und lesbar.

Start:
    python glaeserner_agent.py
    (dann Frage tippen, z.B.: Ist Auftrag 4711 termingerecht?)
    Beenden mit  exit

Einmal-Modus (ohne Tippen, z.B. zum Testen):
    python glaeserner_agent.py --frage "Ist Auftrag 4711 termingerecht?"

LLM dahinter: OpenAI-kompatibel (Default: DeepInfra-Cloud ueber den Schluessel
in der Projekt-.env). Auf LOKAL (Ollama) umstellen: einfach die zwei Zeilen
unter KONFIG aendern (BASIS_URL + MODELL) - der Rest bleibt gleich.
"""

import os, sys, json, re, urllib.request, urllib.error

# ============================ KONFIG ============================
# Cloud (Default): DeepInfra, OpenAI-kompatibel. Schluessel kommt aus der .env.
BASIS_URL = os.environ.get("AGENT_BASIS_URL", "https://api.deepinfra.com/v1/openai")
MODELL    = os.environ.get("AGENT_MODELL",    "meta-llama/Llama-3.3-70B-Instruct")
# Lokal (Ollama) waere z.B.:
#   BASIS_URL = "http://localhost:11434/v1"
#   MODELL    = "qwen2.5:7b"
MAX_RUNDEN = 6
ENV_PFAD = r"C:\Users\JörgWFischer\PycharmProjects\tbx_stzrim\.env"

# ============================ DATEN (frei editierbar) ============================
# Kleine Produkt-Tabelle. Nur diese Werte "kennt" der Agent ueber seine Werkzeuge.
AUFTRAEGE = {
    "4711": ["Welle", "Ritzel", "Lager"],
    "4712": ["Gehaeuse", "Deckel"],
}
# Teil -> (Bestand in Stueck, Wiederbeschaffungszeit in Tagen)
BESTAND = {
    "Welle":    (5, 0),
    "Ritzel":   (3, 0),
    "Lager":    (0, 15),     # <- der Engpass im Leitbeispiel
    "Gehaeuse": (2, 0),
    "Deckel":   (10, 0),
}

# ============================ WERKZEUGE ============================
def werkzeug_stueckliste(argument):
    teile = AUFTRAEGE.get(str(argument).strip())
    if teile is None:
        return f"Kein Auftrag/keine Baugruppe '{argument}' gefunden."
    return "Teile: " + ", ".join(teile)

def werkzeug_bestand(argument):
    eintrag = BESTAND.get(str(argument).strip())
    if eintrag is None:
        return f"Kein Bestand fuer '{argument}' gefunden."
    stk, tage = eintrag
    if stk > 0:
        return f"{stk} Stueck auf Lager, Wiederbeschaffung {tage} Tage."
    return f"0 Stueck auf Lager, Wiederbeschaffung {tage} Tage."

WERKZEUGE = {
    "stueckliste": (werkzeug_stueckliste, "stueckliste(argument): Teile eines Auftrags/einer Baugruppe"),
    "bestand":     (werkzeug_bestand,     "bestand(argument): Lagerbestand + Wiederbeschaffungszeit eines Teils"),
}

SYSTEM = (
    "Du bist ein hilfreicher KI-Agent mit Werkzeugen. Antworte auf Deutsch.\n"
    "Arbeite in Runden. In JEDER Runde gibst du aus:\n"
    'zuerst eine Zeile "Gedanke: <ein kurzer Satz, was du als Naechstes tust und warum>",\n'
    "danach GENAU eine JSON-Zeile - entweder ein Werkzeugaufruf oder die Endantwort:\n"
    '  {"werkzeug": "stueckliste", "argument": "4711"}\n'
    '  oder  {"antwort": "..."}\n'
    "Verfuegbare Werkzeuge:\n"
    "- stueckliste(argument): Teile eines Auftrags/einer Baugruppe\n"
    "- bestand(argument): Lagerbestand + Wiederbeschaffungszeit EINES Teils\n"
    "Ablauf: Ein Auftrag (z.B. 4711) ist KEIN Teil. Rufe ZUERST stueckliste(auftrag);\n"
    "danach bestand(teil) fuer JEDES Teil aus der Stueckliste - ALLE Teile, BEVOR du\n"
    "antwortest. Antworte NIE nach nur einem Teil. Wiederhole NIE denselben Aufruf.\n"
    "Regeln: Rate NICHT. Nutze nur Werkzeug-Ergebnisse. Ein Auftrag ist NICHT\n"
    "termingerecht, sobald AUCH NUR EIN Teil 0 auf Lager hat und Wiederbeschaffung > 0\n"
    "Tage; sonst termingerecht. Nenne in der Antwort das kritische Teil.\n"
    "Wenn du genug weisst, gib die Endantwort mit {\"antwort\": ...}."
)

# ============================ LLM-Aufruf (OpenAI-kompatibel) ============================
def lade_schluessel():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    try:
        with open(ENV_PFAD, "r", encoding="utf-8") as f:
            for zeile in f:
                if zeile.strip().startswith("OPENAI_API_KEY="):
                    return zeile.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None

def frage_llm(nachrichten, schluessel):
    daten = json.dumps({
        "model": MODELL,
        "messages": nachrichten,
        "temperature": 0,
        "max_tokens": 400,
    }).encode("utf-8")
    req = urllib.request.Request(
        BASIS_URL.rstrip("/") + "/chat/completions",
        data=daten,
        headers={"Authorization": f"Bearer {schluessel}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        antwort = json.loads(r.read().decode("utf-8"))
    return antwort["choices"][0]["message"]["content"]

# ============================ Parsing ============================
def finde_json(text):
    """Findet das erste {...}-Objekt im Text und gibt es als dict zurueck (oder None)."""
    tiefe = 0; start = -1
    for i, c in enumerate(text):
        if c == "{":
            if tiefe == 0: start = i
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0 and start >= 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    start = -1
    return None

# ============================ Die Agenten-Schleife ============================
def agenten_schritte(frage, schluessel):
    """Generator: liefert je Schritt ein dict. Wird von Terminal UND Web genutzt."""
    yield {"art": "frage", "text": frage}
    verlauf = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": frage},
    ]
    gesehen = {}   # (werkzeug, argument) -> letztes Ergebnis  (Wiederholungs-Sperre)
    for runde in range(1, MAX_RUNDEN + 1):
        yield {"art": "runde", "n": runde, "kontext": len(verlauf)}
        try:
            roh = frage_llm(verlauf, schluessel)
        except urllib.error.HTTPError as e:
            yield {"art": "fehler", "text": f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}"}
            return
        except Exception as e:
            yield {"art": "fehler", "text": str(e)}
            return

        yield {"art": "denken", "text": roh.strip()}
        verlauf.append({"role": "assistant", "content": roh})

        entscheidung = finde_json(roh)
        if entscheidung is None:
            yield {"art": "antwort", "text": roh.strip()}
            return
        if "antwort" in entscheidung:
            yield {"art": "antwort", "text": str(entscheidung["antwort"])}
            return

        name = entscheidung.get("werkzeug")
        arg = entscheidung.get("argument", "")
        yield {"art": "aktion", "werkzeug": name, "argument": arg}
        merk = (name, str(arg))
        if name not in WERKZEUGE:
            beob = f"Unbekanntes Werkzeug '{name}'. Verfuegbar: {', '.join(WERKZEUGE)}."
        elif merk in gesehen:
            beob = (f"STOPP: {name}({arg}) wurde bereits versucht (Ergebnis: {gesehen[merk]}). "
                    f"Waehle ein ANDERES Werkzeug/Argument oder gib jetzt die Antwort.")
        else:
            beob = WERKZEUGE[name][0](arg)
            gesehen[merk] = beob
        yield {"art": "beobachtung", "werkzeug": name, "text": beob}
        verlauf.append({"role": "user", "content": f"Beobachtung von {name}: {beob}"})
    yield {"art": "ende", "text": "Runden-Limit erreicht, keine Endantwort."}


def agenten_lauf(frage, schluessel):
    print("\n" + "=" * 66)
    for s in agenten_schritte(frage, schluessel):
        a = s["art"]
        if a == "frage":
            print(f"FRAGE:  {s['text']}\n" + "=" * 66)
        elif a == "runde":
            print(f"\n----- Runde {s['n']} -----")
            print(f"[hoch]  Kontext an das LLM: {s['kontext']} Nachrichten")
        elif a == "denken":
            print("[runter] Das Modell denkt/antwortet:")
            for zeile in s["text"].splitlines():
                print("         " + zeile)
        elif a == "aktion":
            print(f"[aktion] Werkzeug-Aufruf:  {s['werkzeug']}({s['argument']!r})")
        elif a == "beobachtung":
            print(f"[beob]   Ergebnis:         {s['text']}")
        elif a == "antwort":
            print(f"\n>>> ENDANTWORT: {s['text']}")
        elif a == "fehler":
            print(f"[FEHLER] {s['text']}")
        elif a == "ende":
            print(f"\n>>> {s['text']}")

# ============================ Start ============================
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    schluessel = lade_schluessel()
    if not schluessel:
        print("Kein OPENAI_API_KEY gefunden (Umgebung oder .env). Abbruch.")
        sys.exit(1)
    print(f"Modell: {MODELL}   (Endpunkt: {BASIS_URL})")

    if "--frage" in sys.argv:
        i = sys.argv.index("--frage")
        frage = sys.argv[i + 1] if i + 1 < len(sys.argv) else "Ist Auftrag 4711 termingerecht?"
        agenten_lauf(frage, schluessel)
        return

    print("\nGlaeserner Agent bereit. Tippen Sie eine Frage (oder 'exit').")
    print("Beispiel:  Ist Auftrag 4711 termingerecht?")
    while True:
        try:
            frage = input("\nIhre Frage> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTschuess.")
            return
        if frage.lower() in ("exit", "quit", "ende", ""):
            print("Tschuess.")
            return
        agenten_lauf(frage, schluessel)

if __name__ == "__main__":
    main()
