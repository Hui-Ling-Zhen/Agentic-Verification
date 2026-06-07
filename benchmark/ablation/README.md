# Runtime Ablation — Supervised Codex vs Raw / Legacy

This is the phase-2 benchmark entry point for proving why Agentic-Verification uses a **two-layer agent runtime** instead of a plain LLM wrapper.

This experiment belongs under `benchmark/` rather than `examples/`: it is not a new DUT case. It compares runtime modes on existing cases such as Adder or Mux.

The first DUT is **Adder** because it is small, deterministic, and already uses the baseline workflow/checker path. Mux is better for a later bug-discovery demo, but Adder is the smallest case for measuring lifecycle, retry, recovery, and artifact quality.

## Question

For the same DUT, does the outer VeriAgent supervisor improve stability, recovery, and auditability compared with raw or legacy Codex usage?

## Modes

| Mode | Meaning | Expected manifest quality |
|------|---------|---------------------------|
| `A_supervised` | `VeriAgent + Codex SDK + workflow + checker + journal` | Full `stage_trace`, `codex_turn_trace`, `supervisor_signals`, recovery context |
| `B_raw_codex` | Raw Codex prompt baseline without outer stage/checker loop | No comparable stage gating; artifact quality must be judged post-hoc |
| `C_legacy_codex_exec` | Compatibility-only `codex exec` style backend | Opaque inner state; weak or missing thread/turn/event contract |

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

## Synthetic simulation

The simulation does not call Codex. It creates synthetic `run_manifest.json` files for A/B/C so the comparison shape, fields, and benchmark pipeline are fixed before spending time on real model runs.

```bash
make ablation-simulate
make ablation-benchmark
```

Outputs:

- `output/ablation_simulated/*/.veriagent/run_manifest.json`
- `benchmark/ablation_simulated.json`
- `benchmark/ablation_summary.csv`
- `benchmark/ablation_runs.json`

## Real-run plan

After the synthetic shape is accepted, replace each synthetic manifest with real workspaces:

```bash
# A: official supervised runtime
make mcp_Adder CWD=output/ablation_real/A_supervised_Adder \
  ARGS="--exit-on-completion --mcp-server-port -1"

# C: legacy opaque Codex exec path
make mcp_Adder CWD=output/ablation_real/C_legacy_Adder \
  ARGS="--backend=codex --loop --exit-on-completion --mcp-server-port -1"

# B: raw Codex baseline is intentionally outside the official VeriAgent contract.
# Keep its prompt, logs, wall time, and artifacts in output/ablation_real/B_raw_Adder,
# then add a manual manifest with the same fields used by the synthetic run.
```

Then aggregate:

```bash
python3 scripts/benchmark_collect.py \
  --scan output/ablation_real \
  --out benchmark/ablation_real_summary.csv \
  --json benchmark/ablation_real_runs.json
```

## Interpretation

The supervised mode should not be judged only by speed. The key evidence is whether it produces:

- fewer unrecovered checker failures,
- clearer failure reasons,
- higher artifact quality,
- richer stage/turn trace,
- and better recovery after checker feedback or supervisor signals.

That is the intended advantage of **using an agent runtime to supervise another agent runtime**.
