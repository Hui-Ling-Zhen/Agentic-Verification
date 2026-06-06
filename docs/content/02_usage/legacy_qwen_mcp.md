# Legacy 外部 MCP

!!! warning "历史兼容模式"
    本页保留旧外部 Code Agent + 被动 MCP 的通用说明，便于兼容旧流程和排障。新任务请优先使用监督式 Codex SDK：`--backend=codex_app_server --mcp-server-no-file-tools --loop --config examples/.../workflow/*.yaml`。

## 模式说明

旧外部 MCP 模式需要两个进程：

1. VeriAgent 启动 MCP server 和 TUI。
2. 外部 MCP client 在另一个终端连接 VeriAgent。

该模式可以调用 VeriAgent 的 MCP 工具，但外层 runtime 无法可靠获得外部 client 的 turn/event 信息，因此不具备官方 Codex SDK 路径的完整监督能力，也不会提供同等质量的 `run_manifest.json` / `codex_events.jsonl`。

## 通用 MCP Client 配置

不同外部 client 的配置文件位置不同。核心是把 MCP URL 指向 VeriAgent：

```json
{
  "mcpServers": {
    "veriagent": {
      "httpUrl": "http://localhost:5000/mcp",
      "timeout": 10000
    }
  }
}
```

外部 client 的安装和登录不属于 Agentic-Verification 官方依赖；请按对应工具自己的文档准备。

## 启动 VeriAgent MCP server

示例仍需显式传入 workflow：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s \
  --backend=<legacy-backend>
```

该方式不包含 `codex_app_server` 的 thread/turn/event contract，仅用于旧流程兼容。

## 注意事项

- 该模式需要人工观察 TUI 判断阶段是否卡住。
- 外部 client 的 turn/event 不会像 `codex_app_server` 一样进入 `.veriagent/codex_events.jsonl`。
- 如果外部 client 停止但 stage 未完成，需要手动继续或检查 `Check` / `Complete` 返回。
- 对新 example、benchmark 和可复现实验，请使用监督式 Codex SDK 路径。
