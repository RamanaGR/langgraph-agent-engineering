"""MVP auth — X-API-Key + role (recruiter | candidate)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException

from talentscreen.config import get_settings

Role = str


@dataclass
class AuthContext:
    role: Role
    tenant_id: str


def _validate_key(api_key: str | None, role: str | None) -> AuthContext:
    settings = get_settings()
    if not settings.auth_enabled:
        return AuthContext(role=role or "recruiter", tenant_id=settings.default_tenant_id)

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    if api_key == settings.api_key_recruiter:
        return AuthContext(role="recruiter", tenant_id=settings.default_tenant_id)
    if api_key == settings.api_key_candidate:
        return AuthContext(role="candidate", tenant_id=settings.default_tenant_id)

    raise HTTPException(status_code=403, detail="Invalid API key")


def require_recruiter(
    x_api_key: Annotated[str | None, Header()] = None,
    x_role: Annotated[str | None, Header()] = None,
) -> AuthContext:
    ctx = _validate_key(x_api_key, x_role or "recruiter")
    if ctx.role != "recruiter":
        raise HTTPException(status_code=403, detail="Recruiter role required")
    return ctx


def require_candidate(
    x_api_key: Annotated[str | None, Header()] = None,
    x_role: Annotated[str | None, Header()] = None,
) -> AuthContext:
    ctx = _validate_key(x_api_key, x_role or "candidate")
    if ctx.role != "candidate":
        raise HTTPException(status_code=403, detail="Candidate role required")
    return ctx


def require_any_auth(
    x_api_key: Annotated[str | None, Header()] = None,
    x_role: Annotated[str | None, Header()] = None,
) -> AuthContext:
    return _validate_key(x_api_key, x_role or "recruiter")
