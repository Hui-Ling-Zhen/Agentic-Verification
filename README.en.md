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

### Two-layer architecture: VeriAgent supervising Codex

Agentic-Verification is not a black-box LLM wrapper. The official backend in `veriagent/abackend/codex_sdk.py` uses the OpenAI Codex app-server SDK to manage Codex threads, turns, event streams, approval handling, and turn context.

- Codex events become supervisor signals: command risk, protected-input diffs, MCP startup errors, and plan/stage mismatch are recorded in `codex_turn_trace` and `codex_supervisor_signals`.
- `VeriAgentTurnContext` passes stage goal, checker feedback, read requirements, journal state, previous signals, and recovery context to Codex before each turn.
- `SetCurrentStageJournal` requires `plan`, `evidence_read`, `changes_made`, `checker_result`, and `next_risk`, so Codex can explore while VeriAgent requires an auditable reasoning trail.
- `run_manifest.json` records `stage_trace`, `codex_turn_trace`, `checker_retry_total`, `stage_recovery_count`, and `skill_usage_summary`, making the supervisor's value measurable.

### Demo result: why the two-layer runtime helps

The current ablation demo compares the same Adder task shape across three modes:

| Mode | Stage measurement | Completed | Stages | Recovery | Artifact quality | What it shows |
|------|-------------------|-----------|--------|----------|------------------|---------------|
| `A_agent_for_agent_runtime` | Runtime-observed | Yes | `4/4` | `1` recovered stage | `0.93` | VeriAgent keeps workflow/checker/skill state outside Codex, then feeds checker feedback and supervisor signals into the next turn. |
| `B_single_layer_llm_agent` | Post-hoc artifact review | No | `2/4` | `N/A` | `0.62` | A single prompt can produce plausible notes, but stage recovery is not observable without the outer stage/checker runtime. |
| `C_black_box_agent_backend` | Runtime-observed | No | `2/4` | `0` | `0.55` | `codex exec` is usable as a fallback, but its inner state is opaque without SDK thread/turn/event signals. |

`Recovery` means a VeriAgent-observed failed stage later completed after structured checker/supervisor feedback. For the single-layer LLM baseline this is `N/A`, not `0`, because there is no runtime stage loop observing recovery.

Artifact quality is a weighted 0-1 score: stage completion `0.30`, checker quality `0.20`, required artifact completeness `0.20`, journal/evidence auditability `0.15`, recovery feedback usage `0.10`, and reproducibility/trace quality `0.05`.

The supervised mode makes progress **auditable, recoverable, and measurable**. See [`benchmark/ablation/report.md`](/benchmark/ablation/report.md) or regenerate the demo:

```bash
make ablation-benchmark
```

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
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

Do not use passive MCP (second terminal), `--backend=codex`, or `--backend=langchain` as the primary path. **`--config` is required** — the runtime does not ship a built-in UT/Formal workflow.

Codex SDK thread resume is guarded by DUT/workflow/workspace/backend fingerprints. Use `--resume-codex-thread` only to force reuse intentionally.

Sandbox note: `veriagent_policy` in `.codex/config.toml` is an audit hint, not a policy engine. Hard boundaries come from Codex sandbox settings, `writable_roots`, and OS read-only permissions on protected inputs. Network access defaults to `enabled`; disable it when a case does not need network:

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server \
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
