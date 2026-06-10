#!/usr/bin/env python3
# coding=utf-8
"""Run a sandbox FIFO mutation demo for the coverage-closure example.

The script compares two test sets:

- smoke_baseline: reset/basic push/pop/order tests
- gap_directed: tests derived from the uncovered bins in coverage_report_initial.md

It does not invoke Codex or picker. It is a deterministic sandbox experiment
that demonstrates why coverage-gap-driven directed tests can outperform a
simple smoke-test baseline.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


DEPTH = 4

ALL_BINS = (
    "COV-RESET-EMPTY",
    "COV-SINGLE-PUSH",
    "COV-SINGLE-POP",
    "COV-BASIC-DATA-ORDER",
    "COV-COUNT-UP",
    "COV-COUNT-DOWN",
    "COV-FULL-FLAG",
    "COV-EMPTY-FLAG",
    "COV-FULL-PUSH-BLOCK",
    "COV-EMPTY-POP-BLOCK",
    "COV-WRAPAROUND",
    "COV-SIMULTANEOUS-PUSH-POP",
)

INITIAL_COVERED_BINS = {
    "COV-RESET-EMPTY",
    "COV-SINGLE-PUSH",
    "COV-SINGLE-POP",
    "COV-BASIC-DATA-ORDER",
    "COV-COUNT-UP",
    "COV-COUNT-DOWN",
    "COV-FULL-FLAG",
    "COV-EMPTY-FLAG",
}

UNCOVERED_BINS = {
    "COV-FULL-PUSH-BLOCK",
    "COV-EMPTY-POP-BLOCK",
    "COV-WRAPAROUND",
    "COV-SIMULTANEOUS-PUSH-POP",
}

MUTATIONS = {
    "MUT-FULL-PUSH-OVERWRITE": "Allows push while full, corrupting stored FIFO order.",
    "MUT-EMPTY-POP-UNDERFLOW": "Allows pop while empty, corrupting count/data state.",
    "MUT-NO-POINTER-WRAP": "Prevents pointer wrap-around after the last entry.",
    "MUT-SIM-PUSH-POP-COUNT": "Updates count incorrectly during simultaneous push/pop.",
}


@dataclass
class FifoModel:
    mutation: str | None = None
    depth: int = DEPTH
    mem: list[int] = field(default_factory=lambda: [0] * DEPTH)
    wr_ptr: int = 0
    rd_ptr: int = 0
    count: int = 0
    data_out: int = 0

    @property
    def full(self) -> bool:
        return self.count == self.depth

    @property
    def empty(self) -> bool:
        return self.count == 0

    def reset(self) -> None:
        self.mem = [0] * self.depth
        self.wr_ptr = 0
        self.rd_ptr = 0
        self.count = 0
        self.data_out = 0

    def _inc_ptr(self, ptr: int) -> int:
        if self.mutation == "MUT-NO-POINTER-WRAP":
            return min(ptr + 1, self.depth - 1)
        return (ptr + 1) % self.depth

    def step(self, push: bool = False, pop: bool = False, data_in: int = 0) -> int:
        was_full = self.full
        was_empty = self.empty
        do_push = push and not was_full
        do_pop = pop and not was_empty

        if self.mutation == "MUT-FULL-PUSH-OVERWRITE" and push:
            do_push = True
        if self.mutation == "MUT-EMPTY-POP-UNDERFLOW" and pop:
            do_pop = True

        if do_push:
            self.mem[self.wr_ptr] = data_in
            self.wr_ptr = self._inc_ptr(self.wr_ptr)

        if do_pop:
            self.data_out = self.mem[self.rd_ptr]
            self.rd_ptr = self._inc_ptr(self.rd_ptr)

        if do_push and not do_pop:
            if not was_full:
                self.count += 1
        elif do_pop and not do_push:
            if self.mutation == "MUT-EMPTY-POP-UNDERFLOW" and was_empty:
                self.count = -1
            elif not was_empty:
                self.count -= 1
        elif do_push and do_pop:
            if self.mutation == "MUT-SIM-PUSH-POP-COUNT":
                self.count += 1

        return self.data_out


TestFn = Callable[[FifoModel], set[str]]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_reset_empty(fifo: FifoModel) -> set[str]:
    fifo.reset()
    _assert(fifo.empty and not fifo.full and fifo.count == 0, "reset must produce empty FIFO")
    return {"COV-RESET-EMPTY"}


def test_single_push_pop(fifo: FifoModel) -> set[str]:
    fifo.reset()
    fifo.step(push=True, data_in=0x12)
    _assert(fifo.count == 1 and not fifo.empty, "single push must increment count")
    value = fifo.step(pop=True)
    _assert(value == 0x12 and fifo.count == 0 and fifo.empty, "single pop must return pushed data")
    return {"COV-SINGLE-PUSH", "COV-SINGLE-POP", "COV-COUNT-UP", "COV-COUNT-DOWN"}


def test_basic_order_and_flags(fifo: FifoModel) -> set[str]:
    fifo.reset()
    for value in (1, 2, 3, 4):
        fifo.step(push=True, data_in=value)
    _assert(fifo.full and fifo.count == DEPTH, "four pushes must fill FIFO")
    popped = [fifo.step(pop=True) for _ in range(DEPTH)]
    _assert(popped == [1, 2, 3, 4], f"basic order mismatch: {popped}")
    _assert(fifo.empty and fifo.count == 0, "four pops must empty FIFO")
    return {"COV-BASIC-DATA-ORDER", "COV-FULL-FLAG", "COV-EMPTY-FLAG"}


def test_full_push_block(fifo: FifoModel) -> set[str]:
    fifo.reset()
    for value in (1, 2, 3, 4):
        fifo.step(push=True, data_in=value)
    fifo.step(push=True, data_in=99)
    _assert(fifo.full and fifo.count == DEPTH, "full push must keep FIFO full with stable count")
    popped = [fifo.step(pop=True) for _ in range(DEPTH)]
    _assert(popped == [1, 2, 3, 4], f"full push corrupted stored data: {popped}")
    return {"COV-FULL-PUSH-BLOCK"}


def test_empty_pop_block(fifo: FifoModel) -> set[str]:
    fifo.reset()
    fifo.step(pop=True)
    _assert(fifo.empty and fifo.count == 0, "empty pop must keep FIFO empty with stable count")
    return {"COV-EMPTY-POP-BLOCK"}


def test_wraparound_order(fifo: FifoModel) -> set[str]:
    fifo.reset()
    for value in (1, 2, 3, 4):
        fifo.step(push=True, data_in=value)
    _assert([fifo.step(pop=True), fifo.step(pop=True)] == [1, 2], "initial drain mismatch")
    fifo.step(push=True, data_in=5)
    fifo.step(push=True, data_in=6)
    popped = [fifo.step(pop=True) for _ in range(DEPTH)]
    _assert(popped == [3, 4, 5, 6], f"wrap-around order mismatch: {popped}")
    return {"COV-WRAPAROUND"}


def test_simultaneous_push_pop(fifo: FifoModel) -> set[str]:
    fifo.reset()
    fifo.step(push=True, data_in=1)
    fifo.step(push=True, data_in=2)
    before = fifo.count
    value = fifo.step(push=True, pop=True, data_in=3)
    _assert(value == 1, "simultaneous push/pop should pop oldest value")
    _assert(fifo.count == before, "simultaneous push/pop should keep count stable")
    popped = [fifo.step(pop=True), fifo.step(pop=True)]
    _assert(popped == [2, 3], f"simultaneous push/pop order mismatch: {popped}")
    return {"COV-SIMULTANEOUS-PUSH-POP"}


TEST_SETS: dict[str, list[TestFn]] = {
    "smoke_baseline": [
        test_reset_empty,
        test_single_push_pop,
        test_basic_order_and_flags,
    ],
    "gap_directed": [
        test_reset_empty,
        test_single_push_pop,
        test_basic_order_and_flags,
        test_full_push_block,
        test_empty_pop_block,
        test_wraparound_order,
        test_simultaneous_push_pop,
    ],
}


def run_tests(test_set: list[TestFn], mutation: str | None = None) -> tuple[bool, set[str], str | None]:
    covered: set[str] = set()
    fifo = FifoModel(mutation=mutation)
    try:
        for test in test_set:
            covered.update(test(fifo))
        return True, covered, None
    except AssertionError as exc:
        return False, covered, str(exc)


def build_report() -> dict:
    results = {}
    for name, tests in TEST_SETS.items():
        ok, covered, failure = run_tests(tests)
        detected = {}
        for mutation in MUTATIONS:
            mut_ok, _, mut_failure = run_tests(tests, mutation=mutation)
            detected[mutation] = {
                "detected": not mut_ok,
                "failure": mut_failure,
            }
        results[name] = {
            "passes_golden": ok,
            "golden_failure": failure,
            "covered_bins": sorted(covered),
            "covered_bin_count": len(covered),
            "total_bin_count": len(ALL_BINS),
            "initially_uncovered_bins_hit": sorted(covered & UNCOVERED_BINS),
            "initially_uncovered_bin_count": len(covered & UNCOVERED_BINS),
            "mutations_detected": sum(1 for item in detected.values() if item["detected"]),
            "mutation_total": len(MUTATIONS),
            "mutation_results": detected,
        }
    return {
        "dut": "FIFO",
        "demo": "coverage_closure_mutation",
        "all_bins": list(ALL_BINS),
        "initial_covered_bins": sorted(INITIAL_COVERED_BINS),
        "initial_uncovered_bins": sorted(UNCOVERED_BINS),
        "mutations": MUTATIONS,
        "test_sets": results,
    }


def write_markdown(report: dict, path: Path) -> None:
    smoke = report["test_sets"]["smoke_baseline"]
    directed = report["test_sets"]["gap_directed"]
    lines = [
        "# FIFO Coverage Closure Mutation Report",
        "",
        "This sandbox experiment compares a smoke-test baseline against coverage-gap-directed tests.",
        "",
        "## Summary",
        "",
        "| Test set | Golden passes | Covered bins | Initially uncovered bins hit | Mutations detected |",
        "|----------|---------------|--------------|------------------------------|--------------------|",
    ]
    for name, result in report["test_sets"].items():
        lines.append(
            f"| `{name}` | {result['passes_golden']} | "
            f"{result['covered_bin_count']}/{result['total_bin_count']} | "
            f"{result['initially_uncovered_bin_count']}/{len(UNCOVERED_BINS)} | "
            f"{result['mutations_detected']}/{result['mutation_total']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `smoke_baseline` exercises reset/basic push/pop/order but does not target the coverage gaps from `coverage_report_initial.md`.",
        "- `gap_directed` adds tests for full push block, empty pop block, pointer wrap-around, and simultaneous push/pop.",
        "- The directed set detects all injected corner-case mutations in this sandbox model; the smoke set detects none.",
        "",
        "## Missing Bins Closed by Directed Tests",
        "",
        f"- Smoke baseline: {', '.join(smoke['initially_uncovered_bins_hit']) or 'none'}",
        f"- Gap-directed: {', '.join(directed['initially_uncovered_bins_hit'])}",
        "",
        "## Mutation Results",
        "",
        "| Mutation | Meaning | Smoke detected | Directed detected |",
        "|----------|---------|----------------|-------------------|",
    ])
    for mutation, desc in report["mutations"].items():
        lines.append(
            f"| `{mutation}` | {desc} | "
            f"{smoke['mutation_results'][mutation]['detected']} | "
            f"{directed['mutation_results'][mutation]['detected']} |"
        )
    lines.extend([
        "",
        "## Demo Claim",
        "",
        "This does not prove that an agent writes better tests than an expert engineer. It shows that when coverage gaps are explicit, a supervised agent workflow can systematically translate those gaps into directed tests and auditable closure evidence.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run FIFO coverage closure mutation demo")
    parser.add_argument(
        "--out-json",
        default="mutation_report.json",
        help="Path for JSON report",
    )
    parser.add_argument(
        "--out-md",
        default="mutation_report.md",
        help="Path for Markdown report",
    )
    args = parser.parse_args()

    report = build_report()
    json_path = Path(args.out_json)
    md_path = Path(args.out_md)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    for name, result in report["test_sets"].items():
        print(
            f"{name}: covered {result['covered_bin_count']}/{result['total_bin_count']} bins, "
            f"hit {result['initially_uncovered_bin_count']}/{len(UNCOVERED_BINS)} initial gaps, "
            f"detected {result['mutations_detected']}/{result['mutation_total']} mutations"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
