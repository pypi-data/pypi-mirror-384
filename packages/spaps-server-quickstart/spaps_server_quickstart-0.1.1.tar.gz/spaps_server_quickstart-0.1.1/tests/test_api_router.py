from __future__ import annotations

from fastapi import APIRouter

from spaps_server_quickstart.api.router import build_base_router


def test_build_base_router_includes_child_routers() -> None:
    first = APIRouter()
    second = APIRouter()

    @first.get("/first")
    def first_handler():  # pragma: no cover - not executed
        return {"ok": True}

    @second.get("/second")
    def second_handler():  # pragma: no cover - not executed
        return {"ok": True}

    base = build_base_router(first, (second, {"prefix": "/v1"}))

    assert len(base.routes) == len(first.routes) + len(second.routes)
    assert any(route.path.startswith("/v1") for route in base.routes)
