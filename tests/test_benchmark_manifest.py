#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.util.benchmark import build_run_manifest


def test_run_manifest_v3_includes_policy_audit_fields(tmp_path):
    manifest = build_run_manifest(
        workspace=str(tmp_path),
        dut_name="Demo",
        workflow_config="examples/01-baseline/workflow/default.yaml",
        backend="codex_app_server",
        backend_class="veriagent.abackend.codex_sdk.CodexAppServerBackend",
        backend_status="official",
        backend_legacy=False,
        version="test",
        seed=None,
        stage_index=0,
        all_completed=False,
        time_begin=None,
        time_end=None,
        stages_info={
            0: {
                "name": "spec_stage",
                "is_completed": False,
                "fail_count": 1,
                "reference_files": {"Guide_Doc/spec.md": True},
                "output_files": ["unity_test/test_demo.py"],
                "skill_usage": {"ut": {"read": True}},
                "journal": "stage note",
                "checker_feedback": "pytest failed",
            }
        },
        is_agent_exit=False,
        run_status="starting",
        last_turn={
            "thread_id": "thread-1",
            "turn_id": "turn-1",
            "status": "failed",
            "turn_context": {"stage_id": "spec_stage"},
            "turn_context_file": str(tmp_path / ".veriagent" / "codex_turn_context.json"),
            "turn_trace": {"commands": [{"command": "rm -rf tmp"}]},
            "supervisor_signals": [
                {"kind": "potentially_risky_command", "severity": "warning"},
                {"kind": "protected_input_touched", "severity": "error"},
            ],
        },
        policy={
            "codex_config_file": str(tmp_path / ".codex" / "config.toml"),
            "codex_bin": "/usr/local/bin/codex",
            "codex_metadata": {"serverInfo": {"name": "codex", "version": "test"}},
            "sandbox_mode": "workspace-write",
            "turn_sandbox_policy": {"type": "workspaceWrite"},
            "network_access": "disabled",
            "writable_roots": [str(tmp_path)],
            "protected_inputs": [str(tmp_path / "Demo")],
            "policy_enforcement": "codex_sandbox_os_permissions",
            "veriagent_policy": "audit_hint_only",
            "codex_write_policy": "workspace_only",
            "codex_command_policy": "codex_sandbox",
            "policy_warnings": ["example warning"],
        },
    )

    assert manifest["schema_version"] == "3"
    assert manifest["backend_status"] == "official"
    assert manifest["backend_legacy"] is False
    assert manifest["run_status"] == "starting"
    assert manifest["stage_trace"][0]["stage_id"] == "spec_stage"
    assert manifest["stage_trace"][0]["checker_feedback"] == "pytest failed"
    assert manifest["codex_turn_total"] == 1
    assert manifest["checker_retry_total"] == 1
    assert manifest["stage_recovery_count"] == 0
    assert manifest["skill_usage_summary"]["ut"]["read"] == 1
    assert manifest["tool_action_trace"]["commands"][0]["command"] == "rm -rf tmp"
    assert manifest["codex_turn_context"]["stage_id"] == "spec_stage"
    assert manifest["codex_turn_context_file"].endswith("codex_turn_context.json")
    assert manifest["codex_turn_trace"]["commands"][0]["command"] == "rm -rf tmp"
    assert manifest["codex_supervisor_signals"][1]["severity"] == "error"
    assert manifest["sandbox_mode"] == "workspace-write"
    assert manifest["codex_bin"] == "/usr/local/bin/codex"
    assert manifest["codex_metadata"]["serverInfo"]["version"] == "test"
    assert manifest["turn_sandbox_policy"] == {"type": "workspaceWrite"}
    assert manifest["network_access"] == "disabled"
    assert manifest["writable_roots"] == [str(tmp_path)]
    assert manifest["protected_inputs"] == [str(tmp_path / "Demo")]
    assert manifest["policy_enforcement"] == "codex_sandbox_os_permissions"
    assert manifest["veriagent_policy"] == "audit_hint_only"
    assert manifest["codex_write_policy"] == "workspace_only"
    assert manifest["codex_command_policy"] == "codex_sandbox"
    assert manifest["policy_warnings"] == ["example warning"]
