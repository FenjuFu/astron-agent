import pytest
from fastapi import HTTPException

from workflow.api.v1.chat.node_debug import router as node_debug_router
from workflow.extensions.fastapi.middleware.auth import (
    WORKFLOW_INTERNAL_API_KEY_ENV,
    WORKFLOW_INTERNAL_API_KEY_PLACEHOLDER,
    require_workflow_internal_api_key,
)


@pytest.mark.asyncio
async def test_internal_api_auth_accepts_configured_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WORKFLOW_INTERNAL_API_KEY_ENV, "server-secret")

    await require_workflow_internal_api_key("server-secret")


@pytest.mark.asyncio
async def test_internal_api_auth_rejects_missing_or_wrong_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(WORKFLOW_INTERNAL_API_KEY_ENV, "server-secret")

    for supplied_key in (None, "", "wrong-secret"):
        with pytest.raises(HTTPException) as exc_info:
            await require_workflow_internal_api_key(supplied_key)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("configured_key", ["", WORKFLOW_INTERNAL_API_KEY_PLACEHOLDER])
async def test_internal_api_auth_fails_closed_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
    configured_key: str,
) -> None:
    monkeypatch.setenv(WORKFLOW_INTERNAL_API_KEY_ENV, configured_key)

    with pytest.raises(HTTPException) as exc_info:
        await require_workflow_internal_api_key(configured_key)

    assert exc_info.value.status_code == 503


def test_every_node_debug_route_requires_internal_auth() -> None:
    for route in node_debug_router.routes:
        assert any(
            dependency.call is require_workflow_internal_api_key
            for dependency in route.dependant.dependencies
        ), route.path
