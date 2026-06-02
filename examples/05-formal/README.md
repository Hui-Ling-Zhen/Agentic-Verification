# 05-formal — 形式化验证

UT 基线见 [01-baseline/adder](../01-baseline/adder/README.md)。本线演示 SVA + FormalMC 范式。

| Case | README | 命令 |
|------|--------|------|
| Adder（smoke） | [Adder/README.md](Adder/README.md) | `make formal_mcp_Adder` |
| arbiter | [arbiter/README.md](arbiter/README.md) | `make example-formal` |
| traffic | [traffic/README.md](traffic/README.md) | `make formal_mcp_traffic` |

**Workflow：** [workflow/formal.yaml](workflow/formal.yaml) · **运行：** [supervised-codex.md](../_shared/supervised-codex.md)（UT 类）/ Formal 见各 case README（含 `--use-skill`）

**索引：** [examples/README.md](../README.md)
