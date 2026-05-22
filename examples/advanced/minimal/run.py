"""Minimal example: build a Literal harness from an in-memory catalog dict."""

from literal import Harness, Registry

catalog = {
    "actions": {
        "turn_on": {"verbs": ["turn on", "enable"]},
        "turn_off": {"verbs": ["turn off", "disable"]},
    },
    "capabilities": {
        "Workspace lights": {
            "actions": ["turn_on", "turn_off"],
            "aliases": ["desk lights"],
            "state": {"status": "inactive"},
        }
    },
    "groups": {},
    "scenarios": {},
    "policies": {"fuzzy_cutoff": 0.62},
}

h = Harness(Registry(catalog))

print(h.simulate("turn on desk lights"))
print(h.inspect("Workspace lights"))
