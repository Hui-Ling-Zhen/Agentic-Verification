# ALU754 — IEEE 754 单精度浮点 ALU

> **Optional**：运行时间与 corner case 数量均高于 IntegerDivider。UT 入门见 [01-baseline/adder](../../01-baseline/adder/)。

## 验证故事

验证 IEEE 754 浮点 ALU 在加减乘除与比较操作下的数值正确性与异常处理。

## 难度

预计 Agent 轮次：很高 | Mock：否 | Formal：否 | 人工审查：可选

## 前置条件

- 同 IntegerDivider
- 可选：`NEED_REF_MODEL=true` 启用参考模型 stage

## 监督式 Codex 运行

```bash
make mcp_ALU754
```

```bash
veriagent output/workspace_ALU754/ ALU754 \
  --config examples/04-algorithm/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

## 快速运行

## 验证关注点

- NaN / Inf 传播与比较
- 舍入模式与 overflow/underflow
- 加、减、乘、除、比较各操作路径

## 预期产物

- ALU 功能测试与覆盖率文档
- 不预置 golden

## 与 Agentic Verification 的关系

04-algorithm **可选** 浮点例，见 [总览](../README.md)。

---

### IEEE 754 ALU

Implemented an IEEE 754 single precision floating-point ALU in Verilog supporting addition, subtraction, multi- plication, division, and comparison, with integrated handling of overflow and underflow conditions.

Source: https://github.com/ThamadaAnkita/IEEE754-Floating-Point-ALU

### 验证目标

只要验证ALU相关的功能，其他验证，例如波形、接口等，不需要出现

### 其他

所有的文档和注释都用中文编写

### bug分析

在bug分析时，请参考源码：ALU754/ 目录下的 *.v 文件
