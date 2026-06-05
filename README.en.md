# Agentic-Verification

LLM-powered **Agentic Verification** for hardware — CLI **`veriagent`**

[中文](/README.zh.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [Examples](/examples/README.md) · [Developer docs](/docs/content/00_index.md)

---

## What this repo is

**VeriAgent runtime** owns the stage machine, Checkers, MCP verification tools, and the supervised loop. **Codex** handles each round of RTL reading, test writing, and complex edits.

**Official verification path = supervised Codex SDK** (`--backend=codex_app_server` + MCP + `--loop`). Other backends (`codex` CLI, `langchain`, passive MCP-only, etc.) are **compatibility-only legacy** in this repo.

Workflow YAML is **externalized** under `examples/*/workflow/` — pass it with **`--config`** (required). See [`examples/_shared/supervised-codex.md`](/examples/_shared/supervised-codex.md).

### Design idea: verify by repeated checks

Agentic-Verification is built around a simple loop: **ask Codex to make progress, check the result, feed the failure back, and repeat until the stage passes**. VeriAgent does not try to replace Codex as a general-purpose coding agent. Instead, it supervises Codex with explicit workflow stages, deterministic Checkers, verification-domain MCP tools, human checkpoints, and a measurable `run_manifest.json`.

This is why the official path is a two-layer runtime: Codex performs the inner read/write/debug turn, while VeriAgent owns the outer verification contract. Every stage is expected to end in `Check` / `Complete`, not just in a plausible-looking answer.

---

## Requirements

- Python 3.11+, Linux / macOS, 4GB+ RAM
- [OpenAI Codex](https://github.com/openai/codex) executable on `PATH` or exported via `CODEX_BIN`
- MCP Python package (`mcp`) installed by `requirements.txt`
- OpenAI Codex open-source SDK: `codex/sdk/python` / package `openai-codex-app-server-sdk`, importable as `codex_app_server`
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
pip3 install -e .
git clone https://github.com/openai/codex ../codex
pip3 install -e ../codex/sdk/python
# The SDK install does not provide a binary; install or build OpenAI Codex too:
npm install -g @openai/codex  # or: brew install --cask codex
export CODEX_BIN="$(which codex)"
python -c "import codex_app_server; print('ok: codex_app_server')"
codex --version
codex app-server --help >/dev/null
picker --version
veriagent --check
make example-baseline
```

Equivalent CLI (from repo root, after `init_Adder` via `make mcp_Adder`):

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

Do not use passive MCP (second terminal), `--backend=codex`, or `--backend=langchain` as the primary path. **`--config` is required** — the runtime does not ship a built-in UT/Formal workflow.

Codex SDK thread resume is guarded by DUT/workflow/workspace/backend fingerprints. Use `--resume-codex-thread` only to force reuse intentionally.

Sandbox note: `veriagent_policy` in `.codex/config.toml` is an audit hint, not a policy engine. Hard boundaries come from Codex sandbox settings, `writable_roots`, and OS read-only permissions on protected inputs. Network access defaults to `enabled`; disable it when a case does not need network:

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server \
  --override backend.codex_app_server.args.codex_network_access=disabled
```

---

## Benchmark

Each run writes `.veriagent/run_manifest.json` as soon as the runtime starts, then updates it after backend/stage initialization, each Codex turn, and stage saves. It records backend status (`official` vs compatibility-only `legacy`), run status, stages, duration, last Codex thread/turn, token usage, MCP tool calls, file changes, failure reason, and sandbox/policy audit fields. SDK events are appended to `.veriagent/codex_events.jsonl`. Aggregate with:

```bash
make benchmark   # → benchmark/summary.csv, benchmark/runs.json
```

See [benchmark/README.md](/benchmark/README.md).

---

## Backend status

| Path | Status |
|------|--------|
| Supervised Codex SDK (`--backend=codex_app_server`, MCP, `--loop`) | **Official / tested** |
| Codex CLI (`--backend=codex`) | Compatibility-only legacy fallback; opaque `codex exec` path without the SDK thread/turn/event/manifest contract |
| `langchain` / API-only | Compatibility-only legacy path, not maintained for benchmark comparison |
| Passive MCP (no `--loop`) | Compatibility-only legacy path |

---

## Which README to read?

| Goal | Read |
|------|------|
| Install + supervised Codex | **This file** · [`supervised-codex.md`](/examples/_shared/supervised-codex.md) |
| All cases | [`examples/README.md`](/examples/README.md) |
| One case | `examples/.../<dut>/README.md` |
| Customize workflow | [`docs/content/03_develop/03_workflow.md`](/docs/content/03_develop/03_workflow.md) |

Case index: same table as [README.zh.md](/README.zh.md#case-readme-索引).

---

## Common commands

| Command | Case |
|---------|------|
| `make example-baseline` | Adder UT |
| `make example-formal` | Formal arbiter |
| `make mcp_<DUT>` | UT with auto workflow |
| `make formal_mcp_<DUT>` | Formal + `--use-skill` |
| `make benchmark` | Aggregate run manifests |

---

## More

- [Supervised Codex](/examples/_shared/supervised-codex.md)
- [Web Master](/docs/content/02_usage/07_web_master.md) · [FAQ](/docs/content/02_usage/05_faq.md)
