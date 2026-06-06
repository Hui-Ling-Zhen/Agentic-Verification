# 直接使用：监督式 Codex SDK

本页说明如何不经过 Web Master，直接用本地 CLI 启动官方路径：

```text
VeriAgent supervisor + Codex SDK inner runtime + external workflow + manifest benchmark
```

!!! warning "不要使用根目录 config.yaml 作为 workflow"
    Agentic-Verification 的 workflow 位于 `examples/*/workflow/*.yaml`，普通运行必须通过 `--config` 显式指定。根目录 `config.yaml` 仅用于历史/模型配置示例，不是 UT/Formal workflow。

## 前置条件

- `codex` CLI 在 `PATH` 中。
- `codex_app_server` Python SDK 可 import。
- `mcp` Python package 已安装。
- `picker` 可用。
- 已配置 OpenAI-compatible endpoint：

```bash
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://你的端点/v1
export OPENAI_MODEL=...
```

## 推荐：使用 Makefile

```bash
make example-baseline
```

或对指定 DUT：

```bash
make mcp_Adder
```

这些目标会自动选择外置 workflow，并注入官方参数组合：

```text
--mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

## 直接用 CLI 启动

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s \
  --loop \
  --backend=codex_app_server
```

参数含义：

- `output/workspace_Adder/`：工作区。
- `Adder`：DUT 名称。
- `--config examples/01-baseline/workflow/default.yaml`：外置 workflow。
- `--backend=codex_app_server`：官方 Codex SDK backend。
- `--loop`：启动 supervisor 循环。
- `--mcp-server-no-file-tools`：MCP 只暴露验证域工具，文件/命令操作由 Codex 本地 runtime 处理。

## 常用变体

关闭网络访问：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server \
  --override backend.codex_app_server.args.codex_network_access=disabled
```

强制从某个 stage 开始：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server \
  --force-stage-index 3
```

Formal workflow：

```bash
veriagent output/workspace_arbiter/ arbiter \
  --config examples/05-formal/workflow/formal.yaml \
  --use-skill \
  --guid-doc-path examples/05-formal/arbiter/Guide_Doc \
  --output formal_test \
  --mcp-server-no-file-tools -s --loop --backend=codex_app_server
```

## 运行结果

每次运行都会在 workspace 中生成：

```text
.veriagent/run_manifest.json
.veriagent/codex_events.jsonl
unity_test/ 或 formal_test/
uc_test_report/
```

其中 `run_manifest.json` 记录 stage 进度、Codex thread/turn、MCP tool calls、file changes、failure reason，以及 sandbox/policy audit 字段。

聚合 benchmark：

```bash
make benchmark
```

## Legacy 入口

旧外部 Code Agent 双终端 / 被动 MCP / legacy CLI backend 不再作为主路径。需要兼容旧流程时，请阅读：

- [Legacy 被动 MCP](00_mcp.md)
- [Legacy 外部 MCP](legacy_qwen_mcp.md)
