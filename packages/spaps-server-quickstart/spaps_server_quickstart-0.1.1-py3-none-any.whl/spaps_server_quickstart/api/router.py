"""
Router composition helpers.
"""

from __future__ import annotations

from typing import Any, TypeAlias, cast

from fastapi import APIRouter

_IncludeSpec: TypeAlias = tuple[APIRouter, dict[str, Any]]
RouterMount: TypeAlias = APIRouter | _IncludeSpec


def build_base_router(*routers: RouterMount) -> APIRouter:
    """
    Compose a base API router from child routers.

    Each positional argument can be either an `APIRouter` (included with default
    options) or a tuple of `(router, include_kwargs)` mirroring FastAPI's
    `include_router` signature.
    """

    base = APIRouter()
    for mount in routers:
        include_kwargs: dict[str, Any]
        if isinstance(mount, tuple):
            router, include_kwargs = cast(_IncludeSpec, mount)
        else:
            router = mount
            include_kwargs = {}
        base.include_router(router, **include_kwargs)
    return base
