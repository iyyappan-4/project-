from flask import Flask, render_template, jsonify, request
from simulation.engine import TrafficEngine

app = Flask(__name__)
engine = TrafficEngine()

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/state")
def state():
    return jsonify(engine.state())

@app.post("/api/control")
def control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action == "start": engine.running = True
    elif action == "stop": engine.running = False
    elif action == "reset": engine.reset()
    elif action == "demo": engine.demo_mode = not engine.demo_mode
    elif action == "accident": engine.trigger_accident(data.get("road", "E"))
    elif action == "clear_accident": engine.clear_accident()
    elif action == "emergency": engine.add_emergency(data.get("road", "N"), data.get("kind", "AMBULANCE"))
    elif action == "density": engine.density = max(10, min(100, int(data.get("value", 55))))
    elif action == "inject": engine.inject(data.get("road", "N"), int(data.get("count", 5)))
    elif action == "ai": engine.ai_enabled = bool(data.get("enabled", True))
    return jsonify(engine.state())

@app.post("/api/tick")
def tick():
    return jsonify(engine.tick())

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5055)
