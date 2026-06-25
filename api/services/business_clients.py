"""
Business system clients used by tool execution.

These clients keep external-system contracts away from the agent/tool router.
They currently return deterministic mock data unless a real API base URL is
configured.
"""

import json
import socket
from typing import Any, Dict, Optional, Tuple
from urllib import error, request

from api.config import settings
from api.services.business_contracts import (
    BusinessContractError,
    derive_profit_chain,
    NUMBER_TYPES,
    PROFIT_CHAIN_STEP_REQUIRED_FIELDS,
    PROFIT_REQUIRED_FIELDS,
    PROFIT_TOOL_NAME,
    RISK_HIT_RULE_REQUIRED_FIELDS,
    RISK_REQUIRED_FIELDS,
    RISK_TOOL_NAME,
    RequiredFieldSpec,
    endpoint_path,
    type_label,
)


def _get_json(*, base_url: str, api_key: str, timeout: int, path: str) -> Dict[str, Any]:
    """Fetch JSON from a configured business API."""
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raise ConnectionError(f"Business API HTTP error: status={exc.code}") from exc
    except (TimeoutError, socket.timeout) as exc:
        raise TimeoutError("Business API request timed out") from exc
    except (error.URLError, OSError) as exc:
        raise ConnectionError("Business API connection failed") from exc
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise BusinessContractError(
            "Business API returned invalid JSON",
            diagnostic_code="invalid_json",
            invalid_fields=["response body invalid JSON"],
        ) from exc
    if not isinstance(data, dict):
        raise BusinessContractError(
            "Business API returned non-object JSON",
            diagnostic_code="non_object_json",
        )
    return data


def _type_name(types: Tuple[type, ...]) -> str:
    return type_label(types)


def _is_valid_type(value: Any, expected_types: Tuple[type, ...]) -> bool:
    if expected_types == NUMBER_TYPES:
        return isinstance(value, NUMBER_TYPES) and not isinstance(value, bool)
    return isinstance(value, expected_types)


def _validate_required_fields(
    *,
    contract_name: str,
    data: Dict[str, Any],
    required_fields: RequiredFieldSpec,
) -> None:
    """Validate the minimal response contract without logging payload values."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise BusinessContractError(
            f"{contract_name} API response contract violation: "
            f"missing required fields: {', '.join(missing_fields)}",
            diagnostic_code="missing_required_fields",
            missing_fields=missing_fields,
        )

    invalid_fields = [
        f"{field} expected {_type_name(expected_types)}"
        for field, expected_types in required_fields.items()
        if not _is_valid_type(data[field], expected_types)
    ]
    if invalid_fields:
        raise BusinessContractError(
            f"{contract_name} API response contract violation: "
            f"invalid field types: {', '.join(invalid_fields)}",
            diagnostic_code="invalid_field_types",
            invalid_fields=invalid_fields,
        )


def _validate_risk_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate risk event detail response shape."""
    _validate_required_fields(
        contract_name="Risk",
        data=data,
        required_fields=RISK_REQUIRED_FIELDS,
    )

    invalid_rules = []
    for index, rule in enumerate(data["hit_rules"], start=1):
        if not isinstance(rule, dict):
            invalid_rules.append(f"hit_rules[{index}] expected object")
            continue

        missing_rule_fields = [
            field for field in RISK_HIT_RULE_REQUIRED_FIELDS if field not in rule
        ]
        if missing_rule_fields:
            invalid_rules.append(
                f"hit_rules[{index}] missing {', '.join(missing_rule_fields)}"
            )
            continue

        invalid_rule_fields = [
            field
            for field, expected_types in RISK_HIT_RULE_REQUIRED_FIELDS.items()
            if not _is_valid_type(rule[field], expected_types)
        ]
        if invalid_rule_fields:
            invalid_rules.append(
                f"hit_rules[{index}] invalid {', '.join(invalid_rule_fields)}"
            )

    if invalid_rules:
        raise BusinessContractError(
            "Risk API response contract violation: "
            f"invalid hit_rules: {'; '.join(invalid_rules)}",
            diagnostic_code="invalid_hit_rules",
            invalid_fields=invalid_rules,
        )

    return data


