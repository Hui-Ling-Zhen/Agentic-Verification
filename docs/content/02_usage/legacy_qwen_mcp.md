# Legacy Qwen MCP

!!! warning "历史兼容模式"
    本页保留旧 Qwen Code + 被动 MCP 的使用方式，便于兼容旧流程和排障。新任务请优先使用监督式 Codex SDK：`--backend=codex_app_server --loop --config examples/.../workflow/*.yaml`。

## 模式说明

旧 Qwen MCP 模式需要两个进程：

1. VeriAgent 启动 MCP server 和 TUI。
2. Qwen Code 在另一个终端作为 MCP client 连接 VeriAgent。

该模式可以调用 VeriAgent 的 MCP 工具，但外层 runtime 无法可靠获得 Qwen 的 turn/event 信息，因此不具备官方 Codex SDK 路径的完整监督能力。

## 准备工作

安装 Qwen Code CLI：

```bash
npm install -g @qwen-code/qwen-code
```

配置 `~/.qwen/settings.json`：

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

## 启动 VeriAgent MCP server

示例仍需显式传入 workflow：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --backend=qwen
```

也可以只把 VeriAgent 作为 MCP 工具服务使用，但该方式不再作为推荐路径。

## 启动 Qwen Code

另开一个终端，进入 workspace：

```bash
cd output/workspace_Adder
qwen
```

建议初始提示：

```text
请通过工具 RoleInfo 获取你的角色信息和基本指导，然后完成任务。请使用工具 ReadTextFile 读取文件。你需要在当前工作目录进行文件操作，不要超出该目录。
```

## 注意事项

- 该模式需要人工观察 TUI 判断阶段是否卡住。
- 外部 Qwen 的 turn/event 不会像 `codex_app_server` 一样进入 `.veriagent/codex_events.jsonl`。
- 如果 Qwen 停止但 stage 未完成，需要手动输入“继续”或检查 `Check` / `Complete` 返回。
- 对新 example 和 benchmark，请使用监督式 Codex SDK 路径。
