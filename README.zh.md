# Agentic-Verification

面向硬件的 **Agentic Verification** 平台 —— CLI **`veriagent`**

[English](/README.en.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [全部示例](/examples/README.md) · [开发者文档](/docs/content/00_index.md)

---

## 项目是什么

**Runtime（VeriAgent）** 负责阶段机、Checker、MCP 验证工具与监督循环；**Codex** 负责每轮读 RTL、写测试与复杂代码修改。全仓库统一为 **监督式 Codex**（MCP + loop + `--backend=codex`），见 [`examples/_shared/supervised-codex.md`](/examples/_shared/supervised-codex.md)。

---

## 环境要求

- Python 3.11+，Linux / macOS，建议 4GB+ 内存
- [Codex CLI](https://github.com/openai/codex)（`codex` 在 PATH 中）
- [picker](https://github.com/XS-MLVP/picker)
- 模型端点（供 Codex 使用，OpenAI 兼容）：

```bash
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://你的端点/v1
export OPENAI_MODEL=...
```

---

## 快速开始

```bash
git clone https://github.com/Hui-Ling-Zhen/Agentic-Verification.git
cd Agentic-Verification
pip3 install -r requirements.txt   # 或：pip3 install -e .
```

**首次运行（Adder 基线）：**

```bash
make example-baseline
```

等价于（仓库根目录，先 `make init_Adder` 已由 `mcp_Adder` 触发）：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex
```

无需另开终端手动启动 Qwen/Claude；**不要**使用纯 langchain API 或「仅 MCP、无 loop」模式。

---

## 应该看哪个 README？

| 我想… | 看这个 |
|-------|--------|
| 安装、监督式 Codex 说明 | **本文件** · [`supervised-codex.md`](/examples/_shared/supervised-codex.md) |
| 浏览全部 case | [`examples/README.md`](/examples/README.md) |
| 某个具体 case | `examples/.../<dut>/README.md` |
| 改 workflow / checker | [`docs/content/03_develop/03_workflow.md`](/docs/content/03_develop/03_workflow.md) |

### Case README 索引

| Case | README |
|------|--------|
| Adder | [`examples/01-baseline/adder/README.md`](/examples/01-baseline/adder/README.md) |
| Mux | [`examples/01-baseline/mux/README.md`](/examples/01-baseline/mux/README.md) |
| Adder 增量 | [`examples/01-baseline/increment/README.md`](/examples/01-baseline/increment/README.md) |
| uart_16550 | [`examples/02-peripheral-ip/uart_16550/README.md`](/examples/02-peripheral-ip/uart_16550/README.md) |
| Sbuffer | [`examples/03-microarch/Sbuffer/README.md`](/examples/03-microarch/Sbuffer/README.md) |
| IntegerDivider / ALU754 | [`integer-divider`](/examples/04-algorithm/integer-divider/README.md) · [`ieee754-alu`](/examples/04-algorithm/ieee754-alu/README.md) |
| Formal | [`Adder`](/examples/05-formal/Adder/README.md) · [`arbiter`](/examples/05-formal/arbiter/README.md) · [`traffic`](/examples/05-formal/traffic/README.md) |
| GenSpec / Gencov | [`genspec`](/examples/06-planning/genspec/README.md) · [`gencov`](/examples/06-planning/gencov/README.md) |

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `make example-baseline` | Adder UT |
| `make example-bug` | Mux bug |
| `make example-formal` | Formal arbiter |
| `make mcp_<DUT>` | 任意 UT DUT（自动 workflow） |
| `make formal_mcp_<DUT>` | Formal（含 `--use-skill`） |

---

## 仓库结构

```
Agentic-Verification/
├── README.md
├── veriagent/              # Runtime（默认 backend=codex）
├── examples/               # case + workflow + skills
└── Makefile                # VERIAGENT_SUPERVISED_CODEX 标准参数
```

---

## 延伸阅读

- [监督式 Codex 说明](/examples/_shared/supervised-codex.md)
- [Web Master](/docs/content/02_usage/07_web_master.md) · [TUI](/docs/content/02_usage/04_tui.md) · [FAQ](/docs/content/02_usage/05_faq.md)
