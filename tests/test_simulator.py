from engine.simulator import EngineSimulator

def test_power_increases_with_rpm():
    sim = EngineSimulator()
    sim.rpm = 3000
    low_hp, *_ = sim.step()
    sim.rpm = 6000
    high_hp, *_ = sim.step()
    assert high_hp > low_hp
