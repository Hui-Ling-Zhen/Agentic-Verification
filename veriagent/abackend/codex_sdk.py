# coding: utf-8

"""Codex app-server SDK backend for VeriAgent."""

from __future__ import annotations

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .base import AgentBackendBase
from .codex_events import CodexRuntimeEvent, normalize_codex_notification
from .codex_session import CodexSessionStore
from veriagent.util.functions import get_abs_path_cwd_veriagent
from veriagent.util.log import info, warning


class CodexAppServerBackend(AgentBackendBase):
    """Structured Codex backend using the Python app-server SDK.

    One VeriAgent mission maps to one Codex Thread; one VeriAgent outer-loop
    round maps to one Codex Turn.
    """

    def __init__(
        self,
        vagent,
        config,
        codex_bin: str | None = None,
        model: str | None = None,
        model_provider: str | None = None,
        approval_policy: str | None = "never",
        sandbox: str | None = None,
        effort: str | None = None,
        personality: str | None = None,
        base_instructions: str | None = None,
        developer_instructions: str | None = None,
        service_tier: str | None = None,
        config_overrides: list[str] | tuple[str, ...] | None = None,
        render_files: dict[str, str] | None = None,
        compact_on_stage_complete: bool = False,
        codex_factory=None,
        **kwargs,
    ):
        super().__init__(vagent, config, **kwargs)
        self.codex_bin = codex_bin
        self.model = model
        self.model_provider = model_provider
        self.approval_policy = approval_policy
        self.sandbox = sandbox
        self.effort = effort
        self.personality = personality
        self.base_instructions = base_instructions
        self.developer_instructions = developer_instructions
        self.service_tier = service_tier
        self.config_overrides = tuple(config_overrides or ())
        self.render_files = render_files or {}
        self.compact_on_stage_complete = compact_on_stage_complete
        self.codex_factory = codex_factory

        self.CWD = None
        self._codex = None
        self._thread = None
        self._active_turn = None
        self._thread_state = None
        self._session_store = None
        self._events: list[CodexRuntimeEvent] = []
        self._last_turn = {}
        self._token_usage: dict[str, Any] | None = None
        self._last_response = ""

    def _get_assets_path(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        asset_path = os.path.join(current_path, "../assets")
        return os.path.abspath(asset_path)

    def _get_mcp_port(self):
        try:
            mcp = self.vagent.pdb._mcp_server
            if mcp is not None:
                return mcp.port
        except AttributeError:
            pass
        return self.config.mcp_server.port

    def _get_dft_ctx(self):
        ctx = os.environ.copy()
        ctx.update({
            "ASSETS": self._get_assets_path(),
            "CWD": self.CWD or self.vagent.workspace,
            "PORT": self._get_mcp_port(),
        })
        return ctx

    def _get_fmt_str(self, template):
        return template.format(**self._get_dft_ctx())

    def render_config_files(self):
        if not self.render_files:
            return
        context = self._get_dft_ctx()
        for src, dst in self.render_files.items():
            src_path = self._get_fmt_str(src)
            dst_path = self._get_fmt_str(dst)
            env = Environment(
                loader=FileSystemLoader(os.path.dirname(src_path)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            tmp = env.get_template(os.path.basename(src_path))
            dist_path = os.path.dirname(dst_path)
            if dist_path and not os.path.exists(dist_path):
                os.makedirs(dist_path, exist_ok=True)
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(tmp.render(context))
            info(f"Rendered Codex config file from {src_path} to {dst_path}.")

    def init(self):
        self.CWD = self.vagent.workspace
        self.MSG_FILE = get_abs_path_cwd_veriagent(self.CWD, "codex_sdk_last_prompt.txt")
        self._session_store = CodexSessionStore(self.CWD)
        self.render_config_files()
        self._codex = self._create_codex_client()
        self.start_or_resume_thread()
        info("Init Codex app-server backend complete")

    def _create_codex_client(self):
        if self.codex_factory is not None:
            return self.codex_factory()
        try:
            from codex_app_server import AppServerConfig, Codex
        except ImportError as exc:
            raise ImportError(
                "Codex app-server SDK is required for backend 'codex_app_server'. "
                "Install codex_app_server or use the legacy 'codex' CLI backend."
            ) from exc

        app_config = AppServerConfig(
            codex_bin=self.codex_bin,
            config_overrides=self.config_overrides,
            cwd=self.CWD,
            client_name="veriagent",
            client_title="Agentic-Verification",
        )
        return Codex(config=app_config)

    def _thread_kwargs(self):
        return {
            "approval_policy": self.approval_policy,
            "base_instructions": self.base_instructions,
            "cwd": self.CWD,
            "developer_instructions": self.developer_instructions,
            "model": self.model,
            "model_provider": self.model_provider,
            "personality": self.personality,
            "sandbox": self.sandbox,
            "service_tier": self.service_tier,
        }

    def _turn_kwargs(self):
        return {
            "approval_policy": self.approval_policy,
            "cwd": self.CWD,
            "effort": self.effort,
            "model": self.model,
            "personality": self.personality,
            "service_tier": self.service_tier,
        }

    def _clean_kwargs(self, kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

    def start_or_resume_thread(self):
        if self._codex is None:
            raise RuntimeError("Codex backend is not initialized")
        state = self._session_store.load()
        kwargs = self._clean_kwargs(self._thread_kwargs())
        if state.thread_id:
            try:
                self._thread = self._codex.thread_resume(state.thread_id, **kwargs)
                info(f"Resumed Codex thread: {state.thread_id}")
            except Exception as exc:
                warning(f"Failed to resume Codex thread {state.thread_id}: {exc}; starting a new thread.")
                self._thread = self._codex.thread_start(**kwargs)
        else:
            self._thread = self._codex.thread_start(**kwargs)
            info(f"Started Codex thread: {self._thread.id}")

        self._thread_state = self._session_store.save(
            state.__class__(
                thread_id=self._thread.id,
                last_turn_id=state.last_turn_id,
                model=self.model or state.model,
                cwd=self.CWD,
                backend="codex_app_server",
            )
        )
        try:
            self._thread.set_name(f"VeriAgent: {self.vagent.dut_name}")
        except Exception:
            pass
        return self._thread

    def model_name(self):
        return self.model or "codex_app_server"

    def get_human_message(self, text: str):
        return "[Human]: " + text

    def get_system_message(self, text: str):
        return "[System]: " + text

    def messages_get_raw(self):
        return []

    def _merge_messages(self, instructions):
        assert "messages" in instructions, "Messages not found in instructions."
        messages = [str(m) for m in instructions["messages"]]
        return "\n\n---------------\n\n".join(messages)

    def do_work_stream(self, instructions, config):
        return self.do_work_values(instructions, config)

    def do_work_values(self, instructions, config):
        prompt = self._merge_messages(instructions)
        os.makedirs(os.path.dirname(self.MSG_FILE), exist_ok=True)
        with open(self.MSG_FILE, "w", encoding="utf-8") as f:
            f.write(prompt)
        return self.run_turn(prompt, config)

    def run_turn(self, prompt, config=None):
        if self._thread is None:
            self.start_or_resume_thread()
        self._last_response = ""
        self._events = []
        kwargs = self._clean_kwargs(self._turn_kwargs())
        self._active_turn = self._thread.turn(str(prompt), **kwargs)
        self._session_store.update(last_turn_id=self._active_turn.id)
        self._thread_state = self._session_store.load()
        try:
            for notification in self._active_turn.stream():
                for event in normalize_codex_notification(notification, self.CWD):
                    self._handle_event(event)
        finally:
            self._active_turn = None
        return self._last_turn

    def stream_events(self, turn_handle=None):
        return iter(self._events)

    def _handle_event(self, event: CodexRuntimeEvent):
        self._events.append(event)
        if event.kind in {"agent_message_delta", "command_output_delta"} and event.text:
            self._last_response += event.text
            self.vagent.message_echo(event.text)
        elif event.kind in {"command_started", "command_completed"} and event.command:
            self.vagent.message_echo(f"[codex:{event.kind}] {event.command}")
        elif event.kind in {"mcp_tool_started", "mcp_tool_completed"} and event.tool:
            self._stat_msg_count_tool += 1 if event.kind == "mcp_tool_completed" else 0
            self.vagent.message_echo(f"[codex:{event.kind}] {event.tool}")
        elif event.kind.startswith("file_change") and event.file_paths:
            self.vagent.message_echo(f"[codex:{event.kind}] {', '.join(event.file_paths)}")

        if event.kind == "file_observed":
            self._notify_file_observed(event.file_paths)
        elif event.kind.startswith("file_change"):
            self._notify_file_observed(event.file_paths)
        elif event.kind == "token_usage_updated":
            self._token_usage = event.usage
        elif event.kind == "turn_completed":
            if event.usage:
                self._token_usage = event.usage
            self._last_turn = {
                "thread_id": event.thread_id or self.current_thread_id(),
                "turn_id": event.turn_id or self.current_turn_id(),
                "status": event.status,
                "usage": self._token_usage,
                "response": self._last_response,
            }
            self._thread_state = self._session_store.update(last_turn_id=self._last_turn["turn_id"])
            self._stat_msg_count_ai += 1

    def _notify_file_observed(self, paths: list[str]):
        if not paths:
            return
        stage_manager = getattr(self.vagent, "stage_manager", None)
        if stage_manager is None or not hasattr(stage_manager, "on_file_observed"):
            return
        for path in paths:
            stage_manager.on_file_observed(path, source="codex")

    def interrupt(self):
        if self._active_turn is None:
            return False
        try:
            self._active_turn.interrupt()
            return True
        except Exception as exc:
            warning(f"Failed to interrupt Codex turn {self.current_turn_id()}: {exc}")
            return False

    def current_thread_id(self):
        if self._thread is not None:
            return self._thread.id
        if self._thread_state is not None:
            return self._thread_state.thread_id
        return None

    def current_turn_id(self):
        if self._active_turn is not None:
            return self._active_turn.id
        if self._thread_state is not None:
            return self._thread_state.last_turn_id
        return None

    def last_turn_summary(self):
        return dict(self._last_turn)

    def token_total(self) -> int:
        total = (self._token_usage or {}).get("total")
        if isinstance(total, dict):
            for key in ("totalTokens", "total_tokens", "tokens"):
                if key in total:
                    return total[key]
        return -1

    def get_statistics(self) -> dict:
        return {
            "message_in": -1,
            "message_out": len(self._last_response),
            "thread_id": self.current_thread_id(),
            "turn_id": self.current_turn_id(),
            "token_usage": self._token_usage,
        }

    def requires_verification_only_mcp(self) -> bool:
        return True

    def on_stage_complete(self, stage):
        if not self.compact_on_stage_complete or self._thread is None:
            return
        try:
            self._thread.compact()
        except Exception as exc:
            warning(f"Codex thread compact failed after stage complete: {exc}")

    def exit(self):
        if self._codex is not None:
            self._codex.close()
            self._codex = None

    def close(self):
        return self.exit()
