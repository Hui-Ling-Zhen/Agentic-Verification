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
        version="test",
        seed=None,
        stage_index=0,
        all_completed=False,
        time_begin=None,
        time_end=None,
        stages_info={},
        is_agent_exit=False,
        policy={
            "codex_config_file": str(tmp_path / ".codex" / "config.toml"),
            "sandbox_mode": "workspace-write",
            "network_access": "disabled",
            "writable_roots": [str(tmp_path)],
            "protected_inputs": [str(tmp_path / "Demo")],
            "policy_enforcement": "codex_sandbox_os_permissions",
            "veriagent_policy": "audit_hint_only",
            "policy_warnings": ["example warning"],
        },
    )

    assert manifest["schema_version"] == "3"
    assert manifest["sandbox_mode"] == "workspace-write"
    assert manifest["network_access"] == "disabled"
    assert manifest["writable_roots"] == [str(tmp_path)]
    assert manifest["protected_inputs"] == [str(tmp_path / "Demo")]
    assert manifest["policy_enforcement"] == "codex_sandbox_os_permissions"
    assert manifest["veriagent_policy"] == "audit_hint_only"
    assert manifest["policy_warnings"] == ["example warning"]
