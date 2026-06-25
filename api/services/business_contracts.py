"""
Shared business-system contracts.

This module is the single source of truth for the fields that real risk/profit
systems must return and the fields that may be exposed to prompts or frontend
views.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from api.services.prompt_templates import business_prompt_contract_snapshot


RequiredFieldSpec = Dict[str, Tuple[type, ...]]

NUMBER_TYPES = (int, float)

RISK_TOOL_NAME = "get_risk_event_detail"
PROFIT_TOOL_NAME = "get_profit_chain_detail"
PROFIT_CHAIN_TERMINAL_NODE = "平台净毛利"
ORDER_ID_REQUEST_FIELD = "order_id"
RISK_ENDPOINT_TEMPLATE = "/risk/events/{order_id}"
PROFIT_ENDPOINT_TEMPLATE = "/profit/orders/{order_id}/chain"
ORDER_ID_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")

BUSINESS_TOOL_ENDPOINT_TEMPLATES = {
    RISK_TOOL_NAME: RISK_ENDPOINT_TEMPLATE,
    PROFIT_TOOL_NAME: PROFIT_ENDPOINT_TEMPLATE,
}

BUSINESS_TOOL_REQUIRED_REQUEST_FIELDS = {
    RISK_TOOL_NAME: [ORDER_ID_REQUEST_FIELD],
    PROFIT_TOOL_NAME: [ORDER_ID_REQUEST_FIELD],
}

BUSINESS_TOOL_CONTRACT_VERSIONS = {
    RISK_TOOL_NAME: "v1",
    PROFIT_TOOL_NAME: "v1",
}

RISK_REQUIRED_FIELDS: RequiredFieldSpec = {
    "order_id": (str,),
    "decision": (str,),
    "risk_score": NUMBER_TYPES,
    "hit_rules": (list,),
    "recommended_action": (str,),
}

RISK_HIT_RULE_REQUIRED_FIELDS: RequiredFieldSpec = {
    "rule_id": (str,),
    "rule_name": (str,),
    "evidence": (str,),
}

PROFIT_REQUIRED_FIELDS: RequiredFieldSpec = {
    "order_id": (str,),
    "gross_amount": NUMBER_TYPES,
    "platform_commission": NUMBER_TYPES,
    "driver_income": NUMBER_TYPES,
    "subsidy": NUMBER_TYPES,
    "coupon": NUMBER_TYPES,
    "platform_net_profit": NUMBER_TYPES,
}

PROFIT_CHAIN_STEP_REQUIRED_FIELDS: RequiredFieldSpec = {
    "node": (str,),
    "amount": NUMBER_TYPES,
}

PROFIT_CHAIN_STEP_OPTIONAL_FIELDS: RequiredFieldSpec = {
    "source_field": (str,),
    "role": (str,),
    "tone": (str,),
    "note": (str,),
}

RISK_FIELD_CATALOG = [
    {
        "name": "order_id",
        "label": "订单号",
        "type": "string",
        "required": True,
        "description": "业务订单唯一标识，用于定位风控事件。",
    },
    {
        "name": "decision",
        "label": "系统决策",
        "type": "string",
        "required": True,
        "description": "风控系统给出的最终动作，例如 block、review、pass。",
    },
    {
        "name": "risk_score",
        "label": "风险分",
        "type": "number",
        "required": True,
        "description": "统一风险评分，便于排序、分级和阈值判断。",
    },
    {
        "name": "risk_level",
        "label": "风险等级",
        "type": "string",
        "required": False,
        "description": "高/中/低等离散等级，便于前端和运营快速识别。",
    },
    {
        "name": "hit_rules",
        "label": "命中规则",
        "type": "array<object>",
        "required": True,
        "description": "命中的规则列表，每条至少包含 rule_id、rule_name、evidence。",
    },
    {
        "name": "recommended_action",
        "label": "建议动作",
        "type": "string",
        "required": True,
        "description": "风控系统对人工或自动流程给出的下一步建议。",
    },
    {
        "name": "transaction_context",
        "label": "交易上下文",
        "type": "object",
        "required": False,
        "description": "订单金额、城市、支付渠道等辅助解释字段。",
    },
    {
        "name": "customer_context",
        "label": "用户上下文",
        "type": "object",
        "required": False,
        "description": "账号年龄、拒付次数等用户侧辅助信息。",
    },
]

PROFIT_FIELD_CATALOG = [
    {
        "name": "order_id",
        "label": "订单号",
        "type": "string",
        "required": True,
        "description": "业务订单唯一标识，用于定位毛利链路。",
    },
    {
        "name": "gross_amount",
        "label": "乘客支付",
        "type": "number",
        "required": True,
        "description": "乘客侧实付金额，作为 GMV 和毛利比例的基数。",
    },
    {
        "name": "platform_commission",
        "label": "平台抽成",
        "type": "number",
        "required": True,
        "description": "平台从订单中留存的抽成收入。",
    },
    {
        "name": "driver_income",
        "label": "司机收入",
        "type": "number",
        "required": True,
        "description": "履约完成后结算给司机的收入。",
    },
    {
        "name": "subsidy",
        "label": "平台补贴",
        "type": "number",
        "required": True,
        "description": "平台为促单或保供承担的补贴成本。",
    },
    {
        "name": "coupon",
        "label": "用户优惠",
        "type": "number",
        "required": True,
        "description": "订单使用的优惠券或直减成本。",
    },
    {
        "name": "channel_fee",
        "label": "渠道成本",
        "type": "number",
        "required": False,
        "description": "支付、流量或渠道分发产生的成本。",
    },
    {
        "name": "platform_net_profit",
        "label": "平台净毛利",
        "type": "number",
        "required": True,
        "description": "抽成扣除补贴、优惠、渠道费后的最终平台留存。",
    },
    {
        "name": "chain",
        "label": "钱流链路",
        "type": "array<object>",
        "required": False,
        "description": "可直接展示的钱流链路节点列表；未返回时可由顶层金额字段自动派生。",
    },
    {
        "name": "settlement_status",
        "label": "结算状态",
        "type": "string",
        "required": False,
        "description": "订单是否已结算，便于判断金额是否稳定。",
    },
    {
        "name": "commission_rate",
        "label": "抽成比例",
        "type": "string",
        "required": False,
        "description": "平台抽成占乘客支付的比例展示字段。",
    },
    {
        "name": "driver_income_detail",
        "label": "司机收入拆解",
        "type": "object",
        "required": False,
        "description": "司机收入的基础费、里程费、服务费抵扣等拆解信息。",
    },
]

PROFIT_DERIVED_CHAIN_STEPS = [
    {
        "node": "乘客支付",
        "field": "gross_amount",
        "sign": 1,
        "required": True,
        "role": "订单收入",
        "tone": "income",
        "note": "乘客实付基数",
    },
    {
        "node": "平台抽成",
        "field": "platform_commission",
        "sign": 1,
        "required": True,
        "role": "平台收入",
        "tone": "income",
        "note": "收入进入毛利公式",
    },
    {
        "node": "司机收入",
        "field": "driver_income",
        "sign": 1,
        "required": True,
        "role": "司机结算",
        "tone": "payout",
        "note": "履约侧结算",
    },
    {
        "node": "平台补贴",
        "field": "subsidy",
        "sign": -1,
        "required": True,
        "role": "平台成本",
        "tone": "cost",
        "note": "平台承担成本",
    },
    {
        "node": "用户优惠",
        "field": "coupon",
        "sign": -1,
        "required": True,
        "role": "营销成本",
        "tone": "cost",
        "note": "优惠消耗抽成",
    },
    {
        "node": "渠道成本",
        "field": "channel_fee",
        "sign": -1,
        "required": False,
        "role": "渠道成本",
        "tone": "cost",
        "note": "获客/支付渠道成本",
    },
    {
        "node": PROFIT_CHAIN_TERMINAL_NODE,
        "field": "platform_net_profit",
        "sign": 1,
        "required": True,
        "role": "经营结果",
        "tone": "net",
        "note": "最终留存",
    },
]

PROFIT_DISPLAY_METADATA_FIELDS = [
    {
        "name": "chain_source",
        "label": "链路来源",
        "type": "string",
        "required": False,
        "description": "后端展示元信息，用于标记当前链路为真实接口原生返回(api)还是按最小合同自动派生(derived)。",
    }
]

RISK_EXAMPLE_RESPONSE: Dict[str, Any] = {
    "order_id": "ORD12345",
    "decision": "block",
    "risk_score": 87,
    "risk_level": "high",
    "hit_rules": [
        {
            "rule_id": "RISK-velocity-001",
            "rule_name": "短时间多次高额交易",
            "evidence": "10 分钟内同卡 4 次交易，累计金额 1820 元",
        }
    ],
    "transaction_context": {
        "amount": 680.0,
        "city": "上海",
        "channel": "app",
        "payment_method": "credit_card",
    },
    "customer_context": {
        "user_level": "standard",
        "recent_chargebacks": 1,
        "account_age_days": 42,
    },
    "recommended_action": "建议保持拦截，并引导用户完成二次验证后重试。",
}

PROFIT_EXAMPLE_RESPONSE: Dict[str, Any] = {
    "order_id": "ORD88888",
    "settlement_status": "settled",
    "gross_amount": 128.6,
    "platform_commission": 19.29,
    "commission_rate": "15.0%",
    "driver_income": 92.35,
    "driver_income_detail": {
        "base_fare": 78.0,
        "distance_fee": 16.35,
        "service_fee_deduction": -2.0,
    },
    "subsidy": 8.0,
    "coupon": 6.0,
    "channel_fee": 2.96,
    "platform_net_profit": 2.33,
    "chain": [
        {
            "node": "乘客支付",
            "amount": 128.6,
            "source_field": "gross_amount",
            "role": "订单收入",
            "tone": "income",
            "note": "乘客实付基数",
        },
        {
            "node": "平台抽成",
            "amount": 19.29,
            "source_field": "platform_commission",
            "role": "平台收入",
            "tone": "income",
            "note": "收入进入毛利公式",
        },
        {
            "node": "司机收入",
            "amount": 92.35,
            "source_field": "driver_income",
            "role": "司机结算",
            "tone": "payout",
            "note": "履约侧结算",
        },
        {
            "node": "平台补贴",
            "amount": -8.0,
            "source_field": "subsidy",
            "role": "平台成本",
            "tone": "cost",
            "note": "平台承担成本",
        },
        {
            "node": "用户优惠",
            "amount": -6.0,
            "source_field": "coupon",
            "role": "营销成本",
            "tone": "cost",
            "note": "优惠消耗抽成",
        },
        {
            "node": "渠道成本",
            "amount": -2.96,
            "source_field": "channel_fee",
            "role": "渠道成本",
            "tone": "cost",
            "note": "获客/支付渠道成本",
        },
        {
            "node": PROFIT_CHAIN_TERMINAL_NODE,
            "amount": 2.33,
            "source_field": "platform_net_profit",
            "role": "经营结果",
            "tone": "net",
            "note": "最终留存",
        },
    ],
}


def fake_risk_payload(order_id: str) -> Dict[str, Any]:
    """Return a deterministic fake HTTP payload for risk smoke checks."""
    safe_order_id = normalize_order_id(order_id)
    return {
        "order_id": safe_order_id,
        "decision": "pass",
        "risk_score": 18,
        "risk_level": "low",
        "hit_rules": [
            {
                "rule_id": "RISK-low-001",
                "rule_name": "低风险订单",
                "evidence": "未命中高危规则",
            }
        ],
        "recommended_action": "建议放行。",
    }


def fake_profit_payload(order_id: str) -> Dict[str, Any]:
    """Return a deterministic fake HTTP payload for profit smoke checks."""
    safe_order_id = normalize_order_id(order_id)
    return {
        "order_id": safe_order_id,
        "gross_amount": 128.6,
        "platform_commission": 19.29,
        "driver_income": 92.35,
        "subsidy": 8.0,
        "coupon": 6.0,
        "channel_fee": 2.96,
        "platform_net_profit": 2.33,
        "chain": [
            {
                "node": "乘客支付",
                "amount": 128.6,
                "source_field": "gross_amount",
                "role": "订单收入",
                "tone": "income",
                "note": "乘客实付基数",
            },
            {
                "node": "平台抽成",
                "amount": 19.29,
                "source_field": "platform_commission",
                "role": "平台收入",
                "tone": "income",
                "note": "收入进入毛利公式",
            },
            {
                "node": "司机收入",
                "amount": 92.35,
                "source_field": "driver_income",
                "role": "司机结算",
                "tone": "payout",
                "note": "履约侧结算",
            },
            {
                "node": "平台补贴",
                "amount": -8.0,
                "source_field": "subsidy",
                "role": "平台成本",
                "tone": "cost",
                "note": "平台承担成本",
            },
            {
                "node": "用户优惠",
                "amount": -6.0,
                "source_field": "coupon",
                "role": "营销成本",
                "tone": "cost",
                "note": "优惠消耗抽成",
            },
            {
                "node": "渠道成本",
                "amount": -2.96,
                "source_field": "channel_fee",
                "role": "渠道成本",
                "tone": "cost",
                "note": "获客/支付渠道成本",
            },
            {
                "node": PROFIT_CHAIN_TERMINAL_NODE,
                "amount": 2.33,
                "source_field": "platform_net_profit",
                "role": "经营结果",
                "tone": "net",
                "note": "最终留存",
            },
        ],
    }

ORDER_ID_REQUEST_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": [ORDER_ID_REQUEST_FIELD],
    "additionalProperties": False,
    "properties": {
        ORDER_ID_REQUEST_FIELD: {
            "type": "string",
            "pattern": ORDER_ID_VALUE_PATTERN.pattern,
            "maxLength": 128,
            "description": "Business order identifier used as the path parameter.",
        }
    },
}

RISK_RESPONSE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": list(RISK_REQUIRED_FIELDS.keys()),
    "additionalProperties": True,
    "properties": {
        "order_id": {"type": "string"},
        "decision": {"type": "string"},
        "risk_score": {"type": "number"},
        "risk_level": {"type": "string"},
        "hit_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": list(RISK_HIT_RULE_REQUIRED_FIELDS.keys()),
                "additionalProperties": True,
                "properties": {
                    "rule_id": {"type": "string"},
                    "rule_name": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        },
        "transaction_context": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "amount": {"type": "number"},
                "city": {"type": "string"},
                "channel": {"type": "string"},
                "payment_method": {"type": "string"},
            },
        },
        "customer_context": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "user_level": {"type": "string"},
                "recent_chargebacks": {"type": "number"},
                "account_age_days": {"type": "number"},
            },
        },
        "recommended_action": {"type": "string"},
    },
}

PROFIT_RESPONSE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": list(PROFIT_REQUIRED_FIELDS.keys()),
    "additionalProperties": True,
    "properties": {
        "order_id": {"type": "string"},
        "settlement_status": {"type": "string"},
        "gross_amount": {"type": "number"},
        "platform_commission": {"type": "number"},
        "commission_rate": {"type": "string"},
        "driver_income": {"type": "number"},
        "driver_income_detail": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "base_fare": {"type": "number"},
                "distance_fee": {"type": "number"},
                "service_fee_deduction": {"type": "number"},
            },
        },
        "subsidy": {"type": "number"},
        "coupon": {"type": "number"},
        "channel_fee": {"type": "number"},
        "platform_net_profit": {"type": "number"},
        "chain": {
            "type": "array",
            "description": (
                "Recommended display chain. "
                f"The final node should be {PROFIT_CHAIN_TERMINAL_NODE}."
            ),
            "items": {
                "type": "object",
                "required": list(PROFIT_CHAIN_STEP_REQUIRED_FIELDS.keys()),
                "additionalProperties": True,
                "properties": {
                    "node": {"type": "string"},
                    "amount": {"type": "number"},
                    "source_field": {"type": "string"},
                    "role": {"type": "string"},
                    "tone": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
        },
    },
}

BUSINESS_TOOL_INTEGRATION_HANDOFF = {
    "recommended_sequence": [
        "export_contracts",
        "validate_captured_samples",
        "fake_http_acceptance",
        "external_http_strict_gate",
        "frontend_evidence_check",
    ],
    "commands": {
        "export_contracts": "make business-contracts",
        "validate_captured_samples": (
            "make business-validate-samples "
            "RISK_RESPONSE_FILE=/tmp/risk_response.json "
            "PROFIT_RESPONSE_FILE=/tmp/profit_response.json"
        ),
        "fake_http_acceptance": "make business-acceptance-pack BUSINESS_SMOKE_FAKE_HTTP=1",
        "external_http_strict_gate": "make business-smoke-strict",
    },
    "go_live_gates": [
        "real_http_configured",
        "external_http_configured",
        "access_control_enabled",
        "persistent_audit_enabled",
        "audit_traceability",
        "captured_sample_validation",
    ],
    "integration_modes": {
        "mock": "Base URL is empty; no external business system is called.",
        "fake_http": "In-process fake transport exercises the HTTP client path; not a production rollout.",
        "external_http": "Configured Base URL points to the real external risk/profit system.",
    },
    "safety_notes": [
        "Extra response fields are accepted but filtered by the display allowlist.",
        "Validation reports expose field names and diagnostic codes, not payload values.",
        "Fake HTTP acceptance cannot replace the external_http_configured go-live gate.",
    ],
}

BUSINESS_TOOL_RESULT_ALLOWLIST: Dict[str, Dict[str, Any]] = {
    RISK_TOOL_NAME: {
        "order_id": None,
        "decision": None,
        "risk_score": None,
        "risk_level": None,
        "hit_rules": {
            "rule_id": None,
            "rule_name": None,
            "evidence": None,
        },
        "transaction_context": {
            "amount": None,
            "city": None,
            "channel": None,
            "payment_method": None,
        },
        "customer_context": {
            "user_level": None,
            "recent_chargebacks": None,
            "account_age_days": None,
        },
        "recommended_action": None,
    },
    PROFIT_TOOL_NAME: {
        "order_id": None,
        "settlement_status": None,
        "gross_amount": None,
        "platform_commission": None,
        "commission_rate": None,
        "driver_income": None,
        "driver_income_detail": {
            "base_fare": None,
            "distance_fee": None,
            "service_fee_deduction": None,
        },
        "subsidy": None,
        "coupon": None,
        "channel_fee": None,
        "platform_net_profit": None,
        "chain_source": None,
        "chain": {
            "node": None,
            "amount": None,
            "source_field": None,
            "role": None,
            "tone": None,
            "note": None,
        },
    },
}


class BusinessContractError(ValueError):
    """Safe business API contract error with structured diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        diagnostic_code: str,
        missing_fields: Optional[List[str]] = None,
        invalid_fields: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.diagnostic_code = diagnostic_code
        self.missing_fields = missing_fields or []
        self.invalid_fields = invalid_fields or []


