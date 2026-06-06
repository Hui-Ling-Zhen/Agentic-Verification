#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from types import SimpleNamespace

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.server.api_mcp import PdbMcpServer
from veriagent.server import api_mcp


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

    assert [tool.name for tool in filtered] == [
        "Check",
        "Complete",
        "RunTestCases",
    ]


def test_mcp_server_start_fails_fast_when_port_is_busy(monkeypatch):
    server = PdbMcpServer.__new__(PdbMcpServer)
    server._running = False
    server.host = "127.0.0.1"
    server.port = 5000
    server.pdb = SimpleNamespace(agent=None)
    monkeypatch.setattr(api_mcp, "is_port_free", lambda host, port: False)

    ok, msg = server.start()

    assert ok is False
    assert "already in use" in msg


def test_mcp_health_check_validates_tool_surface():
    server = PdbMcpServer.__new__(PdbMcpServer)
    server._running = True
    server._thread = SimpleNamespace(is_alive=lambda: True)
    server.exposed_tool_names = ["Check", "Complete", "RunTestCases"]

    ok, msg = server.health_check(
        required_tools={"Check", "Complete"},
        forbidden_tools={"ReadTextFile"},
    )

    assert ok is True
    assert "healthy" in msg

    ok, msg = server.health_check(
        required_tools={"Check", "Complete"},
        forbidden_tools={"RunTestCases"},
    )

    assert ok is False
    assert "forbidden tools exposed" in msg
