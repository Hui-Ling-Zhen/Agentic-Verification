import sys
import json
from types import ModuleType


class FakeBackend:
    def __init__(self):
        self.inited = False
        self.debug = None

    def get_message_manage_node(self):
        return None

    def init(self):
        self.inited = True

    def set_debug(self, debug):
        self.debug = debug

    def interrupt(self):
        return False

    def close(self):
        return None

    def last_turn_summary(self):
        return {}

    def policy_summary(self):
        return {}


def test_verify_agent_can_be_instantiated_with_external_workflow(monkeypatch, tmp_path):
    langfuse = ModuleType("langfuse")
    langfuse.Langfuse = object
    langfuse_langchain = ModuleType("langfuse.langchain")
    langfuse_langchain.CallbackHandler = object
    monkeypatch.setitem(sys.modules, "langfuse", langfuse)
    monkeypatch.setitem(sys.modules, "langfuse.langchain", langfuse_langchain)

    from veriagent import verify_agent, verify_pdb
    from veriagent.stage import vstage

    workspace = tmp_path / "workspace"
    dut = workspace / "Adder"
    rtl = workspace / "Adder_RTL"
    dut.mkdir(parents=True)
    rtl.mkdir()
    (dut / "README.md").write_text("# Adder\n", encoding="utf-8")
    (dut / "__init__.py").write_text("", encoding="utf-8")
    (rtl / "Adder.v").write_text("module Adder; endmodule\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    fake_backend = FakeBackend()
    monkeypatch.setattr(verify_agent, "get_backend", lambda agent, cfg: fake_backend)
    monkeypatch.setattr(verify_agent, "uuid4", lambda: "test-session")
    monkeypatch.setattr(verify_pdb, "set_console_sync_handler", lambda handler: None)
    monkeypatch.setattr(verify_pdb.VerifyPDB, "_install_persistent_console_mirror", lambda self: None)
    monkeypatch.setattr(vstage.diff_ops, "is_git_repo", lambda path: True)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
mission:
  name: "Smoke {DUT}"
  prompt:
    system: "Smoke test workflow."
stage:
  - name: smoke_stage
    desc: "Smoke stage"
    task:
      - "Validate VerifyAgent construction."
    checker:
      - name: smoke_check
        clss: "NopChecker"
        args: {}
""",
        encoding="utf-8",
    )

    agent = verify_agent.VerifyAgent(
        workspace=str(workspace),
        dut_name="Adder",
        output="unity_test",
        config_file=str(workflow),
        cfg_override={
            "skill.use_skill": False,
            "langfuse.enable": False,
        },
        no_embed_tools=True,
        no_history=True,
        init_cmd=[],
    )

    assert agent.dut_name == "Adder"
    assert agent.config_file == str(workflow)
    assert agent.cfg.backend.key_name == "codex_app_server"
    assert agent.stage_manager is not None
    assert fake_backend.inited is True
    assert "Adder" in agent.cfg.un_write_dirs
    assert "Adder_RTL" in agent.cfg.un_write_dirs
    manifest = workspace / ".veriagent" / "run_manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["run_status"] == "initialized"
    assert data["backend_status"] == "official"


def test_official_codex_path_starts_mcp_before_backend(monkeypatch):
    from types import SimpleNamespace

    langfuse = ModuleType("langfuse")
    langfuse.Langfuse = object
    langfuse_langchain = ModuleType("langfuse.langchain")
    langfuse_langchain.CallbackHandler = object
    monkeypatch.setitem(sys.modules, "langfuse", langfuse)
    monkeypatch.setitem(sys.modules, "langfuse.langchain", langfuse_langchain)

    from veriagent import verify_agent

    started = []

    class FakeBackend:
        def requires_verification_only_mcp(self):
            return True

    class FakePdbMcpServer:
        def __init__(self, pdb, host, port, no_file_ops=False):
            self.pdb = pdb
            self.host = host
            self.port = port
            self.no_file_ops = no_file_ops
            self.is_running = True

        def start(self):
            started.append((self.host, self.port, self.no_file_ops))
            return True, "started"

    server_module = ModuleType("veriagent.server")
    server_module.PdbMcpServer = FakePdbMcpServer
    monkeypatch.setitem(sys.modules, "veriagent.server", server_module)

    agent = verify_agent.VerifyAgent.__new__(verify_agent.VerifyAgent)
    agent.backend = FakeBackend()
    agent.pdb = SimpleNamespace(_mcp_server=None)
    agent.cfg = SimpleNamespace(mcp_server=SimpleNamespace(host="127.0.0.1", port=5000))
    monkeypatch.setattr(
        verify_agent.VerifyAgent,
        "_wait_for_mcp_server_ready",
        lambda self, host, port: None,
    )

    agent._ensure_official_codex_mcp_server()

    assert started == [("127.0.0.1", 5000, True)]
    assert agent.pdb._mcp_server.no_file_ops is True


def test_verify_agent_exit_stops_mcp_server(monkeypatch):
    from types import SimpleNamespace

    from veriagent import verify_agent

    stopped = []

    class FakeMcpServer:
        is_running = True

        def stop(self):
            stopped.append(True)
            self.is_running = False
            return True, "stopped"

    agent = verify_agent.VerifyAgent.__new__(verify_agent.VerifyAgent)
    agent._is_exit = False
    agent.pdb = SimpleNamespace(_mcp_server=FakeMcpServer())
    agent.backend = FakeBackend()
    agent.cwd_read_only_files = []

    monkeypatch.setattr(verify_agent.fc, "chmode_rw", lambda files: None)

    agent.exit()

    assert stopped == [True]
    assert agent._is_exit is True


def test_verify_agent_registers_runtime_loop_service(monkeypatch):
    from veriagent import verify_agent

    agent = verify_agent.VerifyAgent.__new__(verify_agent.VerifyAgent)
    agent.runtime_services = verify_agent.RuntimeServices()
    agent.runtime_service_plan = agent.runtime_services.to_manifest()
    agent._run_manifest_status = "initialized"
    monkeypatch.setattr(
        verify_agent.VerifyAgent,
        "_update_run_manifest_safely",
        lambda self, status=None: None,
    )

    agent._register_runtime_loop_service()

    services = agent.runtime_services.to_manifest()["runtime_managed"]
    assert any(item["service"] == "loop" and item["command"] == "run_loop" for item in services)
