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

### 双层架构：用一个 agent runtime 构建另一个 agent runtime

Agentic-Verification 的目标不是把一个 prompt 丢给 LLM，而是让 **VeriAgent 监督 Codex**。

| 层级 | 职责 |
|------|------|
| **内层 agent runtime：Codex** | 读取 RTL/spec、修改文件、运行命令、流式输出事件，并维护 Codex thread/turn 状态。 |
| **外层 supervisor runtime：VeriAgent** | 维护 workflow 阶段、Checker、验证域 MCP 工具、结构化 journal、policy 检查、失败恢复上下文和 benchmark manifest。 |

官方 backend `veriagent/abackend/codex_sdk.py` 已经不是黑盒 CLI 调用，而是通过 OpenAI Codex app-server SDK 管理 Codex 的 **thread**、**turn**、**event stream**、**approval handler** 和 **turn context**。旧 `codex exec` backend 只作为 compatibility-only fallback 保留，因为它没有 SDK 的 thread/turn/event 契约。

VeriAgent 会把 Codex event 提升成 supervisor signal：

- command risk、protected input diff、MCP startup error、plan/stage mismatch 会进入 `codex_turn_trace` 和 `codex_supervisor_signals`；
- failed turn 会把结构化 recovery context 带到下一轮 Codex，而不是只留下普通文本错误；
- approval request 会由 VeriAgent policy 决策，并记录 approve/deny reason。

每个 Codex turn 前，**`VeriAgentTurnContext`** 会把当前 stage goal、checker feedback、read requirements、journal、previous supervisor signals 和 recovery context 结构化传给 Codex。这比普通 prompt 拼接更接近 runtime contract。

阶段完成前还必须写入可审计 journal。`SetCurrentStageJournal` 强制字段：

```json
{
  "plan": "...",
  "evidence_read": ["..."],
  "changes_made": ["..."],
  "checker_result": "...",
  "next_risk": "..."
}
```

这体现了当前架构的分工：**Codex 负责探索和实现，VeriAgent 负责要求可审计的推理轨迹和验证闭环。**

### Demo 对比结果：为什么双层 runtime 有优势

当前 ablation demo 在同一个 Adder 任务形态上比较三种模式：

| 模式 | 阶段度量方式 | 是否完成 | 阶段通过 | 恢复能力 | artifact 质量 | 说明 |
|------|--------------|----------|----------|----------|----------------|------|
| `A_agent_for_agent_runtime` | Runtime-observed | 是 | `4/4` | `1` 个阶段恢复 | `0.93` | VeriAgent 把 workflow、checker、skill 状态放在 Codex 外层，并把 checker feedback 和 supervisor signals 注入下一轮。 |
| `B_single_layer_llm_agent` | Post-hoc artifact review | 否 | `2/4` | `N/A` | `0.62` | 单层 prompt 能生成看起来合理的文档，但没有外层 stage/checker runtime，因此 stage recovery 不可观测。 |
| `C_black_box_agent_backend` | Runtime-observed | 否 | `2/4` | `0` | `0.55` | `codex exec` 可作为 fallback，但缺少 SDK thread/turn/event 信号，内层状态对 VeriAgent 不透明。 |

这里的“恢复能力”指：VeriAgent 观测到某个 stage 因 checker 失败，然后通过结构化 feedback/supervisor signals 让该 stage 后续完成。对单层 LLM baseline 来说，这个指标是 `N/A` 而不是 `0`，因为没有 runtime stage loop 可以观测恢复过程。

这个 benchmark 的目标不是证明“LLM 能不能一次性写出看起来合理的文本”，而是衡量 **外层 supervisor runtime 是否带来可观测的验证价值**。因此三种模式使用同一个 DUT/task 形态，但把 runtime-observed progress 和 post-hoc artifact review 分开：

