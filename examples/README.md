# Examples 索引

`examples/` 只放 **真实 DUT 验证 case**：每个 case 都有 DUT、workflow、checker/skill 入口，并可以通过 `make example-*`、`make mcp_*` 或 `make formal_mcp_*` 运行。

本目录不放 benchmark/ablation 实验设计，也不放 synthetic 数据生成脚本：

- A/B/C runtime 对比实验在 [`benchmark/ablation/README.md`](../benchmark/ablation/README.md)。
- benchmark 聚合说明在 [`benchmark/README.md`](../benchmark/README.md)。
- 自动化脚本说明在 [`scripts/README.md`](../scripts/README.md)。

每个 **case** 的说明在其目录下的 **`README.md`**。本文件只做导航，不重复 case 内容。

操作与安装见仓库根目录 [README.zh.md](../README.zh.md) / [README.en.md](../README.en.md)。

**运行方式：** 全仓库 [**监督式 Codex**](_shared/supervised-codex.md)（`--mcp-server-no-file-tools --loop --backend=codex_app_server`）。`make mcp_*` / `make formal_mcp_*` 已内置该参数。

---

## 推荐学习顺序

1. [Adder UT 基线](01-baseline/adder/README.md) — `make example-baseline`
2. [Mux bug 分析](01-baseline/mux/README.md) — `make example-bug`
3. [Adder 增量](01-baseline/increment/README.md) — `make example-increment`（需先完成 1）
4. [uart_16550](02-peripheral-ip/uart_16550/README.md) — `make example-peripheral`
5. [Sbuffer flagship](03-microarch/Sbuffer/README.md) — `make example-flagship`
6. [IntegerDivider](04-algorithm/integer-divider/README.md) — `make example-algorithm`
7. [Formal arbiter](05-formal/arbiter/README.md) — `make example-formal`
8. [GenSpec / Gencov](06-planning/README.md) — 高级规划（可选）

如果想比较 supervised Codex / raw Codex / legacy Codex 的双层 runtime 优势，请看 [`benchmark/ablation/README.md`](../benchmark/ablation/README.md)。这不是新的 DUT case，而是基于现有 case 的 benchmark/ablation 实验。

---

## 全部 Case 一览

| # | Case | README | 根目录命令 | 难度 |
|---|------|--------|------------|:----:|
| 1 | Adder | [01-baseline/adder/README.md](01-baseline/adder/README.md) | `make example-baseline` | ⭐ |
| 2 | Mux | [01-baseline/mux/README.md](01-baseline/mux/README.md) | `make example-bug` | ⭐⭐ |
| 3 | Adder increment | [01-baseline/increment/README.md](01-baseline/increment/README.md) | `make example-increment` | ⭐⭐ |
| 4 | uart_16550 | [02-peripheral-ip/uart_16550/README.md](02-peripheral-ip/uart_16550/README.md) | `make example-peripheral` | ⭐⭐⭐ |
| 5 | Sbuffer | [03-microarch/Sbuffer/README.md](03-microarch/Sbuffer/README.md) | `make example-flagship` | ⭐⭐⭐⭐⭐ |
| 6 | IntegerDivider | [04-algorithm/integer-divider/README.md](04-algorithm/integer-divider/README.md) | `make example-algorithm` | ⭐⭐⭐⭐ |
| 7 | ALU754 | [04-algorithm/ieee754-alu/README.md](04-algorithm/ieee754-alu/README.md) | `make mcp_ALU754` | ⭐⭐⭐⭐ |
| 8 | Formal Adder | [05-formal/Adder/README.md](05-formal/Adder/README.md) | `make formal_mcp_Adder` | ⭐⭐⭐ |
| 9 | Formal arbiter | [05-formal/arbiter/README.md](05-formal/arbiter/README.md) | `make example-formal` | ⭐⭐⭐ |
| 10 | Formal traffic | [05-formal/traffic/README.md](05-formal/traffic/README.md) | `make formal_mcp_traffic` | ⭐⭐⭐⭐ |
| 11 | GenSpec DCache | [06-planning/genspec/README.md](06-planning/genspec/README.md) | 见 case README | ⭐⭐⭐⭐ |
| 12 | Gencov IFU | [06-planning/gencov/README.md](06-planning/gencov/README.md) | 见 case README | ⭐⭐⭐⭐ |

---

## 故事线目录（仅分类）

| 目录 | 主题 | 本层 README 作用 |
|------|------|------------------|
| [01-baseline](01-baseline/README.md) | UT 入门 / bug / 增量 | 列出本线 case，详情在子目录 |
| [02-peripheral-ip](02-peripheral-ip/README.md) | 外设 IP | 同上 |
| [03-microarch](03-microarch/README.md) | Mock + 黑盒 | 同上 |
| [04-algorithm](04-algorithm/README.md) | 算法 RTL | 同上 |
| [05-formal](05-formal/README.md) | 形式化 | 同上 |
| [06-planning](06-planning/README.md) | Spec / 覆盖率规划 | 同上 |

各故事线共享资源（不单独写 README）：

- **Workflow：** `examples/<storyline>/workflow/*.yaml`
- **Skills：** `examples/<storyline>/skills/`
- **运行方式：** [_shared/supervised-codex.md](_shared/supervised-codex.md)
- **新 case 模板：** [_shared/README.template.md](_shared/README.template.md)

框架级 workflow schema：[`veriagent/lang/zh/config/README.md`](../veriagent/lang/zh/config/README.md)