def _validate_profit_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate profit chain response shape."""
    _validate_required_fields(
        contract_name="Profit",
        data=data,
        required_fields=PROFIT_REQUIRED_FIELDS,
    )

    chain = data.get("chain")
    if chain is not None:
        if not isinstance(chain, list):
            raise BusinessContractError(
                "Profit API response contract violation: chain expected list",
                diagnostic_code="invalid_chain",
                invalid_fields=["chain expected list"],
            )

        invalid_steps = []
        for index, step in enumerate(chain, start=1):
            if not isinstance(step, dict):
                invalid_steps.append(f"chain[{index}] expected object")
                continue
            for field, expected_types in PROFIT_CHAIN_STEP_REQUIRED_FIELDS.items():
                if field not in step or not _is_valid_type(step.get(field), expected_types):
                    invalid_steps.append(
                        f"chain[{index}].{field} expected {_type_name(expected_types)}"
                    )

        if invalid_steps:
            raise BusinessContractError(
                "Profit API response contract violation: "
                f"invalid chain: {'; '.join(invalid_steps)}",
                diagnostic_code="invalid_chain",
                invalid_fields=invalid_steps,
            )

    return data


def validate_business_response(tool_name: str, data: Any) -> Dict[str, Any]:
    """Validate a business API response sample against the shared tool contract."""
    if not isinstance(data, dict):
        raise BusinessContractError(
            "Business API returned non-object JSON",
            diagnostic_code="non_object_json",
        )
    if tool_name == RISK_TOOL_NAME:
        return _validate_risk_contract(data)
    if tool_name == PROFIT_TOOL_NAME:
        return _validate_profit_contract(data)
    raise ValueError(f"Unknown business tool: {tool_name}")


class RiskSystemClient:
    """Client boundary for risk event detail lookups."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = settings.risk_api_base_url if base_url is None else base_url
        self.api_key = settings.risk_api_key if api_key is None else api_key
        self.timeout = settings.business_tool_timeout if timeout is None else timeout

    def get_event_detail(self, order_id: str) -> Dict[str, Any]:
        """Return risk decision details for an order."""
        if self.base_url:
            return _validate_risk_contract(
                _get_json(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                    path=endpoint_path(RISK_TOOL_NAME, order_id=order_id),
                )
            )

        return _validate_risk_contract({
            "order_id": order_id,
            "decision": "block",
            "risk_score": 87,
            "risk_level": "high",
            "hit_rules": [
                {
                    "rule_id": "RISK-velocity-001",
                    "rule_name": "短时间多次高额交易",
                    "evidence": "10 分钟内同卡 4 次交易，累计金额 1820 元",
                },
                {
                    "rule_id": "RISK-device-003",
                    "rule_name": "新设备异常登录后交易",
                    "evidence": "交易前 6 分钟发生新设备登录",
                },
            ],
            "customer_context": {
                "user_level": "standard",
                "recent_chargebacks": 1,
                "account_age_days": 42,
            },
            "transaction_context": {
                "amount": 680.0,
                "city": "上海",
                "channel": "app",
                "payment_method": "credit_card",
            },
            "recommended_action": (
                "建议保持拦截，并引导用户完成二次验证后重试。"
            ),
        })


class ProfitSystemClient:
    """Client boundary for profit chain detail lookups."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = settings.profit_api_base_url if base_url is None else base_url
        self.api_key = settings.profit_api_key if api_key is None else api_key
        self.timeout = settings.business_tool_timeout if timeout is None else timeout

    def get_chain_detail(self, order_id: str) -> Dict[str, Any]:
        """Return commission, driver income, and settlement chain for an order."""
        if self.base_url:
            return _validate_profit_contract(
                _get_json(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                    path=endpoint_path(PROFIT_TOOL_NAME, order_id=order_id),
                )
            )

        gross_amount = 128.6
        platform_commission = 19.29
        driver_income = 92.35
        subsidy = 8.0
        coupon = 6.0
        channel_fee = 2.96
        platform_net_profit = round(platform_commission - subsidy - coupon - channel_fee, 2)
        payload = {
            "order_id": order_id,
            "settlement_status": "settled",
            "gross_amount": gross_amount,
            "platform_commission": platform_commission,
            "commission_rate": "15.0%",
            "driver_income": driver_income,
            "driver_income_detail": {
                "base_fare": 78.0,
                "distance_fee": 16.35,
                "service_fee_deduction": -2.0,
            },
            "subsidy": subsidy,
            "coupon": coupon,
            "channel_fee": channel_fee,
            "platform_net_profit": platform_net_profit,
        }
        payload["chain"] = derive_profit_chain(payload)
        return _validate_profit_contract(payload)


_risk_system_client: Optional[RiskSystemClient] = None
_profit_system_client: Optional[ProfitSystemClient] = None


def get_risk_system_client() -> RiskSystemClient:
    """Get risk system client singleton."""
    global _risk_system_client
    if _risk_system_client is None:
        _risk_system_client = RiskSystemClient()
    return _risk_system_client


def get_profit_system_client() -> ProfitSystemClient:
    """Get profit system client singleton."""
    global _profit_system_client
    if _profit_system_client is None:
        _profit_system_client = ProfitSystemClient()
    return _profit_system_client


def reset_business_clients() -> None:
    """Reset business API client singletons after runtime settings change."""
    global _risk_system_client, _profit_system_client
    _risk_system_client = None
    _profit_system_client = None
