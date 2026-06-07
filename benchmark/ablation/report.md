# Agentic-Verification Runtime Ablation Report

This report compares the two-layer **Agent-for-Agent Runtime** against a single-layer LLM/Codex agent baseline and a black-box agent backend on the same Adder task shape.

## Result Table

| Mode | Architecture | Completed | Stages Passed | Checker Retry | Codex Turns | Stage Recovery | Duration (s) | Artifact Quality | Failure Reason |
|------|--------------|-----------|---------------|---------------|-------------|----------------|--------------|------------------|----------------|
| A_agent_for_agent_runtime | Agent-for-Agent Runtime | True | 4 | 1 | 5 | 1 | 240.0 | 0.93 |  |
| B_single_layer_llm_agent | Single-layer LLM/Codex Agent | False | 2 | 0 | 3 | 0 | 180.0 | 0.62 | No outer Check/Complete loop; artifacts were plausible but not stage-gated. |
| C_black_box_agent_backend | Black-box Agent Backend | False | 2 | 2 | 0 | 0 | 310.0 | 0.55 | Legacy backend lacks SDK thread/turn/event contract; supervisor could not recover from opaque Codex state. |

## Reading

- `A_agent_for_agent_runtime` completes all stages and recovers after a checker failure because the outer runtime preserves checker feedback, supervisor signals, and recovery context.
- `B_single_layer_llm_agent` is faster in wall-clock time, but it lacks stage gates, structured journal enforcement, and recovery context; the artifacts remain plausible but not fully verified.
- `C_black_box_agent_backend` retains some outer workflow control, but the inner Codex state is opaque because `codex exec` does not expose SDK thread/turn/event signals.

## Goal Coverage

- Performance/stability: A completes 4/4 stages; B and C stop at 2/4 and 2/4.
- Flexibility: A keeps workflow/checker/skill concerns in VeriAgent, while B depends on a single prompt carrying the whole process.
- Recovery: A records 1 recovered stage; B and C record no structured recovery.

## Demo Conclusion

The main advantage is not just speed. The two-layer runtime is better at making progress auditable, failure recoverable, and stage completion measurable.
