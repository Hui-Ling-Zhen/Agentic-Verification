# coding=utf-8
"""Official runtime contract for VeriAgent supervising Codex."""

OFFICIAL_BACKEND = "codex_app_server"
OFFICIAL_BACKEND_STATUS = "official"
LEGACY_BACKEND_STATUS = "legacy"

OFFICIAL_SUPERVISED_CODEX_CONTRACT = {
    "backend": OFFICIAL_BACKEND,
    "config_required": True,
    "loop_required": True,
    "mcp_server_no_file_tools_required": True,
    "mcp_server_forbidden": True,
    "break_or_tui_required": True,
    "network_policy_key": "backend.codex_app_server.args.codex_network_access",
    "default_network_access": "enabled",
}

OFFICIAL_SUPERVISED_CODEX_ARGS = [
    "--mcp-server-no-file-tools",
    "-s",
    "-hm",
    "--tui",
    "--loop",
    "--backend=codex_app_server",
]


def official_launch_args_string() -> str:
    return " ".join(OFFICIAL_SUPERVISED_CODEX_ARGS)


def backend_status_from_config(cfg, backend_name: str | None = None) -> tuple[str, bool]:
    """Return (status, legacy) for a configured backend."""
    name = backend_name
    try:
        name = name or str(cfg.backend.key_name)
        backend_cfg = cfg.backend.get_value(name, {})
        status = str(backend_cfg.get_value("status", OFFICIAL_BACKEND_STATUS if name == OFFICIAL_BACKEND else LEGACY_BACKEND_STATUS))
        legacy = bool(backend_cfg.get_value("legacy", status == LEGACY_BACKEND_STATUS))
        return status, legacy
    except Exception:
        if name == OFFICIAL_BACKEND:
            return OFFICIAL_BACKEND_STATUS, False
        return LEGACY_BACKEND_STATUS, True


def validate_official_cli_args(args) -> list[str]:
    """Return missing/invalid CLI args for the official supervised Codex path."""
    effective_backend = (getattr(args, "override", None) or {}).get("backend.key_name") or getattr(args, "backend", None) or OFFICIAL_BACKEND
    if effective_backend != OFFICIAL_BACKEND:
        return []
    if getattr(args, "emulate_config", False) or getattr(args, "as_master", None) is not None:
        return []

    errors: list[str] = []
    if getattr(args, "config", None) is None:
        errors.append("--config examples/.../workflow/*.yaml")
    if not getattr(args, "loop", False):
        errors.append("--loop")
    if not getattr(args, "mcp_server_no_file_tools", False):
        errors.append("--mcp-server-no-file-tools")
    if getattr(args, "mcp_server", False):
        errors.append("use --mcp-server-no-file-tools instead of --mcp-server")
    if not (getattr(args, "human", False) or getattr(args, "tui", False)):
        errors.append("-hm/--human or --tui")
    return errors
