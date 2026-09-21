# -*- coding: utf-8 -*-
"""Werkbank-Server fuer den glaesernen Agenten.

Startet einen kleinen lokalen Server (nur 127.0.0.1), serviert die Agent-
Oberflaeche MIT eingebautem LLM-Schluessel und bietet einen Ausfuehr-Endpoint,
ueber den der Agent ECHTEN Python-/PowerShell-Code auf DIESEM Rechner ausfuehrt.
So sehen die Studierenden den Agenten wirklich am Rechner arbeiten.

Start:  Doppelklick auf  start.bat   (oder:  python werkbank_server.py)

Sicherheit: bindet ausschliesslich an 127.0.0.1 (nur dieser Rechner). Der Agent
fuehrt beliebigen Code aus - das ist hier der Lehrzweck. Zum Teilen dient die
reine glaeserner-agent.html (ohne Server und daher OHNE Code-Ausfuehrung).
Reines Python, keine Zusatzpakete. LLM-Schluessel: OPENAI_API_KEY aus der .env.
"""
import json, os, sys, subprocess, tempfile, time, webbrowser, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HIER, "..", "..", ".."))   # tbx_stzrim
HTML = os.path.join(HIER, "glaeserner-agent.html")
PORT = 8761
TIMEOUT = 20   # Sekunden je Code-Ausfuehrung


def lade_key():
    try:
        for z in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
            if z.strip().startswith("OPENAI_API_KEY="):
                return z.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def seite():
    html = open(HTML, encoding="utf-8").read()
    inject = ('<script>window.WERKBANK=true;try{'
              'var _k=' + json.dumps(lade_key()) + ';'
              'var kf=document.getElementById("key");if(kf)kf.value=_k;'
              'var s=document.getElementById("setup");if(s)s.style.display="none";'
              '}catch(e){}</script>')
    return html.replace("</body>", inject + "\n</body>", 1)


def ausfuehren(sprache, code):
    t0 = time.time()
    pfad = None
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"          # Python schreibt UTF-8 in die Pipe (Umlaute bleiben heil)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        if sprache == "powershell":
            # PowerShell-Ausgabe auf UTF-8 zwingen, sonst kommen Umlaute als Mojibake zurueck.
            code = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; " + code
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", code]
        else:
            fd, pfad = tempfile.mkstemp(suffix=".py", dir=HIER)
            os.close(fd)
            with open(pfad, "w", encoding="utf-8") as f:
                f.write(code)
            cmd = [sys.executable, pfad]
        r = subprocess.run(cmd, cwd=HIER, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=TIMEOUT)
        return {"stdout": r.stdout, "stderr": r.stderr, "exit": r.returncode,
                "dauer": int((time.time() - t0) * 1000)}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Zeitlimit (%d s) ueberschritten - abgebrochen." % TIMEOUT,
                "exit": -1, "dauer": TIMEOUT * 1000}
    except Exception as e:
        return {"stdout": "", "stderr": "Server-Fehler: " + str(e),
                "exit": -1, "dauer": int((time.time() - t0) * 1000)}
    finally:
        if pfad:
            try:
                os.remove(pfad)
            except Exception:
                pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self._send(200, "text/html; charset=utf-8", seite().encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/ausfuehren":
            try:
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except Exception:
                data = {}
            res = ausfuehren((data.get("sprache") or "python").lower(), data.get("code") or "")
            self._send(200, "application/json; charset=utf-8",
                       json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = "http://127.0.0.1:%d/" % PORT
    print("Werkbank-Server laeuft:", url)
    print("Beenden mit Strg+C.")
    if not lade_key():
        print("WARNUNG: kein OPENAI_API_KEY in .env gefunden - das Modell antwortet dann nicht.")
    try:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")


if __name__ == "__main__":
    main()
