# -*- coding: utf-8 -*-
"""
Glaeserner Agent - Web-Oberflaeche.
Startet einen kleinen lokalen Webserver und oeffnet den Browser. Sie tippen eine
Frage, der Agent laeuft die Schleife, und JEDER Schritt (Gedanke, Werkzeugaufruf,
Beobachtung, Runde) erscheint live im Browser.

Start:
    python agent_web.py
    (Browser oeffnet sich; sonst http://127.0.0.1:8760 aufrufen)

Nutzt denselben Kern wie glaeserner_agent.py (agenten_schritte). Reines Python,
keine Zusatzpakete. LLM: OpenAI-kompatibel (DeepInfra-Cloud ueber .env-Schluessel);
auf lokal (Ollama) umstellbar in glaeserner_agent.py unter KONFIG.
"""
import json, urllib.parse, webbrowser, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import glaeserner_agent as ag

PORT = 8760

SEITE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Glaeserner Agent</title>
<style>
  :root{--blau:#1F497D;--badge:#4F81BD;--panel:#DCE6F1;--grau:#808080;--bg:#F4F6FA;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:#1a1a1a;font-family:"Segoe UI",Arial,sans-serif}
  header{background:linear-gradient(135deg,#242852,#1C366B 55%,#4A66AC);color:#fff;padding:18px 24px}
  header h1{margin:0;font-size:22px;font-weight:700}
  header p{margin:4px 0 0;font-size:13px;color:#C7D7EF}
  .wrap{max-width:900px;margin:0 auto;padding:20px 24px 60px}
  .frage-zeile{display:flex;gap:10px;margin:18px 0}
  #frage{flex:1;padding:12px 14px;font-size:16px;font-family:inherit;border:1px solid #BFCEE6;border-radius:8px}
  #frage:focus{outline:none;border-color:var(--blau);box-shadow:0 0 0 3px rgba(31,73,125,.15)}
  button{padding:12px 20px;font-size:16px;font-weight:600;font-family:inherit;background:var(--blau);color:#fff;border:none;border-radius:8px;cursor:pointer}
  button:disabled{background:#9aa9c4;cursor:default}
  .bsp{font-size:13px;color:var(--grau);margin:0 0 6px}
  .bsp a{color:var(--blau);cursor:pointer;text-decoration:underline;margin-right:14px}
  #log{margin-top:14px}
  .runde{margin:18px 0 6px;font-weight:700;color:var(--blau);border-top:1px solid #dde3ee;padding-top:10px}
  .kontext{font-size:12px;color:var(--grau);font-weight:400;margin-left:8px}
  .schritt{padding:8px 12px;border-radius:8px;margin:6px 0;font-size:14px;line-height:1.45}
  .lab{display:inline-block;min-width:82px;font-weight:700;font-size:12px;letter-spacing:.03em}
  .denken{background:#fff;border:1px solid #e2e8f2}
  .denken pre{margin:6px 0 0;font-family:"Cascadia Code",Consolas,monospace;font-size:13px;white-space:pre-wrap;color:#333}
  .aktion{background:var(--panel)} .aktion .lab{color:var(--blau)}
  .aktion code{font-family:"Cascadia Code",Consolas,monospace;font-weight:700;color:var(--blau)}
  .beob{background:#ECF7F0;border:1px solid #cfe9d8} .beob .lab{color:#0E7A4B}
  .antwort{background:var(--blau);color:#fff;font-size:18px;font-weight:700;padding:16px 18px}
  .fehler{background:#FDECEA;border:1px solid #f5c2bd;color:#9b2c22}
  .frg{font-weight:700;font-size:16px;margin:6px 0 2px}
</style></head>
<body>
<header><h1>Glaeserner Agent</h1><p>Tippen Sie eine Frage - Sie sehen jeden Gedanken, jeden Werkzeugaufruf und jede Beobachtung.</p></header>
<div class="wrap">
  <p class="bsp">Beispiele:
    <a onclick="setF('Ist Auftrag 4711 termingerecht?')">Ist Auftrag 4711 termingerecht?</a>
    <a onclick="setF('Ist Auftrag 4712 termingerecht?')">Ist Auftrag 4712 termingerecht?</a>
  </p>
  <div class="frage-zeile">
    <input id="frage" placeholder="Ihre Frage ..." autofocus>
    <button id="btn" onclick="start()">Fragen</button>
  </div>
  <div id="log"></div>
</div>
<script>
  var es=null;
  function setF(t){document.getElementById('frage').value=t;document.getElementById('frage').focus();}
  function el(cls,html){var d=document.createElement('div');d.className=cls;d.innerHTML=html;document.getElementById('log').appendChild(d);window.scrollTo(0,document.body.scrollHeight);return d;}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function fertig(){document.getElementById('btn').disabled=false;if(es){es.close();es=null;}}
  function start(){
    var q=document.getElementById('frage').value.trim(); if(!q)return;
    document.getElementById('log').innerHTML='';
    document.getElementById('btn').disabled=true;
    el('frg','Frage: '+esc(q));
    es=new EventSource('/run?frage='+encodeURIComponent(q));
    es.onmessage=function(ev){
      var s; try{s=JSON.parse(ev.data);}catch(e){return;}
      if(s.art==='runde') el('runde','Runde '+s.n+'<span class="kontext">Kontext: '+s.kontext+' Nachrichten an das LLM</span>');
      else if(s.art==='denken') el('schritt denken','<span class="lab">[runter]</span> das Modell denkt:<pre>'+esc(s.text)+'</pre>');
      else if(s.art==='aktion') el('schritt aktion','<span class="lab">[aktion]</span> Werkzeug: <code>'+esc(s.werkzeug)+'('+esc(String(s.argument))+')</code>');
      else if(s.art==='beobachtung') el('schritt beob','<span class="lab">[beob]</span> '+esc(s.text));
      else if(s.art==='antwort'){el('schritt antwort','&#9658; '+esc(s.text));}
      else if(s.art==='fehler'){el('schritt fehler','Fehler: '+esc(s.text));}
      else if(s.art==='ende'){el('schritt fehler',esc(s.text));}
      else if(s.art==='fertig'){fertig();}
    };
    es.onerror=function(){fertig();};
  }
  document.getElementById('frage').addEventListener('keydown',function(e){if(e.key==='Enter')start();});
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            body = SEITE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/run":
            frage = urllib.parse.parse_qs(u.query).get("frage", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            schluessel = ag.lade_schluessel()
            try:
                if not schluessel:
                    self._sse({"art": "fehler", "text": "Kein OPENAI_API_KEY in .env/Umgebung."})
                else:
                    for schritt in ag.agenten_schritte(frage, schluessel):
                        self._sse(schritt)
            except Exception as e:
                try:
                    self._sse({"art": "fehler", "text": str(e)})
                except Exception:
                    pass
            try:
                self._sse({"art": "fertig"})
            except Exception:
                pass
            return
        self.send_response(404)
        self.end_headers()

    def _sse(self, obj):
        self.wfile.write(("data: " + json.dumps(obj, ensure_ascii=False) + "\n\n").encode("utf-8"))
        self.wfile.flush()


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Glaeserner Agent (Web) laeuft: {url}")
    print("Beenden mit Strg+C.")
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
