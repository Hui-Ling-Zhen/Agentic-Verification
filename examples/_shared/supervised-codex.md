# 监督式 Codex（全仓库标准运行方式）

Agentic-Verification **仅支持**这一种接入方式：

| 层 | 职责 |
|----|------|
| **VeriAgent Runtime** | Stage 状态机、`Complete`/`Check`、Checker、每轮注入 `CurrentTips`、MCP 暴露验证工具 |
| **Codex（`--backend=codex`）** | 每轮 `codex exec` 子进程：读 RTL、写 pytest、复杂代码修改 |

## 标准 CLI 参数

```text
--mcp-server-no-file-tools   # 启动 MCP；文件类操作由 Codex 本地完成
-s -hm --tui                 # 流式输出、人工审查点、TUI
--loop                       # Runtime 监督循环（注入阶段任务后 spawn Codex）
--backend=codex              # CmdLineBackend → codex exec，并渲染 .codex/config.toml 连 MCP
```

## 命令模板

将 `{WORKSPACE}`、`{DUT}`、`{WORKFLOW}` 替换为本 case 的值：

```bash
veriagent {WORKSPACE}/ {DUT} \
  --config {WORKFLOW} \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex
```

Formal 另加：`--use-skill`、`--guid-doc-path ...`、`--output formal_test`（见各 Formal case README）。

## 前置条件

1. 已安装 [Codex CLI](https://github.com/openai/codex) 且 `codex` 在 `PATH` 中。
2. 配置模型（写入 `~/.veriagent_env` 或环境变量，供 Codex 渲染配置使用）：
   ```bash
   export OPENAI_API_KEY=...
   export OPENAI_API_BASE=https://你的端点/v1
   export OPENAI_MODEL=...
   ```
3. 已完成 `make init_<DUT>` 或对应 example 的 `make quick` / `formal_init_*`。

## 仓库根目录 Make

```bash
make mcp_<DUT>    # UT 类 DUT，自动选择 storyline workflow
make formal_mcp_<DUT>   # Formal，含 --use-skill
```

无需再开第二个终端手动启动 Qwen/Codex；也**不要**使用纯 `--backend=langchain` 或「仅 MCP、无 loop」的被动模式。