- A 衡量官方 agent-for-agent 路径：VeriAgent 可以观测 stage、checker、Codex event、recovery 和最终 artifact。
- B 衡量单层 LLM/Codex agent：artifact 可以事后审阅，但 runtime 中没有可观测的 stage recovery。
- C 衡量 legacy 黑盒 backend：VeriAgent 仍有外层 loop，但内层 Codex 状态不透明。

`artifact_quality_score` 是 0-1 加权 reward：

| 组成项 | 权重 | 为什么重要 |
|--------|------|------------|
| Stage completion | `0.30` | 奖励完成 workflow 要求的阶段，而不是只产出部分 notes。 |
| Checker result quality | `0.20` | 奖励 checker 通过，或产生可行动的 checker feedback。 |
| Required artifact completeness | `0.20` | 奖励生成 plan、basic-info、functions/checks、test 等必需产物。 |
| Journal/evidence auditability | `0.15` | 奖励结构化 journal、evidence read 和 changed-artifact trace。 |
| Recovery feedback usage | `0.10` | 奖励利用 checker feedback 或 supervisor signals 从失败阶段恢复。 |
| Reproducibility/trace quality | `0.05` | 奖励 manifest、turn trace、command trace、policy trace 的完整性。 |

这个 reward 有意奖励 **可审计的验证进展**，而不是单纯奖励速度或流畅但不可验证的输出。

这个结果想说明的不是“哪个最快”，而是双层 runtime 能让进展 **可审计、可恢复、可度量**：失败会变成 checker feedback，Codex event 会变成 supervisor signal，最终 manifest 会记录证据。完整报告见 [`benchmark/ablation/report.md`](/benchmark/ablation/report.md)，也可以重新生成：

```bash
make ablation-benchmark
```

### Demo 对比结果：coverage gap directed tests

FIFO coverage-closure demo 展示了：把 coverage gaps 作为 agent 输入后，生成的 directed tests 比普通 smoke baseline 更能覆盖 corner case：

| Test set | Covered bins | Initial gaps hit | Injected mutations detected |
|----------|--------------|------------------|-----------------------------|
| `smoke_baseline` | `8/12` | `0/4` | `0/4` |
| `gap_directed` | `12/12` | `4/4` | `4/4` |

这不表示 Agent 替代资深验证工程师，而是说明 supervised agent workflow 可以系统地把明确 coverage gap 转成 directed tests 和可审计 closure evidence。完整报告见 [`examples/07-coverage/fifo_coverage/mutation_report.md`](/examples/07-coverage/fifo_coverage/mutation_report.md)，也可以重新生成：

```bash
make -C examples/07-coverage mutation-demo
```

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

每次运行在 workspace 下启动即写入 `.veriagent/run_manifest.json`，随后在 backend/stage 初始化、每个 Codex turn 之后、stage 保存时继续更新。SDK 事件追加到 `.veriagent/codex_events.jsonl`。

manifest 是衡量外层 supervisor 价值的主要产物：

- `stage_trace`：阶段进展、checker feedback、journal、reference/output evidence、skill usage；
- `codex_turn_trace`：Codex plan、diff、command、approval、MCP startup 状态和未来未知事件；
- `checker_retry_total`：外层 Checker 迫使 Codex 重试的次数；
- `stage_recovery_count`：失败后恢复并完成的阶段数量；
- `skill_usage_summary`：workflow 要求的 skill 是否被 list/read/use；
- `codex_supervisor_signals`：command risk、protected input touch、MCP startup error、plan mismatch、approval decision；
- sandbox/policy 审计字段：`protected_inputs`、`writable_roots`、`network_access`、`policy_enforcement`。

汇总：

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
| Coverage Closure | [`FIFO`](/examples/07-coverage/fifo_coverage/README.md) · mutation demo：smoke `0/4` vs directed `4/4` injected bugs |

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `make example-baseline` | Adder UT |
| `make example-bug` | Mux bug |
| `make example-formal` | Formal arbiter |
| `make example-coverage` | FIFO coverage closure |
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
