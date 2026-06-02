# Adder — 64 位全加器

## 验证故事

用参数化 64 位全加器跑通 VeriAgent 默认 11-stage UT 全流程，作为所有示例的基准。

## 难度

预计 Agent 轮次：低 | Mock：否 | Formal：否 | 人工审查：可选

## 前置条件

- Python 3.11+、`picker`、**Codex CLI**、VeriAgent 依赖
- `OPENAI_API_KEY` / `OPENAI_API_BASE` / `OPENAI_MODEL`（供 Codex 使用）

## 监督式 Codex 运行

| 项 | 值 |
|----|-----|
| Workspace（`make quick`） | `examples/01-baseline/output/workspace_Adder/` |
| Workspace（仓库根） | `output/workspace_Adder/` |
| Workflow | `examples/01-baseline/workflow/default.yaml` |

```bash
make example-baseline
# 或：make mcp_Adder
```

等价 CLI：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex
```

说明：[`_shared/supervised-codex.md`](../../_shared/supervised-codex.md)

## 快速运行（Make）

## 验证关注点（FG/FC/CK 摘要）

- 算术正确性：`{cout, sum} = a + b + cin`
- 端口位宽与参数 `WIDTH` 一致性
- pytest API / fixture 基础结构
- 功能覆盖率 FG/FC/CK 骨架

## 预期产物

- `{OUT}/Adder_verification_needs_and_plan.md`
- `{OUT}/Adder_functions_and_checks.md`
- `{OUT}/tests/Adder_api.py`、功能测试与覆盖率定义

不预置 golden；所有产物由 Agent 运行时生成。

## DUT 说明

### 接口

| 端口 | 方向 | 说明 |
|------|------|------|
| a, b | input | 加数 |
| cin | input | 进位输入 |
| sum | output | 和 |
| cout | output | 进位输出 |

功能：$\{cout, sum\} = a + b + cin$

## 与 Agentic Verification 的关系

**基线 benchmark**：验证 Agent + Stage + Checker 机制是否正常工作。

## 延伸阅读

- [Examples 索引](../../README.md)
- [根 README 操作说明](../../../README.zh.md)
- [工作流文档](../../../docs/content/03_develop/03_workflow.md)
