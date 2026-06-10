# Agentic-Verification

LLM-powered **Agentic Verification** for hardware — CLI **`veriagent`**

[中文](README.zh.md) · [English (extended)](README.en.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [Examples](examples/README.md)

---

## What this repo is

**VeriAgent runtime** owns the stage machine, Checkers, MCP verification tools, and the supervised loop. **Codex** handles each round of RTL reading, test writing, and complex edits.

**Official verification path = supervised Codex SDK** (`--backend=codex_app_server` + MCP + `--loop`). Other backends (`codex` CLI, `langchain`, passive MCP-only, etc.) are **compatibility-only legacy**.

Workflow definitions live **outside** the runtime under `examples/*/workflow/*.yaml`. You must pass one explicitly via `--config` (or use `make mcp_<DUT>` which selects it for you).

See [supervised-codex.md](examples/_shared/supervised-codex.md) for the two-layer model.

### Design idea: verify by repeated checks

Agentic-Verification is built around a simple loop: **ask Codex to make progress, check the result, feed the failure back, and repeat until the stage passes**. VeriAgent does not try to replace Codex as a general-purpose coding agent. Instead, it supervises Codex with explicit workflow stages, deterministic Checkers, verification-domain MCP tools, human checkpoints, and a measurable `run_manifest.json`.

This is why the official path is a two-layer runtime: Codex performs the inner read/write/debug turn, while VeriAgent owns the outer verification contract. Every stage is expected to end in `Check` / `Complete`, not just in a plausible-looking answer.

### Two-layer architecture: agent runtime over agent runtime

Agentic-Verification is designed as **VeriAgent supervising Codex**, not as a black-box prompt wrapper around an LLM.

| Layer | Responsibility |
|-------|----------------|
| **Inner agent runtime: Codex** | Reads RTL/specs, edits files, runs commands, streams events, and manages Codex thread/turn state. |
| **Outer supervisor runtime: VeriAgent** | Owns workflow stages, Checkers, verification-domain MCP tools, structured journal requirements, policy checks, recovery feedback, and benchmark manifests. |

The official backend in `veriagent/abackend/codex_sdk.py` uses the OpenAI Codex app-server SDK. It manages Codex **threads**, **turns**, **event streams**, **approval handling**, and **turn context** directly. The legacy `codex exec` backend is kept only for compatibility because it does not expose this thread/turn/event contract.

VeriAgent also promotes Codex events into supervisor-visible signals:

- command risk, protected-input diffs, MCP startup errors, and plan/stage mismatch are recorded in `codex_turn_trace` and `codex_supervisor_signals`;
- failed turns carry structured recovery context into the next Codex turn instead of becoming only terminal text;
- approval requests are evaluated by VeriAgent policy and logged with approve/deny reasons.

Before each turn, **`VeriAgentTurnContext`** passes the current stage goal, checker feedback, required reads, journal state, previous supervisor signals, and recovery context to Codex. This is closer to a runtime contract than ordinary prompt concatenation.

Stage completion also requires an auditable journal. `SetCurrentStageJournal` enforces:

```json
{
  "plan": "...",
  "evidence_read": ["..."],
  "changes_made": ["..."],
  "checker_result": "...",
  "next_risk": "..."
}
```

The intent is simple: **Codex explores and implements; VeriAgent requires an auditable reasoning trail before the stage can advance.**

### Demo result: why the two-layer runtime helps

The current ablation demo compares the same Adder task shape across three modes:

| Mode | Stage measurement | Completed | Stages | Recovery | Artifact quality | What it shows |
|------|-------------------|-----------|--------|----------|------------------|---------------|
| `A_agent_for_agent_runtime` | Runtime-observed | Yes | `4/4` | `1` recovered stage | `0.93` | VeriAgent keeps workflow/checker/skill state outside Codex, then feeds checker feedback and supervisor signals into the next turn. |
| `B_single_layer_llm_agent` | Post-hoc artifact review | No | `2/4` | `N/A` | `0.62` | A single prompt can produce plausible notes, but stage recovery is not observable without the outer stage/checker runtime. |
| `C_black_box_agent_backend` | Runtime-observed | No | `2/4` | `0` | `0.55` | `codex exec` is usable as a fallback, but its inner state is opaque without SDK thread/turn/event signals. |

`Recovery` means a VeriAgent-observed failed stage later completed after structured checker/supervisor feedback. For the single-layer LLM baseline this is `N/A`, not `0`, because there is no runtime stage loop observing recovery.

The benchmark is designed to measure the value of the **outer supervisor runtime**, not just whether an LLM can write plausible text once. That is why all modes use the same DUT/task shape, but the metrics separate runtime-observed progress from post-hoc artifact review:

- A measures the official agent-for-agent path: VeriAgent observes stages, checks, Codex events, recovery, and final artifacts.
- B measures a single-layer LLM/Codex agent: artifacts can be reviewed after the fact, but stage recovery is not observable at runtime.
- C measures the legacy black-box backend: VeriAgent still has an outer loop, but the inner Codex state is opaque.

`artifact_quality_score` is a weighted 0-1 reward:

| Component | Weight | Why it matters |
|-----------|--------|----------------|
| Stage completion | `0.30` | Rewards finishing the required workflow, not just producing partial notes. |
| Checker result quality | `0.20` | Rewards passing checks or producing actionable checker feedback. |
| Required artifact completeness | `0.20` | Rewards generating the expected plan, basic-info, functions/checks, and test artifacts. |
| Journal/evidence auditability | `0.15` | Rewards structured journal entries, evidence read, and changed-artifact traces. |
| Recovery feedback usage | `0.10` | Rewards using checker feedback or supervisor signals to recover from a failed stage. |
| Reproducibility/trace quality | `0.05` | Rewards manifest, turn trace, command trace, and policy trace completeness. |

This reward intentionally favors **auditable verification progress** over raw speed or fluent-looking output.

The key result is not raw speed. The supervised mode makes progress **auditable, recoverable, and measurable**: failures become checker feedback, Codex events become supervisor signals, and the final manifest records the evidence. See [benchmark/ablation/report.md](benchmark/ablation/report.md) or regenerate the demo with:

```bash
make ablation-benchmark
```

### Demo result: coverage-gap-directed tests

The FIFO coverage-closure demo shows why using coverage gaps as agent input can produce stronger directed tests than a generic smoke baseline:

| Test set | Covered bins | Initial gaps hit | Injected mutations detected |
|----------|--------------|------------------|-----------------------------|
| `smoke_baseline` | `8/12` | `0/4` | `0/4` |
| `gap_directed` | `12/12` | `4/4` | `4/4` |

This does not claim the agent replaces an expert verification engineer. It shows that a supervised agent workflow can systematically translate explicit coverage gaps into directed tests and auditable closure evidence. See [examples/07-coverage/fifo_coverage/mutation_report.md](examples/07-coverage/fifo_coverage/mutation_report.md) or regenerate it with:

```bash
make -C examples/07-coverage mutation-demo
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

Equivalent CLI (from repo root):

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

**`--config` is required.** Running without it exits with an error and example paths. Do not rely on a built-in default workflow inside `veriagent/`.

Codex SDK thread resume is fingerprint-safe by default: saved threads are reused only when DUT, workflow, workspace input hash, and backend args match. Use `--resume-codex-thread` only when you intentionally want to override that guard.

Sandbox note: `veriagent_policy` in `.codex/config.toml` is an audit hint, not a policy engine. Hard boundaries come from Codex sandbox settings, `writable_roots`, and OS read-only permissions on protected inputs. Network access defaults to `enabled`; disable it when a case does not need network:

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server \
  --override backend.codex_app_server.args.codex_network_access=disabled
```

---

## Benchmark / measurable output

Each run writes **`.veriagent/run_manifest.json`** in the workspace as soon as the runtime starts, then updates it after backend/stage initialization, each Codex turn, and stage saves. SDK events are appended to **`.veriagent/codex_events.jsonl`**.

The manifest is the main artifact for measuring whether the outer supervisor helped:

- `stage_trace`: stage progress, checker feedback, journal, reference/output evidence, and skill usage;
- `codex_turn_trace`: Codex plans, diffs, commands, approvals, MCP startup status, and unknown future events;
- `checker_retry_total`: how often the outer checker forced another attempt;
- `stage_recovery_count`: how many stages recovered after earlier failures;
- `skill_usage_summary`: whether workflow-required skills were listed/read/used;
- `codex_supervisor_signals`: command risk, protected input touch, MCP startup errors, plan mismatch, and approval decisions;
- sandbox/policy audit fields such as `protected_inputs`, `writable_roots`, `network_access`, and `policy_enforcement`.

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
| `make example-coverage` | FIFO coverage closure |
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
| Coverage Closure | [FIFO](examples/07-coverage/fifo_coverage/README.md) · mutation demo: smoke `0/4` vs directed `4/4` injected bugs |

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
| Codex CLI (`--backend=codex`) | Compatibility-only legacy fallback; opaque `codex exec` path without the SDK thread/turn/event/manifest contract |
| `langchain` / API-only backend | Compatibility-only legacy path, not maintained for benchmark comparison |
| Passive MCP (no `--loop`) | Compatibility-only legacy path, not the product path |

---

## More docs

- [Supervised Codex](examples/_shared/supervised-codex.md)
- [Workflow customization](docs/content/03_develop/03_workflow.md)
- [Web Master](docs/content/02_usage/07_web_master.md) · [FAQ](docs/content/02_usage/05_faq.md)
