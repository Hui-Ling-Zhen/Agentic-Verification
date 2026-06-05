# 多 VeriAgent 并发执行

本页说明如何在官方路径下并发运行多个 VeriAgent 任务：

```text
VeriAgent supervisor + Codex SDK inner runtime + external workflow + manifest benchmark
```

旧的“双终端 Code Agent + 被动 MCP”并发方式仅作为 legacy 兼容模式保留，不作为新实验路径。

## 基本原则

每个并发任务应拥有独立的：

- workspace，例如 `output/workspace_Adder_A/`
- DUT 输入目录，例如 `Adder/` 与 `Adder_RTL/`
- `.veriagent/` 状态目录
- MCP 端口，可用 `--mcp-server-port -1` 自动选择

所有任务都应使用官方参数组合：

```bash
--config examples/.../workflow/*.yaml \
--mcp-server-no-file-tools \
-s -hm --tui \
--loop \
--backend=codex_app_server
```

## 推荐：Makefile 并发

在仓库根目录启动两个独立任务：

```bash
make mcp_Adder CWD=output/workspace_Adder_A ARGS="--mcp-server-port -1"
make mcp_Mux CWD=output/workspace_Mux_B ARGS="--mcp-server-port -1"
```

也可以使用不同终端或 tmux：

```bash
tmux new-session -d -s veriagent_multi
tmux send-keys -t veriagent_multi:0.0 \
  'make mcp_Adder CWD=output/workspace_Adder_A ARGS="--mcp-server-port -1"' C-m
tmux split-window -h -t veriagent_multi:0.0
tmux send-keys -t veriagent_multi:0.1 \
  'make mcp_Mux CWD=output/workspace_Mux_B ARGS="--mcp-server-port -1"' C-m
tmux attach-session -t veriagent_multi
```

## 直接 CLI

如果已手动准备好 workspace：

```bash
veriagent output/workspace_Adder_A/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  --mcp-server-port -1 \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

另一个 DUT：

```bash
veriagent output/workspace_Mux_B/ Mux \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  --mcp-server-port -1 \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

## 结果汇总

每个 workspace 都会生成独立 manifest：

```text
output/workspace_Adder_A/.veriagent/run_manifest.json
output/workspace_Mux_B/.veriagent/run_manifest.json
```

汇总：

```bash
make benchmark
```

输出：

```text
benchmark/summary.csv
benchmark/runs.json
```

## Web Master 并发

Web Master Launch 默认使用 `codex_app_server`、`--loop` 和 `--mcp-server-no-file-tools`。在 Launch 页面为每个任务创建独立 workspace，并在 Command Preview 中确认：

- workflow 指向 `examples/*/workflow/*.yaml`
- backend 为 `codex_app_server`
- MCP 为 no-file-tools
- loop 已开启

## 常见问题

端口冲突：使用 `--mcp-server-port -1` 自动选择端口。

任务互相覆盖：检查每个任务的 `CWD` 或 workspace 是否唯一。

manifest 缺失：确认任务至少完成过一次 stage 保存，或查看 `.veriagent/codex_events.jsonl` 辅助排查。
