#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.abackend.codex_session import CodexSessionStore


def test_codex_session_store_round_trip(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    store = CodexSessionStore(str(workspace))
    state = store.update(
        thread_id="thread-1",
        last_turn_id="turn-1",
        model="gpt-test",
        cwd=str(workspace),
        backend="codex_app_server",
    )

    assert state.thread_id == "thread-1"
    assert state.last_turn_id == "turn-1"

    loaded = store.load()
    assert loaded.thread_id == "thread-1"
    assert loaded.last_turn_id == "turn-1"
    assert loaded.model == "gpt-test"
    assert loaded.cwd == str(workspace)
