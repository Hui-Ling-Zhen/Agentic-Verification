#!/usr/bin/env python3
# coding=utf-8
"""Generate A/B/C demo manifests for the benchmark ablation experiment.

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


ARTIFACT_QUALITY_RUBRIC: dict[str, dict[str, Any]] = {
    "stage_completion": {
        "weight": 0.30,
        "description": "How many required workflow stages completed.",
    },
    "checker_result_quality": {
        "weight": 0.20,
        "description": "Whether checkers passed or produced actionable feedback.",
    },
    "required_artifact_completeness": {
        "weight": 0.20,
        "description": "Whether required plan/basic-info/functions/checks/tests artifacts exist.",
    },
    "journal_evidence_auditability": {
        "weight": 0.15,
        "description": "Whether journal, evidence-read, and changed-artifact traces are inspectable.",
    },
    "recovery_feedback_usage": {
        "weight": 0.10,
        "description": "Whether checker feedback or supervisor signals were used to recover.",
    },
    "reproducibility_trace_quality": {
        "weight": 0.05,
        "description": "Whether manifest, turn trace, command trace, and policy trace are complete.",
    },
}


SCENARIOS: list[dict[str, Any]] = [
    {
        "ablation_mode": "A_agent_for_agent_runtime",
        "architecture": "Agent-for-Agent Runtime",
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
        "quality_components": {
            "stage_completion": 1.00,
            "checker_result_quality": 0.85,
            "required_artifact_completeness": 0.95,
            "journal_evidence_auditability": 0.95,
            "recovery_feedback_usage": 0.80,
            "reproducibility_trace_quality": 0.95,
        },
        "artifact_quality_notes": "Complete plan/basic-info/functions-checks artifacts with structured journal and checker recovery.",
        "signals": [
            {"kind": "plan_missing_stage_context", "severity": "warning", "message": "Plan missed current stage once and was corrected."}
        ],
        "commands": ["python -m pytest unity_test/tests/test_adder_basic.py"],
    },
    {
        "ablation_mode": "B_single_layer_llm_agent",
        "architecture": "Single-layer LLM/Codex Agent",
        "backend": "single_layer_codex_prompt",
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
        "quality_components": {
            "stage_completion": 0.50,
            "checker_result_quality": 0.70,
            "required_artifact_completeness": 0.85,
            "journal_evidence_auditability": 0.60,
            "recovery_feedback_usage": 0.35,
            "reproducibility_trace_quality": 0.70,
        },
        "artifact_quality_notes": "Generated readable notes, but no enforced journal schema or checker-driven recovery.",
        "signals": [],
        "commands": ["codex exec <raw prompt>"],
    },
    {
        "ablation_mode": "C_black_box_agent_backend",
        "architecture": "Black-box Agent Backend",
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
        "quality_components": {
            "stage_completion": 0.50,
            "checker_result_quality": 0.65,
            "required_artifact_completeness": 0.75,
            "journal_evidence_auditability": 0.50,
            "recovery_feedback_usage": 0.25,
            "reproducibility_trace_quality": 0.40,
        },
        "artifact_quality_notes": "Some artifacts exist, but turn trace and recovery context are missing.",
        "signals": [
            {"kind": "legacy_backend_opaque", "severity": "warning", "message": "No structured Codex event stream."}
        ],
        "commands": ["codex exec <veriagent prompt>"],
    },
]


def _now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).replace(microsecond=0).isoformat()


def _artifact_quality_breakdown(scenario: dict[str, Any]) -> dict[str, Any]:
    components = scenario["quality_components"]
    weighted: dict[str, dict[str, Any]] = {}
    total = 0.0
    for name, rubric in ARTIFACT_QUALITY_RUBRIC.items():
        component_score = float(components[name])
        weight = float(rubric["weight"])
        contribution = component_score * weight
        total += contribution
        weighted[name] = {
            "score": component_score,
            "weight": weight,
            "weighted": round(contribution, 4),
            "description": rubric["description"],
        }
    return {
        "score": round(total, 2),
        "rubric": weighted,
    }


def _manifest_for_scenario(base_dir: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    workspace = base_dir / scenario["ablation_mode"]
    quality = _artifact_quality_breakdown(scenario)
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
            } if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else None,
            "checker_feedback": None,
        },
        {
            "stage_id": "dut_function_understanding",
            "completed": scenario["stages_passed"] >= 2,
            "skipped": False,
            "fail_count": 0,
            "reference_files": {"Adder/README.md": True, "Adder/__init__.py": scenario["ablation_mode"] == "A_agent_for_agent_runtime"},
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
            "reference_files": {"Guide_Doc/dut_functions_and_checks.md": scenario["ablation_mode"] == "A_agent_for_agent_runtime"},
            "output_files": ["unity_test/Adder_functions_and_checks.md"],
            "observed_files": ["Guide_Doc/dut_functions_and_checks.md"] if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else [],
            "skill_usage": {"functions-and-checks": {"list": True, "read": scenario["ablation_mode"] == "A_agent_for_agent_runtime", "use": scenario["ablation_mode"] == "A_agent_for_agent_runtime"}},
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
        "mcp_startup": [{"status": "healthy"}] if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else [],
        "unknown_events": [],
    }
    return {
        "schema_version": "3",
        "project": "Agentic-Verification",
        "dut": "Adder",
        "ablation_mode": scenario["ablation_mode"],
        "architecture": scenario["architecture"],
        "workspace": str(workspace.resolve()),
        "workflow_config": "examples/01-baseline/workflow/default.yaml",
        "backend": scenario["backend"],
        "backend_class": "demo.ablation",
        "backend_status": scenario["backend_status"],
        "backend_legacy": scenario["backend_legacy"],
        "version": "demo",
        "seed": 42,
        "stage_index": min(scenario["stages_passed"], scenario["stages_total"]),
        "all_completed": scenario["all_completed"],
        "is_agent_exit": scenario["all_completed"],
        "run_status": "demo_completed" if scenario["all_completed"] else "demo_incomplete",
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
                "read": 1 if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else 0,
                "use": 1 if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else 0,
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
        "codex_thread_id": "demo-thread" if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else None,
        "codex_turn_id": "demo-turn-5" if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else None,
        "codex_turn_status": "completed" if scenario["all_completed"] else "failed",
        "codex_token_usage": {"total": {"totalTokens": 12000 if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else 9000}},
        "codex_mcp_tool_calls": 8 if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else 0,
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
        "sandbox_mode": "workspace-write" if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else None,
        "network_access": "disabled",
        "protected_inputs": [str(workspace / "Adder"), str(workspace / "Adder_RTL")],
        "policy_enforcement": "codex_sandbox_os_permissions" if scenario["ablation_mode"] == "A_agent_for_agent_runtime" else "not_available",
        "artifact_quality_score": quality["score"],
        "artifact_quality_breakdown": quality,
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
                    "kind": "ablation_demo",
                    "status": scenario["ablation_mode"],
                    "raw": {"note": "Demo event stream placeholder"},
                    "ts": _now(),
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        manifests.append(manifest)
    return manifests


def _write_report(path: Path, summary: list[dict[str, Any]]) -> None:
    by_mode = {item["ablation_mode"]: item for item in summary}
    a = by_mode["A_agent_for_agent_runtime"]
    b = by_mode["B_single_layer_llm_agent"]
    c = by_mode["C_black_box_agent_backend"]
    lines = [
        "# Agentic-Verification Runtime Ablation Report",
        "",
        "This report compares the two-layer **Agent-for-Agent Runtime** against a single-layer LLM/Codex agent baseline and a black-box agent backend on the same Adder task shape.",
        "",
        "## Result Table",
        "",
        "| Mode | Architecture | Completed | Stages Passed | Checker Retry | Codex Turns | Stage Recovery | Duration (s) | Artifact Quality | Failure Reason |",
        "|------|--------------|-----------|---------------|---------------|-------------|----------------|--------------|------------------|----------------|",
    ]
    for item in summary:
        lines.append(
            "| {ablation_mode} | {architecture} | {all_completed} | {stages_passed} | "
            "{checker_retry_total} | {codex_turn_total} | {stage_recovery_count} | "
            "{duration_sec} | {artifact_quality_score} | {failure_reason} |".format(
                **{**item, "failure_reason": item["failure_reason"] or ""}
            )
        )
    lines.extend([
        "",
        "## Artifact Quality Rubric",
        "",
        "`artifact_quality_score` is a weighted 0-1 score:",
        "",
        "| Component | Weight | Meaning |",
        "|-----------|--------|---------|",
    ])
    for name, rubric in ARTIFACT_QUALITY_RUBRIC.items():
        lines.append(
            f"| `{name}` | {rubric['weight']:.2f} | {rubric['description']} |"
        )
    lines.extend([
        "",
        "## Artifact Quality Breakdown",
        "",
        "| Mode | Stage | Checker | Artifacts | Journal/Evidence | Recovery | Trace | Score |",
        "|------|-------|---------|-----------|------------------|----------|-------|-------|",
    ])
    for item in summary:
        rubric = item["artifact_quality_breakdown"]["rubric"]
        lines.append(
            "| {mode} | {stage:.2f} | {checker:.2f} | {artifacts:.2f} | "
            "{journal:.2f} | {recovery:.2f} | {trace:.2f} | {score:.2f} |".format(
                mode=item["ablation_mode"],
                stage=rubric["stage_completion"]["score"],
                checker=rubric["checker_result_quality"]["score"],
                artifacts=rubric["required_artifact_completeness"]["score"],
                journal=rubric["journal_evidence_auditability"]["score"],
                recovery=rubric["recovery_feedback_usage"]["score"],
                trace=rubric["reproducibility_trace_quality"]["score"],
                score=item["artifact_quality_score"],
            )
        )
    lines.extend([
        "",
        "## Reading",
        "",
        "- `A_agent_for_agent_runtime` completes all stages and recovers after a checker failure because the outer runtime preserves checker feedback, supervisor signals, and recovery context.",
        "- `B_single_layer_llm_agent` is faster in wall-clock time, but it lacks stage gates, structured journal enforcement, and recovery context; the artifacts remain plausible but not fully verified.",
        "- `C_black_box_agent_backend` retains some outer workflow control, but the inner Codex state is opaque because `codex exec` does not expose SDK thread/turn/event signals.",
        "",
        "## Goal Coverage",
        "",
        f"- Performance/stability: A completes {a['stages_passed']}/{a['stages_total']} stages; B and C stop at {b['stages_passed']}/{b['stages_total']} and {c['stages_passed']}/{c['stages_total']}.",
        "- Flexibility: A keeps workflow/checker/skill concerns in VeriAgent, while B depends on a single prompt carrying the whole process.",
        f"- Recovery: A records {a['stage_recovery_count']} recovered stage; B and C record no structured recovery.",
        "",
        "## Demo Conclusion",
        "",
        "The main advantage is not just speed. The two-layer runtime is better at making progress auditable, failure recoverable, and stage completion measurable.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate A/B/C ablation demo manifests")
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "output" / "ablation_demo"),
        help="Directory where demo workspaces are written",
    )
    parser.add_argument(
        "--summary",
        default=str(ROOT / "benchmark" / "ablation_demo.json"),
        help="Compact comparison JSON path",
    )
    parser.add_argument(
        "--report",
        default=str(ROOT / "benchmark" / "ablation" / "report.md"),
        help="Markdown report path",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    manifests = write_manifests(out_dir)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = [
        {
            "ablation_mode": item["ablation_mode"],
            "architecture": item["architecture"],
            "all_completed": item["all_completed"],
            "stages_total": item["stages_total"],
            "stages_passed": item["stages_passed"],
            "checker_retry_total": item["checker_retry_total"],
            "codex_turn_total": item["codex_turn_total"],
            "stage_recovery_count": item["stage_recovery_count"],
            "duration_sec": item["duration_sec"],
            "artifact_quality_score": item["artifact_quality_score"],
            "artifact_quality_breakdown": item["artifact_quality_breakdown"],
            "failure_reason": item["codex_failure_reason"],
        }
        for item in manifests
    ]
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path = Path(args.report)
    _write_report(report_path, summary)
    print(f"Wrote {len(manifests)} demo manifests under {out_dir}")
    print(f"Summary: {summary_path}")
    print(f"Report : {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
