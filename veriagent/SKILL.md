---
name: veriagent
description: VeriAgent 是 Agentic-Verification 的外层监督 runtime。本技能说明如何编写外置 workflow、使用监督式 Codex SDK 官方路径、记录 benchmark manifest，以及开发兼容的 Checker/Tool。
---

# VeriAgent

VeriAgent 是 Agentic-Verification 的外层监督 runtime：它负责 workflow stage、`Check` / `Complete`、Checker、MCP 验证工具、人工检查点和 run manifest。官方执行路径是 **监督式 Codex SDK**：

```text
veriagent {WORKSPACE}/ {DUT} \
  --config examples/.../workflow/*.yaml \
  --mcp-server-no-file-tools \
  -s -hm --tui \
  --loop \
  --backend=codex_app_server
```

不要把根目录 `config.yaml` 当作 workflow。Agentic-Verification 的 UT/Formal/Planning workflow 全部外置在 `examples/*/workflow/*.yaml`，普通运行必须显式传入 `--config`。

> 兼容命名说明：部分内置 Checker / Tool 仍保留 `UnityChip*` 或 `RunUnityChipTest` 类名，目的是兼容已有 workflow YAML。对用户和产品语义而言，它们属于 Agentic-Verification / VeriAgent 的验证组件。

## 官方运行方式

推荐先运行仓库示例：

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

关键约束：

- `--config` 必须指向外置 workflow YAML。
- `--backend=codex_app_server` 是官方路径。
- `--loop` 必须开启，否则外层 supervisor 不会持续推进。
- `--mcp-server-no-file-tools` 必须开启，MCP 只暴露验证域工具，文件/命令操作由 Codex 本地 runtime 处理。
- legacy backend（`codex` CLI、`qwen`、`langchain`、被动 MCP）仅用于兼容，不作为新任务路径。

## Workflow 编写规范

Workflow YAML 至少包含：

```yaml
mission:
  name: "{DUT} 验证任务"
  prompt:
    system: |
      你是硬件验证工程师。按阶段任务执行，并通过 Complete / Check 推进。

stage:
  - name: requirement_analysis
    desc: "需求分析"
    task:
      - "阅读 {DUT}/README.md"
      - "输出 {OUT}/{DUT}_verification_needs_and_plan.md"
    output_files:
      - "{OUT}/{DUT}_verification_needs_and_plan.md"
    checker:
      - name: markdown_file_check
        clss: "MarkDownHeadChecker"
        args:
          file_path: "{OUT}/{DUT}_verification_needs_and_plan.md"
          header_levels: 2
```

建议从现有 workflow 复制后修改：

- `examples/01-baseline/workflow/default.yaml`
- `examples/01-baseline/workflow/inc.yaml`
- `examples/05-formal/workflow/formal.yaml`
- `examples/06-planning/workflow/genspec.yaml`
- `examples/06-planning/workflow/gencov.yaml`

配置合并时，`stage` 这类列表是整体替换，不是元素级合并。因此增删阶段时要复制完整 `stage:` 列表到新的 workflow YAML，再通过 `--config` 加载。

## Checker / Tool 开发

Checker 负责判断阶段产物是否满足要求。所有 Checker 继承 `veriagent.checkers.base.Checker`，实现 `do_check()`。

```python
from veriagent.checkers.base import Checker


class VeriAgentCheckerMyCustomCheck(Checker):
    def __init__(self, file_path: str, **kwargs):
        super().__init__()
        self.file_path = file_path
        self.set_human_check_needed(kwargs.get("need_human_check", False))

    def do_check(self, timeout=0, **kwargs):
        path = self.get_path(self.file_path)
        if not path.exists():
            return False, {"error": f"file not found: {self.file_path}"}
        return True, {"message": "check passed"}
```

Workflow 中使用：

```yaml
checker:
  - name: my_custom_check
    clss: "mypkg.checkers.VeriAgentCheckerMyCustomCheck"
    args:
      file_path: "{OUT}/result.md"
```

Tool 负责暴露给 Agent 调用。内层 Codex SDK 路径下，MCP 默认只开放验证域工具；通用文件读写由 Codex 本地 runtime 处理。

## Skills 使用

Skills 已外置到 examples：

- UT skills：`examples/<storyline>/skills/unitytest/`
- Formal skills：`examples/05-formal/skills/formal/`

Formal workflow 通常需要：

```bash
veriagent {WORKSPACE}/ {DUT} \
  --config examples/05-formal/workflow/formal.yaml \
  --use-skill \
  --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server
```

UT workflow 默认可以带 skills 目录，但不一定强制 `--use-skill`。以具体 workflow 中的 `skill.use_skill`、`skill_list`、`force_use_skill` 为准。

## Benchmark / Manifest

每次运行会写：

```text
<workspace>/.veriagent/run_manifest.json
<workspace>/.veriagent/codex_events.jsonl
```

`run_manifest.json` 记录 DUT、workflow、backend、stage 进度、Codex thread/turn、token/tool/file 事件摘要，以及 sandbox/policy 审计字段。

聚合：

```bash
make benchmark
```

输出：

```text
benchmark/summary.csv
benchmark/runs.json
```

## Sandbox / Policy

`.codex/config.toml` 中的 `veriagent_policy` 是 audit hint，不是强制策略引擎。真正的强边界来自：

- Codex sandbox
- `writable_roots`
- OS 只读权限

默认 `codex_network_access=enabled`。不需要联网时建议关闭：

```bash
--override backend.codex_app_server.args.codex_network_access=disabled
```

## 校验命令

检查 workflow 加载：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml \
  --emulate-config
```

检查包和 CLI：

```bash
python -c "from veriagent.abackend.codex_sdk import CodexAppServerBackend"
veriagent --help
```

如果要运行官方路径，还需要先从 OpenAI Codex 开源仓库安装 `codex/sdk/python`（package `openai-codex-app-server-sdk`），确保 `codex_app_server` Python SDK 可 import，并设置 `CODEX_BIN` 指向 `codex` binary。
