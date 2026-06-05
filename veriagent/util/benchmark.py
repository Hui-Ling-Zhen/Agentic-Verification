# coding=utf-8
"""Run manifest helpers for Agentic-Verification benchmark collection."""

from __future__ import annotations

import datetime as _dt
import os
from typing import Any, Dict, List, Optional

from veriagent.util.functions import get_abs_path_cwd_veriagent, load_json_file, save_json_file

MANIFEST_SCHEMA_VERSION = "3"
MANIFEST_FILENAME = "run_manifest.json"


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def _count_stages(stages_info: Dict[Any, Any]) -> Dict[str, int]:
    total = len(stages_info)
    passed = 0
    skipped = 0
    for item in stages_info.values():
        if not isinstance(item, dict):
            continue
        if item.get("skipped"):
            skipped += 1
        if item.get("completed") or item.get("is_completed"):
            passed += 1
    return {"total": total, "passed": passed, "skipped": skipped}


def build_run_manifest(
    *,
    workspace: str,
    dut_name: str,
    workflow_config: Optional[str],
    backend: str,
    backend_class: Optional[str],
    version: str,
    seed: Optional[int],
    stage_index: int,
    all_completed: bool,
    time_begin: Optional[float],
    time_end: Optional[float],
    stages_info: Dict[Any, Any],
    is_agent_exit: bool,
    last_turn: Optional[Dict[str, Any]] = None,
    policy: Optional[Dict[str, Any]] = None,
    previous: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    prev = previous or {}
    counts = _count_stages(stages_info if isinstance(stages_info, dict) else {})
    duration_sec = None
    if time_begin is not None and time_end is not None:
        duration_sec = max(0.0, float(time_end) - float(time_begin))

    manifest: Dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project": "Agentic-Verification",
        "dut": dut_name,
        "workspace": os.path.abspath(workspace),
        "workflow_config": workflow_config,
        "backend": backend,
        "backend_class": backend_class,
        "version": version,
        "seed": seed,
        "stage_index": stage_index,
        "all_completed": bool(all_completed),
        "is_agent_exit": bool(is_agent_exit),
        "stages_total": counts["total"],
        "stages_passed": counts["passed"],
        "stages_skipped": counts["skipped"],
        "time_begin": time_begin,
        "time_end": time_end,
        "duration_sec": duration_sec,
        "started_at": prev.get("started_at") or _utc_now(),
        "updated_at": _utc_now(),
    }
    turn = last_turn or {}
    manifest.update({
        "codex_thread_id": turn.get("thread_id"),
        "codex_turn_id": turn.get("turn_id"),
        "codex_turn_status": turn.get("status"),
        "codex_token_usage": turn.get("usage"),
        "codex_mcp_tool_calls": turn.get("mcp_tool_calls", 0),
        "codex_file_changes": turn.get("file_changes", 0),
        "codex_failure_reason": turn.get("failure_reason"),
        "codex_event_log": turn.get("event_log"),
    })
    policy_data = policy or {}
    manifest.update({
        "codex_config_file": policy_data.get("codex_config_file"),
        "codex_bin": policy_data.get("codex_bin"),
        "sandbox_mode": policy_data.get("sandbox_mode"),
        "network_access": policy_data.get("network_access"),
        "writable_roots": policy_data.get("writable_roots", []),
        "protected_inputs": policy_data.get("protected_inputs", []),
        "policy_enforcement": policy_data.get("policy_enforcement"),
        "veriagent_policy": policy_data.get("veriagent_policy"),
        "policy_warnings": policy_data.get("policy_warnings", []),
    })
    return manifest


def manifest_path(workspace: str) -> str:
    return get_abs_path_cwd_veriagent(workspace, MANIFEST_FILENAME)


def load_run_manifest(workspace: str) -> Dict[str, Any]:
    path = manifest_path(workspace)
    if not os.path.isfile(path):
        return {}
    try:
        data = load_json_file(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_run_manifest(workspace: str, manifest: Dict[str, Any]) -> str:
    path = manifest_path(workspace)
    save_json_file(path, manifest)
    return path


def update_run_manifest_from_agent(agent, stage_manager) -> Optional[str]:
    """Persist `.veriagent/run_manifest.json` from current agent/stage state."""
    if not getattr(agent, "workspace", None):
        return None
    backend = "unknown"
    try:
        backend = str(agent.cfg.backend.key_name)
    except Exception:
        pass
    backend_class = None
    try:
        backend_class = agent.backend.__class__.__module__ + "." + agent.backend.__class__.__name__
    except Exception:
        pass
    last_turn = {}
    try:
        last_turn = agent.backend.last_turn_summary()
    except Exception:
        last_turn = getattr(agent, "_last_backend_turn_result", {}) or {}
    policy = {}
    try:
        policy = agent.backend.policy_summary()
    except Exception:
        policy = {}
    if isinstance(policy, dict):
        warnings = list(policy.get("policy_warnings", []) or [])
        warnings.extend(getattr(agent, "policy_warnings", []) or [])
        policy["policy_warnings"] = warnings
    previous = load_run_manifest(agent.workspace)
    stages_info = {}
    if hasattr(stage_manager, "stages"):
        for idx, stage in enumerate(stage_manager.stages):
            try:
                stages_info[idx] = stage.detail()
            except Exception:
                stages_info[idx] = {"name": getattr(stage, "name", f"stage_{idx}")}
    manifest = build_run_manifest(
        workspace=agent.workspace,
        dut_name=getattr(agent, "dut_name", ""),
        workflow_config=getattr(agent, "config_file", None),
        backend=backend,
        backend_class=backend_class,
        version=getattr(agent, "__version__", ""),
        seed=getattr(agent, "seed", None),
        stage_index=getattr(stage_manager, "stage_index", 0),
        all_completed=getattr(stage_manager, "all_completed", False),
        time_begin=getattr(stage_manager, "time_begin", None),
        time_end=getattr(stage_manager, "time_end", None),
        stages_info=stages_info,
        is_agent_exit=agent.is_exit() if hasattr(agent, "is_exit") else False,
        last_turn=last_turn,
        policy=policy,
        previous=previous,
    )
    return save_run_manifest(agent.workspace, manifest)


def find_manifest_files(search_roots: List[str]) -> List[str]:
    found: List[str] = []
    for root in search_roots:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if ".veriagent" in dirnames:
                candidate = os.path.join(dirpath, ".veriagent", MANIFEST_FILENAME)
                if os.path.isfile(candidate):
                    found.append(candidate)
            if MANIFEST_FILENAME in filenames and os.path.basename(dirpath) == ".veriagent":
                found.append(os.path.join(dirpath, MANIFEST_FILENAME))
    return sorted(set(found))
