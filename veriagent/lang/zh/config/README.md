# VeriAgent 工作流配置（包内）

Runtime **不再内置** UT / Formal 完整工作流。Mission、Stage、Checker 由 example 目录下的 YAML 通过 `--config` 显式加载。

## 包内文件

| 文件 | 用途 |
|------|------|
| `empty.yaml` | 最小 scaffold：空 `stage` 列表，供 runtime 启动时使用 |
| `README.md` | 本说明与 schema 摘要 |

## Example 工作流位置

```text
examples/01-baseline/workflow/default.yaml   # 11-stage UT（基线）
examples/01-baseline/workflow/inc.yaml       # 增量验证
examples/02-peripheral-ip/workflow/default.yaml
examples/03-microarch/workflow/default.yaml
examples/04-algorithm/workflow/default.yaml
examples/05-formal/workflow/formal.yaml      # Formal 11-stage
examples/06-planning/workflow/genspec.yaml   # Spec 生成（独立 workflow）
```

Makefile 与 Web Master 会指向上述路径；也可手动：

```bash
veriagent output/workspace_Adder/ Adder \
  --config examples/01-baseline/workflow/default.yaml --loop
```

## 配置加载顺序

1. `veriagent/setting.yaml` — runtime 默认（模型、backend、skill 开关等）
2. `~/.veriagent/setting.yaml` — 用户覆盖
3. `lang/zh/config/empty.yaml` — 空 workflow scaffold
4. `{workspace}/.veriagent/setting.yaml` — workspace 级（若有）
5. `--config <workflow.yaml>` — **example 工作流（mission + stage + checker）**
6. `--cfg-override` — 临时覆盖

## Workflow YAML Schema（摘要）

```yaml
template_overwrite:          # 模板变量
  DOC_GEN_LANG: "中文"
  RTL_PATH: "{DUT}_RTL"

mission:
  name: "{DUT}芯片验证任务"
  prompt:
    system: |
      ...
    skill_system: |         # 可选；use_skill 时注入
      ...

hooks:                       # 可选；continue / cagent_init 等
  continue: >
    ...

tools:                       # 可选；RunTestCases 等工具参数
  ignore_tools: []

skill:                       # 可选；覆盖 setting.yaml 中的 skill 段
  use_skill: true

stage:
  - name: requirement_analysis_and_planning
    desc: "..."
    task:
      - "..."
    reference_files: []
    output_files: []
    skill_list: []           # 可选
    force_use_skill: false
    checker:
      - name: file_check
        clss: "OrginFileMustExistChecker"
        args: {}
    stage: []                 # 可选子 stage
```

完整字段说明见 [`docs/content/03_develop/03_workflow.md`](../../../docs/content/03_develop/03_workflow.md) 与根目录 [`veriagent/SKILL.md`](../../SKILL.md)。

## 定制建议

- **故事线级**：编辑 `examples/<storyline>/workflow/default.yaml`
- **DUT 级**：复制为 `examples/<storyline>/<dut>/workflow/default.yaml`，Makefile 中设置 `CFG=` 或扩展 `WORKFLOW_CFG_<DUT>`
- **临时试验**：`--emulate-config --config path/to/workflow.yaml`

与 UCAgent 的差异：UCAgent 在包内 `ucagent/lang/zh/config/default.yaml` 自带完整 UT 流程；Agentic-Verification 将 workflow 外置到 example，runtime 只提供机制。
