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
| `backend` | e.g. `codex` |
| `all_completed` | All stages finished |
| `stage_index` | Current stage index |
| `stages_total` / `stages_passed` / `stages_skipped` | Stage counts |
| `duration_sec` | Wall time (when available) |
| `version` | `veriagent` version |
| `started_at` / `updated_at` | UTC timestamps |

Schema version: `schema_version: "1"` (see `veriagent/util/benchmark.py`).

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
