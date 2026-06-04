# Mux — 4 选 1 多路选择器（含故意缺陷）

## 验证故事

RTL 在 `sel=2'b11` 时错误选择 `in_data[0]`，Agent 需通过 failing test 发现 bug、写定向用例并完成根因分析。

## 难度

预计 Agent 轮次：低–中 | Mock：否 | Formal：否 | 人工审查：否

## 前置条件

- 同 Adder；需已安装 **Codex CLI**

## 监督式 Codex 运行

| 项 | 值 |
|----|-----|
| Workflow | `examples/01-baseline/workflow/default.yaml` |

```bash
make example-bug
# 或：make mcp_Mux
```

```bash
veriagent output/workspace_Mux/ Mux \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

## 快速运行

## 验证关注点

- `<CK-SEL-11>`：`sel=11` 应选 `in_data[3]`，当前 RTL 选错
- 四路选择基本功能
- bug 分析文档与定向测试 `test_mux_sel_11_bug.py`

## 预期产物

- `Mux_bug_analysis.md`（含根因与修复建议）
- 触发 bug 的 failing test

## 已知缺陷（题目设定）

```verilog
// sel=2'b11 时 default 分支错误地选择了 in_data[0]
default: out = in_data[0];  // 应为 in_data[3]
```

参考 golden（可选）：[`../golden/mux/`](../golden/mux/)

## 与 Agentic Verification 的关系

演示 **Agent 在 Checker/test 驱动下的缺陷定位能力**，衔接 Adder 基线与更复杂 DUT。

## 延伸阅读

- [Examples 索引](../../README.md)
- [根 README](../../../README.zh.md)
