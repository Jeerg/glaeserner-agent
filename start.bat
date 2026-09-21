@echo off
rem Startet den Werkbank-Server des glaesernen Agenten und oeffnet den Browser.
rem Doppelklick genuegt. Beenden: dieses Fenster schliessen oder Strg+C.
cd /d "%~dp0"
py -3 werkbank_server.py 2>nul || python werkbank_server.py
pause
