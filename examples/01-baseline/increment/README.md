# Increment — Adder 增量验证

## 验证故事

在已有 Adder 全量验证基线上，对 RTL 做小改动（修位宽 bug + 增加有符号模式），演示 Agent 如何执行**增量验证**而非重写全部测试。

## 难度

预计 Agent 轮次：中 | Mock：否 | Formal：否 | 人工审查：是（`hmcheck_pass` 写入增量需求）

## 前置条件

- **必须先完成** [`01-baseline` 模式 A](../README.md)（`make quick`），基线位于 `01-baseline/output/workspace_Adder/`
- 已安装 `picker`
- 增量配置：[`../workflow/inc.yaml`](../workflow/inc.yaml)

## 监督式 Codex 运行

| 项 | 值 |
|----|-----|
| Workspace | `increment/output/workspace_Adder/` |
| Workflow | `examples/01-baseline/workflow/inc.yaml` |

```bash
make increment
# 或在 increment/ 目录：make init
```

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/inc.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server \
  --no-embed-tools
```

## 快速运行

## 典型流程

1. 完成 Adder 全量验证（`cd .. && make quick`）
2. `make init` — 复制基线到 `increment/output/` 并启动 VeriAgent
3. VeriAgent 终端：`protect_files_off`
4. 新终端：`make diff` — 应用 `Adder_new.v`
5. VeriAgent 终端：`protect_files_on`
6. 人工审核：`hmcheck_pass Adder的bug已修复且增加了有符号加功能，请完成修改部分的验证`
7. 在 VeriAgent TUI / 监督循环中继续：`增量任务已给出，请 Complete 该阶段，从下一个阶段获取具体任务并完成`

## 验证关注点

- 位宽修复后 sum/cout 语义是否正确
- `signed_mode` 有符号与无符号路径
- 增量范围：仅变更相关测试与文档，不全量重写

## 预期产物

- 更新后的 `unity_test/tests/` 中与有符号加法相关的用例
- 增量阶段的 journal 与 diff 记录

## 本例 RTL 变更（`Adder_new.v`）

1. 修复位宽：`sum` 为 `[WIDTH-1:0]`
2. 新增 `signed_mode`：1 时有符号相加，否则无符号

## 与 Agentic Verification 的关系

展示工业场景中最常见的 **design change → 增量 regression** 范式，与默认 11-stage 全量 flow 形成对照。

## 延伸阅读

- [Adder 基线 case](../adder/README.md)（必须先完成）
- [Examples 索引](../../README.md)
- [根 README](../../../README.zh.md)
