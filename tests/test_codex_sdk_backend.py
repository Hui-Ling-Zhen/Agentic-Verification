#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pytest
from types import SimpleNamespace

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.abackend.codex_sdk import CodexAppServerBackend
from veriagent.abackend.codex_session import CodexSessionStore


class FakeTurnHandle:
    def __init__(self, thread_id, turn_id):
        self.thread_id = thread_id
        self.id = turn_id
        self.interrupted = False

    def stream(self):
        yield SimpleNamespace(
            method="item/agentMessage/delta",
            payload={"thread_id": self.thread_id, "turn_id": self.id, "delta": "hello"},
        )
        yield SimpleNamespace(
            method="item/completed",
            payload={
                "thread_id": self.thread_id,
                "turn_id": self.id,
                "item": {
                    "id": "item-1",
                    "type": "mcpToolCall",
                    "tool": "ReadTextFile",
                    "arguments": {"file_path": "Guide_Doc/spec.md"},
                    "status": "completed",
                },
            },
        )
        yield SimpleNamespace(
            method="thread/tokenUsage/updated",
            payload={
                "thread_id": self.thread_id,
                "turn_id": self.id,
                "token_usage": {"total": {"totalTokens": 42}},
            },
        )
        yield SimpleNamespace(
            method="turn/completed",
            payload={
                "thread_id": self.thread_id,
                "turn": {"id": self.id, "status": "completed"},
            },
        )

    def interrupt(self):
        self.interrupted = True


class FakeThread:
    def __init__(self, thread_id):
        self.id = thread_id
        self.turns = []

    def turn(self, prompt, **kwargs):
        turn = FakeTurnHandle(self.id, f"turn-{len(self.turns) + 1}")
        self.turns.append((prompt, kwargs, turn))
        return turn

    def set_name(self, name):
        self.name = name

    def compact(self):
        self.compacted = True


class FakeCodex:
    def __init__(self):
        self.started = []
        self.resumed = []
        self.thread = FakeThread("thread-1")
        self.closed = False

    def thread_start(self, **kwargs):
        self.started.append(kwargs)
        return self.thread

    def thread_resume(self, thread_id, **kwargs):
        self.resumed.append((thread_id, kwargs))
        self.thread = FakeThread(thread_id)
        return self.thread

    def close(self):
        self.closed = True


class FakeStageManager:
    def __init__(self):
        self.observed = []

    def on_file_observed(self, path, source="unknown"):
        self.observed.append((path, source))


class FakeAgent:
    def __init__(self, workspace, dut_name="Demo"):
        self.workspace = workspace
        self.dut_name = dut_name
        self.config_file = None
        self.pdb = SimpleNamespace(_mcp_server=None)
        self.stage_manager = FakeStageManager()
        self.messages = []

    def message_echo(self, txt):
        self.messages.append(txt)


