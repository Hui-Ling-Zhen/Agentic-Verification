# Scripts

This directory contains small automation scripts for Agentic-Verification. These are **not examples** and they do not define DUT workflows.

## Current scripts

| Script | What it does | Typical command |
|--------|--------------|-----------------|
| `benchmark_collect.py` | Collects `.veriagent/run_manifest.json` files from completed VeriAgent workspaces and writes aggregate CSV/JSON files. | `make benchmark` |
| `ablation_simulate.py` | Generates synthetic A/B/C ablation manifests for the phase-2 benchmark scaffold. It does not call Codex or run a DUT. | `make ablation-simulate` |

## How they fit together

`ablation_simulate.py` creates synthetic workspaces under:

```text
output/ablation_simulated/
```

Each synthetic workspace contains:

```text
.veriagent/run_manifest.json
```

`benchmark_collect.py` then scans those manifests and writes:

```text
benchmark/ablation_summary.csv
benchmark/ablation_runs.json
```

For normal VeriAgent runs, `benchmark_collect.py` scans real workspaces instead:

```bash
make benchmark
```

For the phase-2 ablation scaffold:

```bash
make ablation-benchmark
```

The experiment design and interpretation live in [`benchmark/ablation/README.md`](../benchmark/ablation/README.md).
