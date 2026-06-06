#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.stage.vmanager import JOURNAL_REQUIRED_FIELDS, normalize_stage_journal


def test_stage_journal_schema_accepts_auditable_object():
    journal, error = normalize_stage_journal({
        "plan": "inspect requirements",
        "evidence_read": ["Guide_Doc/spec.md"],
        "changes_made": ["unity_test/test_demo.py"],
        "checker_result": "pytest passed",
        "next_risk": "none",
    })

    assert error is None
    assert list(journal.keys()) == list(JOURNAL_REQUIRED_FIELDS)


def test_stage_journal_schema_rejects_unstructured_text():
    journal, error = normalize_stage_journal("I did the work")

    assert journal is None
    assert "JSON object" in error


def test_stage_journal_schema_rejects_missing_required_fields():
    journal, error = normalize_stage_journal({
        "plan": "inspect requirements",
        "evidence_read": ["Guide_Doc/spec.md"],
    })

    assert journal is None
    assert "missing" in error
