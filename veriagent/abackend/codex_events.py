# coding: utf-8

"""Normalize Codex app-server notifications for VeriAgent."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodexRuntimeEvent:
    """Small VeriAgent-facing event independent of Codex SDK model classes."""

    kind: str
    thread_id: str | None = None
    turn_id: str | None = None
    item_id: str | None = None
    text: str | None = None
    tool: str | None = None
    command: str | None = None
    file_paths: list[str] = field(default_factory=list)
    usage: dict[str, Any] | None = None
    status: str | None = None
    raw: Any = None

    def to_record(self) -> dict[str, Any]:
        """Return a JSON-serializable event record for supervisor audit logs."""
        raw = _dump_model(self.raw) or self.raw
        try:
            import json
            json.dumps(raw)
        except Exception:
            raw = str(raw)
        return {
            "kind": self.kind,
            "thread_id": self.thread_id,
            "turn_id": self.turn_id,
            "item_id": self.item_id,
            "text": self.text,
            "tool": self.tool,
            "command": self.command,
            "file_paths": list(self.file_paths),
            "usage": self.usage,
            "status": self.status,
            "raw": raw,
        }


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _unwrap_root(obj: Any) -> Any:
    return _get_attr(obj, "root", obj)


def _dump_model(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(by_alias=True, mode="json", exclude_none=True)
        except TypeError:
            return obj.model_dump()
    return {}


def _status_to_str(status: Any) -> str | None:
    if status is None:
        return None
    return getattr(status, "value", str(status))


def _event_ids(payload: Any) -> tuple[str | None, str | None]:
    thread_id = _get_attr(payload, "thread_id")
    turn_id = _get_attr(payload, "turn_id")
    if thread_id is None:
        thread_id = _get_attr(payload, "threadId")
    if turn_id is None:
        turn_id = _get_attr(payload, "turnId")
    return thread_id, turn_id


def _item_payload(payload: Any) -> Any:
    return _unwrap_root(_get_attr(payload, "item"))


def _item_id(item: Any) -> str | None:
    return _get_attr(item, "id")


def _item_type(item: Any) -> str | None:
    return _get_attr(item, "type")


def _file_paths_from_changes(changes: Any) -> list[str]:
    paths: list[str] = []
    for change in changes or []:
        path = _get_attr(change, "path")
        if path:
            paths.append(str(path))
    return paths


def _file_paths_from_tool_args(arguments: Any) -> list[str]:
    data = _dump_model(arguments) or arguments
    if not isinstance(data, dict):
        return []
    keys = ("file_path", "path", "target_file", "filename")
    paths = []
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    return paths


def _normalize_file_path(workspace: str | None, path: str) -> str:
    if workspace is None:
        return path
    abs_workspace = os.path.abspath(workspace)
    abs_path = path if os.path.isabs(path) else os.path.abspath(os.path.join(abs_workspace, path))
    try:
        return os.path.relpath(abs_path, abs_workspace)
    except ValueError:
        return path


def _unknown_event(method: Any, payload: Any, notification: Any) -> CodexRuntimeEvent:
    thread_id, turn_id = _event_ids(payload)
    return CodexRuntimeEvent(
        "unknown",
        thread_id,
        turn_id,
        status=str(method or "unknown"),
        raw=notification,
    )


def normalize_codex_notification(notification: Any, workspace: str | None = None) -> list[CodexRuntimeEvent]:
    """Convert one Codex SDK notification into zero or more runtime events."""

    method = _get_attr(notification, "method")
    payload = _get_attr(notification, "payload")
    thread_id, turn_id = _event_ids(payload)
    events: list[CodexRuntimeEvent] = []

    if method == "item/agentMessage/delta":
        text = _get_attr(payload, "delta") or _get_attr(payload, "text")
        if text:
            return [CodexRuntimeEvent("agent_message_delta", thread_id, turn_id, text=str(text), raw=notification)]
        return [_unknown_event(method, payload, notification)]

    if method == "item/commandExecution/outputDelta":
        text = _get_attr(payload, "delta") or _get_attr(payload, "text")
        if text:
            return [CodexRuntimeEvent("command_output_delta", thread_id, turn_id, text=str(text), raw=notification)]
        return [_unknown_event(method, payload, notification)]

    if method == "item/fileChange/patchUpdated":
        raw_paths = _file_paths_from_changes(_get_attr(payload, "changes"))
        paths = [_normalize_file_path(workspace, p) for p in raw_paths]
        events.append(
            CodexRuntimeEvent(
                "file_change_updated",
                thread_id,
                turn_id,
                item_id=_get_attr(payload, "item_id") or _get_attr(payload, "itemId"),
                file_paths=paths,
                raw=notification,
            )
        )
        return events

    if method not in {"item/started", "item/completed"}:
        if method == "turn/started":
            turn = _get_attr(payload, "turn")
            events.append(
                CodexRuntimeEvent(
                    "turn_started",
                    thread_id,
                    _get_attr(turn, "id") or turn_id,
                    status=_status_to_str(_get_attr(turn, "status")),
                    raw=notification,
                )
            )
            return events
        if method == "turn/diff/updated":
            events.append(
                CodexRuntimeEvent(
                    "turn_diff_updated",
                    thread_id,
                    turn_id,
                    text=str(_get_attr(payload, "diff", "")),
                    raw=notification,
                )
            )
            return events
        if method == "turn/plan/updated":
            plan = _dump_model(_get_attr(payload, "plan")) or _get_attr(payload, "plan")
            events.append(
                CodexRuntimeEvent(
                    "turn_plan_updated",
                    thread_id,
                    turn_id,
                    text=str(plan or ""),
                    raw=notification,
                )
            )
            return events
        if method == "error":
            error_payload = _dump_model(_get_attr(payload, "error")) or _dump_model(payload) or payload
            events.append(
                CodexRuntimeEvent(
                    "error",
                    thread_id,
                    turn_id,
                    text=str(error_payload),
                    status="failed",
                    raw=notification,
                )
            )
            return events
        if method == "mcpServer/startupStatus/updated":
            events.append(
                CodexRuntimeEvent(
                    "mcp_server_startup_status",
                    thread_id,
                    turn_id,
                    tool=_get_attr(payload, "name"),
                    status=_status_to_str(_get_attr(payload, "status")),
                    text=str(_get_attr(payload, "error") or ""),
                    raw=notification,
                )
            )
            return events
        if method == "thread/tokenUsage/updated":
            usage = _dump_model(_get_attr(payload, "token_usage")) or _dump_model(_get_attr(payload, "tokenUsage"))
            events.append(
                CodexRuntimeEvent(
                    "token_usage_updated",
                    thread_id,
                    turn_id,
                    usage=usage or None,
                    raw=notification,
                )
            )
            return events
        if method == "turn/completed":
            turn = _get_attr(payload, "turn")
            usage = _dump_model(_get_attr(payload, "usage")) or _dump_model(_get_attr(turn, "usage"))
            events.append(
                CodexRuntimeEvent(
                    "turn_completed",
                    thread_id,
                    _get_attr(turn, "id") or turn_id,
                    usage=usage or None,
                    status=_status_to_str(_get_attr(turn, "status")),
                    raw=notification,
                )
            )
        return events or [_unknown_event(method, payload, notification)]

    phase = "started" if method == "item/started" else "completed"
    item = _item_payload(payload)
    item_type = _item_type(item)
    base = {
        "thread_id": thread_id,
        "turn_id": turn_id,
        "item_id": _item_id(item),
        "status": _status_to_str(_get_attr(item, "status")),
        "raw": notification,
    }

    if item_type == "commandExecution":
        events.append(
            CodexRuntimeEvent(
                f"command_{phase}",
                command=_get_attr(item, "command"),
                text=_get_attr(item, "aggregated_output"),
                **base,
            )
        )
        return events

    if item_type == "fileChange":
        raw_paths = _file_paths_from_changes(_get_attr(item, "changes"))
        paths = [_normalize_file_path(workspace, p) for p in raw_paths]
        events.append(CodexRuntimeEvent(f"file_change_{phase}", file_paths=paths, **base))
        return events

    if item_type == "mcpToolCall":
        tool = _get_attr(item, "tool")
        paths = [
            _normalize_file_path(workspace, p)
            for p in _file_paths_from_tool_args(_get_attr(item, "arguments"))
        ]
        events.append(CodexRuntimeEvent(f"mcp_tool_{phase}", tool=tool, file_paths=paths, **base))
        if tool == "ReadTextFile" and paths:
            events.append(CodexRuntimeEvent("file_observed", tool=tool, file_paths=paths, **base))
        return events

    return [_unknown_event(method, payload, notification)]
