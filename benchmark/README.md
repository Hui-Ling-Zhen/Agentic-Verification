# Benchmark artifacts

Agentic-Verification records **measurable run output** so verification is not only documentation — each workspace gets a machine-readable manifest.

## Per-run: `run_manifest.json`

After stage progress is saved, the runtime writes:

```text
<workspace>/.veriagent/run_manifest.json
```

Example fields:

| Field | Meaning |
|-------|---------|
| `dut` | DUT name |
| `workflow_config` | Path passed to `--config` |
| `backend` | e.g. `codex_app_server` |
| `backend_class` | Python backend implementation |
| `codex_thread_id` / `codex_turn_id` | Last Codex SDK thread/turn identity |
| `codex_turn_status` | `completed`, `failed`, `interrupted`, or `requires_approval` |
| `codex_token_usage` | Token usage payload reported by Codex |
| `codex_mcp_tool_calls` | MCP tool calls completed in the last turn |
| `codex_file_changes` | File paths changed in the last turn |
| `codex_failure_reason` | Reason for non-completed turns |
| `codex_event_log` | Path to `.veriagent/codex_events.jsonl` |
| `codex_approval_requests` | Approval requests intercepted by VeriAgent |
| `backend_status` / `backend_legacy` | Whether the run used the official SDK backend or compatibility-only backend |
| `run_status` | Latest lifecycle checkpoint, e.g. `starting`, `initialized`, `codex_turn_completed`, or failure/interruption status |
| `codex_config_file` | Rendered `.codex/config.toml` used by the SDK backend |
| `codex_bin` | OpenAI Codex binary resolved from `CODEX_BIN` or `PATH` |
| `codex_metadata` | Codex app-server initialize metadata when available |
| `sandbox_mode` | Codex sandbox mode written to config |
| `turn_sandbox_policy` | Sandbox policy passed to the current Codex turn |
| `network_access` | Codex network access setting |
| `writable_roots` | Writable roots from the rendered sandbox policy |
| `protected_inputs` | Input directories VeriAgent expects to keep read-only |
| `policy_enforcement` | Current enforcement model, usually `codex_sandbox_os_permissions` |
| `veriagent_policy` | `audit_hint_only`; not a Codex-enforced policy engine |
| `codex_write_policy` / `codex_command_policy` | VeriAgent audit hints rendered into `.codex/config.toml` |
| `policy_warnings` | Read-only/protection warnings observed at startup |
| `all_completed` | All stages finished |
| `stage_index` | Current stage index |
| `stages_total` / `stages_passed` / `stages_skipped` | Stage counts |
| `duration_sec` | Wall time (when available) |
| `version` | `veriagent` version |
| `started_at` / `updated_at` | UTC timestamps |

Schema version: `schema_version: "3"` (see `veriagent/util/benchmark.py`).

## Per-event: `codex_events.jsonl`

The SDK backend appends normalized Codex notifications to:

```text
<workspace>/.veriagent/codex_events.jsonl
```

Each line contains one event record with `kind`, `thread_id`, `turn_id`, tool/command/file data when available, token usage updates, and an UTC timestamp.

## Aggregate: `make benchmark`

From repo root:

```bash
make example-baseline   # or any mcp_/formal_mcp_ target
make benchmark
```

This runs `scripts/benchmark_collect.py`, scanning `output/` and `examples/` for manifests, and writes:

- `benchmark/summary.csv` — one row per run (spreadsheet-friendly)
- `benchmark/runs.json` — full JSON bundle

Clean aggregated files only (manifests in workspaces are untouched):

```bash
make benchmark-clean
```

Custom scan roots:

```bash
python3 scripts/benchmark_collect.py --scan output /path/to/other/workspaces
```

## Typical workflow

1. Run one or more cases (`make mcp_Adder`, `make formal_mcp_arbiter`, …).
2. `make benchmark` to refresh CSV/JSON.
3. Compare `all_completed`, `duration_sec`, and `stages_passed` across DUTs or workflow versions.

No manifests yet? The collector prints a hint to run a case first.

## Runtime ablation demo

Phase-2 evaluation compares three modes on the same small DUT:

| Mode | Meaning |
|------|---------|
| `A_supervised` | VeriAgent + Codex SDK + workflow + checker + structured journal |
| `B_raw_codex` | Raw Codex prompt baseline without the outer stage/checker loop |
| `C_legacy_codex_exec` | Compatibility-only opaque `codex exec` style path |

Full experiment notes: [`benchmark/ablation/README.md`](ablation/README.md).

To validate the comparison shape without spending model/runtime cost:

```bash
make ablation-benchmark
```

This writes synthetic manifests under `output/ablation_simulated/` and aggregates:

- `benchmark/ablation_simulated.json`
- `benchmark/ablation_summary.csv`
- `benchmark/ablation_runs.json`

The important columns are:

- `all_completed`
- `stages_passed`
- `checker_retry_total`
- `codex_turn_total`
- `stage_recovery_count`
- `duration_sec`
- `codex_failure_reason`
- `artifact_quality_score`
- `codex_supervisor_signal_count`

Synthetic results are not claims about model performance. They are a reproducible scaffold for the real Adder/Mux ablation runs.
