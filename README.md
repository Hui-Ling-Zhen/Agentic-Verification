# Agentic-Verification

LLM-powered **Agentic Verification** for hardware — CLI **`veriagent`**

[中文](README.zh.md) · [English (extended)](README.en.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [Examples](examples/README.md)

---

## What this repo is

**VeriAgent runtime** owns the stage machine, Checkers, MCP verification tools, and the supervised loop. **Codex** handles each round of RTL reading, test writing, and complex edits.

**Official verification path = supervised Codex SDK** (`--backend=codex_app_server` + MCP + `--loop`). Other backends (`codex` CLI, `langchain`, passive MCP-only, etc.) are **legacy / untested** — kept for compatibility only.

Workflow definitions live **outside** the runtime under `examples/*/workflow/*.yaml`. You must pass one explicitly via `--config` (or use `make mcp_<DUT>` which selects it for you).

See [supervised-codex.md](examples/_shared/supervised-codex.md) for the two-layer model.

---

## Requirements

- Python 3.11+, Linux / macOS, 4GB+ RAM
- [Codex CLI](https://github.com/openai/codex) on `PATH`
- [picker](https://github.com/XS-MLVP/picker)
- OpenAI-compatible endpoint for Codex:

```bash
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://your-endpoint/v1
export OPENAI_MODEL=...
```

---

## Quick start

```bash
git clone https://github.com/Hui-Ling-Zhen/Agentic-Verification.git
cd Agentic-Verification
pip3 install -r requirements.txt
make example-baseline
```

Equivalent CLI (from repo root):

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

**`--config` is required.** Running without it exits with an error and example paths. Do not rely on a built-in default workflow inside `veriagent/`.

---

## Benchmark / measurable output

Each run writes **`.veriagent/run_manifest.json`** in the workspace (DUT, workflow, backend, stage progress, duration, last Codex thread/turn, token usage, MCP tool calls, file changes, and failure reason). SDK events are appended to **`.veriagent/codex_events.jsonl`**.

After one or more runs:

```bash
make benchmark          # → benchmark/summary.csv + benchmark/runs.json
```

```bash
make benchmark-clean   # remove aggregated CSV/JSON only
```

Details: [benchmark/README.md](benchmark/README.md).

---

## Common commands

| Command | Case |
|---------|------|
| `make example-baseline` | Adder UT |
| `make example-formal` | Formal arbiter |
| `make mcp_<DUT>` | UT with auto workflow + `--config` |
| `make formal_mcp_<DUT>` | Formal + `--use-skill` |
| `make benchmark` | Aggregate run manifests |

---

## Case index

| Case | README |
|------|--------|
| Adder | [examples/01-baseline/adder/README.md](examples/01-baseline/adder/README.md) |
| Mux | [examples/01-baseline/mux/README.md](examples/01-baseline/mux/README.md) |
| Incremental | [examples/01-baseline/increment/README.md](examples/01-baseline/increment/README.md) |
| uart_16550 | [examples/02-peripheral-ip/uart_16550/README.md](examples/02-peripheral-ip/uart_16550/README.md) |
| Sbuffer | [examples/03-microarch/Sbuffer/README.md](examples/03-microarch/Sbuffer/README.md) |
| IntegerDivider / ALU754 | [integer-divider](examples/04-algorithm/integer-divider/README.md) · [ieee754-alu](examples/04-algorithm/ieee754-alu/README.md) |
| Formal | [Adder](examples/05-formal/Adder/README.md) · [arbiter](examples/05-formal/arbiter/README.md) · [traffic](examples/05-formal/traffic/README.md) |
| GenSpec / Gencov | [genspec](examples/06-planning/genspec/README.md) · [gencov](examples/06-planning/gencov/README.md) |

Full listing: [examples/README.md](examples/README.md).

---

## Repository layout

```
Agentic-Verification/
├── README.md                 # GitHub landing (this file)
├── README.zh.md / README.en.md
├── veriagent/                # Runtime (settings only; no shipped UT workflow)
├── examples/
│   ├── */workflow/*.yaml     # Required workflow configs (--config)
│   └── */skills/             # Per-case Codex skills
├── benchmark/                # make benchmark output
└── Makefile                  # VERIAGENT_SUPERVISED_CODEX standard flags
```

---

## Backend status

| Path | Status |
|------|--------|
| Supervised Codex SDK (`--backend=codex_app_server`, MCP, `--loop`) | **Official / tested** |
| Codex CLI (`--backend=codex`) | Legacy fallback; opaque `codex exec` path |
| `langchain` / API-only backend | Legacy, not maintained for this repo |
| Passive MCP (no `--loop`) | Legacy, not the product path |

---

## More docs

- [Supervised Codex](examples/_shared/supervised-codex.md)
- [Workflow customization](docs/content/03_develop/03_workflow.md)
- [Web Master](docs/content/02_usage/07_web_master.md) · [FAQ](docs/content/02_usage/05_faq.md)
