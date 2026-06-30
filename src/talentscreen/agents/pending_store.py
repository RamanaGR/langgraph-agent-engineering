"""In-memory store for HITL pending approvals (demo / dev)."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Any

_lock = threading.Lock()
_pending: dict[str, dict[str, Any]] = {}


def register_pending(
    *,
    thread_id: str,
    pending_approval: dict[str, Any],
    tenant_id: str,
    preview: str | None = None,
) -> None:
    with _lock:
        _pending[thread_id] = {
            "thread_id": thread_id,
            "tenant_id": tenant_id,
            "pending_approval": pending_approval,
            "preview": preview,
            "created_at": datetime.now(UTC).isoformat(),
        }


def list_pending(*, tenant_id: str | None = None) -> list[dict[str, Any]]:
    with _lock:
        items = list(_pending.values())
    if tenant_id:
        items = [item for item in items if item.get("tenant_id") == tenant_id]
    return sorted(items, key=lambda item: item.get("created_at", ""), reverse=True)


def remove_pending(thread_id: str) -> None:
    with _lock:
        _pending.pop(thread_id, None)


def clear_pending() -> None:
    with _lock:
        _pending.clear()
