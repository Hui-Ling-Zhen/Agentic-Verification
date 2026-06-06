# Legacy 被动 MCP 模式

!!! warning "非官方主路径"
    当前官方验证路径是 **监督式 Codex SDK**：`--backend=codex_app_server` + `--loop` + `--config examples/.../workflow/*.yaml`。请优先阅读 [快速入门](../01_start/02_quickstart.md) 和仓库中的 `examples/_shared/supervised-codex.md`。

被动 MCP 模式指的是：VeriAgent 只启动 MCP server，另一个外部 Code Agent 客户端连接该 MCP server，并由用户在另一个终端手动推动任务。这是历史兼容模式，不具备官方 SDK 路径的完整 turn/event/manifest 可观测性。

## 为什么降级为 Legacy

与 `codex_app_server` 相比，被动 MCP 模式存在几个结构性限制：

- 外层 VeriAgent runtime 不能稳定感知外部 Agent 的每个 turn。
- 失败、暂停、审批和工具调用状态不能统一进入 backend turn contract。
- `.veriagent/codex_events.jsonl` 和 `run_manifest.json` 无法完整记录内层 Agent 行为。
- 需要用户手动维护两个进程和上下文，容易出现阶段状态与 Agent 对话状态不一致。

## 仍然适用的场景

该模式只建议用于：

- 兼容旧外部 Code Agent MCP 客户端。
- 调试 VeriAgent MCP 工具本身。
- 对比不同 Code Agent 的工具调用行为。

如果目标是运行本仓库 examples，请使用：

```bash
make example-baseline
```

或显式 CLI：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s \
  --loop \
  --backend=codex_app_server
```

## 旧外部 MCP 文档

旧外部 Code Agent 双终端流程已移到 [Legacy 外部 MCP](legacy_qwen_mcp.md)。该页面仅用于兼容和排障，不作为新用户 onboarding 路径。
