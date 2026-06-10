# 07-coverage — Coverage Closure

本故事线展示 Agentic-Verification 在 **coverage closure** 场景中的优势：Agent 读取已有 coverage report，理解缺失 bins，生成 directed tests，并用 checker 约束 closure report。

| Case | README | 命令 |
|------|--------|------|
| FIFO coverage closure | [fifo_coverage/README.md](fifo_coverage/README.md) | `make example-coverage` |

**Workflow：** [workflow/coverage_closure.yaml](workflow/coverage_closure.yaml)

**对比叙事：**

- 传统模式：人工查看 coverage report，手工判断 gap，手写 directed tests，再反复跑回归。
- Agent 模式：VeriAgent 把 coverage gap 作为 stage 输入，Codex 负责分析缺口并生成 directed tests，checker 要求 gap analysis、test plan 和 closure report 可审计。

**Mutation demo 结果：** `smoke_baseline` 覆盖 `8/12` bins、命中 `0/4` 初始 gaps、检测 `0/4` injected mutations；`gap_directed` 覆盖 `12/12` bins、命中 `4/4` gaps、检测 `4/4` mutations。运行：

```bash
make mutation-demo
```

**索引：** [examples/README.md](../README.md)
