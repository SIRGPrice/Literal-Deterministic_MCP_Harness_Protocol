from literal.harness import ToolHarness
from literal.registry import CapabilityRegistry
from literal.router import DirectRoute


def registry() -> CapabilityRegistry:
    return CapabilityRegistry(
        catalog={
            "actions": {
                "turn_on": {"verbs": ["turn on", "enable"]},
                "turn_off": {"verbs": ["turn off", "disable"]},
                "set": {"verbs": ["set", "adjust"]},
                "unlock": {"verbs": ["unlock"], "confirmation_required": True},
            },
            "capabilities": {
                "Lobby lights": {
                    "aliases": ["front lights"],
                    "actions": ["turn_on", "turn_off", "set"],
                    "parameters": {"level": {"values": ["low", "medium", "high"]}},
                    "state": {"status": "inactive", "level": "medium"},
                },
                "Server room door": {
                    "aliases": ["data room door"],
                    "actions": ["unlock"],
                    "parameters": {},
                    "state": {"status": "locked"},
                },
            },
            "groups": {
                "Public areas": {
                    "members": ["Lobby lights"],
                    "actions": ["turn_on", "turn_off"],
                    "aliases": ["front of house"],
                }
            },
            "scenarios": {
                "Opening mode": {
                    "aliases": ["morning mode"],
                    "steps": [
                        {"target": "Lobby lights", "action": "set", "parameters": {"level": "high"}},
                        {"target": "Public areas", "action": "turn_on", "parameters": {}},
                    ],
                }
            },
        },
        policy={"fuzzy_cutoff": 0.6, "scenario_verbs": ["run"], "inspect_verbs": ["status"]},
    )


def test_router_fast_path_direct_command():
    harness = ToolHarness(registry())

    route = harness.router.classify("turn on front lights")

    assert isinstance(route, DirectRoute)
    assert route.kind == "invoke"
    assert route.target == "Lobby lights"
    assert route.action == "turn_on"


def test_harness_simulates_direct_command_and_updates_state():
    harness = ToolHarness(registry())

    result = harness.simulate("turn on front lights")

    assert result["ok"] is True
    assert result["route"] == "invoke"
    assert harness.inspect("Lobby lights")["state"]["status"] == "active"


def test_harness_routes_inspection():
    harness = ToolHarness(registry())

    result = harness.simulate("status front lights")

    assert result["ok"] is True
    assert result["route"] == "inspect"
    assert result["target"] == "Lobby lights"


def test_harness_routes_scenario():
    harness = ToolHarness(registry())

    result = harness.simulate("run morning mode")

    assert result["ok"] is True
    assert result["route"] == "scenario"
    assert result["scenario"] == "Opening mode"
    assert len(result["steps"]) == 2


def test_confirmation_prevents_unsafe_execution():
    harness = ToolHarness(registry())

    result = harness.simulate("unlock data room door")

    assert result["ok"] is False
    assert result["requires_confirmation"] is True
