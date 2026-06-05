# 批处理执行模式

批处理模式用于按官方监督式 Codex SDK 路径串联多个 case，并用 `run_manifest.json` / `make benchmark` 汇总结果。

旧的 Code Agent hooks 自动继续方案属于 legacy 被动 MCP 模式，不作为新实验路径。

## 单个 DUT 批处理

推荐使用 Makefile：

```bash
make mcp_Adder ARGS="--exit-on-completion --mcp-server-port -1"
```

等价 CLI：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  --mcp-server-port -1 \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server \
  --exit-on-completion
```

关键点：

- `--config` 必须指向外置 workflow。
- `--backend=codex_app_server` 是官方路径。
- `--loop` 必须开启。
- `--mcp-server-no-file-tools` 必须开启。
- `-hm` 或 `--tui` 需要至少一个，用于执行启动 MCP 的初始化命令。
- `--exit-on-completion` 让任务完成后自动退出，便于脚本串联。

## 串联多个任务

```bash
#!/usr/bin/env bash
set -euo pipefail

DUTS=(Adder Mux IntegerDivider)

for dut in "${DUTS[@]}"; do
  echo "==== run $dut ===="
  make "mcp_${dut}" ARGS="--exit-on-completion --mcp-server-port -1" || true
done

make benchmark
```

如果某个 DUT 没有 Makefile 映射，请显式指定 `CWD`、`DUT_SRC_DIR` 或 `CFG`：

```bash
make mcp_Adder \
  CWD=output/workspace_Adder_batch \
  DUT_SRC_DIR=examples/01-baseline/adder \
  CFG=examples/01-baseline/workflow/default.yaml \
  ARGS="--exit-on-completion --mcp-server-port -1"
```

## 结果目录

每个任务会写：

```text
<workspace>/.veriagent/run_manifest.json
<workspace>/.veriagent/codex_events.jsonl
<workspace>/unity_test/
<workspace>/uc_test_report/
```

批处理结束后：

```bash
make benchmark
```

会生成：

```text
benchmark/summary.csv
benchmark/runs.json
```

## Web Master 批处理

如果通过 Web Master 管理批量任务，建议：

1. 在 Launch 页面为每个 DUT 创建独立 workspace。
2. 使用默认 backend `codex_app_server`。
3. 确认 Command Preview 包含 `--loop`、`--mcp-server-no-file-tools` 和外置 `--config`。
4. 在 Task 页面按 failed/stopped/completed 过滤。
5. 最后运行 `make benchmark` 汇总 manifest。

## 排障

`codex_app_server` import 失败：确认已安装 Codex app-server SDK：

```bash
python -c "import codex_app_server"
```

任务未调用 Checker：确认命令包含 `--mcp-server-no-file-tools`，并且有 `-hm` 或 `--tui` 触发 MCP 初始化。

没有 manifest：优先查看 `.veriagent/codex_events.jsonl` 和任务日志，确认是否在 stage 保存前异常退出。
