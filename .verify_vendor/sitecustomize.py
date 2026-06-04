"""Temporary test compatibility shims for the local .verify_vendor environment."""

import typing

try:
    from typing_extensions import NotRequired, Required, Self
except Exception:  # pragma: no cover - best-effort shim
    NotRequired = None
    Required = None
    Self = None

if NotRequired is not None and not hasattr(typing, "NotRequired"):
    typing.NotRequired = NotRequired

if Required is not None and not hasattr(typing, "Required"):
    typing.Required = Required

if Self is not None and not hasattr(typing, "Self"):
    typing.Self = Self
