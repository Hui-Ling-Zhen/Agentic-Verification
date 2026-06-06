# Agentic-Verification

面向硬件的 **Agentic Verification** 平台 —— CLI **`veriagent`**

[English](/README.en.md) · [GitHub](https://github.com/Hui-Ling-Zhen/Agentic-Verification) · [全部示例](/examples/README.md) · [开发者文档](/docs/content/00_index.md)

---

## 项目是什么

**Runtime（VeriAgent）** 负责阶段机、Checker、MCP 验证工具与监督循环；**Codex** 负责每轮读 RTL、写测试与复杂代码修改。

**官方验证路径 = 监督式 Codex SDK**（`--backend=codex_app_server` + MCP + `--loop`）。其它 backend（`codex` CLI、`langchain`、纯 MCP 无 loop 等）为 **compatibility-only legacy**。

Workflow **外置**于 `examples/*/workflow/`，必须通过 **`--config`** 显式传入。见 [`examples/_shared/supervised-codex.md`](/examples/_shared/supervised-codex.md)。

### 设计思路：反复检查，而不是一次性生成

Agentic-Verification 的核心循环很简单：**让 Codex 推进一步，运行 Checker 检查结果，把失败原因反馈给 Codex，再重复直到阶段通过**。VeriAgent 不试图替代 Codex 成为通用代码 Agent，而是用外置 workflow、确定性的 Checker、验证领域 MCP 工具、人工检查点和可度量的 `run_manifest.json` 监督 Codex。

因此官方路径是双层 runtime：Codex 负责内层读写、调试和修改；VeriAgent 负责外层验证契约。每个阶段都应该以 `Check` / `Complete` 闭环，而不是只产出一段看起来合理的回答。

---

## 环境要求

- Python 3.11+，Linux / macOS，建议 4GB+ 内存
- [OpenAI Codex](https://github.com/openai/codex) 可执行文件（`codex` 在 `PATH` 中，或通过 `CODEX_BIN` 指定）
- MCP Python 包（`mcp`），由 `requirements.txt` 安装
- OpenAI Codex 开源 SDK：`codex/sdk/python` / package `openai-codex-app-server-sdk`，可 import 为 `codex_app_server`
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
pip3 install -e .
git clone https://github.com/openai/codex ../codex
pip3 install -e ../codex/sdk/python
# SDK editable install 不会提供 codex binary；还需要安装或构建 OpenAI Codex：
npm install -g @openai/codex  # 或：brew install --cask codex
export CODEX_BIN="$(which codex)"
python -c "import codex_app_server; print('ok: codex_app_server')"
codex --version
codex app-server --help >/dev/null
picker --version
veriagent --check
```

**首次运行（Adder 基线）：**

```bash
make example-baseline
```

等价于（仓库根目录，先 `make init_Adder` 已由 `mcp_Adder` 触发）：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

无需另开终端手动启动外部 Code Agent。**不要**使用旧 `codex` CLI、langchain API 或「仅 MCP、无 loop」作为主路径。**必须**提供 `--config`，Runtime 不内置 UT/Formal workflow。

Codex SDK thread 默认受 DUT / workflow / workspace 输入 / backend 参数指纹保护；只有确认要跨指纹复用旧 thread 时才使用 `--resume-codex-thread`。

Sandbox 说明：`.codex/config.toml` 中的 `veriagent_policy` 是审计提示，不是强制策略引擎。真正的强边界来自 Codex sandbox、`writable_roots` 和输入目录的 OS 只读权限。默认 `codex_network_access=enabled`；不需要联网的 case 建议显式关闭：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server \
  --override backend.codex_app_server.args.codex_network_access=disabled
```

---

## 可度量产出（Benchmark）

每次运行在 workspace 下启动即写入 `.veriagent/run_manifest.json`，随后在 backend/stage 初始化、每个 Codex turn 之后、stage 保存时继续更新。manifest 记录 backend 状态（`official` 或 compatibility-only `legacy`）、run 状态、DUT、workflow、阶段进度、耗时、最后一个 Codex thread/turn、token、MCP tool 次数、文件变更数、失败原因与 sandbox/policy 审计字段。SDK 事件追加到 `.veriagent/codex_events.jsonl`。汇总：

```bash
make benchmark   # → benchmark/summary.csv、benchmark/runs.json
```

详见 [benchmark/README.md](/benchmark/README.md)。

---

## Backend 状态

| 路径 | 状态 |
|------|------|
| 监督式 Codex SDK（`--backend=codex_app_server` + MCP + `--loop`） | **官方 / 已测试** |
| Codex CLI（`--backend=codex`） | Compatibility-only legacy fallback，黑盒 `codex exec` 路径，不提供 SDK thread/turn/event/manifest 契约 |
| `langchain` / 纯 API | Compatibility-only legacy，本仓库不作为 benchmark 对比路径维护 |
| 被动 MCP（无 `--loop`） | Compatibility-only legacy |

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
| `make benchmark` | 汇总 run_manifest.json |

---

## 仓库结构

```
Agentic-Verification/
├── README.md
├── veriagent/              # Runtime（默认 backend=codex_app_server）
├── examples/               # case + workflow + skills
└── Makefile                # VERIAGENT_SUPERVISED_CODEX 标准参数
```

---

## 延伸阅读

- [监督式 Codex 说明](/examples/_shared/supervised-codex.md)
- [Web Master](/docs/content/02_usage/07_web_master.md) · [TUI](/docs/content/02_usage/04_tui.md) · [FAQ](/docs/content/02_usage/05_faq.md)
