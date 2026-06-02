# Agentic-Verification

LLM-powered **Agentic Verification** for hardware — CLI **`veriagent`**

[中文](/README.zh.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [Examples](/examples/README.md) · [Developer docs](/docs/content/00_index.md)

---

## What this repo is

**VeriAgent runtime** owns the stage machine, Checkers, MCP verification tools, and the supervised loop. **Codex** handles each round of RTL reading, test writing, and complex edits. The repo standardizes on **supervised Codex** only: MCP + `--loop` + `--backend=codex`. See [`examples/_shared/supervised-codex.md`](/examples/_shared/supervised-codex.md).

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

Equivalent CLI (from repo root, after `init_Adder` via `make mcp_Adder`):

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex
```

Do not use passive MCP (second terminal) or `--backend=langchain` as the primary path.

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

---

## More

- [Supervised Codex](/examples/_shared/supervised-codex.md)
- [Web Master](/docs/content/02_usage/07_web_master.md) · [FAQ](/docs/content/02_usage/05_faq.md)
