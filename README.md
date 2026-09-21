# Glaeserner Agent - Lehr-Demonstrator (Kap 2.2 Agentic AI)

Ein Agent zum Zuschauen: Sie tippen eine Frage, und jeder Schritt wird sichtbar -
der komplette Nachrichtenverlauf ans Modell, der Gedanke und die Entscheidung des
Modells, jeder Werkzeugaufruf, jede Beobachtung, der Token-Verbrauch je Runde und
ein mitwachsendes Sequenzdiagramm. Gerechnet und wirklich ausgefuehrt, nicht behauptet.

## Zwei Ebenen von Werkzeugen

**Ebene 1 - Vorgehen (fester Ablauf, im Code erzwungen):** der Agent arbeitet immer
in der Reihenfolge `diskutieren` -> `planen` -> `umsetzen`. So sieht man den echten
Agentic-Zyklus: erst versteht er die Aufgabe, dann plant er, dann fuehrt er aus.

**Ebene 2 - echte Arbeit auf diesem Rechner:**
- `python_ausfuehren(code)` - der Agent schreibt Python, der Rechner fuehrt es aus, die echte Ausgabe kommt zurueck.
- `powershell_ausfuehren(code)` - dito mit PowerShell (Dateien, Systeminfo, Verzeichnisse - echte Rechner-Aktionen).
- `spawn_agent(teilfragen)` - der Haupt-Agent startet fuer mehrere Teilfragen eigene Subagenten (parallel, je eigene Spur).

Datenbasis ist die echte Datei `auftraege.csv` (Spalten: `auftrag,teil,bestand,wiederbeschaffung_tage,faelligkeit_tage`).
Der Agent liest sie mit selbst geschriebenem Python - kein eingebautes Fake-Verzeichnis.

## Schluessel eintragen (einmalig)

Der Agent spricht ein Sprachmodell ueber eine OpenAI-kompatible Cloud an und braucht
dafuer einen Schluessel (z.B. von DeepInfra). Zwei Wege:

- **Reine Browser-Version:** `glaeserner-agent.html` doppelklicken und den Schluessel
  oben im Setup-Feld eintragen (bleibt nur im Browser).
- **Server-Version:** `.env.example` nach `.env` kopieren und den Schluessel eintragen
  (`OPENAI_API_KEY=...`). Alternativ vor dem Start `set OPENAI_API_KEY=...` (Windows).

## Starten (empfohlen: mit echter Code-Ausfuehrung)

**Doppelklick auf `start.bat`.** Der lokale Werkbank-Server startet (nur `127.0.0.1`)
und der Browser oeffnet sich. Den Schluessel liest er aus der `.env` (oder der
Umgebungsvariable). Beenden: das Server-Fenster schliessen oder Strg+C.

Alternativ von Hand, im Ordner dieses Repos:

```
python werkbank_server.py      (oder: py -3 werkbank_server.py)
```

Beispiele zum Ausprobieren:
- `Ist Auftrag 4711 termingerecht?` - der Agent schreibt Python, liest die CSV, rechnet.
- `Welche Teile sind laut auftraege.csv gar nicht auf Lager?` - Python-Auswertung der echten Datei.
- `Liste mit PowerShell die Dateien in diesem Ordner auf.` - echte Rechner-Aktion.
- `Zeig mir mit PowerShell den Rechnernamen und die Windows-Version.` - echte Systeminfo.
- `Vergleiche die Auftraege 4711 und 4712 - welcher ist termingerecht?` - der Agent spawnt zwei Subagenten.
- `Lies die Datei bestellungen.csv und zeig die ersten Zeilen.` - die Datei gibt es nicht: der erste
  Code-Versuch schlaegt fehl (rot markiert), der Agent liest die Fehlermeldung und korrigiert sich selbst.

Deep-Link fuers Vorfuehren (Frage vorausgefuellt, laeuft automatisch los):
`http://127.0.0.1:8761/?frage=Ist%20Auftrag%204711%20termingerecht%3F&run=1`

## Ohne Server (nur Browser, ohne Code-Ausfuehrung)

- `glaeserner-agent.html` - reine Browser-Version, per Doppelklick. Fragt den
  Schluessel ab (wird nur im Browser gemerkt, steht nicht in der Datei).
  **Ohne** laufenden Werkbank-Server ist die Code-Ausfuehrung aus Sicherheitsgruenden
  abgeschaltet - allgemeine Fragen gehen trotzdem. Gefahrlos weitergebbar.

## Sicherheit

Der Agent fuehrt beliebigen Code aus - das ist hier der Lehrzweck. Der Werkbank-Server
bindet ausschliesslich an `127.0.0.1` (nur dieser Rechner) und hat je Ausfuehrung ein
Zeitlimit von 20 s. Zum Teilen dient die reine `glaeserner-agent.html` ohne Server.

## LLM dahinter

Default: OpenAI-kompatible Cloud (DeepInfra) ueber den `OPENAI_API_KEY` aus der
Projekt-.env - Internet noetig, laeuft sofort. Modell einstellbar oben im Setup-Feld
(Default `meta-llama/Llama-3.3-70B-Instruct`). Auf lokal (Ollama) umstellbar ueber
`BASIS_URL`/`MODELL` - Ollama muss dann installiert und ein Modell geladen sein.

## Dateien

| Datei | Zweck |
|---|---|
| `start.bat` | Doppelklick: startet Server + Browser |
| `werkbank_server.py` | lokaler Server (127.0.0.1), fuehrt Python/PowerShell aus |
| `glaeserner-agent.html` | die Oberflaeche (auch ohne Server als reine Browser-Datei nutzbar) |
| `.env.example` | Vorlage fuer den Schluessel: nach `.env` kopieren |
| `auftraege.csv` | echte Datenbasis der Auftraege/Bestaende |
| `glaeserner_agent.py`, `agent_web.py` | aeltere, einfache Terminal-/Web-Variante (ohne Code-Ausfuehrung) |

## Benoetigt

Nur Python (Standardbibliothek, keine Zusatzpakete). Getestet mit Python 3.13/3.14.
