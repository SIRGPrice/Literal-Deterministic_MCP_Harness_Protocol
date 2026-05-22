import json
from pathlib import Path

from literal.cli import main
from literal.prompt import PromptCacheBuilder
from literal.registry import CapabilityRegistry
from literal.state import AtomicStateStore


def test_state_store_persists_atomically(tmp_path: Path):
    path = tmp_path / "state.json"
    store = AtomicStateStore(path, initial_state={"Workspace lights": {"status": "inactive"}})

    store.apply("Workspace lights", "turn_on", {"level": "high"})

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["revision"] == 1
    assert loaded["targets"]["Workspace lights"]["level"] == "high"


def test_prompt_builder_uses_compact_catalog():
    registry = CapabilityRegistry(
        catalog={
            "actions": {"turn_on": {"verbs": ["turn on"]}},
            "capabilities": {"Workspace lights": {"actions": ["turn_on"], "parameters": {}}},
            "groups": {},
            "scenarios": {},
        }
    )

    prompt = PromptCacheBuilder(registry).build()

    assert "Workspace lights" in prompt
    assert "invoke(target, action, parameters)" in prompt
    assert len(prompt) < 1500


def test_cli_init_and_doctor(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 0
    assert (tmp_path / "literal.catalog.json").exists()
    assert (tmp_path / "literal.policy.json").exists()
    assert main(["doctor"]) == 0


def test_cli_dev_can_prepare_missing_config(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    catalog = tmp_path / ".literal" / "catalog.json"
    policy = tmp_path / ".literal" / "policy.json"

    from literal.cli import _copy_template

    _copy_template("catalog.smart-office.json", catalog, force=False)
    _copy_template("policy.default.json", policy, force=False)

    assert catalog.exists()
    assert policy.exists()