def type_label(expected_types: Tuple[type, ...]) -> str:
    """Return a stable type label for docs, tests, and contract errors."""
    if expected_types == NUMBER_TYPES:
        return "number"
    return " or ".join(type_item.__name__ for type_item in expected_types)


def contract_snapshot() -> Dict[str, Any]:
    """Return a serializable snapshot of the current business tool contracts."""
    return {
        "integration_handoff": BUSINESS_TOOL_INTEGRATION_HANDOFF,
        "prompt_contract": business_prompt_contract_snapshot(),
        "risk": {
            "tool_name": RISK_TOOL_NAME,
            "contract_version": BUSINESS_TOOL_CONTRACT_VERSIONS[RISK_TOOL_NAME],
            "endpoint_template": RISK_ENDPOINT_TEMPLATE,
            "required_request_fields": BUSINESS_TOOL_REQUIRED_REQUEST_FIELDS[RISK_TOOL_NAME],
            "request_json_schema": ORDER_ID_REQUEST_JSON_SCHEMA,
            "required_fields": _format_required_fields(RISK_REQUIRED_FIELDS),
            "hit_rule_required_fields": _format_required_fields(RISK_HIT_RULE_REQUIRED_FIELDS),
            "field_catalog": RISK_FIELD_CATALOG,
            "response_json_schema": RISK_RESPONSE_JSON_SCHEMA,
            "example_response": RISK_EXAMPLE_RESPONSE,
            "exposed_fields": sorted(BUSINESS_TOOL_RESULT_ALLOWLIST[RISK_TOOL_NAME].keys()),
        },
        "profit": {
            "tool_name": PROFIT_TOOL_NAME,
            "contract_version": BUSINESS_TOOL_CONTRACT_VERSIONS[PROFIT_TOOL_NAME],
            "endpoint_template": PROFIT_ENDPOINT_TEMPLATE,
            "required_request_fields": BUSINESS_TOOL_REQUIRED_REQUEST_FIELDS[PROFIT_TOOL_NAME],
            "request_json_schema": ORDER_ID_REQUEST_JSON_SCHEMA,
            "required_fields": _format_required_fields(PROFIT_REQUIRED_FIELDS),
            "chain_step_required_fields": _format_required_fields(
                PROFIT_CHAIN_STEP_REQUIRED_FIELDS
            ),
            "chain_step_optional_fields": _format_required_fields(
                PROFIT_CHAIN_STEP_OPTIONAL_FIELDS
            ),
            "chain_terminal_node": PROFIT_CHAIN_TERMINAL_NODE,
            "derived_chain_steps": PROFIT_DERIVED_CHAIN_STEPS,
            "display_metadata_fields": PROFIT_DISPLAY_METADATA_FIELDS,
            "field_catalog": PROFIT_FIELD_CATALOG,
            "response_json_schema": PROFIT_RESPONSE_JSON_SCHEMA,
            "example_response": PROFIT_EXAMPLE_RESPONSE,
            "exposed_fields": sorted(BUSINESS_TOOL_RESULT_ALLOWLIST[PROFIT_TOOL_NAME].keys()),
        },
    }


