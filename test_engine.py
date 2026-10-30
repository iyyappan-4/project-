from simulation.engine import TrafficEngine

def test_engine():
    e=TrafficEngine(); s=e.tick(); assert 'congestion' in s
