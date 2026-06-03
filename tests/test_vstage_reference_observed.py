#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.stage.vstage import VerifyStage


def _stage(workspace):
    stage = VerifyStage.__new__(VerifyStage)
    stage.workspace = str(workspace)
    stage.name = "demo"
    stage.reference_files = {"Guide_Doc/spec.md": False}
    stage.skill_list = {}
    stage.force_unactive = False
    stage.is_curent_active = lambda: True
    stage.is_skill_path = lambda _path: False
    return stage


def test_on_file_observed_marks_reference_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    stage = _stage(workspace)

    stage.on_file_observed("Guide_Doc/spec.md", source="codex")

    assert stage.reference_files["Guide_Doc/spec.md"] is True


def test_on_file_read_still_marks_reference_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    stage = _stage(workspace)

    stage.on_file_read(True, "Guide_Doc/spec.md", "content")

    assert stage.reference_files["Guide_Doc/spec.md"] is True
