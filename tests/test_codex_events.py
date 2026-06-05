#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pytest
from types import SimpleNamespace

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.abackend.codex_events import normalize_codex_notification


def _notification(method, payload):
    return SimpleNamespace(method=method, payload=payload)


def test_mcp_read_text_file_event_marks_file_observed(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    payload = {
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "item": {
            "id": "item-1",
            "type": "mcpToolCall",
            "tool": "ReadTextFile",
            "arguments": {"file_path": "Guide_Doc/spec.md"},
            "status": "completed",
        },
    }

    events = normalize_codex_notification(
        _notification("item/completed", payload),
        workspace=str(workspace),
    )

    assert [event.kind for event in events] == ["mcp_tool_completed", "file_observed"]
    assert events[-1].file_paths == ["Guide_Doc/spec.md"]


def test_file_change_event_extracts_changed_paths(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    changed = workspace / "unity_test" / "test_demo.py"
    changed.parent.mkdir()
    changed.write_text("# demo", encoding="utf-8")
    payload = {
        "thread_id": "thread-1",
        "turn_id": "turn-1",
        "item": {
            "id": "item-2",
            "type": "fileChange",
            "changes": [{"path": str(changed), "kind": "update", "diff": ""}],
            "status": "applied",
        },
    }

    events = normalize_codex_notification(
        _notification("item/completed", payload),
        workspace=str(workspace),
    )

    assert len(events) == 1
    assert events[0].kind == "file_change_completed"
    assert events[0].file_paths == [os.path.join("unity_test", "test_demo.py")]


def test_unknown_codex_notification_is_preserved():
    events = normalize_codex_notification(
        _notification("future/event", {"threadId": "thread-1", "turnId": "turn-1"})
    )

    assert len(events) == 1
    assert events[0].kind == "unknown"
    assert events[0].status == "future/event"


def test_typed_codex_turn_started_notification_is_normalized():
    pytest.importorskip("codex_app_server")
    from codex_app_server.generated.v2_all import TurnStartedNotification
    from codex_app_server.models import Notification

    notification = Notification(
        method="turn/started",
        payload=TurnStartedNotification.model_validate(
            {
                "threadId": "thread-1",
                "turn": {"id": "turn-1", "items": [], "status": "inProgress"},
            }
        ),
    )

    events = normalize_codex_notification(notification)

    assert len(events) == 1
    assert events[0].kind == "turn_started"
    assert events[0].turn_id == "turn-1"
