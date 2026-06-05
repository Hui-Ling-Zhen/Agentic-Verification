# FAQ

## 为什么运行时必须传 `--config`？

Agentic-Verification 不在 runtime 内置 UT/Formal workflow。Workflow 已外置到 `examples/*/workflow/*.yaml`，普通运行必须显式传入：

```bash
--config examples/01-baseline/workflow/default.yaml
```

根目录 `config.yaml` 不是默认 workflow；它只保留为历史/模型配置示例。

## 官方启动命令是什么？

推荐：

```bash
make example-baseline
```

等价 CLI：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

## 为什么 `codex_app_server` 时必须开 `--loop` 和 `--mcp-server-no-file-tools`？

`codex_app_server` 是官方监督式路径：VeriAgent 外层 runtime 每一轮注入 stage 任务，Codex SDK 内层 runtime 执行一个 turn，并通过 MCP 调用 `Check` / `Complete` 等验证工具。

如果没有 `--loop`，外层不会持续监督推进；如果没有 MCP，Codex 无法调用验证工具；如果使用全量 MCP 文件工具，则文件权限边界会变得模糊。CLI 会对官方路径做 fail-fast 校验。

## `codex_app_server` import 失败怎么办？

官方路径使用 OpenAI Codex 开源 SDK：`codex/sdk/python` / package `openai-codex-app-server-sdk`。从本地开源 Codex 仓库安装，例如：

```bash
git clone https://github.com/openai/codex ../codex
pip install -e ../codex/sdk/python
export CODEX_BIN="$(which codex)"
python -c "import codex_app_server"
```

基础依赖仍通过：

```bash
pip install -r requirements.txt
```

## 如何恢复中断的任务？

默认情况下，Codex SDK thread resume 受指纹保护：DUT、workflow、workspace 输入和 backend 参数一致时才复用旧 thread。

正常恢复：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

只有确认要跨指纹复用旧 Codex thread 时，才使用：

```bash
--resume-codex-thread
```

## Check 失败怎么办？

按顺序处理：

1. 用 `StdCheck` 查看失败日志。
2. 阅读当前 stage 的 `reference_files`。
3. 修复生成的测试、文档或环境。
4. 重新运行 `Check`。
5. 通过后调用 `Complete` 推进阶段。

## 运行结果在哪里？

典型输出：

```text
<workspace>/
├── unity_test/ 或 formal_test/
├── uc_test_report/
└── .veriagent/
    ├── run_manifest.json
    ├── codex_events.jsonl
    └── codex_thread.json
```

`run_manifest.json` 是 benchmark 和审计入口，包含 stage 进度、Codex thread/turn、tool calls、file changes、failure reason、sandbox/policy 字段。

## 如何汇总 benchmark？

```bash
make benchmark
```

输出：

```text
benchmark/summary.csv
benchmark/runs.json
```

## 如何关闭 Codex 网络访问？

默认 `codex_network_access=enabled`。不需要联网的 case 建议显式关闭：

```bash
--override backend.codex_app_server.args.codex_network_access=disabled
```

## `veriagent_policy` 是强制策略吗？

不是。`.codex/config.toml` 中的 `veriagent_policy` 是 audit hint，不是 Codex 原生强制策略。真正强边界来自 Codex sandbox、`writable_roots` 和 OS 只读权限。

## 为什么找不到 `WriteTextFile` 工具？

该工具已移除。请使用 `EditTextFile`（overwrite / append / replace）或其它文件工具。官方 Codex SDK 路径下，通用文件操作主要由 Codex 本地 runtime 执行，MCP 侧只保留验证域工具。

## 旧外部 Code Agent 双终端流程还支持吗？

作为 legacy 兼容保留，但不再作为推荐路径。请参考 [Legacy 外部 MCP](legacy_qwen_mcp.md)。
