#!/usr/bin/env python3
# coding=utf-8
"""Generate synthetic A/B/C ablation manifests for the runtime-demo case.

This script does not call Codex. It fixes the comparison shape first, so the
same benchmark/report pipeline can later be fed by real VeriAgent runs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


SCENARIOS: list[dict[str, Any]] = [
    {
        "ablation_mode": "A_supervised",
        "backend": "codex_app_server",
        "backend_status": "official",
        "backend_legacy": False,
        "all_completed": True,
        "stages_passed": 4,
        "stages_total": 4,
        "checker_retry_total": 1,
        "codex_turn_total": 5,
        "stage_recovery_count": 1,
        "duration_sec": 240.0,
        "codex_failure_reason": None,
        "artifact_quality_score": 0.93,
        "artifact_quality_notes": "Complete plan/basic-info/functions-checks artifacts with structured journal and checker recovery.",
        "signals": [
            {"kind": "plan_missing_stage_context", "severity": "warning", "message": "Plan missed current stage once and was corrected."}
        ],
        "commands": ["python -m pytest unity_test/tests/test_adder_basic.py"],
    },
    {
        "ablation_mode": "B_raw_codex",
        "backend": "raw_codex_prompt",
        "backend_status": "external_baseline",
        "backend_legacy": True,
        "all_completed": False,
        "stages_passed": 2,
        "stages_total": 4,
        "checker_retry_total": 0,
        "codex_turn_total": 3,
        "stage_recovery_count": 0,
        "duration_sec": 180.0,
        "codex_failure_reason": "No outer Check/Complete loop; artifacts were plausible but not stage-gated.",
        "artifact_quality_score": 0.62,
        "artifact_quality_notes": "Generated readable notes, but no enforced journal schema or checker-driven recovery.",
        "signals": [],
        "commands": ["codex exec <raw prompt>"],
    },
    {
        "ablation_mode": "C_legacy_codex_exec",
        "backend": "codex",
        "backend_status": "legacy",
        "backend_legacy": True,
        "all_completed": False,
        "stages_passed": 2,
        "stages_total": 4,
        "checker_retry_total": 2,
        "codex_turn_total": 0,
        "stage_recovery_count": 0,
        "duration_sec": 310.0,
        "codex_failure_reason": "Legacy backend lacks SDK thread/turn/event contract; supervisor could not recover from opaque Codex state.",
        "artifact_quality_score": 0.55,
        "artifact_quality_notes": "Some artifacts exist, but turn trace and recovery context are missing.",
        "signals": [
            {"kind": "legacy_backend_opaque", "severity": "warning", "message": "No structured Codex event stream."}
        ],
        "commands": ["codex exec <veriagent prompt>"],
    },
]


def _now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).replace(microsecond=0).isoformat()


def _manifest_for_scenario(base_dir: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    workspace = base_dir / scenario["ablation_mode"]
    stage_trace = [
        {
            "stage_id": "requirement_analysis_and_planning",
            "completed": scenario["stages_passed"] >= 1,
            "skipped": False,
            "fail_count": 0,
            "reference_files": {"Adder/README.md": True},
            "output_files": ["unity_test/Adder_verification_needs_and_plan.md"],
            "observed_files": ["Adder/README.md"],
            "skill_usage": {},
            "journal": {
                "plan": "Read Adder requirements and define verification scope.",
                "evidence_read": ["Adder/README.md"],
                "changes_made": ["unity_test/Adder_verification_needs_and_plan.md"],
                "checker_result": "markdown_file_check passed" if scenario["stages_passed"] >= 1 else "not checked",
                "next_risk": "Need function/check decomposition.",
            } if scenario["ablation_mode"] == "A_supervised" else None,
            "checker_feedback": None,
        },
        {
            "stage_id": "dut_function_understanding",
            "completed": scenario["stages_passed"] >= 2,
            "skipped": False,
            "fail_count": 0,
            "reference_files": {"Adder/README.md": True, "Adder/__init__.py": scenario["ablation_mode"] == "A_supervised"},
            "output_files": ["unity_test/Adder_basic_info.md"],
            "observed_files": ["Adder/README.md"],
            "skill_usage": {},
            "journal": None,
            "checker_feedback": None,
        },
        {
            "stage_id": "functional_specification_analysis",
            "completed": scenario["stages_passed"] >= 3,
            "skipped": False,
            "fail_count": scenario["checker_retry_total"],
            "reference_files": {"Guide_Doc/dut_functions_and_checks.md": scenario["ablation_mode"] == "A_supervised"},
            "output_files": ["unity_test/Adder_functions_and_checks.md"],
            "observed_files": ["Guide_Doc/dut_functions_and_checks.md"] if scenario["ablation_mode"] == "A_supervised" else [],
            "skill_usage": {"functions-and-checks": {"list": True, "read": scenario["ablation_mode"] == "A_supervised", "use": scenario["ablation_mode"] == "A_supervised"}},
            "journal": None,
            "checker_feedback": "Label structure failed once, then recovered." if scenario["stage_recovery_count"] else scenario["codex_failure_reason"],
        },
        {
            "stage_id": "test_generation",
            "completed": scenario["stages_passed"] >= 4,
            "skipped": False,
            "fail_count": 0,
            "reference_files": {},
            "output_files": ["unity_test/tests/test_adder_basic.py"],
            "observed_files": [],
            "skill_usage": {},
            "journal": None,
            "checker_feedback": None,
        },
    ]
    turn_trace = {
        "plans": [{"text": "Complete Adder verification stages with Check/Complete gates."}],
        "diffs": [{"file_paths": ["unity_test/Adder_functions_and_checks.md"]}],
        "commands": [{"command": cmd} for cmd in scenario["commands"]],
        "errors": [],
        "approvals": [],
        "mcp_startup": [{"status": "healthy"}] if scenario["ablation_mode"] == "A_supervised" else [],
        "unknown_events": [],
    }
    return {
        "schema_version": "3",
        "project": "Agentic-Verification",
        "dut": "Adder",
        "ablation_mode": scenario["ablation_mode"],
        "workspace": str(workspace.resolve()),
        "workflow_config": "examples/01-baseline/workflow/default.yaml",
        "backend": scenario["backend"],
        "backend_class": "synthetic.ablation",
        "backend_status": scenario["backend_status"],
        "backend_legacy": scenario["backend_legacy"],
        "version": "synthetic",
        "seed": 42,
        "stage_index": min(scenario["stages_passed"], scenario["stages_total"]),
        "all_completed": scenario["all_completed"],
        "is_agent_exit": scenario["all_completed"],
        "run_status": "simulated_completed" if scenario["all_completed"] else "simulated_incomplete",
        "stages_total": scenario["stages_total"],
        "stages_passed": scenario["stages_passed"],
        "stages_skipped": 0,
        "stage_trace": stage_trace,
        "codex_turn_total": scenario["codex_turn_total"],
        "checker_retry_total": scenario["checker_retry_total"],
        "stage_recovery_count": scenario["stage_recovery_count"],
        "skill_usage_summary": {
            "functions-and-checks": {
                "list": 1,
                "read": 1 if scenario["ablation_mode"] == "A_supervised" else 0,
                "use": 1 if scenario["ablation_mode"] == "A_supervised" else 0,
            }
        },
        "tool_action_trace": {
            "commands": turn_trace["commands"],
            "diffs": turn_trace["diffs"],
            "approvals": [],
            "mcp_startup": turn_trace["mcp_startup"],
        },
        "duration_sec": scenario["duration_sec"],
        "started_at": _now(),
        "updated_at": _now(),
        "codex_thread_id": "synthetic-thread" if scenario["ablation_mode"] == "A_supervised" else None,
        "codex_turn_id": "synthetic-turn-5" if scenario["ablation_mode"] == "A_supervised" else None,
        "codex_turn_status": "completed" if scenario["all_completed"] else "failed",
        "codex_token_usage": {"total": {"totalTokens": 12000 if scenario["ablation_mode"] == "A_supervised" else 9000}},
        "codex_mcp_tool_calls": 8 if scenario["ablation_mode"] == "A_supervised" else 0,
        "codex_file_changes": 4 if scenario["all_completed"] else 2,
        "codex_failure_reason": scenario["codex_failure_reason"],
        "codex_event_log": str(workspace / ".veriagent" / "codex_events.jsonl"),
        "codex_approval_requests": [],
        "codex_turn_context": {
            "stage_id": "functional_specification_analysis",
            "checker_feedback": ["Label structure failed once, then recovered."] if scenario["stage_recovery_count"] else [],
            "recovery_context": {"status": "failed"} if scenario["stage_recovery_count"] else {},
        },
        "codex_turn_context_file": str(workspace / ".veriagent" / "codex_turn_context.json"),
        "codex_turn_trace": turn_trace,
        "codex_supervisor_signals": scenario["signals"],
        "sandbox_mode": "workspace-write" if scenario["ablation_mode"] == "A_supervised" else None,
        "network_access": "disabled",
        "protected_inputs": [str(workspace / "Adder"), str(workspace / "Adder_RTL")],
        "policy_enforcement": "codex_sandbox_os_permissions" if scenario["ablation_mode"] == "A_supervised" else "not_available",
        "artifact_quality_score": scenario["artifact_quality_score"],
        "artifact_quality_notes": scenario["artifact_quality_notes"],
    }


def write_manifests(base_dir: Path) -> list[dict[str, Any]]:
    manifests = []
    for scenario in SCENARIOS:
        manifest = _manifest_for_scenario(base_dir, scenario)
        manifest_dir = Path(manifest["workspace"]) / ".veriagent"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        event_log = Path(manifest["codex_event_log"])
        event_log.write_text(
            json.dumps(
                {
                    "kind": "synthetic_ablation",
                    "status": scenario["ablation_mode"],
                    "raw": {"note": "Synthetic event stream placeholder"},
                    "ts": _now(),
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        manifests.append(manifest)
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic A/B/C ablation manifests")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "output" / "ablation_simulated"),
        help="Directory where simulated workspaces are written",
    )
    parser.add_argument(
        "--summary",
        default=str(ROOT / "benchmark" / "ablation_simulated.json"),
        help="Compact comparison JSON path",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    manifests = write_manifests(out_dir)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = [
        {
            "ablation_mode": item["ablation_mode"],
            "all_completed": item["all_completed"],
            "stages_passed": item["stages_passed"],
            "checker_retry_total": item["checker_retry_total"],
            "codex_turn_total": item["codex_turn_total"],
            "stage_recovery_count": item["stage_recovery_count"],
            "duration_sec": item["duration_sec"],
            "artifact_quality_score": item["artifact_quality_score"],
            "failure_reason": item["codex_failure_reason"],
        }
        for item in manifests
    ]
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(manifests)} simulated manifests under {out_dir}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
