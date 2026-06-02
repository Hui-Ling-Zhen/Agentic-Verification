# Case README 模板

复制到 `examples/<storyline>/<dut>/README.md`。运行方式见 [`supervised-codex.md`](supervised-codex.md)。

## 验证故事

一句话：{本例证明 VeriAgent 能做什么}

## 难度

预计 Agent 轮次：{N} | Mock：{是/否} | Formal：{是/否} | 人工审查：{是/否}

## 前置条件

- {picker / docker / 环境变量等}

## 快速运行

```bash
{make xxx}
```

## 验证关注点（FG/FC/CK 摘要）

- {3~5 个关键检测点}

## 预期产物

- 文档：{...}
- 代码：{...}
- 不预置 golden 产物（参考输出见 `golden/` 目录，如有）

## 与 Agentic Verification 的关系

{本例在整体研究/演示中扮演的角色}

## 延伸阅读

- [Examples 索引](../README.md)
- [根 README](../../README.zh.md)
