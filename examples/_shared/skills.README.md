# Example Skills

本目录存放该故事线（或单个 DUT）的 VeriAgent 技能，结构与 Agent Skills 规范一致：

```text
skills/
├── unitytest/                 # UT workflow（01–04 故事线）
│   ├── functions-and-checks/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── ...
└── formal/                    # Formal workflow（05-formal）
    ├── func-spec/
    ├── sva-gen/
    └── ...
```

## 定制方式

1. **故事线级**：直接编辑 `examples/<storyline>/skills/` 下的 `SKILL.md` 或脚本。
2. **DUT 级**：在 `examples/<storyline>/<dut>/skills/` 创建同名技能目录，会覆盖故事线默认（`make init_<DUT>` 优先复制 DUT 目录）。
3. **运行时覆盖**：`veriagent ... --use-skill --extra-skill-path /path/to/skills`

修改后重新 `make init_<DUT>`（或 `make formal_init_<DUT>`）即可刷新 workspace。
