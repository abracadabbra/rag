"""
Business tool contract routes.
"""

from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from api.models.schemas import (
    BusinessToolAuditEventsResponse,
    BusinessToolBatchValidationResponse,
    BusinessToolContractsResponse,
    BusinessToolProbeResponse,
    BusinessToolReadinessResponse,
    BusinessToolRuntimeStatusResponse,
    BusinessToolValidationResponse,
    ToolIntent,
)
from api.security.business_tools import BUSINESS_TOOL_TOKEN_HEADER, require_business_tool_access
from api.services.business_contracts import (
    contract_snapshot,
    fake_profit_payload,
    fake_risk_payload,
    normalize_order_id,
)
from api.services.tool_service import get_tool_service

router = APIRouter()


class BusinessToolProbeRequest(BaseModel):
    """Business tool probe request."""

    tool_name: str = Field(..., min_length=1, max_length=128)
    order_id: str = Field(..., min_length=1, max_length=128)


class BusinessToolIntentInspectRequest(BaseModel):
    """Business tool intent inspection request."""

    query: str = Field(..., min_length=1, max_length=1000)
    scene_type: str = Field(..., min_length=1, max_length=64)


class BusinessToolValidateResponseRequest(BaseModel):
    """Business tool response sample validation request."""

    tool_name: str = Field(..., min_length=1, max_length=128)
    payload: Any = Field(...)


class BusinessToolBatchValidateResponseRequest(BaseModel):
    """Business tool response sample batch validation request."""

    tool_name: str = Field(..., min_length=1, max_length=128)
    payloads: list[Any] = Field(..., min_length=1, max_length=50)


def _normalize_fake_http_order_id(order_id: str) -> str:
    try:
        return normalize_order_id(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/contracts",
    response_model=BusinessToolContractsResponse,
    summary="获取业务工具接口合同",
)
async def get_business_tool_contracts():
    """
    Return the machine-readable risk/profit business tool contracts.

    This endpoint is intentionally read-only and does not call external
    business systems.
    """
    return contract_snapshot()


@router.get("/fake-http/risk/events/{order_id}", summary="本地 fake 风控 HTTP 响应")
async def get_fake_risk_http_payload(order_id: str):
    """
    Return a deterministic fake risk payload for local smoke checks.

    This route is read-only and exists only so local smoke tests can exercise
    the real HTTP client path without binding another local port.
    """
    safe_order_id = _normalize_fake_http_order_id(order_id)
    return fake_risk_payload(safe_order_id)


@router.get(
    "/fake-http/profit/orders/{order_id}/chain",
    summary="本地 fake 毛利 HTTP 响应",
)
async def get_fake_profit_http_payload(order_id: str):
    """
    Return a deterministic fake profit payload for local smoke checks.

    This route is read-only and exists only so local smoke tests can exercise
    the real HTTP client path without binding another local port.
    """
    safe_order_id = _normalize_fake_http_order_id(order_id)
    return fake_profit_payload(safe_order_id)


@router.get(
    "/runtime-status",
    response_model=BusinessToolRuntimeStatusResponse,
    summary="获取业务工具运行态自检",
)
async def get_business_tool_runtime_status(
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Return safe runtime readiness metadata for business tools.

    The payload contains modes, booleans, endpoint templates, and counts only.
    It never returns API base URLs, API keys, shared tokens, or order payloads.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    return get_tool_service().runtime_status()


@router.get(
    "/readiness",
    response_model=BusinessToolReadinessResponse,
    summary="获取业务工具接入检查",
)
async def get_business_tool_readiness(
    limit: int = Query(default=20, ge=1, le=100),
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Return safe integration readiness gates for business tools.

    This endpoint does not call external business systems. It only combines
    runtime configuration booleans, contract availability, and recent safe audit
    metadata.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    return get_tool_service().readiness(limit=limit)


@router.post(
    "/probe",
    response_model=BusinessToolProbeResponse,
    response_model_exclude_none=True,
    summary="探测业务工具接口",
)
async def probe_business_tool(
    body: BusinessToolProbeRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Probe a risk/profit business tool with an explicit order id.

    The response is allowlisted for display and never includes raw exception
    details or non-contract fields.
    """
    require_business_tool_access(token=x_business_tool_token, scope="execute")
    try:
        return await run_in_threadpool(
            get_tool_service().probe,
            tool_name=body.tool_name,
            order_id=body.order_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/intent",
    response_model=ToolIntent,
    summary="预检业务工具意图",
)
async def inspect_business_tool_intent(
    body: BusinessToolIntentInspectRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Inspect whether a natural-language query would select a business tool.

    This endpoint never executes risk/profit systems. It exposes the same
    routing contract used by query flows so operators can debug tool selection
    before calling order-level interfaces.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    return await run_in_threadpool(
        get_tool_service().inspect_intent,
        query=body.query,
        scene_type=body.scene_type,
    )


@router.post(
    "/validate-response",
    response_model=BusinessToolValidationResponse,
    summary="校验业务工具响应样例",
)
async def validate_business_tool_response(
    body: BusinessToolValidateResponseRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Validate a response sample against the selected business tool contract.

    This route never calls external business systems and never returns the
    submitted payload values.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    try:
        return await run_in_threadpool(
            get_tool_service().validate_response_contract,
            tool_name=body.tool_name,
            payload=body.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/validate-responses",
    response_model=BusinessToolBatchValidationResponse,
    summary="批量校验业务工具响应样例",
)
async def validate_business_tool_responses(
    body: BusinessToolBatchValidateResponseRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Validate response samples against the selected business tool contract.

    This route never calls external business systems and never returns the
    submitted payload values. It is intended for real-system integration
    handoffs where teams provide multiple captured response samples.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    try:
        return await run_in_threadpool(
            get_tool_service().validate_response_contract_batch,
            tool_name=body.tool_name,
            payloads=body.payloads,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/audit-events",
    response_model=BusinessToolAuditEventsResponse,
    summary="获取最近业务工具审计事件",
)
async def get_business_tool_audit_events(
    limit: int = Query(default=20, ge=1, le=100),
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    Return recent safe business tool audit events.

    Events only include sanitized arguments, endpoint templates, result key
    names, status, duration, data source, and error type.
    """
    require_business_tool_access(token=x_business_tool_token, scope="read")
    runtime_status = get_tool_service().runtime_status()
    audit_status = runtime_status.get("audit") or {}
    return {
        "events": get_tool_service().list_audit_events(limit=limit),
        "limit": limit,
        "audit_status": {
            "file_enabled": bool(audit_status.get("file_enabled")),
            "file_configured": bool(audit_status.get("file_configured")),
            "file_name": audit_status.get("file_name"),
            "file_exists": bool(audit_status.get("file_exists")),
            "file_readable": bool(audit_status.get("file_readable")),
            "persisted_event_count": int(audit_status.get("persisted_event_count") or 0),
            "memory_event_count": int(audit_status.get("memory_event_count") or 0),
            "memory_event_limit": int(audit_status.get("memory_event_limit") or 0),
        },
    }
