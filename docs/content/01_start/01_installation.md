# 安装

## 系统要求

- Python 版本： 3.11+
- 操作系统：Linux / macOS
- API 需求：可访问 OpenAI 兼容 API
- 内存：建议 4GB+
- 依赖：
  - [picker](https://github.com/XS-MLVP/picker)（将 Verilog DUT 导出为 Python 包）
  - [Codex CLI](https://github.com/openai/codex)（`codex` 可执行文件在 `PATH` 中）
  - Codex app-server Python SDK（可 `import codex_app_server`，从团队批准的包源或 direct URL 安装）
  - MCP Python 包（`mcp`，由 `pip install .` / `requirements.txt` 安装）


## 安装方式

- 方式一：克隆仓库并安装依赖

  ```bash
  git clone https://github.com/Hui-Ling-Zhen/Agentic-Verification.git
  cd Agentic-Verification
  pip3 install -e .
  # 安装 Codex app-server SDK（按团队发布流程提供的 pinned requirement）
  pip3 install "${CODEX_APP_SERVER_PACKAGE}"
  ```

- 方式二（pip 安装）
  ```bash
  pip3 install git+https://github.com/Hui-Ling-Zhen/Agentic-Verification
  pip3 install "${CODEX_APP_SERVER_PACKAGE}"
  veriagent --help # 确认安装成功
  ```

## 安装检查

运行官方监督式 Codex 路径前，建议先检查：

```bash
python -c "import veriagent; print('ok: veriagent')"
python -c "import codex_app_server; print('ok: codex_app_server')"
codex --version
picker --version
veriagent --help
```

新任务请使用 `--backend=codex_app_server --mcp-server-no-file-tools --loop --config examples/.../workflow/*.yaml`。旧外部 Code Agent / 被动 MCP 方式仅作为 legacy 兼容保留，见 [Legacy 外部 MCP](../02_usage/legacy_qwen_mcp.md)。
