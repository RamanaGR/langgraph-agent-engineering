"""Optional Langfuse tracing for /query pipeline."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from talentscreen.config import get_settings


class _NoOpTrace:
    id: str = ""

    def generation(self, **kwargs: Any) -> _NoOpTrace:
        return self

    def span(self, **kwargs: Any) -> _NoOpTrace:
        return self

    def event(self, **kwargs: Any) -> None:
        return None

    def update(self, **kwargs: Any) -> None:
        return None

    def end(self, **kwargs: Any) -> None:
        return None


@contextmanager
def trace_query(
    *,
    name: str,
    input_data: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    settings = get_settings()
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        yield _NoOpTrace()
        return

    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        trace = client.trace(
            id=str(uuid4()),
            name=name,
            input=input_data,
            metadata=metadata or {},
        )
        try:
            yield trace
        finally:
            client.flush()
    except Exception:
        yield _NoOpTrace()
