import sys

import pytest


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


def test_codex_app_server_requires_break_mode_for_mcp_init(monkeypatch, tmp_path):
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
            "--loop",
            "--backend=codex_app_server",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        cli.run()

    assert exc.value.code == 1
