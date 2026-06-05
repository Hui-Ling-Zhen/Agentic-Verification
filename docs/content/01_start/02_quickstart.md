# 快速入门：监督式 Codex SDK

Agentic-Verification 的官方运行方式是 **VeriAgent runtime 监督 Codex SDK**：

```text
veriagent + --config examples/.../workflow/*.yaml + --backend=codex_app_server + --loop
```

旧的 Qwen 双终端 / 被动 MCP 模式仍可兼容，但不再是推荐路径；需要时请参考 [Legacy Qwen MCP](../02_usage/legacy_qwen_mcp.md)。

## 前置条件

- Python 3.11+
- 已安装 Codex CLI，并且 `codex` 在 `PATH` 中
- 已安装 MCP Python 包（`mcp`）
- 已安装 Codex app-server Python SDK，并可 `import codex_app_server`。该 SDK 目前不能通过公开 PyPI 的 `codex_app_server` 包名安装，请从批准的包源或 direct URL 安装。
- 已安装 `picker`
- 已配置 OpenAI-compatible 模型端点：

```bash
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://你的端点/v1
export OPENAI_MODEL=...
```

## 安装

从仓库运行：

```bash
git clone https://github.com/Hui-Ling-Zhen/Agentic-Verification.git
cd Agentic-Verification
pip3 install -r requirements.txt
# 然后从批准的包源安装 Codex app-server SDK：
# pip3 install "${CODEX_APP_SERVER_PACKAGE}"
```

也可以使用 pip 安装：

```bash
pip3 install git+https://github.com/Hui-Ling-Zhen/Agentic-Verification
```

## 一键运行 Adder 基线

推荐先跑仓库内置 example：

```bash
make example-baseline
```

该命令会完成：

1. 准备 `examples/01-baseline/adder` 输入材料。
2. 用 `picker` 导出 Adder DUT。
3. 复制 workflow、Guide_Doc 和 skills 到工作区。
4. 启动 VeriAgent TUI、MCP server 和监督循环。
5. 通过 `codex_app_server` 后端让 Codex 逐轮完成验证任务。

等价的标准 CLI 形式如下：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

## 关键参数

| 参数 | 作用 |
|------|------|
| `--config examples/.../workflow/*.yaml` | 必须显式指定外置 workflow；runtime 不内置 UT/Formal 流程 |
| `--backend=codex_app_server` | 官方 Codex SDK backend，提供 thread/turn/event 可观测性 |
| `--loop` | 启动 VeriAgent 监督循环 |
| `--mcp-server-no-file-tools` | MCP 只暴露验证域工具，文件/命令操作由 Codex 本地 runtime 处理 |
| `-s -hm --tui` | 流式输出、人工审查点、TUI 界面 |

不要在官方路径中省略 `--config`；不带 workflow 的运行会直接报错，并提示 `examples/*/workflow/*.yaml` 示例路径。

Sandbox 边界说明：`.codex/config.toml` 中的 `veriagent_policy` 是 audit hint，不是强制策略。强制边界来自 Codex sandbox、`writable_roots` 和 OS 只读权限。默认网络访问为 `enabled`；如果 case 不需要联网，可追加：

```bash
--override backend.codex_app_server.args.codex_network_access=disabled
```

## 运行结果

默认输出位于 workspace 内，例如 `output/workspace_Adder/`：

```text
output/workspace_Adder/
├── Adder/                    # DUT 输入与说明
├── Adder_RTL/                # RTL / 源码输入
├── Guide_Doc/                # 验证规范和模板
├── unity_test/               # 生成的验证文档和测试代码
├── uc_test_report/           # pytest / coverage 报告
└── .veriagent/
    ├── codex_thread.json     # Codex SDK thread 状态
    ├── codex_events.jsonl    # Codex turn/event 审计日志
    └── run_manifest.json     # 可度量运行结果
```

其中：

- `unity_test/*.md` 记录功能点、覆盖率、bug 分析和验证总结。
- `unity_test/tests/` 保存生成的 pytest/toffee 测试代码。
- `.veriagent/run_manifest.json` 保存 DUT、workflow、backend、stage 进度、Codex thread/turn、token usage、MCP tool calls、file changes 和 failure reason。

## 汇总 benchmark

跑完一个或多个 case 后：

```bash
make benchmark
```

该命令会扫描 `output/` 和 `examples/` 下的 `run_manifest.json`，生成：

- `benchmark/summary.csv`
- `benchmark/runs.json`

## 跑其它 example

常用入口：

```bash
make example-bug
make example-increment
make example-peripheral
make example-flagship
make example-algorithm
make example-formal
```

也可以直接使用统一模板：

```bash
veriagent {WORKSPACE}/ {DUT} \
  --config examples/{storyline}/workflow/{workflow}.yaml \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

更多 case 请查看 [Examples 索引](../../../examples/README.md) 和 [监督式 Codex 说明](../../../examples/_shared/supervised-codex.md)。
