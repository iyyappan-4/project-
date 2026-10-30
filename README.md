# ATLAS V2 — AI Traffic Command Center

A laptop-only, hackathon-ready AI traffic management digital twin.

## Run
Windows:
1. Extract this ZIP.
2. Open the folder in VS Code.
3. Open Terminal.
4. Run:
   `python -m pip install -r requirements.txt`
5. Run:
   `python app.py`
6. Open http://127.0.0.1:5000

## Demo sequence
1. Click RUN AI.
2. Set demand to HIGH/EXTREME.
3. Use the DIRECTIONAL TRAFFIC CONTROL cards to inject any number of vehicles into North/East/South/West.
4. The selected direction immediately updates vehicle count and congestion %, and injected vehicles enter the same movement/queue simulation so the AI can respond to the changed traffic pressure.
5. Trigger AMBULANCE on North.
6. Watch priority override.
7. Trigger an accident on West.
8. Clear it and show recovery.
9. Use DEMO MODE for an automatic showcase.

No hardware, camera, paid API, or external database is required.
