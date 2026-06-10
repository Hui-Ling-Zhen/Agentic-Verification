# FIFO Initial Coverage Report

This report is intentionally incomplete. The goal of the example is to let the agent read the uncovered bins, design directed tests, and produce a closure report.

## Summary

| Metric | Covered | Total | Percent |
|--------|---------|-------|---------|
| Functional bins | 8 | 12 | 66.7% |
| Boundary bins | 2 | 6 | 33.3% |
| Directed corner bins | 0 | 4 | 0.0% |

## Covered Bins

| Bin | Status | Evidence |
|-----|--------|----------|
| `<COV-RESET-EMPTY>` | covered | reset drives `empty=1`, `full=0`, `count=0` |
| `<COV-SINGLE-PUSH>` | covered | one push increments count |
| `<COV-SINGLE-POP>` | covered | one pop decrements count after push |
| `<COV-BASIC-DATA-ORDER>` | covered | first pushed value is first popped value |
| `<COV-COUNT-UP>` | covered | count increases on push |
| `<COV-COUNT-DOWN>` | covered | count decreases on pop |
| `<COV-FULL-FLAG>` | covered | filling four entries asserts `full` |
| `<COV-EMPTY-FLAG>` | covered | popping all entries asserts `empty` |

## Uncovered Bins

| Bin | Missing Scenario | Directed Test Hint |
|-----|------------------|--------------------|
| `<COV-FULL-PUSH-BLOCK>` | Push while `full=1` | Fill FIFO, attempt extra push, verify `count` and stored data are unchanged. |
| `<COV-EMPTY-POP-BLOCK>` | Pop while `empty=1` | Reset or drain FIFO, attempt pop, verify `count` remains zero. |
| `<COV-WRAPAROUND>` | Pointer wrap-around | Push/pop enough entries to wrap both pointers and then verify ordering. |
| `<COV-SIMULTANEOUS-PUSH-POP>` | Push and pop in same cycle | Drive `push=1` and `pop=1` when FIFO is neither full nor empty; verify `count` is stable. |

## Closure Criteria

The closure report must explain how each uncovered bin is targeted and where the corresponding directed test lives. It must use the exact bin labels above so the checker can audit the mapping.
