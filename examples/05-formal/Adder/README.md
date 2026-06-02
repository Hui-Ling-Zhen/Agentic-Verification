# Formal Adder — Smoke Test

> **5 分钟 smoke test**：确认 Formal workflow 与监督式 Codex 环境可用。  
> **完整 UT 请使用** [01-baseline/adder](../../01-baseline/adder/README.md)。

## 监督式 Codex 运行

| 项 | 值 |
|----|-----|
| Workspace | `examples/05-formal/output/workspace_Adder/` |
| Workflow | `examples/05-formal/workflow/formal.yaml` |
| 额外 | `--use-skill`、`--output formal_test` |

```bash
make formal_mcp_Adder
```

```bash
veriagent examples/05-formal/output/workspace_Adder/ Adder \
  --config examples/05-formal/workflow/formal.yaml \
  --guid-doc-path veriagent/lang/zh/doc/Formal_Doc/ \
  --output formal_test \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex \
  --use-skill
```

## 预期

- 少量算术 SVA（溢出、结果正确性）
- 快速得到 `avis.log` 通过/失败摘要

## 延伸阅读

- [05-formal 索引](../README.md) · [`supervised-codex.md`](../../_shared/supervised-codex.md)
