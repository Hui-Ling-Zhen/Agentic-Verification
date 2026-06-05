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
| `codex_config_file` | Rendered `.codex/config.toml` used by the SDK backend |
| `sandbox_mode` | Codex sandbox mode written to config |
| `network_access` | Codex network access setting |
| `writable_roots` | Writable roots from the rendered sandbox policy |
| `protected_inputs` | Input directories VeriAgent expects to keep read-only |
| `policy_enforcement` | Current enforcement model, usually `codex_sandbox_os_permissions` |
| `veriagent_policy` | `audit_hint_only`; not a Codex-enforced policy engine |
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
