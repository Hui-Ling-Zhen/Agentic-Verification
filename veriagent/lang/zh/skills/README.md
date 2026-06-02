# Skills 目录说明

可复用的 **SKILL.md** 技能已迁移到各 example 故事线目录，便于按 DUT 个性化定制：

```text
examples/01-baseline/skills/          # UT 技能（unitytest/*）
examples/02-peripheral-ip/skills/
examples/03-microarch/skills/
examples/04-algorithm/skills/
examples/05-formal/skills/            # Formal 技能（formal/*）
examples/<storyline>/<dut>/skills/    # 可选：单个 DUT 覆盖故事线默认技能
```

`make init_<DUT>` / `make formal_init_<DUT>` 会将对应 example 下的 `skills/` 复制到 workspace 的 `skills/`。
启用 `--use-skill` 后，VeriAgent 再将其同步到 `.veriagent/skills/` 供 Agent 使用。

本目录仅保留 **Formal 框架库**（`formal/lib/`），供 checker 与 skill 脚本 import，不是可编辑的技能内容。
