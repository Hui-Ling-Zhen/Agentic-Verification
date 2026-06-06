import sys
from types import ModuleType

import pytest


def test_official_contract_is_headless_by_default():
    from veriagent.runtime_contract import official_launch_args_string

    args = official_launch_args_string().split()

    assert "--mcp-server-no-file-tools" in args
    assert "--loop" in args
    assert "--backend=codex_app_server" in args
    assert "-hm" not in args
    assert "--tui" not in args


def test_codex_app_server_requires_loop(monkeypatch, tmp_path):
    from veriagent import cli

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dut = workspace / "Adder"
    dut.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "veriagent",
            str(workspace),
            "Adder",
            "--config",
            "examples/01-baseline/workflow/default.yaml",
            "--mcp-server-no-file-tools",
            "--backend=codex_app_server",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli.run()

    assert exc.value.code == 1


def test_codex_app_server_cli_does_not_enqueue_runtime_lifecycle_commands(monkeypatch, tmp_path):
    from veriagent import cli

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dut = workspace / "Adder"
    dut.mkdir()
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text("stage: []\n", encoding="utf-8")

    captured = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def set_break(self, value):
            captured["break"] = value

        def run(self):
            captured["run"] = True

    fake_module = ModuleType("veriagent.verify_agent")
    fake_module.VerifyAgent = FakeAgent
    monkeypatch.setitem(sys.modules, "veriagent.verify_agent", fake_module)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "veriagent",
            str(workspace),
            "Adder",
            "--config",
            str(workflow),
            "--mcp-server-no-file-tools",
            "--loop",
            "--backend=codex_app_server",
        ],
    )

    cli.run()

    assert captured["run"] is True
    assert not any(str(cmd).startswith("start_mcp_server") for cmd in captured["init_cmd"])
    assert not any(str(cmd).startswith("loop") for cmd in captured["init_cmd"])
    assert "break" not in captured


def test_codex_app_server_allows_headless_supervised_loop(monkeypatch, tmp_path):
    from veriagent import cli

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dut = workspace / "Adder"
    dut.mkdir()
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text("stage: []\n", encoding="utf-8")

    captured = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def set_break(self, value):
            captured["break"] = value

        def run(self):
            captured["run"] = True

    fake_module = ModuleType("veriagent.verify_agent")
    fake_module.VerifyAgent = FakeAgent
    monkeypatch.setitem(sys.modules, "veriagent.verify_agent", fake_module)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "veriagent",
            str(workspace),
            "Adder",
            "--config",
            str(workflow),
            "--mcp-server-no-file-tools",
            "--loop",
            "--backend=codex_app_server",
        ],
    )

    cli.run()

    assert captured["run"] is True
    assert "break" not in captured
