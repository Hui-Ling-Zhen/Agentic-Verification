#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
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
    def __init__(self, workspace):
        self.workspace = workspace
        self.dut_name = "Demo"
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
