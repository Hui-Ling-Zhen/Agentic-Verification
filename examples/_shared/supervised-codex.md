# 监督式 Codex（全仓库标准运行方式）

Agentic-Verification 的官方验证路径是 **Codex SDK backend**：

| 层 | 职责 |
|----|------|
| **VeriAgent Runtime** | Stage 状态机、`Complete`/`Check`、Checker、每轮注入 `CurrentTips`、MCP 暴露验证工具 |
| **Codex SDK（`--backend=codex_app_server`）** | 一个 VeriAgent 外层轮次对应一个 Codex Turn：读 RTL、写 pytest、复杂代码修改，并回流 thread/turn/event |

## 标准 CLI 参数

```text
--mcp-server-no-file-tools   # 启动 MCP；文件类操作由 Codex 本地完成
-s -hm --tui                 # 流式输出、人工审查点、TUI
--loop                       # Runtime 监督循环（注入阶段任务后 spawn Codex）
--backend=codex_app_server   # Codex app-server SDK；持久化 thread/turn，并渲染 .codex/config.toml 连 MCP
```

默认情况下，SDK backend 只会在 DUT、workflow、workspace 输入文件和 backend 参数指纹都匹配时恢复 `.veriagent/codex_thread.json`。如果确实要跨指纹强制复用旧 Codex thread，可显式追加 `--resume-codex-thread`。

官方 SDK 路径使用 `workspace-write` sandbox，并把网络、写入和命令策略写入 `.codex/config.toml`。VeriAgent 同时会把 `{DUT}`、`{DUT}_RTL`、`Guide_Doc`、`skills` 这些任务输入目录设为只读，生成测试和报告仍写入输出目录。

注意：`.codex/config.toml` 中的 `veriagent_policy` 是可审计策略声明，真正的强制边界来自 Codex sandbox 与上述 OS 只读权限。

默认 `codex_network_access` 为 `enabled`。如果 case 不需要联网，建议显式关闭：

```bash
veriagent {WORKSPACE}/ {DUT} \
  --config {WORKFLOW} \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server \
  --override backend.codex_app_server.args.codex_network_access=disabled
```

每次运行的 `.veriagent/run_manifest.json` 会记录 `sandbox_mode`、`network_access`、`writable_roots`、`protected_inputs`、`policy_enforcement` 与 `policy_warnings`，便于审计实际边界。

## 命令模板

将 `{WORKSPACE}`、`{DUT}`、`{WORKFLOW}` 替换为本 case 的值：

```bash
veriagent {WORKSPACE}/ {DUT} \
  --config {WORKFLOW} \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

Formal 另加：`--use-skill`、`--guid-doc-path ...`、`--output formal_test`（见各 Formal case README）。

## 前置条件

1. 已安装 [OpenAI Codex](https://github.com/openai/codex) 且 `codex` 在 `PATH` 中，或通过 `CODEX_BIN` 指定。
2. 已安装 OpenAI Codex 开源 SDK：`codex/sdk/python` / package `openai-codex-app-server-sdk`，可 `import codex_app_server`。
3. 配置模型（写入 `~/.veriagent_env` 或环境变量，供 Codex 渲染配置使用）：
   ```bash
   export OPENAI_API_KEY=...
   export OPENAI_API_BASE=https://你的端点/v1
   export OPENAI_MODEL=...
   ```
4. 已完成 `make init_<DUT>` 或对应 example 的 `make quick` / `formal_init_*`。

## 仓库根目录 Make

```bash
make mcp_<DUT>          # UT 类 DUT，自动选择 storyline workflow 与 --config
make formal_mcp_<DUT>   # Formal，含 --use-skill
make benchmark          # 汇总各 workspace 的 run_manifest.json
```

无需再开第二个终端手动启动外部 Code Agent。

## 官方路径 vs Legacy backend

| 路径 | 状态 |
|------|------|
| **监督式 Codex SDK**（`--backend=codex_app_server` + MCP + `--loop`） | **官方验证路径**，本仓库 Makefile 与示例均按此测试 |
| `--backend=codex` / `codex exec` CLI | **Legacy**，黑盒路径，外层 runtime 无法稳定感知 Codex turn/event |
| `--backend=langchain` / 纯 API | **Legacy**，未在本仓库持续验证 |
| 仅 MCP、无 `--loop` 的被动模式 | **Legacy**，非产品化路径 |

也**不要**省略 `--config`：workflow 外置在 `examples/*/workflow/`，Runtime 不内置 UT/Formal 流程。
