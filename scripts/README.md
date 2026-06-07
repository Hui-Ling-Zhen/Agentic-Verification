# Scripts

This directory contains small automation scripts for Agentic-Verification. These are **not examples** and they do not define DUT workflows.

## Current scripts

| Script | What it does | Typical command |
|--------|--------------|-----------------|
| `benchmark_collect.py` | Collects `.veriagent/run_manifest.json` files from completed VeriAgent workspaces and writes aggregate CSV/JSON files. | `make benchmark` |
| `ablation_simulate.py` | Generates A/B/C demo manifests for the phase-2 benchmark scaffold. It compares agent-for-agent runtime, single-layer LLM/Codex agent, and black-box backend modes. It does not call Codex or run a DUT. | `make ablation-simulate` |

## How they fit together

`ablation_simulate.py` creates demo workspaces under:

```text
output/ablation_demo/
```

Each demo workspace contains:

```text
.veriagent/run_manifest.json
```

`benchmark_collect.py` then scans those manifests and writes:

```text
benchmark/ablation_summary.csv
benchmark/ablation_runs.json
benchmark/ablation/report.md
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
