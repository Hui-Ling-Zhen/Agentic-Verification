# FIFO Coverage Closure — Directed Tests from Coverage Gaps

## 验证故事

本例展示 **Agent 读取 coverage report 并自动补 directed tests** 的流程。传统方式通常由验证工程师人工查看 coverage 缺口、判断缺失场景、手写 directed tests；本例把 coverage report 作为 VeriAgent stage 输入，让 Codex 在外层 checker 约束下生成 gap analysis、directed tests 和 closure report。

## 难度

预计 Agent 轮次：中 | Mock：否 | Formal：否 | 人工审查：可选

## 前置条件

- Python 3.11+、`picker`、OpenAI Codex binary / app-server SDK、VeriAgent 依赖
- `OPENAI_API_KEY` / `OPENAI_API_BASE` / `OPENAI_MODEL`

## 监督式 Codex 运行

| 项 | 值 |
|----|-----|
| Workflow | `examples/07-coverage/workflow/coverage_closure.yaml` |
| Initial coverage report | `FIFO/coverage_report_initial.md` |

```bash
make example-coverage
# 或：make mcp_FIFO DUT_SRC_DIR=examples/07-coverage/fifo_coverage CFG=examples/07-coverage/workflow/coverage_closure.yaml
```

等价 CLI：

```bash
veriagent output/workspace_FIFO/ FIFO \
  --config examples/07-coverage/workflow/coverage_closure.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

## DUT 说明

`FIFO.v` 是一个 4-depth、8-bit 的同步 FIFO，包含：

- `push` / `pop`
- `data_in` / `data_out`
- `full` / `empty`
- `count`
- read/write pointer wrap-around

## 初始 Coverage Gap

`coverage_report_initial.md` 故意留下几个未覆盖 bins：

- `<COV-FULL-PUSH-BLOCK>`：FIFO full 时继续 push，应保持 `count==DEPTH` 且不覆盖旧数据。
- `<COV-EMPTY-POP-BLOCK>`：FIFO empty 时 pop，应保持 `count==0` 且不产生非法读。
- `<COV-WRAPAROUND>`：write/read pointer wrap-around 后数据顺序仍正确。
- `<COV-SIMULTANEOUS-PUSH-POP>`：非空非满时同时 push/pop，`count` 应保持不变。

## Mutation Demo 结果

为了展示 directed tests 的实际效果，本例提供一个纯 Python 沙箱实验：

```bash
cd examples/07-coverage
make mutation-demo
```

实验比较两组测试：

- `smoke_baseline`：只覆盖 reset、单次 push/pop、基本 FIFO order。
- `gap_directed`：从 initial coverage report 的 uncovered bins 出发，补 full push block、empty pop block、wrap-around、simultaneous push/pop。

当前结果：

| Test set | Golden passes | Covered bins | Initial gaps hit | Mutations detected |
|----------|---------------|--------------|------------------|--------------------|
| `smoke_baseline` | True | `8/12` | `0/4` | `0/4` |
| `gap_directed` | True | `12/12` | `4/4` | `4/4` |

Injected mutations:

| Mutation | Smoke | Directed |
|----------|-------|----------|
| `MUT-FULL-PUSH-OVERWRITE` | missed | detected |
| `MUT-EMPTY-POP-UNDERFLOW` | missed | detected |
| `MUT-NO-POINTER-WRAP` | missed | detected |
| `MUT-SIM-PUSH-POP-COUNT` | missed | detected |

完整报告：[`mutation_report.md`](mutation_report.md)，结构化结果：[`mutation_report.json`](mutation_report.json)。

这个结果不表示 Agent 天然比资深验证工程师更会写测试。它展示的是：当 coverage gaps 明确时，supervised agent workflow 可以系统地把 gap 转成 directed tests，并用 checker/manifest 保留 closure evidence。人的角色从“逐个手写第一版 directed tests”转为“审查 test intent、剩余风险和最终 closure 质量”。

## 预期产物

- `{OUT}/FIFO_coverage_gap_analysis.md`
- `{OUT}/FIFO_directed_test_plan.md`
- `{OUT}/tests/test_fifo_coverage_directed.py`
- `{OUT}/FIFO_coverage_closure_report.md`

## 与 Agentic Verification 的关系

这是一个 **agent 优于纯脚本/人工流程** 的展示 case：

- 传统模式：人工读 coverage report，手动设计 directed tests。
- Agentic-Verification 模式：VeriAgent 把 coverage gap 固化为阶段任务和 checker；Codex 负责把 gap 转成可执行 directed tests；manifest 记录 stage、checker、turn trace 和 artifact 质量。

## 延伸阅读

- [07-coverage 索引](../README.md)
- [Examples 索引](../../README.md)
- [根 README](../../../README.zh.md)
