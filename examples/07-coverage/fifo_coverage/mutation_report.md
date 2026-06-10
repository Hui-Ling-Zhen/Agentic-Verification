# FIFO Coverage Closure Mutation Report

This sandbox experiment compares a smoke-test baseline against coverage-gap-directed tests.

## Summary

| Test set | Golden passes | Covered bins | Initially uncovered bins hit | Mutations detected |
|----------|---------------|--------------|------------------------------|--------------------|
| `smoke_baseline` | True | 8/12 | 0/4 | 0/4 |
| `gap_directed` | True | 12/12 | 4/4 | 4/4 |

## Interpretation

- `smoke_baseline` exercises reset/basic push/pop/order but does not target the coverage gaps from `coverage_report_initial.md`.
- `gap_directed` adds tests for full push block, empty pop block, pointer wrap-around, and simultaneous push/pop.
- The directed set detects all injected corner-case mutations in this sandbox model; the smoke set detects none.

## Missing Bins Closed by Directed Tests

- Smoke baseline: none
- Gap-directed: COV-EMPTY-POP-BLOCK, COV-FULL-PUSH-BLOCK, COV-SIMULTANEOUS-PUSH-POP, COV-WRAPAROUND

## Mutation Results

| Mutation | Meaning | Smoke detected | Directed detected |
|----------|---------|----------------|-------------------|
| `MUT-FULL-PUSH-OVERWRITE` | Allows push while full, corrupting stored FIFO order. | False | True |
| `MUT-EMPTY-POP-UNDERFLOW` | Allows pop while empty, corrupting count/data state. | False | True |
| `MUT-NO-POINTER-WRAP` | Prevents pointer wrap-around after the last entry. | False | True |
| `MUT-SIM-PUSH-POP-COUNT` | Updates count incorrectly during simultaneous push/pop. | False | True |

## Demo Claim

This does not prove that an agent writes better tests than an expert engineer. It shows that when coverage gaps are explicit, a supervised agent workflow can systematically translate those gaps into directed tests and auditable closure evidence.
