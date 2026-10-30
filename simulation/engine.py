import random, time
from collections import deque

ROADS = ["N", "E", "S", "W"]
NAMES = {"N": "North", "E": "East", "S": "South", "W": "West"}
STOP_LINE = 92.0
EXIT_POINT = 122.0
MIN_GAP = 10.0

class TrafficEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.running = True
        self.ai_enabled = True
        self.demo_mode = False
        self.density = 45
        self.tick_no = 0
        self.phase = "N"
        self.phase_elapsed = 0
        self.green_time = 20
        self.total_throughput = 0
        self.total_decisions = 0
        self.total_emergency = 0
        self.accident_road = None
        self.emergency = None
        self.emergency_eta = 0
        self.next_vehicle_id = 1
        self.logs = deque(maxlen=16)
        self.waiting_history = deque(maxlen=40)
        self.congestion_history = deque(maxlen=40)
        self.roads = {}
        initial = {"N": 5, "E": 4, "S": 5, "W": 4}
        for r in ROADS:
            self.roads[r] = {
                "queue": 0, "speed": random.randint(28, 36), "wait": random.randint(3, 7),
                "flow": 0, "score": 0.0, "vehicles": [], "injected": 0,
            }
            for i in range(initial[r]):
                self._create_vehicle(r, position=20 + i * 14)
            self._refresh_road_metrics(r)
        self.log("SYSTEM", "ATLAS V2 initialized — AI control online")

    def log(self, tag, msg):
        self.logs.appendleft({"time": time.strftime("%H:%M:%S"), "tag": tag, "msg": msg})

    def _create_vehicle(self, road, position=None, vehicle_type="CAR"):
        v = {"id": self.next_vehicle_id, "position": float(position if position is not None else 2),
             "speed": 0.0, "wait": 0.0, "type": vehicle_type}
        self.next_vehicle_id += 1
        self.roads[road]["vehicles"].append(v)
        return v

    def _spawn_vehicle(self, road, vehicle_type="CAR"):
        vehicles = self.roads[road]["vehicles"]
        if vehicles and min(v["position"] for v in vehicles) < MIN_GAP:
            return False
        self._create_vehicle(road, 2, vehicle_type)
        return True

    def _refresh_road_metrics(self, road):
        d = self.roads[road]
        vehicles = d["vehicles"]
        stopped = [v for v in vehicles if STOP_LINE - 6 <= v["position"] <= STOP_LINE + 2]
        d["queue"] = len(stopped) if self.phase != road else max(0, len(stopped) - 1)
        d["flow"] = len(vehicles)
        if vehicles:
            moving = [v["speed"] for v in vehicles if v["speed"] > 0.1]
            d["speed"] = int(round(sum(moving) / len(moving))) if moving else 8
            d["wait"] = round(sum(v["wait"] for v in vehicles) / len(vehicles), 1)
        else:
            d["speed"], d["wait"] = 35, 0.0
        # Congestion responds immediately to manual injection as well as to
        # vehicles waiting at the signal. This makes every injection visible
        # in the directional dashboard without waiting for a later tick.
        density_component = min(100.0, d["flow"] / 25.0 * 100.0)
        queue_component = min(100.0, d["queue"] / max(1, d["flow"]) * 100.0)
        d["congestion"] = round(min(100.0, density_component * 0.45 + queue_component * 0.55), 1)

    def trigger_accident(self, road):
        self.accident_road = road
        for v in self.roads[road]["vehicles"]:
            v["speed"] = 0
        self.log("INCIDENT", f"{NAMES[road]} road blockage detected")

    def clear_accident(self):
        if self.accident_road:
            self.log("RECOVERY", f"{NAMES[self.accident_road]} road reopened")
        self.accident_road = None

    def add_emergency(self, road, kind="AMBULANCE"):
        # The selected road is stored and immediately given signal priority.
        self.emergency = {"road": road, "kind": kind, "started": self.tick_no}
        self.emergency_eta = 12
        self.total_emergency += 1
        self.phase = road
        self.phase_elapsed = 0
        self.green_time = 18
        self.log("PRIORITY", f"{kind} dispatched on {NAMES[road]} approach — {NAMES[road]} GREEN")

    def inject(self, road, count):
        count = max(1, min(30, int(count)))
        vehicles = self.roads[road]["vehicles"]
        # Add injected vehicles behind the existing traffic while preserving
        # physical spacing so every injected vehicle becomes a real simulated
        # vehicle and can move, queue, contribute to congestion and influence AI.
        back = min([v["position"] for v in vehicles], default=12.0)
        added = 0
        for _ in range(count):
            pos = max(2.0, back - MIN_GAP)
            # If the approach is already packed near the entry, keep the vehicle
            # at the entry; it will naturally queue until space opens.
            if pos < 2.0:
                pos = 2.0
            self._create_vehicle(road, pos)
            added += 1
            back = pos
        self.roads[road]["injected"] += added
        self._refresh_road_metrics(road)
        self.log("INJECT", f"+{added} vehicles added to {NAMES[road]} approach")
        return added

    def choose_phase(self):
        if self.emergency:
            return self.emergency["road"], "Emergency vehicle priority"
        scores = {}
        for r in ROADS:
            d = self.roads[r]
            incident = 25 if self.accident_road == r else 0
            scores[r] = d["queue"] * 3.0 + d["wait"] * 1.6 + max(0, 45 - d["speed"]) * 0.5 + incident
            d["score"] = round(scores[r], 1)
        best = max(scores, key=scores.get)
        return best, f"{NAMES[best]} has highest pressure ({scores[best]:.1f})"

    def _advance_road(self, road):
        d = self.roads[road]
        vehicles = d["vehicles"]
        if not vehicles:
            return 0
        vehicles.sort(key=lambda v: v["position"], reverse=True)
        green = road == self.phase and self.accident_road != road
        max_speed = 9.0 if green else 0.0
        if self.emergency and self.emergency["road"] == road:
            max_speed = 11.0
        for index, vehicle in enumerate(vehicles):
            ahead = vehicles[index - 1] if index > 0 else None
            pos = vehicle["position"]
            if not green and pos >= STOP_LINE:
                speed = 0.0
            elif not green:
                target = pos + min(4.0, max(0.8, (STOP_LINE - pos) * 0.18))
                target = min(target, STOP_LINE)
                if ahead is not None:
                    target = min(target, ahead["position"] - MIN_GAP)
                speed = max(0.0, target - pos)
            else:
                target = pos + max_speed
                if ahead is not None:
                    target = min(target, ahead["position"] - MIN_GAP)
                speed = 0.0 if target < pos else min(max_speed, target - pos)
            if speed < 0.25:
                vehicle["wait"] += 1
            else:
                vehicle["wait"] = max(0.0, vehicle["wait"] - 0.25)
            vehicle["speed"] = round(speed * 4.0, 1)
            vehicle["position"] = round(pos + speed, 2)
        exited = [v for v in vehicles if v["position"] >= EXIT_POINT]
        self.total_throughput += len(exited)
        d["vehicles"] = [v for v in vehicles if v["position"] < EXIT_POINT]
        return len(exited)

    def tick(self):
        if not self.running:
            return self.state()
        self.tick_no += 1
        self.phase_elapsed += 1
        arrival_probability = 0.08 + (self.density / 100.0) * 0.32
        for r in ROADS:
            if random.random() < arrival_probability:
                self._spawn_vehicle(r)
            if self.demo_mode and random.random() < 0.12:
                self._spawn_vehicle(r)
            self._advance_road(r)
            self._refresh_road_metrics(r)
        if self.emergency:
            self.emergency_eta -= 1
            if self.emergency_eta <= 0:
                self.log("CLEAR", f"{self.emergency['kind']} passed the intersection on {NAMES[self.emergency['road']]} approach")
                self.emergency = None
        if self.phase_elapsed >= self.green_time:
            old = self.phase
            if self.ai_enabled:
                self.phase, reason = self.choose_phase()
                self.total_decisions += 1
                pressure = self.roads[self.phase]["score"]
                self.green_time = max(12, min(36, int(16 + pressure * 0.18)))
                self.log("AI", f"{NAMES[self.phase]} GREEN for {self.green_time}s — {reason}")
            else:
                idx = (ROADS.index(old) + 1) % 4
                self.phase = ROADS[idx]
                self.green_time = 18
                self.log("SIGNAL", f"Fixed cycle → {NAMES[self.phase]} GREEN")
            self.phase_elapsed = 0
        congestion = self._congestion()
        avg_wait = self._avg_wait()
        self.waiting_history.append(avg_wait)
        self.congestion_history.append(congestion)
        return self.state()

    def _congestion(self):
        values = [d["congestion"] for d in self.roads.values()]
        return round(sum(values) / len(values), 1) if values else 0.0

    def _avg_wait(self):
        all_vehicles = [v for d in self.roads.values() for v in d["vehicles"]]
        return round(sum(v["wait"] for v in all_vehicles) / len(all_vehicles), 1) if all_vehicles else 0.0

    def state(self):
        return {
            "running": self.running, "ai_enabled": self.ai_enabled, "demo_mode": self.demo_mode,
            "density": self.density, "phase": self.phase, "phase_elapsed": self.phase_elapsed,
            "green_time": self.green_time, "remaining": max(0, self.green_time - self.phase_elapsed),
            "congestion": self._congestion(), "avg_wait": self._avg_wait(),
            "vehicles": sum(len(d["vehicles"]) for d in self.roads.values()),
            "throughput": self.total_throughput, "decisions": self.total_decisions,
            "emergencies": self.total_emergency, "accident": self.accident_road,
            "emergency": self.emergency, "roads": self.roads, "logs": list(self.logs),
            "history": {"wait": list(self.waiting_history), "congestion": list(self.congestion_history)}
        }
