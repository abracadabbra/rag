"""
Business tool access control helpers.

This module intentionally stays small: it protects order-level business data
without introducing a full user/role system into the demo application.
"""

import hmac
import logging
from typing import Literal, Optional

from fastapi import HTTPException

from api.config import settings

logger = logging.getLogger(__name__)

BUSINESS_TOOL_SCENES = {"risk_rule", "profit"}
BUSINESS_TOOL_TOKEN_HEADER = "X-Business-Tool-Token"
BusinessToolAccessScope = Literal["read", "execute"]


def require_business_tool_access(
    *,
    scene_type: Optional[str] = None,
    token: Optional[str] = None,
    scope: BusinessToolAccessScope = "execute",
) -> None:
    """Require a configured token before exposing order-level business data."""
    if not settings.enable_business_tool_access_control:
        return

    if scene_type is not None and scene_type not in BUSINESS_TOOL_SCENES:
        return

    expected_tokens = _expected_tokens(scope)
    if not expected_tokens:
        logger.warning(
            "Business tool access denied - reason=missing_token_config scene=%s scope=%s",
            scene_type or "business_tools",
            scope,
        )
        raise HTTPException(
            status_code=503,
            detail="业务工具访问控制未配置，请联系系统管理员。",
        )

    provided_token = (token or "").strip()
    if not provided_token or not any(
        hmac.compare_digest(provided_token, expected_token)
        for expected_token in expected_tokens
    ):
        logger.warning(
            "Business tool access denied - reason=invalid_token scene=%s scope=%s",
            scene_type or "business_tools",
            scope,
        )
        raise HTTPException(
            status_code=403,
            detail="无权访问订单级业务工具数据。",
        )


def _expected_tokens(scope: BusinessToolAccessScope) -> list[str]:
    """Return configured tokens accepted for one business access scope."""
    full_access_token = (settings.business_tool_access_token or "").strip()
    read_token = (settings.business_tool_read_token or "").strip()
    execute_token = (settings.business_tool_execute_token or "").strip()

    tokens = []
    if full_access_token:
        tokens.append(full_access_token)
    if scope == "read":
        tokens.extend(token for token in (read_token, execute_token) if token)
    elif execute_token:
        tokens.append(execute_token)
    return tokens
