# coding: utf-8

"""Persistent Codex thread state for the Codex app-server backend."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from veriagent.util.functions import (
    get_abs_path_cwd_veriagent,
    load_json_file,
    save_json_file,
)


CODEX_THREAD_FILE = "codex_thread.json"
CODEX_APP_SERVER_BACKEND = "codex_app_server"


@dataclass
class CodexThreadState:
    """Thread/turn identity owned by the lower-level Codex runtime."""

    thread_id: str | None = None
    last_turn_id: str | None = None
    model: str | None = None
    cwd: str | None = None
    backend: str = CODEX_APP_SERVER_BACKEND
    dut_name: str | None = None
    workflow_config: str | None = None
    workflow_hash: str | None = None
    workspace_hash: str | None = None
    backend_args_hash: str | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> "CodexThreadState":
        if not isinstance(data, dict):
            return cls()
        return cls(
            thread_id=data.get("thread_id"),
            last_turn_id=data.get("last_turn_id"),
            model=data.get("model"),
            cwd=data.get("cwd"),
            backend=data.get("backend", CODEX_APP_SERVER_BACKEND),
            dut_name=data.get("dut_name"),
            workflow_config=data.get("workflow_config"),
            workflow_hash=data.get("workflow_hash"),
            workspace_hash=data.get("workspace_hash"),
            backend_args_hash=data.get("backend_args_hash"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class CodexSessionStore:
    """Read/write Codex runtime state under ``.veriagent``."""

    def __init__(self, workspace: str, filename: str = CODEX_THREAD_FILE):
        self.workspace = os.path.abspath(workspace)
        self.filename = filename

    @property
    def path(self) -> str:
        return get_abs_path_cwd_veriagent(self.workspace, self.filename)

    def load(self) -> CodexThreadState:
        if not os.path.exists(self.path):
            return CodexThreadState(cwd=self.workspace)
        return CodexThreadState.from_dict(load_json_file(self.path))

    def save(self, state: CodexThreadState) -> CodexThreadState:
        if state.cwd is None:
            state.cwd = self.workspace
        save_json_file(self.path, state.to_dict())
        return state

    def update(self, **kwargs) -> CodexThreadState:
        state = self.load()
        for key, value in kwargs.items():
            if not hasattr(state, key):
                raise KeyError(f"Unknown Codex thread state field: {key}")
            setattr(state, key, value)
        return self.save(state)
