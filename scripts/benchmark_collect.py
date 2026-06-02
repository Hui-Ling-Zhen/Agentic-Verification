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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from veriagent.util.benchmark import find_manifest_files, load_json_file  # noqa: E402


CSV_FIELDS = [
    "dut",
    "workflow_config",
    "backend",
    "all_completed",
    "stage_index",
    "stages_total",
    "stages_passed",
    "stages_skipped",
    "duration_sec",
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

    os.makedirs(os.path.dirname(os.path.abspath(os.path.join(ROOT, args.out))), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(os.path.join(ROOT, args.json))), exist_ok=True)

    csv_path = os.path.join(ROOT, args.out)
    json_path = os.path.join(ROOT, args.json)

    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})

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
