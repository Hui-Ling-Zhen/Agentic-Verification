## GenCov — IFU 功能覆盖率

> 属于 [06-planning](../README.md) 故事线：HVP → 功能覆盖率模型。

## 验证故事

将 IFU 验证计划（HVP）中的测试点转换为可实现的功能覆盖率逻辑，并做一致性检查。

## 难度

预计 Agent 轮次：高 | Mock：否 | Formal：否 | 人工审查：可选

## 最小运行子集

完整 IFU 材料较大，建议 Agent **优先阅读**：

| 类型 | 路径 | 说明 |
|------|------|------|
| HVP | `IFU/hvp/IFU_verification_plan.hvp` 或 `IFU/spec/bosc_IFU_verification_plan.hvp` | 测试点来源 |
| 规格摘要 | `IFU/spec/bosc_IFU_spec_summary.md` | 功能概览 |
| RTL | `IFU/rtl/bosc_Ifu.sv` | 顶层 RTL |
| Chisel（选读） | `IFU/chisel/Ifu.scala`, `PreDecode.scala`, `PredChecker.scala` | 行为理解 |

其余 `IFU/chisel/*.scala` 与 `IFU/spec/bosc_IFU_spec_*.md` 可在 augment 阶段按需 Walk。

## 目录结构

- `IFU/` — 输入材料（hvp / rtl / doc / chisel）
- `GenCov/` — `gencov.yaml`、一致性脚本、skeletons
- `Makefile` — 启动入口

## 监督式 Codex 运行

Workflow：`examples/06-planning/gencov/GenCov/gencov.yaml`

```bash
make -C examples/06-planning/gencov init_IFU
make -C examples/06-planning/gencov gencov_IFU
```

```bash
veriagent output/ IFU \
  --config examples/06-planning/gencov/GenCov/gencov.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex \
  --no-embed-tools
```

## 快速运行

## 与默认 11-stage UT 的关系

Gencov **不跑完整 UT**，产出覆盖率骨架与 FG/FC/CK 对齐检查，供后续 UT（如 01-baseline+）引用。

更多说明：`GenCov/USAGE.md`
