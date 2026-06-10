#!/usr/bin/env python3
# coding=utf-8
"""Check FIFO coverage-closure demo artifacts.

This checker is intentionally lightweight. It does not judge model quality; it
checks that the agent mapped every initial uncovered bin into a directed test
and a closure report.
"""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_BINS = (
    "COV-FULL-PUSH-BLOCK",
    "COV-EMPTY-POP-BLOCK",
    "COV-WRAPAROUND",
    "COV-SIMULTANEOUS-PUSH-POP",
)


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing required artifact: {path}")
    return path.read_text(encoding="utf-8")


def _assert_contains(path: Path, text: str, tokens: tuple[str, ...]) -> list[str]:
    missing = [token for token in tokens if token not in text]
    return [f"{path} missing token: {token}" for token in missing]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FIFO coverage closure artifacts")
    parser.add_argument("--out", default="unity_test", help="VeriAgent output directory")
    args = parser.parse_args()

    out_dir = Path(args.out)
    gap = out_dir / "FIFO_coverage_gap_analysis.md"
    plan = out_dir / "FIFO_directed_test_plan.md"
    test = out_dir / "tests" / "test_fifo_coverage_directed.py"
    report = out_dir / "FIFO_coverage_closure_report.md"

    errors: list[str] = []
    try:
        gap_text = _read(gap)
        plan_text = _read(plan)
        test_text = _read(test)
        report_text = _read(report)
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}")
        return 1

    for path, text in (
        (gap, gap_text),
        (plan, plan_text),
        (test, test_text),
        (report, report_text),
    ):
        errors.extend(_assert_contains(path, text, REQUIRED_BINS))

    directed_keywords = (
        "full",
        "empty",
        "wrap",
        "push",
        "pop",
    )
    errors.extend(_assert_contains(test, test_text.lower(), directed_keywords))

    if "post-hoc" in report_text.lower() and "closure" not in report_text.lower():
        errors.append(f"{report} describes post-hoc review but not coverage closure")

    if errors:
        print("FAIL: coverage closure artifacts are incomplete")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: FIFO coverage closure artifacts map every uncovered bin to directed tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
