#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
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
