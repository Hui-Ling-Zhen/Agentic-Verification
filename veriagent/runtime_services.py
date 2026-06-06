# coding=utf-8
"""Runtime service plan metadata for VeriAgent entrypoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SERVICE_COMMANDS = {
    "cmd_api_start": "cmd_api",
    "terminal_api_start": "terminal_api",
    "master_api_start": "master_api",
    "connect_master_to": "master_client",
    "tui": "tui",
    "start_mcp_server": "mcp",
    "start_mcp_server_no_file_ops": "mcp",
    "loop": "loop",
}


EXPLICIT_RUNTIME_SERVICES = {"mcp", "loop"}


@dataclass
class RuntimeServices:
    """Serializable lifecycle registry for VeriAgent runtime services."""

    services: list[dict[str, Any]] = field(default_factory=list)

    def register(
        self,
        service: str,
        command: str,
        raw_command: str = "",
        lifecycle: str | None = None,
        status: str = "planned",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "service": service,
            "command": command,
            "raw_command": raw_command or command,
            "lifecycle": lifecycle or ("runtime" if service in EXPLICIT_RUNTIME_SERVICES else "pdb_init_command"),
            "status": status,
            "metadata": metadata or {},
        }
        self.services.append(entry)
        return entry

    def register_command(self, raw_command: str) -> dict[str, Any] | None:
        raw = str(raw_command).strip()
        if not raw:
            return None
        command = raw.split()[0]
        service = SERVICE_COMMANDS.get(command)
        if service is None:
            return None
        return self.register(service, command, raw_command=raw)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "services": list(self.services),
            "pdb_init_command_backed": [
                item for item in self.services
                if item.get("lifecycle") == "pdb_init_command"
            ],
            "runtime_managed": [
                item for item in self.services
                if item.get("lifecycle") == "runtime"
            ],
        }


def build_runtime_service_plan(init_cmds: list[str] | tuple[str, ...] | None) -> dict[str, Any]:
    """Summarize runtime services requested through startup commands.

    MCP and supervised loop are now official lifecycle responsibilities for the
    Codex path. The remaining UI/API services are still PDB init-command backed;
    keeping this plan in the manifest makes that boundary visible and measurable.
    """
    registry = RuntimeServices()
    for cmd in init_cmds or []:
        registry.register_command(cmd)
    return registry.to_manifest()
