#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from types import SimpleNamespace

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.server.api_mcp import PdbMcpServer


def test_filter_generic_file_tools_keeps_verification_tools():
    server = PdbMcpServer.__new__(PdbMcpServer)
    tools = [
        SimpleNamespace(name="ReadTextFile"),
        SimpleNamespace(name="SearchText"),
        SimpleNamespace(name="Check"),
        SimpleNamespace(name="Complete"),
        SimpleNamespace(name="RunTestCases"),
    ]

    filtered = server._filter_generic_file_tools(tools)

    assert [tool.name for tool in filtered] == ["Check", "Complete", "RunTestCases"]
