#!/usr/bin/env python3
# coding=utf-8
"""Collect `.veriagent/run_manifest.json` files into benchmark summaries."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_FILENAME = "run_manifest.json"


def load_json_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def find_manifest_files(search_roots: list[str]) -> list[str]:
    found: list[str] = []
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                item for item in dirnames
                if item not in {".git", "__pycache__", ".pytest_cache"}
            ]
            if MANIFEST_FILENAME in filenames and os.path.basename(dirpath) == ".veriagent":
                found.append(os.path.join(dirpath, MANIFEST_FILENAME))
    return sorted(found)


CSV_FIELDS = [
    "dut",
    "ablation_mode",
    "architecture",
    "workflow_config",
    "backend",
    "backend_class",
    "backend_status",
    "backend_legacy",
    "run_status",
    "all_completed",
    "stage_index",
    "stages_total",
    "stages_passed",
    "stages_skipped",
    "codex_turn_total",
    "checker_retry_total",
    "stage_recovery_count",
    "duration_sec",
    "codex_thread_id",
    "codex_turn_id",
    "codex_turn_status",
    "codex_mcp_tool_calls",
    "codex_file_changes",
    "codex_failure_reason",
    "codex_supervisor_signal_count",
    "codex_supervisor_error_count",
    "artifact_quality_score",
    "artifact_quality_breakdown",
    "artifact_quality_notes",
    "codex_bin",
    "sandbox_mode",
    "network_access",
    "codex_write_policy",
    "codex_command_policy",
    "policy_enforcement",
    "version",
    "workspace",
    "updated_at",
]


def _load_manifest(path: str) -> dict:
    try:
        data = load_json_file(path)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        return {"_error": str(exc), "_path": path}


def _derive_ablation_mode(row: dict) -> str:
    if row.get("ablation_mode"):
        return str(row["ablation_mode"])
    workspace = str(row.get("workspace") or "")
    for marker in (
        "A_agent_for_agent_runtime",
        "B_single_layer_llm_agent",
        "C_black_box_agent_backend",
    ):
        if marker in workspace:
            return marker
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect run manifests for benchmarking")
    parser.add_argument(
        "--scan",
        nargs="+",
        default=["output", "examples"],
        help="Directories to scan recursively (default: output examples)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join("benchmark", "summary.csv"),
        help="CSV output path (default: benchmark/summary.csv)",
    )
    parser.add_argument(
        "--json",
        default=os.path.join("benchmark", "runs.json"),
        help="JSON output path (default: benchmark/runs.json)",
    )
    args = parser.parse_args()

    scan_roots = [os.path.join(ROOT, p) if not os.path.isabs(p) else p for p in args.scan]
    manifest_paths = find_manifest_files(scan_roots)
    rows = [_load_manifest(p) for p in manifest_paths]
    rows = [r for r in rows if r and not r.get("_error")]
    for row in rows:
        row["ablation_mode"] = _derive_ablation_mode(row)
        signals = row.get("codex_supervisor_signals") or []
        if isinstance(signals, list):
            row["codex_supervisor_signal_count"] = len(signals)
            row["codex_supervisor_error_count"] = sum(
                1 for signal in signals
                if isinstance(signal, dict) and signal.get("severity") == "error"
            )
    os.makedirs(os.path.dirname(os.path.abspath(os.path.join(ROOT, args.out))), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(os.path.join(ROOT, args.json))), exist_ok=True)

    csv_path = os.path.join(ROOT, args.out)
    json_path = os.path.join(ROOT, args.json)

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            csv_row = {}
            for key in CSV_FIELDS:
                value = row.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                csv_row[key] = value
            writer.writerow(csv_row)

    payload = {
        "project": "Agentic-Verification",
        "manifest_count": len(rows),
        "manifests": rows,
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Found {len(manifest_paths)} manifest file(s), {len(rows)} valid.")
    print(f"CSV : {csv_path}")
    print(f"JSON: {json_path}")
    if not rows:
        print("Hint: run a case first, e.g. `make example-baseline`, then re-run `make benchmark`.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
