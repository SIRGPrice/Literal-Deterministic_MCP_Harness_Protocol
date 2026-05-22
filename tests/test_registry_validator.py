from literal.registry import CapabilityRegistry
from literal.validator import PolicyValidator


def sample_registry() -> CapabilityRegistry:
    return CapabilityRegistry(
        catalog={
            "actions": {
                "turn_on": {"verbs": ["turn on", "enable"]},
                "turn_off": {"verbs": ["turn off", "disable"]},
                "set": {"verbs": ["set"]},
                "unlock": {"verbs": ["unlock"], "confirmation_required": True},
            },
            "capabilities": {
                "Lobby lights": {
                    "aliases": ["front lights"],
                    "actions": ["turn_on", "turn_off", "set"],
                    "parameters": {"level": {"values": ["low", "medium", "high"]}},
                    "state": {"status": "inactive"},
                },
                "Server room door": {
                    "aliases": ["data room door"],
                    "actions": ["unlock"],
                    "parameters": {},
                },
            },
            "groups": {},
            "scenarios": {},
        },
        policy={"fuzzy_cutoff": 0.6, "confirmations": [{"target": "Server room door", "action": "unlock"}]},
    )


def test_registry_loads_targets_and_actions():
    registry = sample_registry()

    assert registry.target_names() == ["Lobby lights", "Server room door"]
    assert "turn_on" in registry.action_names()
    assert registry.valid_actions_for_target("Lobby lights") == ["turn_on", "turn_off", "set"]


def test_validator_resolves_alias_and_value():
    validator = PolicyValidator(sample_registry())

    result = validator.validate("front lights", "turn on", {"level": "hi"})

    assert result.ok
    assert result.invocation is not None
    assert result.invocation.target == "Lobby lights"
    assert result.invocation.action == "turn_on"
    assert result.invocation.parameters == {"level": "high"}
    assert any(match.method in {"alias", "fuzzy"} for match in result.matches)


def test_validator_blocks_invalid_action():
    validator = PolicyValidator(sample_registry())

    result = validator.validate("Server room door", "turn_on", {})

    assert not result.ok
    assert "not allowed" in result.message()


def test_validator_marks_confirmation_required():
    validator = PolicyValidator(sample_registry())

    result = validator.validate("data room door", "unlock", {})

    assert result.ok
    assert result.invocation is not None
    assert result.invocation.requires_confirmation