def test_codex_app_server_backend_runs_turn_and_persists_state(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fake_codex = FakeCodex()
    agent = FakeAgent(str(workspace))
    config = SimpleNamespace(mcp_server=SimpleNamespace(port=5000))

    backend = CodexAppServerBackend(
        agent,
        config=config,
        model="gpt-test",
        codex_factory=lambda: fake_codex,
    )

    backend.init()
    summary = backend.run_turn("do verification work")

    assert fake_codex.started
    assert backend.current_thread_id() == "thread-1"
    assert backend.current_turn_id() == "turn-1"
    assert summary["status"] == "completed"
    assert backend.token_total() == 42
    assert ("Guide_Doc/spec.md", "codex") in agent.stage_manager.observed

    saved = CodexSessionStore(str(workspace)).load()
    assert saved.thread_id == "thread-1"
    assert saved.last_turn_id == "turn-1"
    assert saved.model == "gpt-test"
    assert saved.dut_name == "Demo"
    assert saved.workspace_hash is not None
    assert saved.backend_args_hash is not None


def test_codex_app_server_starts_new_thread_on_fingerprint_mismatch(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    first_codex = FakeCodex()
    first_backend = CodexAppServerBackend(
        FakeAgent(str(workspace), dut_name="DemoA"),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        model="gpt-test",
        codex_factory=lambda: first_codex,
    )
    first_backend.init()

    second_codex = FakeCodex()
    second_backend = CodexAppServerBackend(
        FakeAgent(str(workspace), dut_name="DemoB"),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        model="gpt-test",
        codex_factory=lambda: second_codex,
    )
    second_backend.init()

    assert second_codex.resumed == []
    assert second_codex.started


def test_codex_app_server_can_force_resume_on_fingerprint_mismatch(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    first_codex = FakeCodex()
    first_backend = CodexAppServerBackend(
        FakeAgent(str(workspace), dut_name="DemoA"),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        model="gpt-test",
        codex_factory=lambda: first_codex,
    )
    first_backend.init()

    second_codex = FakeCodex()
    second_backend = CodexAppServerBackend(
        FakeAgent(str(workspace), dut_name="DemoB"),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        model="gpt-test",
        resume_codex_thread=True,
        codex_factory=lambda: second_codex,
    )
    second_backend.init()

    assert second_codex.resumed


def test_codex_app_server_policy_summary_records_sandbox_boundary(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    agent = FakeAgent(str(workspace), dut_name="Demo")
    config = SimpleNamespace(mcp_server=SimpleNamespace(port=5000))
    backend = CodexAppServerBackend(
        agent,
        config=config,
        sandbox="workspace-write",
        codex_network_access="disabled",
        codex_write_policy="workspace_only",
        codex_command_policy="codex_sandbox",
        codex_factory=lambda: FakeCodex(),
    )
    backend.CWD = str(workspace)

    summary = backend.policy_summary()

    assert summary["sandbox_mode"] == "workspace-write"
    assert summary["network_access"] == "disabled"
    assert summary["writable_roots"] == [str(workspace)]
    assert summary["policy_enforcement"] == "codex_sandbox_os_permissions"
    assert summary["veriagent_policy"] == "audit_hint_only"
    assert str(workspace / "Demo") in summary["protected_inputs"]


def test_codex_app_server_resolves_codex_bin_from_env(tmp_path, monkeypatch):
    codex_bin = tmp_path / "codex"
    codex_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    codex_bin.chmod(0o755)
    monkeypatch.setenv("CODEX_BIN", str(codex_bin))

    backend = CodexAppServerBackend(
        FakeAgent(str(tmp_path)),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        codex_factory=lambda: FakeCodex(),
    )

    assert backend._resolve_codex_bin() == str(codex_bin)


def test_codex_app_server_resolves_codex_bin_from_path(tmp_path, monkeypatch):
    codex_bin = tmp_path / "codex"
    codex_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    codex_bin.chmod(0o755)
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))

    backend = CodexAppServerBackend(
        FakeAgent(str(tmp_path)),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        codex_factory=lambda: FakeCodex(),
    )

    assert backend._resolve_codex_bin() == str(codex_bin)


def test_codex_app_server_declines_unowned_approval_requests(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    backend = CodexAppServerBackend(
        FakeAgent(str(workspace)),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        codex_factory=lambda: FakeCodex(),
    )
    backend.CWD = str(workspace)
    backend.EVENT_LOG_FILE = str(workspace / ".veriagent" / "codex_events.jsonl")

    decision = backend._handle_approval_request(
        "item/commandExecution/requestApproval",
        {"threadId": "thread-1", "turnId": "turn-1", "itemId": "item-1"},
    )

    assert decision == {"decision": "decline"}
    assert backend._approval_requests[0]["method"] == "item/commandExecution/requestApproval"
    assert (workspace / ".veriagent" / "codex_events.jsonl").exists()


def test_codex_app_server_kwargs_match_openai_codex_sdk_models(tmp_path):
    pytest.importorskip("codex_app_server")
    from codex_app_server.generated.v2_all import ThreadStartParams, TurnStartParams

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    backend = CodexAppServerBackend(
        FakeAgent(str(workspace)),
        config=SimpleNamespace(mcp_server=SimpleNamespace(port=5000)),
        model="gpt-test",
        sandbox="workspace-write",
        codex_network_access="disabled",
        codex_factory=lambda: FakeCodex(),
    )
    backend.CWD = str(workspace)

    ThreadStartParams(**backend._clean_kwargs(backend._thread_kwargs()))
    TurnStartParams(
        thread_id="thread-1",
        input=[{"type": "text", "text": "hello"}],
        **backend._clean_kwargs(backend._turn_kwargs()),
    )
