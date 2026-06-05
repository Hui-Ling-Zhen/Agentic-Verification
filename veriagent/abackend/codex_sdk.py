# coding: utf-8

"""Codex app-server SDK backend for VeriAgent."""

from __future__ import annotations

import os
import json
import hashlib
import datetime as _dt
import shutil
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .base import (
    AgentBackendBase,
    TURN_STATUS_COMPLETED,
    TURN_STATUS_FAILED,
    TURN_STATUS_INTERRUPTED,
    TURN_STATUS_REQUIRES_APPROVAL,
)
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
        resume_codex_thread: bool = False,
        codex_network_access: str = "enabled",
        codex_write_policy: str = "workspace_only",
        codex_command_policy: str = "codex_sandbox",
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
        self.resume_codex_thread = resume_codex_thread
        self.codex_network_access = codex_network_access
        self.codex_write_policy = codex_write_policy
        self.codex_command_policy = codex_command_policy
        self.codex_factory = codex_factory

        self.CWD = None
        self.CODEX_CONFIG_FILE = None
        self._codex = None
        self._thread = None
        self._active_turn = None
        self._thread_state = None
        self._session_store = None
        self._events: list[CodexRuntimeEvent] = []
        self._last_turn = {}
        self._token_usage: dict[str, Any] | None = None
        self._last_response = ""
        self._event_counts = {"mcp_tool_calls": 0, "file_changes": 0}
        self._failure_reason = None

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
            "DUT": getattr(self.vagent, "dut_name", ""),
            "PORT": self._get_mcp_port(),
            "SANDBOX": self.sandbox or "workspace-write",
            "CODEX_NETWORK_ACCESS": self.codex_network_access,
            "CODEX_WRITE_POLICY": self.codex_write_policy,
            "CODEX_COMMAND_POLICY": self.codex_command_policy,
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
            if os.path.basename(dst_path) == "config.toml" and os.path.basename(os.path.dirname(dst_path)) == ".codex":
                self.CODEX_CONFIG_FILE = dst_path
            info(f"Rendered Codex config file from {src_path} to {dst_path}.")

    def init(self):
        self.CWD = self.vagent.workspace
        self.MSG_FILE = get_abs_path_cwd_veriagent(self.CWD, "codex_sdk_last_prompt.txt")
        self.EVENT_LOG_FILE = get_abs_path_cwd_veriagent(self.CWD, "codex_events.jsonl")
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
                "Install OpenAI Codex open-source SDK from codex/sdk/python "
                "(package 'openai-codex-app-server-sdk'), for example: "
                "`pip install -e ../codex/sdk/python`. Legacy `codex exec` is kept "
                "only for compatibility and does not provide the thread/turn/event contract."
            ) from exc

        codex_bin = self._resolve_codex_bin()
        self.codex_bin = codex_bin
        app_config = AppServerConfig(
            codex_bin=codex_bin,
            config_overrides=self.config_overrides,
            cwd=self.CWD,
            client_name="veriagent",
            client_title="Agentic-Verification",
        )
        return Codex(config=app_config)

    @staticmethod
    def _is_executable_file(path: str) -> bool:
        return os.path.isfile(path) and os.access(path, os.X_OK)

    @classmethod
    def _resolve_configured_codex_bin(cls, value: str, source: str) -> str:
        expanded = os.path.abspath(os.path.expanduser(os.path.expandvars(value)))
        if cls._is_executable_file(expanded):
            info(f"Using OpenAI Codex binary from {source}: {expanded}")
            return expanded

        resolved = shutil.which(value)
        if resolved and cls._is_executable_file(resolved):
            info(f"Using OpenAI Codex binary from {source}: {resolved}")
            return resolved

        raise FileNotFoundError(
            f"Codex binary configured by {source} was not found or is not executable: {value!r}. "
            "Set CODEX_BIN to the open-source Codex binary path, for example "
            "`export CODEX_BIN=\"$(which codex)\"` after installing https://github.com/openai/codex."
        )

    def _resolve_codex_bin(self) -> str:
        """Resolve the open-source Codex binary used by `codex app-server`."""
        if self.codex_bin:
            return self._resolve_configured_codex_bin(str(self.codex_bin), "backend codex_bin")

        env_codex_bin = os.environ.get("CODEX_BIN")
        if env_codex_bin:
            return self._resolve_configured_codex_bin(env_codex_bin, "CODEX_BIN")

        path_codex = shutil.which("codex")
        if path_codex and self._is_executable_file(path_codex):
            info(f"Using OpenAI Codex binary from PATH: {path_codex}")
            return path_codex

        raise FileNotFoundError(
            "Unable to locate the OpenAI Codex binary for `codex app-server`. "
            "Install https://github.com/openai/codex, ensure `codex` is on PATH, or set "
            "`CODEX_BIN` explicitly, for example `export CODEX_BIN=\"$(which codex)\"`. "
            "The legacy `codex exec` backend is not an official replacement because it has "
            "no structured thread/turn/event contract."
        )

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

    def policy_summary(self):
        cwd = self.CWD or self.vagent.workspace
        dut = getattr(self.vagent, "dut_name", "")
        protected_inputs = [
            os.path.join(cwd, rel_path)
            for rel_path in [dut, f"{dut}_RTL", "Guide_Doc", "skills"]
            if rel_path
        ]
        return {
            "codex_config_file": self.CODEX_CONFIG_FILE or os.path.join(cwd, ".codex", "config.toml"),
            "codex_bin": self.codex_bin,
            "sandbox_mode": self.sandbox or "workspace-write",
            "network_access": self.codex_network_access,
            "writable_roots": [cwd],
            "protected_inputs": protected_inputs,
            "policy_enforcement": "codex_sandbox_os_permissions",
            "veriagent_policy": "audit_hint_only",
        }

    def _clean_kwargs(self, kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

    def _sha256_file(self, path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hash_jsonable(self, value):
        payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _resolve_workflow_config_path(self):
        config_file = getattr(self.vagent, "config_file", None)
        if not config_file:
            return None
        if os.path.isabs(config_file) and os.path.isfile(config_file):
            return os.path.abspath(config_file)
        candidates = [
            os.path.abspath(config_file),
            os.path.abspath(os.path.join(self.CWD or self.vagent.workspace, config_file)),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return config_file

    def _workflow_hash(self, workflow_config):
        if workflow_config and os.path.isfile(workflow_config):
            return self._sha256_file(workflow_config)
        return self._hash_jsonable({"workflow_config": workflow_config})

    def _workspace_hash(self):
        """Hash stable task inputs rather than generated output files."""
        roots = [
            os.path.join(self.CWD, getattr(self.vagent, "dut_name", "")),
            os.path.join(self.CWD, f"{getattr(self.vagent, 'dut_name', '')}_RTL"),
            os.path.join(self.CWD, "Guide_Doc"),
            os.path.join(self.CWD, "skills"),
        ]
        records = []
        for root in roots:
            if not root or not os.path.exists(root):
                records.append({"path": os.path.relpath(root, self.CWD), "missing": True})
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in sorted(dirnames) if d not in {"__pycache__", ".git"}]
                for filename in sorted(filenames):
                    if filename.endswith((".pyc", ".pyo")):
                        continue
                    path = os.path.join(dirpath, filename)
                    rel = os.path.relpath(path, self.CWD)
                    try:
                        records.append({"path": rel, "sha256": self._sha256_file(path)})
                    except OSError as exc:
                        records.append({"path": rel, "error": str(exc)})
        return self._hash_jsonable(records)

    def _backend_args_hash(self):
        return self._hash_jsonable({
            "model": self.model,
            "model_provider": self.model_provider,
            "approval_policy": self.approval_policy,
            "sandbox": self.sandbox,
            "effort": self.effort,
            "personality": self.personality,
            "service_tier": self.service_tier,
            "config_overrides": list(self.config_overrides),
            "render_files": self.render_files,
            "codex_network_access": self.codex_network_access,
            "codex_write_policy": self.codex_write_policy,
            "codex_command_policy": self.codex_command_policy,
        })

    def _current_session_fingerprint(self):
        workflow_config = self._resolve_workflow_config_path()
        return {
            "dut_name": getattr(self.vagent, "dut_name", None),
            "workflow_config": workflow_config,
            "workflow_hash": self._workflow_hash(workflow_config),
            "workspace_hash": self._workspace_hash(),
            "backend_args_hash": self._backend_args_hash(),
        }

    def _session_mismatches(self, state, current):
        mismatches = {}
        for key, expected in current.items():
            observed = getattr(state, key, None)
            if observed != expected:
                mismatches[key] = {"saved": observed, "current": expected}
        return mismatches

    def start_or_resume_thread(self):
        if self._codex is None:
            raise RuntimeError("Codex backend is not initialized")
        state = self._session_store.load()
        fingerprint = self._current_session_fingerprint()
        kwargs = self._clean_kwargs(self._thread_kwargs())
        mismatches = self._session_mismatches(state, fingerprint) if state.thread_id else {}
        should_resume = bool(state.thread_id) and (not mismatches or self.resume_codex_thread)
        if mismatches and state.thread_id:
            mismatch_keys = ", ".join(sorted(mismatches.keys()))
            if self.resume_codex_thread:
                warning(
                    f"Codex session fingerprint mismatch ({mismatch_keys}); "
                    "--resume-codex-thread was set, resuming anyway."
                )
            else:
                warning(
                    f"Codex session fingerprint mismatch ({mismatch_keys}); "
                    "starting a new thread. Use --resume-codex-thread to force reuse."
                )
        if should_resume:
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
                last_turn_id=state.last_turn_id if should_resume else None,
                model=self.model or state.model,
                cwd=self.CWD,
                backend="codex_app_server",
                **fingerprint,
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
        self._last_turn = {}
        self._event_counts = {"mcp_tool_calls": 0, "file_changes": 0}
        self._failure_reason = None
        kwargs = self._clean_kwargs(self._turn_kwargs())
        self._active_turn = self._thread.turn(str(prompt), **kwargs)
        self._session_store.update(last_turn_id=self._active_turn.id)
        self._thread_state = self._session_store.load()
        try:
            for notification in self._active_turn.stream():
                for event in normalize_codex_notification(notification, self.CWD):
                    self._handle_event(event)
        except Exception as exc:
            self._failure_reason = str(exc)
            self._last_turn = self._build_turn_summary(TURN_STATUS_FAILED, self._failure_reason)
        finally:
            self._active_turn = None
        if not self._last_turn:
            status = TURN_STATUS_INTERRUPTED if self.vagent.is_break() else TURN_STATUS_FAILED
            reason = "Codex turn ended without a turn_completed event"
            self._failure_reason = None if status == TURN_STATUS_INTERRUPTED else reason
            self._last_turn = self._build_turn_summary(status, reason)
        return self._last_turn

    def stream_events(self, turn_handle=None):
        return iter(self._events)

    def _handle_event(self, event: CodexRuntimeEvent):
        self._events.append(event)
        self._append_event_record(event)
        if event.kind in {"agent_message_delta", "command_output_delta"} and event.text:
            self._last_response += event.text
            self.vagent.message_echo(event.text)
        elif event.kind in {"command_started", "command_completed"} and event.command:
            self.vagent.message_echo(f"[codex:{event.kind}] {event.command}")
        elif event.kind in {"mcp_tool_started", "mcp_tool_completed"} and event.tool:
            self._stat_msg_count_tool += 1 if event.kind == "mcp_tool_completed" else 0
            if event.kind == "mcp_tool_completed":
                self._event_counts["mcp_tool_calls"] += 1
            self.vagent.message_echo(f"[codex:{event.kind}] {event.tool}")
        elif event.kind.startswith("file_change") and event.file_paths:
            if event.kind == "file_change_completed":
                self._event_counts["file_changes"] += len(event.file_paths)
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
            status = self._normalize_turn_status(event.status)
            reason = None if status == TURN_STATUS_COMPLETED else f"Codex turn status: {event.status}"
            self._failure_reason = reason
            self._last_turn = self._build_turn_summary(
                status,
                reason,
                thread_id=event.thread_id or self.current_thread_id(),
                turn_id=event.turn_id or self.current_turn_id(),
            )
            self._thread_state = self._session_store.update(last_turn_id=self._last_turn["turn_id"])
            self._stat_msg_count_ai += 1

    def _append_event_record(self, event: CodexRuntimeEvent):
        os.makedirs(os.path.dirname(self.EVENT_LOG_FILE), exist_ok=True)
        record = event.to_record()
        record["ts"] = _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()
        with open(self.EVENT_LOG_FILE, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def _normalize_turn_status(self, status):
        if status is None:
            return TURN_STATUS_COMPLETED
        raw = str(status or "").lower()
        if raw in {"completed", "success", "succeeded"} or raw.endswith(".completed"):
            return TURN_STATUS_COMPLETED
        if raw in {"cancelled", "canceled", "interrupted", "aborted"} or any(
            token in raw for token in ("cancel", "interrupt", "abort")
        ):
            return TURN_STATUS_INTERRUPTED
        if raw in {"requires_approval", "waiting_for_approval", "approval_required"} or "approval" in raw:
            return TURN_STATUS_REQUIRES_APPROVAL
        return TURN_STATUS_FAILED

    def _build_turn_summary(self, status, failure_reason=None, thread_id=None, turn_id=None):
        return {
            "thread_id": thread_id or self.current_thread_id(),
            "turn_id": turn_id or self.current_turn_id(),
            "status": status,
            "usage": self._token_usage,
            "response": self._last_response,
            "mcp_tool_calls": self._event_counts["mcp_tool_calls"],
            "file_changes": self._event_counts["file_changes"],
            "failure_reason": failure_reason,
            "event_log": self.EVENT_LOG_FILE,
        }

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
