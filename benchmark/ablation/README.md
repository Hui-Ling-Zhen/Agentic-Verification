# Runtime Ablation — Agent-for-Agent vs Single-layer LLM Agent

This is the phase-2 benchmark entry point for proving why Agentic-Verification uses a **two-layer agent runtime** instead of a plain LLM wrapper.

This experiment belongs under `benchmark/` rather than `examples/`: it is not a new DUT case. It compares runtime modes on existing cases such as Adder or Mux.

The first DUT is **Adder** because it is small, deterministic, and already uses the baseline workflow/checker path. Mux is better for a later bug-discovery demo, but Adder is the smallest case for measuring lifecycle, retry, recovery, and artifact quality.

## Question

For the same DUT, does an outer agent runtime (**VeriAgent supervising Codex**) improve stability, recovery, auditability, and flexibility compared with a single-layer LLM/Codex agent?

## Modes

| Mode | Meaning | Expected manifest quality |
|------|---------|---------------------------|
| `A_agent_for_agent_runtime` | VeriAgent is the outer runtime; Codex is the inner agent runtime | Full `stage_trace`, `codex_turn_trace`, `supervisor_signals`, recovery context |
| `B_single_layer_llm_agent` | Codex receives one task prompt and acts as the whole agent | No outer stage/checker runtime; artifact quality must be judged post-hoc |
| `C_black_box_agent_backend` | VeriAgent calls an opaque `codex exec` style backend | Some outer workflow control, but weak or missing thread/turn/event contract |

## Metrics

Compare:

- `all_completed`
- `stages_passed`
- `checker_retry_total`
- `codex_turn_total`
- `stage_recovery_count`
- `duration_sec`
- `codex_failure_reason`
- `artifact_quality_score`
- `codex_supervisor_signals`
- `codex_turn_trace`

## Artifact quality rubric

`artifact_quality_score` is a weighted 0-1 score. The demo writes both the final score and `artifact_quality_breakdown` into each manifest.

| Component | Weight | What it measures |
|-----------|--------|------------------|
| `stage_completion` | 0.30 | How many required workflow stages completed. |
| `checker_result_quality` | 0.20 | Whether checkers passed or produced actionable feedback. |
| `required_artifact_completeness` | 0.20 | Whether required plan/basic-info/functions/checks/tests artifacts exist. |
| `journal_evidence_auditability` | 0.15 | Whether journal, evidence-read, and changed-artifact traces are inspectable. |
| `recovery_feedback_usage` | 0.10 | Whether checker feedback or supervisor signals were used to recover. |
| `reproducibility_trace_quality` | 0.05 | Whether manifest, turn trace, command trace, and policy trace are complete. |

For the current demo this gives `0.93` for `A_agent_for_agent_runtime`, `0.62` for `B_single_layer_llm_agent`, and `0.55` for `C_black_box_agent_backend`.

## Demo run

The demo run does not call Codex. It creates `run_manifest.json` files for A/B/C so the comparison shape, fields, and benchmark pipeline are fixed before spending time on real model runs.

```bash
make ablation-simulate
make ablation-benchmark
```

Outputs:

- `output/ablation_demo/*/.veriagent/run_manifest.json`
- `benchmark/ablation_demo.json`
- `benchmark/ablation_summary.csv`
- `benchmark/ablation_runs.json`
- `benchmark/ablation/report.md`

## Real-run plan

After the demo shape is accepted, replace each demo manifest with real workspaces:

```bash
# A: agent-for-agent runtime
make mcp_Adder CWD=output/ablation_real/A_agent_for_agent_runtime_Adder \
  ARGS="--exit-on-completion --mcp-server-port -1"

# C: black-box agent backend
make mcp_Adder CWD=output/ablation_real/C_black_box_agent_backend_Adder \
  ARGS="--backend=codex --loop --exit-on-completion --mcp-server-port -1"

# B: single-layer LLM/Codex agent baseline is intentionally outside the official VeriAgent contract.
# Keep its prompt, logs, wall time, and artifacts in output/ablation_real/B_single_layer_llm_agent_Adder,
# then add a manual manifest with the same fields used by the demo run.
```

Then aggregate:

```bash
python3 scripts/benchmark_collect.py \
  --scan output/ablation_real \
  --out benchmark/ablation_real_summary.csv \
  --json benchmark/ablation_real_runs.json
```

## Interpretation

The agent-for-agent mode should not be judged only by speed. The key evidence is whether it produces:

- fewer unrecovered checker failures,
- clearer failure reasons,
- higher artifact quality,
- richer stage/turn trace,
- and better recovery after checker feedback or supervisor signals.

That is the intended advantage of **using an agent runtime to supervise another agent runtime**.
