#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "..")))

from veriagent.runtime_services import RuntimeServices, build_runtime_service_plan


def test_runtime_service_plan_marks_pdb_init_command_services():
    plan = build_runtime_service_plan([
        "terminal_api_start 127.0.0.1 8818",
        "cmd_api_start --sock none",
        "connect_master_to 127.0.0.1 9900",
        "tui",
        "loop Continue",
    ])

    lifecycles = {item["service"]: item["lifecycle"] for item in plan["services"]}
    assert lifecycles["terminal_api"] == "pdb_init_command"
    assert lifecycles["cmd_api"] == "pdb_init_command"
    assert lifecycles["master_client"] == "pdb_init_command"
    assert lifecycles["tui"] == "pdb_init_command"
    assert lifecycles["loop"] == "runtime"
    assert len(plan["pdb_init_command_backed"]) == 4


def test_runtime_services_object_registers_runtime_managed_services():
    services = RuntimeServices()
    services.register("loop", "run_loop", lifecycle="runtime", status="running")

    plan = services.to_manifest()

    assert plan["runtime_managed"][0]["service"] == "loop"
    assert plan["runtime_managed"][0]["status"] == "running"