def _format_required_fields(required_fields: RequiredFieldSpec) -> Dict[str, str]:
    return {
        field: type_label(expected_types)
        for field, expected_types in required_fields.items()
    }


def endpoint_path(tool_name: str, *, order_id: str) -> str:
    """Render a business tool endpoint path from the shared endpoint template."""
    template = BUSINESS_TOOL_ENDPOINT_TEMPLATES[tool_name]
    safe_order_id = order_id if order_id == "{order_id}" else normalize_order_id(order_id)
    return template.format(order_id=safe_order_id)


def normalize_order_id(order_id: Any) -> str:
    """Return a safe order id for business-system path parameters."""
    value = str(order_id or "").strip()
    if not value:
        raise ValueError("order_id is required")
    if not ORDER_ID_VALUE_PATTERN.fullmatch(value):
        raise ValueError("order_id contains unsupported characters")
    return value


def derive_profit_chain(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Derive a display-safe profit chain from top-level amount fields."""
    missing_required_fields = [
        step["field"]
        for step in PROFIT_DERIVED_CHAIN_STEPS
        if step["required"] and not _is_number(data.get(step["field"]))
    ]
    if missing_required_fields:
        return []

    chain = []
    for step in PROFIT_DERIVED_CHAIN_STEPS:
        value = data.get(step["field"])
        if not _is_number(value):
            continue
        amount = float(value)
        if step["sign"] < 0:
            amount = -abs(amount)
        chain.append(
            {
                "node": step["node"],
                "amount": round(amount, 2),
                "source_field": step["field"],
                "role": step.get("role"),
                "tone": step.get("tone"),
                "note": step.get("note"),
            }
        )
    return chain


def _is_number(value: Any) -> bool:
    return isinstance(value, NUMBER_TYPES) and not isinstance(value, bool)
