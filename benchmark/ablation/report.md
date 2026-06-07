# Agentic-Verification Runtime Ablation Report

This report compares the two-layer **Agent-for-Agent Runtime** against a single-layer LLM/Codex agent baseline and a black-box agent backend on the same Adder task shape.

## Result Table

| Mode | Architecture | Stage Measurement | Completed | Stages Passed | Checker Retry | Codex Turns | Stage Recovery | Duration (s) | Artifact Quality | Failure Reason |
|------|--------------|-------------------|-----------|---------------|---------------|-------------|----------------|--------------|------------------|----------------|
| A_agent_for_agent_runtime | Agent-for-Agent Runtime | runtime_observed | True | 4 | 1 | 5 | 1 | 240.0 | 0.93 |  |
| B_single_layer_llm_agent | Single-layer LLM/Codex Agent | post_hoc_artifact_review | False | 2 | 0 | 3 | N/A | 180.0 | 0.62 | No outer Check/Complete loop; artifacts were plausible but not stage-gated. |
| C_black_box_agent_backend | Black-box Agent Backend | runtime_observed | False | 2 | 2 | 0 | 0 | 310.0 | 0.55 | Legacy backend lacks SDK thread/turn/event contract; supervisor could not recover from opaque Codex state. |

`stage_recovery_count` means a VeriAgent-observed failed stage later completed after structured checker/supervisor feedback. For `B_single_layer_llm_agent`, this is `N/A` because there is no outer stage/checker runtime observing recovery; its stages are judged post-hoc from artifacts.

## Artifact Quality Rubric

`artifact_quality_score` is a weighted 0-1 score:

| Component | Weight | Meaning |
|-----------|--------|---------|
| `stage_completion` | 0.30 | How many required workflow stages completed. |
| `checker_result_quality` | 0.20 | Whether checkers passed or produced actionable feedback. |
| `required_artifact_completeness` | 0.20 | Whether required plan/basic-info/functions/checks/tests artifacts exist. |
| `journal_evidence_auditability` | 0.15 | Whether journal, evidence-read, and changed-artifact traces are inspectable. |
| `recovery_feedback_usage` | 0.10 | Whether checker feedback or supervisor signals were used to recover. |
| `reproducibility_trace_quality` | 0.05 | Whether manifest, turn trace, command trace, and policy trace are complete. |

## Artifact Quality Breakdown

| Mode | Stage | Checker | Artifacts | Journal/Evidence | Recovery | Trace | Score |
|------|-------|---------|-----------|------------------|----------|-------|-------|
| A_agent_for_agent_runtime | 1.00 | 0.85 | 0.95 | 0.95 | 0.80 | 0.95 | 0.93 |
| B_single_layer_llm_agent | 0.50 | 0.70 | 0.85 | 0.60 | 0.35 | 0.70 | 0.62 |
| C_black_box_agent_backend | 0.50 | 0.65 | 0.75 | 0.50 | 0.25 | 0.40 | 0.55 |

## Reading

- `A_agent_for_agent_runtime` completes all stages and recovers after a checker failure because the outer runtime preserves checker feedback, supervisor signals, and recovery context.
- `B_single_layer_llm_agent` is faster in wall-clock time, but stage recovery is not observable because it lacks the outer stage/checker runtime; the artifacts remain plausible but not fully verified.
- `C_black_box_agent_backend` retains some outer workflow control, but the inner Codex state is opaque because `codex exec` does not expose SDK thread/turn/event signals.

## Goal Coverage

- Performance/stability: A completes 4/4 stages; B and C stop at 2/4 and 2/4.
- Flexibility: A keeps workflow/checker/skill concerns in VeriAgent, while B depends on a single prompt carrying the whole process.
- Recovery: A records 1 recovered stage; B is N/A because recovery is not observable in a single-layer prompt baseline; C records no structured recovery.

## Demo Conclusion

The main advantage is not just speed. The two-layer runtime is better at making progress auditable, failure recoverable, and stage completion measurable.
