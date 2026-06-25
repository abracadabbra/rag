"""
Business tool selection and execution.

The service keeps tool routing independent from the LLM provider so the same
flow works with OpenAI-compatible providers that may not support native tools.
"""

import json
import logging
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from api.config import settings
from api.services.business_clients import (
    get_profit_system_client,
    get_risk_system_client,
    validate_business_response,
)
from api.services.business_contracts import (
    BUSINESS_TOOL_RESULT_ALLOWLIST,
    BUSINESS_TOOL_CONTRACT_VERSIONS,
    BusinessContractError,
    PROFIT_TOOL_NAME,
    PROFIT_REQUIRED_FIELDS,
    PROFIT_EXAMPLE_RESPONSE,
    RISK_TOOL_NAME,
    RISK_REQUIRED_FIELDS,
    RISK_EXAMPLE_RESPONSE,
    derive_profit_chain,
    endpoint_path,
    normalize_order_id,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolDefinition:
    """Executable business tool metadata."""

    name: str
    label: str
    scene_type: str
    description: str
    executor: Callable[[str], Dict[str, Any]]


@dataclass(frozen=True)
class ToolSelection:
    """Selected tool plus routing evidence."""

    tool: ToolDefinition
    selection_source: str
    reason: str
    confidence: float
    order_id: Optional[str]
    missing_fields: List[str]


@dataclass(frozen=True)
class ToolIntent:
    """Structured business-tool intent used before execution."""

    tool_name: Optional[str]
    label: Optional[str]
    scene_type: str
    selection_source: str
    order_id: Optional[str]
    confidence: float
    reason: str
    missing_fields: List[str]
    needs_clarification: bool
    clarification_options: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "label": self.label,
            "scene_type": self.scene_type,
            "selection_source": self.selection_source,
            "order_id": self.order_id,
            "confidence": self.confidence,
            "reason": self.reason,
            "missing_fields": self.missing_fields,
            "needs_clarification": self.needs_clarification,
            "clarification_options": self.clarification_options,
        }


class BusinessToolService:
    """Select and execute scene-specific business tools."""

    ORDER_ID_PATTERN = re.compile(
        r"\b(?:ORD|ORDER|RISK|TRIP|GMV)[-_]?[A-Za-z0-9]{3,}\b|订单\s*([A-Za-z0-9_-]{4,})",
        re.IGNORECASE,
    )
    SENSITIVE_ARGUMENT_KEYS = {
        "order_id",
        "user_id",
        "driver_id",
        "phone",
        "mobile",
        "id_card",
        "card_no",
        "payment_account",
    }
    RESULT_ALLOWLIST = BUSINESS_TOOL_RESULT_ALLOWLIST
    MAX_AUDIT_EVENTS = 100
    AUDIT_EVENT_FIELDS = {
        "audit_id",
        "timestamp",
        "tool_name",
        "label",
        "scene_type",
        "contract_version",
        "data_source",
        "endpoint_path",
        "status",
        "duration_ms",
        "arguments",
        "selection_source",
        "selection_reason",
        "confidence",
        "result_keys",
        "error_type",
        "diagnostic_code",
        "missing_fields",
        "invalid_fields",
    }

    def __init__(self):
        self.risk_client = get_risk_system_client()
        self.profit_client = get_profit_system_client()
        self.llm_client = None
        self.llm_model = self._get_llm_model()
        self._llm_intent_telemetry = self._empty_llm_intent_telemetry()
        self._audit_events: List[Dict[str, Any]] = []
        self._tools = {
            "get_risk_event_detail": ToolDefinition(
                name="get_risk_event_detail",
                label="风控事件详情",
                scene_type="risk_rule",
                description="按订单查询风控命中规则、评分、拦截原因和建议动作",
                executor=self.risk_client.get_event_detail,
            ),
            "get_profit_chain_detail": ToolDefinition(
                name="get_profit_chain_detail",
                label="订单毛利链路",
                scene_type="profit",
                description="按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
                executor=self.profit_client.get_chain_detail,
            ),
        }

    def maybe_execute(self, *, query: str, scene_type: str) -> List[Dict[str, Any]]:
        """Return tool calls when the query asks for order-level business data."""
        if not settings.enable_business_tools:
            logger.info("Business tools disabled by configuration")
            return []

        selection = self._select_tool(query=query, scene_type=scene_type)
        if selection is None:
            return []
        return self._execute_selection(selection)

    def execute_intent(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a previously inspected complete business-tool intent."""
        if not settings.enable_business_tools:
            logger.info("Business tools disabled by configuration")
            return []

        selection = self._selection_from_intent(intent)
        if selection is None:
            return []

        return self._execute_selection(selection)

    def _selection_from_intent(self, intent: Dict[str, Any]) -> Optional[ToolSelection]:
        if not isinstance(intent, dict):
            return None

        if intent.get("needs_clarification") or intent.get("missing_fields"):
            logger.info(
                "Tool intent not executed because clarification is still required - tool: %s, fields: %s",
                intent.get("tool_name"),
                intent.get("missing_fields"),
            )
            return None

        tool_name = intent.get("tool_name")
        tool = self._tools.get(str(tool_name))
        if tool is None:
            return None

        scene_type = intent.get("scene_type")
        if scene_type and scene_type != tool.scene_type:
            logger.info(
                "Tool intent rejected by scene/tool contract - scene=%s tool=%s",
                scene_type,
                tool_name,
            )
            return None

        try:
            order_id = normalize_order_id(intent.get("order_id"))
        except ValueError:
            logger.info("Tool intent not executed because order_id is missing or invalid")
            return None

        confidence = intent.get("confidence")
        if not isinstance(confidence, (int, float)):
            confidence = 0.0

        reason = self._safe_intent_reason(intent.get("reason"))

        return ToolSelection(
            tool=tool,
            selection_source=self._safe_intent_selection_source(intent.get("selection_source")),
            reason=reason.strip(),
            confidence=float(confidence),
            order_id=order_id,
            missing_fields=[],
        )

    def _safe_intent_reason(self, reason: Any) -> str:
        if not isinstance(reason, str):
            return "复用已确认的业务工具意图执行。"
        reason = reason.strip()
        safe_prefixes = (
            "识别到订单号 ",
            "识别到订单级问题信号",
            "LLM 识别到订单级问题信号",
            "复用已确认的业务工具意图执行。",
        )
        if any(reason.startswith(prefix) for prefix in safe_prefixes):
            return reason
        return "复用已确认的业务工具意图执行。"

    def _safe_intent_selection_source(self, value: Any) -> str:
        if value in {"rules", "llm", "none"}:
            return str(value)
        if isinstance(value, str) and value.lower() == "llm":
            return "llm"
        return "rules"

    def _format_selection_source(self, value: Any) -> str:
        labels = {
            "rules": "规则命中",
            "llm": "LLM 兜底",
            "probe": "手动探测",
            "none": "未触发",
        }
        return labels.get(value, str(value or "-"))

    def _execute_selection(self, selection: ToolSelection) -> List[Dict[str, Any]]:
        tool = selection.tool

        if selection.missing_fields:
            logger.info(
                "Tool selected but missing clarification fields - scene: %s, fields: %s",
                tool.scene_type,
                selection.missing_fields,
            )
            return []

        order_id = selection.order_id
        if not order_id:
            logger.info("Tool selected but no order id found - scene: %s", tool.scene_type)
            return []

        arguments = {"order_id": order_id}
        start_time = time.perf_counter()
        try:
            raw_result = tool.executor(order_id)
            result = self._filter_result_for_display(tool.name, raw_result)
            result = self._enrich_result_for_display(tool.name, result)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            audit_id = self._log_tool_audit(
                tool=tool,
                arguments=arguments,
                status="success",
                duration_ms=duration_ms,
                result=result,
                selection_source=selection.selection_source,
                selection_reason=selection.reason,
                confidence=selection.confidence,
            )
            endpoint_path = self._get_endpoint_path(tool.name, order_id)
            data_source = self._get_data_source(tool.name)
            integration_mode = self._get_integration_mode(tool.name)
            contract_metadata = self._get_contract_metadata(tool.name)
            return [
                {
                    "name": tool.name,
                    "label": tool.label,
                    "scene_type": tool.scene_type,
                    "description": tool.description,
                    "audit_id": audit_id,
                    "endpoint_path": endpoint_path,
                    "data_source": data_source,
                    "integration_mode": integration_mode,
                    **contract_metadata,
                    "arguments": arguments,
                    "status": "success",
                    "selection_source": selection.selection_source,
                    "result": result,
                    "summary": self._summarize_result(tool.name, result),
                    "duration_ms": duration_ms,
                    "selection_reason": selection.reason,
                    "confidence": selection.confidence,
                }
            ]
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            audit_id = self._log_tool_audit(
                tool=tool,
                arguments=arguments,
                status="error",
                duration_ms=duration_ms,
                error=exc,
                selection_source=selection.selection_source,
                selection_reason=selection.reason,
                confidence=selection.confidence,
            )
            logger.warning("Tool execution failed - tool: %s, error_type: %s", tool.name, type(exc).__name__)
            endpoint_path = self._get_endpoint_path(tool.name, order_id)
            data_source = self._get_data_source(tool.name)
            integration_mode = self._get_integration_mode(tool.name)
            contract_metadata = self._get_contract_metadata(tool.name)
            return [
                {
                    "name": tool.name,
                    "label": tool.label,
                    "scene_type": tool.scene_type,
                    "description": tool.description,
                    "audit_id": audit_id,
                    "endpoint_path": endpoint_path,
                    "data_source": data_source,
                    "integration_mode": integration_mode,
                    **contract_metadata,
                    "arguments": arguments,
                    "status": "error",
                    "selection_source": selection.selection_source,
                    "result": {},
                    "summary": f"{tool.label}调用失败，请稍后重试或联系系统管理员。",
                    "error_type": type(exc).__name__,
                    "duration_ms": duration_ms,
                    "selection_reason": selection.reason,
                    "confidence": selection.confidence,
                    **self._safe_probe_diagnostic(exc),
                }
            ]

    def format_tool_context(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Format tool results for prompt injection."""
        if not tool_calls:
            return ""

        sections = []
        for index, call in enumerate(tool_calls, 1):
            result = call.get("result") or {}
            lines = [
                f"【工具 {index}】{call.get('label') or call.get('name')}",
                f"状态: {call.get('status')}",
                f"数据源: {call.get('data_source')}",
                f"接口路径: {call.get('endpoint_path')}",
                f"接口模板: {call.get('endpoint_template') or '-'}",
                f"合同版本: {call.get('contract_version') or '-'}",
                f"审计ID: {call.get('audit_id')}",
                f"错误类型: {call.get('error_type') or '-'}",
                f"参数: {call.get('arguments')}",
                f"选择来源: {self._format_selection_source(call.get('selection_source'))}",
                f"选择依据: {call.get('selection_reason')}",
                f"选择置信度: {call.get('confidence')}",
                f"摘要: {call.get('summary')}",
            ]
            if call.get("diagnostic_code") or call.get("missing_fields") or call.get("invalid_fields"):
                lines.extend(
                    [
                        f"合同诊断码: {call.get('diagnostic_code') or '-'}",
                        f"缺失字段: {call.get('missing_fields') or []}",
                        f"异常字段: {call.get('invalid_fields') or []}",
                    ]
                )
            chain_source = self._format_chain_source(result.get("chain_source"))
            if chain_source:
                lines.append(f"链路来源: {chain_source}")
            profit_formula_audit = self._format_profit_formula_audit(call)
            if profit_formula_audit:
                lines.append(profit_formula_audit)
            risk_evidence_summary = self._format_risk_evidence_summary(call)
            if risk_evidence_summary:
                lines.append(risk_evidence_summary)
            lines.extend([
                "结构化数据:",
                self._format_dict(result),
            ])
            sections.append("\n".join(lines))
        return "\n\n---\n\n".join(sections)

    def _format_risk_evidence_summary(self, call: Dict[str, Any]) -> str:
        """Return a concise, allowlisted risk evidence summary for prompt grounding."""
        if call.get("name") != "get_risk_event_detail" or call.get("status") != "success":
            return ""

        result = call.get("result") or {}
        decision = result.get("decision")
        risk_score = result.get("risk_score")
        hit_rules = result.get("hit_rules") or []
        if not decision or not isinstance(risk_score, (int, float)) or not isinstance(hit_rules, list):
            return ""

        risk_level = result.get("risk_level") or "-"
        recommended_action = result.get("recommended_action") or "-"
        rule_summaries = []
        for rule in hit_rules:
            if not isinstance(rule, dict):
                continue
            rule_name = rule.get("rule_name")
            rule_id = rule.get("rule_id")
            if rule_name and rule_id:
                rule_summaries.append(f"{rule_name}({rule_id})")
            elif rule_name:
                rule_summaries.append(str(rule_name))
            elif rule_id:
                rule_summaries.append(str(rule_id))

        rule_summary = "、".join(rule_summaries) if rule_summaries else "无"
        return (
            "风控证据摘要: "
            f"决策={decision}，风险分={risk_score}，风险等级={risk_level}，"
            f"命中规则数={len(hit_rules)}，建议动作={recommended_action}，"
            f"命中规则={rule_summary}"
        )

    def _format_profit_formula_audit(self, call: Dict[str, Any]) -> str:
        """Return a concise net-profit formula check for prompt grounding."""
        if call.get("name") != "get_profit_chain_detail" or call.get("status") != "success":
            return ""

        result = call.get("result") or {}
        commission = result.get("platform_commission")
        subsidy = result.get("subsidy")
        coupon = result.get("coupon")
        net_profit = result.get("platform_net_profit")
        required_values = (commission, subsidy, coupon, net_profit)
        if not all(isinstance(value, (int, float)) for value in required_values):
            return ""

        channel_fee = result.get("channel_fee")
        safe_channel_fee = channel_fee if isinstance(channel_fee, (int, float)) else 0
        calculated = round(float(commission) - float(subsidy) - float(coupon) - float(safe_channel_fee), 2)
        reported = round(float(net_profit), 2)
        delta = round(calculated - reported, 2)
        status = "一致" if abs(delta) < 0.01 else "不一致"
        channel_note = "" if isinstance(channel_fee, (int, float)) else "；未返回渠道费，按 0 核对"
        return (
            "毛利公式核对: "
            "平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利；"
            f"计算值 {calculated:.2f} 元，接口净毛利 {reported:.2f} 元，差异 {delta:+.2f} 元，"
            f"状态: {status}{channel_note}"
        )

    def probe(self, *, tool_name: str, order_id: str) -> Dict[str, Any]:
        """Probe one configured business tool with an explicit order id."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Unknown business tool: {tool_name}")

        order_id = (order_id or "").strip()
        if not order_id:
            raise ValueError("order_id is required")

        arguments = {"order_id": order_id}
        endpoint_path = self._get_endpoint_path(tool.name, order_id)
        data_source = self._get_data_source(tool.name)
        integration_mode = self._get_integration_mode(tool.name)
        contract_metadata = self._get_contract_metadata(tool.name)
        start_time = time.perf_counter()
        try:
            raw_result = tool.executor(order_id)
            result = self._filter_result_for_display(tool.name, raw_result)
            result = self._enrich_result_for_display(tool.name, result)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            audit_id = self._log_tool_audit(
                tool=tool,
                arguments=arguments,
                status="success",
                duration_ms=duration_ms,
                result=result,
                selection_source="probe",
            )
            return {
                "name": tool.name,
                "label": tool.label,
                "scene_type": tool.scene_type,
                "description": tool.description,
                "audit_id": audit_id,
                "endpoint_path": endpoint_path,
                "data_source": data_source,
                "integration_mode": integration_mode,
                **contract_metadata,
                "arguments": arguments,
                "status": "success",
                "selection_source": "probe",
                "duration_ms": duration_ms,
                "summary": self._summarize_result(tool.name, result),
                "result": result,
            }
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            audit_id = self._log_tool_audit(
                tool=tool,
                arguments=arguments,
                status="error",
                duration_ms=duration_ms,
                error=exc,
                selection_source="probe",
            )
            logger.warning(
                "Business tool probe failed - tool: %s, error_type: %s",
                tool.name,
                type(exc).__name__,
            )
            return {
                "name": tool.name,
                "label": tool.label,
                "scene_type": tool.scene_type,
                "description": tool.description,
                "audit_id": audit_id,
                "endpoint_path": endpoint_path,
                "data_source": data_source,
                "integration_mode": integration_mode,
                **contract_metadata,
                "arguments": arguments,
                "status": "error",
                "selection_source": "probe",
                "duration_ms": duration_ms,
                "summary": f"{tool.label}探测失败，请检查接口地址、鉴权和返回字段合同。",
                "result": {},
                "error_type": type(exc).__name__,
                **self._safe_probe_diagnostic(exc),
            }

    def validate_response_contract(self, *, tool_name: str, payload: Any) -> Dict[str, Any]:
        """Validate a response sample without calling external business systems."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Unknown business tool: {tool_name}")

        contract_version = BUSINESS_TOOL_CONTRACT_VERSIONS.get(tool.name)
        start_time = time.perf_counter()
        try:
            raw_result = validate_business_response(tool_name, payload)
            result = self._filter_result_for_display(tool.name, raw_result)
            result = self._enrich_result_for_display(tool.name, result)
            ignored_result_keys = self._ignored_result_keys(
                tool_name=tool.name,
                raw_result=raw_result,
                exposed_result=result,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "name": tool.name,
                "label": tool.label,
                "scene_type": tool.scene_type,
                "contract_version": contract_version,
                "status": "valid",
                "duration_ms": duration_ms,
                "summary": f"{tool.label}响应样例符合合同。",
                "exposed_result_keys": sorted(result.keys()),
                "ignored_result_keys": ignored_result_keys,
                "diagnostic_code": None,
                "missing_fields": [],
                "invalid_fields": [],
            }
        except BusinessContractError as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "name": tool.name,
                "label": tool.label,
                "scene_type": tool.scene_type,
                "contract_version": contract_version,
                "status": "invalid",
                "duration_ms": duration_ms,
                "summary": f"{tool.label}响应样例不符合合同。",
                "exposed_result_keys": [],
                "ignored_result_keys": [],
                "error_type": type(exc).__name__,
                **self._safe_probe_diagnostic(exc),
            }

    def validate_response_contract_batch(
        self,
        *,
        tool_name: str,
        payloads: List[Any],
    ) -> Dict[str, Any]:
        """Validate multiple response samples without returning payload values."""
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Unknown business tool: {tool_name}")

        if not payloads:
            raise ValueError("payloads must contain at least one sample")

        start_time = time.perf_counter()
        items = []
        diagnostic_counts: Dict[str, int] = {}
        missing_fields = set()
        invalid_fields = set()
        ignored_result_keys = set()
        for index, payload in enumerate(payloads):
            item = self.validate_response_contract(tool_name=tool_name, payload=payload)
            safe_item = {
                "index": index,
                "status": item.get("status"),
                "duration_ms": item.get("duration_ms") or 0,
                "summary": item.get("summary") or "",
                "exposed_result_keys": item.get("exposed_result_keys") or [],
                "ignored_result_keys": item.get("ignored_result_keys") or [],
                "error_type": item.get("error_type"),
                "diagnostic": item.get("diagnostic"),
                "diagnostic_code": item.get("diagnostic_code"),
                "missing_fields": item.get("missing_fields") or [],
                "invalid_fields": item.get("invalid_fields") or [],
            }
            diagnostic_code = safe_item.get("diagnostic_code")
            if diagnostic_code:
                diagnostic_counts[diagnostic_code] = diagnostic_counts.get(diagnostic_code, 0) + 1
            missing_fields.update(str(field) for field in safe_item["missing_fields"])
            invalid_fields.update(str(field) for field in safe_item["invalid_fields"])
            ignored_result_keys.update(str(field) for field in safe_item["ignored_result_keys"])
            items.append(safe_item)

        valid_count = sum(1 for item in items if item.get("status") == "valid")
        invalid_count = len(items) - valid_count
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        status = "valid" if invalid_count == 0 else "invalid"
        return {
            "name": tool.name,
            "label": tool.label,
            "scene_type": tool.scene_type,
            "contract_version": BUSINESS_TOOL_CONTRACT_VERSIONS.get(tool.name),
            "status": status,
            "duration_ms": duration_ms,
            "summary": (
                f"{tool.label}批量响应样例校验完成："
                f"{valid_count} 条通过，{invalid_count} 条不通过。"
            ),
            "validation_summary": {
                "total": len(items),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "diagnostic_codes": dict(sorted(diagnostic_counts.items())),
                "missing_fields": sorted(missing_fields),
                "invalid_fields": sorted(invalid_fields),
                "ignored_result_keys": sorted(ignored_result_keys),
            },
            "items": items,
        }

    def inspect_intent(self, *, query: str, scene_type: str) -> Dict[str, Any]:
        """Inspect whether a query wants a business tool without executing it."""
        selection = self._select_tool(query=query, scene_type=scene_type)
        if selection is None:
            return ToolIntent(
                tool_name=None,
                label=None,
                scene_type=scene_type,
                selection_source="none",
                order_id=None,
                confidence=0.0,
                reason="未识别到需要调用业务系统接口的订单级问题。",
                missing_fields=[],
                needs_clarification=False,
                clarification_options=[],
            ).to_dict()

        missing_fields = selection.missing_fields
        needs_clarification = bool(missing_fields)
        return ToolIntent(
            tool_name=selection.tool.name,
            label=selection.tool.label,
            scene_type=selection.tool.scene_type,
            selection_source=selection.selection_source,
            order_id=selection.order_id,
            confidence=selection.confidence,
            reason=selection.reason,
            missing_fields=missing_fields,
            needs_clarification=needs_clarification,
            clarification_options=self._build_clarification_options(selection),
        ).to_dict()

    def list_audit_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent safe audit events, newest first."""
        safe_limit = max(1, min(int(limit or 20), self.MAX_AUDIT_EVENTS))
        events = self._audit_events
        if settings.enable_business_tool_audit_file:
            events = self._merge_audit_events(
                self._load_persisted_audit_events(limit=safe_limit),
                self._audit_events,
            )
        return list(reversed(events[-safe_limit:]))

    def runtime_status(self) -> Dict[str, Any]:
        """Return a safe runtime readiness snapshot without exposing secrets."""
        full_access_configured = bool((settings.business_tool_access_token or "").strip())
        read_configured = bool((settings.business_tool_read_token or "").strip())
        execute_configured = bool((settings.business_tool_execute_token or "").strip())
        access_enabled = bool(settings.enable_business_tool_access_control)
        read_scope_ready = (
            (not access_enabled)
            or full_access_configured
            or read_configured
            or execute_configured
        )
        execute_scope_ready = (
            (not access_enabled)
            or full_access_configured
            or execute_configured
        )
        missing_scopes = []
        if not read_scope_ready:
            missing_scopes.append("read")
        if not execute_scope_ready:
            missing_scopes.append("execute")
        access_ready = (
            not access_enabled
            or full_access_configured
            or (read_configured and execute_configured)
        )
        persisted_events = self._load_persisted_audit_events(limit=self.MAX_AUDIT_EVENTS)
        audit_file = Path(settings.business_tool_audit_file) if settings.business_tool_audit_file else None
        audit_file_exists = bool(audit_file and audit_file.exists())
        audit_file_readable = bool(audit_file and audit_file.is_file())
        tools = [
            self._tool_runtime_status(
                tool=self._tools["get_risk_event_detail"],
                base_url=getattr(self.risk_client, "base_url", ""),
                api_key=getattr(self.risk_client, "api_key", ""),
            ),
            self._tool_runtime_status(
                tool=self._tools["get_profit_chain_detail"],
                base_url=getattr(self.profit_client, "base_url", ""),
                api_key=getattr(self.profit_client, "api_key", ""),
            ),
        ]
        readiness = "ready" if settings.enable_business_tools and access_ready else "disabled"
        if settings.enable_business_tools and not access_ready:
            readiness = "misconfigured"
        status_reason = self._build_runtime_status_reason(
            enabled=bool(settings.enable_business_tools),
            access_enabled=access_enabled,
            missing_scopes=missing_scopes,
        )

        return {
            "status": readiness,
            "status_reason": status_reason,
            "business_tools": {
                "enabled": bool(settings.enable_business_tools),
                "timeout_seconds": settings.business_tool_timeout,
                "tool_count": len(tools),
            },
            "access_control": {
                "enabled": access_enabled,
                "ready": access_ready,
                "full_access_configured": full_access_configured,
                "read_configured": read_configured,
                "execute_configured": execute_configured,
                "read_scope_ready": read_scope_ready,
                "execute_scope_ready": execute_scope_ready,
                "missing_scopes": missing_scopes,
            },
            "audit": {
                "memory_event_count": len(self._audit_events),
                "memory_event_limit": self.MAX_AUDIT_EVENTS,
                "file_enabled": bool(settings.enable_business_tool_audit_file),
                "file_configured": bool((settings.business_tool_audit_file or "").strip()),
                "file_name": Path(settings.business_tool_audit_file).name
                if settings.business_tool_audit_file
                else None,
                "file_exists": audit_file_exists,
                "file_readable": audit_file_readable,
                "persisted_event_count": len(persisted_events),
            },
            "llm_intent": {
                "enabled": bool(settings.enable_business_tool_llm_intent),
                "min_confidence": settings.business_tool_llm_intent_min_confidence,
                "model_configured": bool(self.llm_model),
                **self._llm_intent_runtime_status(),
            },
            "tools": tools,
        }

    def readiness(self, limit: int = 20) -> Dict[str, Any]:
        """Return safe business-tool integration readiness gates."""
        safe_limit = max(1, min(int(limit or 20), self.MAX_AUDIT_EVENTS))
        runtime_status = self.runtime_status()
        audit_events = self.list_audit_events(limit=safe_limit)
        corpus_status = self._corpus_scene_status()
        items = self._build_readiness_items(
            runtime_status=runtime_status,
            audit_events=audit_events,
            corpus_status=corpus_status,
        )
        blockers = [item for item in items if item["status"] == "blocked"]
        warnings = [item for item in items if item["status"] == "warning"]
        passed = [item for item in items if item["status"] == "passed"]
        overall_status = "blocked" if blockers else ("ready_with_warnings" if warnings else "ready")

        return {
            "overall_status": overall_status,
            "status_reason": self._build_readiness_status_reason(
                blockers=blockers,
                warnings=warnings,
            ),
            "passed": [item["id"] for item in passed],
            "warnings": [item["id"] for item in warnings],
            "blockers": [item["id"] for item in blockers],
            "items": items,
            "audit_event_count": len(audit_events),
            "audit_event_limit": safe_limit,
            "corpus_status": corpus_status,
        }

    def _build_readiness_items(
        self,
        *,
        runtime_status: Dict[str, Any],
        audit_events: List[Dict[str, Any]],
        corpus_status: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build safe readiness gates from runtime state and audit metadata."""
        business_tools = runtime_status.get("business_tools") or {}
        access_control = runtime_status.get("access_control") or {}
        audit_status = runtime_status.get("audit") or {}
        llm_intent = runtime_status.get("llm_intent") or {}
        tools = runtime_status.get("tools") or []
        http_tools = [tool for tool in tools if tool.get("data_source") == "http"]
        externally_configured_http_tools = [
            tool for tool in http_tools if tool.get("integration_mode") == "external_http"
        ]
        fake_http_tools = [
            tool for tool in http_tools if tool.get("integration_mode") == "fake_http"
        ]
        external_http_ready = bool(tools) and len(externally_configured_http_tools) == len(tools)
        contract_checks = self._contract_readiness_checks()
        intent_checks = self._intent_precheck_readiness_checks()
        traceable_events = [
            event
            for event in audit_events
            if str(event.get("audit_id") or "").startswith("bt-")
            and event.get("selection_reason")
            and isinstance(event.get("confidence"), (int, float))
        ]
        corpus_scenes = corpus_status.get("scenes") or {}
        required_corpus_scenes = ["risk_rule", "profit"]
        missing_corpus_scenes = [
            scene_type
            for scene_type in required_corpus_scenes
            if not (corpus_scenes.get(scene_type) or {}).get("available")
        ]
        corpus_ingestion_guidance = self._build_corpus_ingestion_guidance(
            missing_corpus_scenes
        )
        corpus_errors = [
            {
                "scene_type": scene_type,
                "error_type": scene_status.get("error_type"),
            }
            for scene_type, scene_status in corpus_scenes.items()
            if scene_status.get("error_type")
        ]
        persisted_audit_ready = (
            audit_status.get("file_enabled")
            and audit_status.get("file_configured")
            and audit_status.get("file_readable")
            and int(audit_status.get("persisted_event_count") or 0) > 0
        )
        persistent_audit_evidence = {
            "file_enabled": bool(audit_status.get("file_enabled")),
            "file_configured": bool(audit_status.get("file_configured")),
            "file_name": audit_status.get("file_name"),
            "file_exists": bool(audit_status.get("file_exists")),
            "file_readable": bool(audit_status.get("file_readable")),
            "persisted_event_count": int(audit_status.get("persisted_event_count") or 0),
            "memory_event_count": audit_status.get("memory_event_count") or 0,
            "memory_event_limit": audit_status.get("memory_event_limit") or 0,
        }

        return [
            self._readiness_item(
                check_id="business_tools_enabled",
                status="passed" if business_tools.get("enabled") else "blocked",
                summary="业务工具开关已启用"
                if business_tools.get("enabled")
                else "业务工具开关未启用",
                evidence={
                    "enabled": bool(business_tools.get("enabled")),
                    "tool_count": business_tools.get("tool_count") or 0,
                    "timeout_seconds": business_tools.get("timeout_seconds"),
                },
            ),
            self._readiness_item(
                check_id="contract_examples_valid",
                status="passed"
                if all(item["example_valid"] and item["required_fields_exposed"] for item in contract_checks)
                else "blocked",
                summary="风控/毛利合同样例和展示字段通过自检"
                if all(item["example_valid"] and item["required_fields_exposed"] for item in contract_checks)
                else "存在合同样例校验失败或必需字段未允许展示",
                evidence={"tools": contract_checks},
            ),
            self._readiness_item(
                check_id="tool_contracts_available",
                status="passed"
                if tools and all(tool.get("contract_available") for tool in tools)
                else "blocked",
                summary="风控/毛利工具合同可用"
                if tools and all(tool.get("contract_available") for tool in tools)
                else "存在不可用的业务工具合同",
                evidence={
                    "tools": [
                        {
                            "tool_name": tool.get("tool_name"),
                            "contract_available": bool(tool.get("contract_available")),
                        }
                        for tool in tools
                    ]
                },
            ),
            self._readiness_item(
                check_id="intent_precheck",
                status="passed"
                if all(item["selected_expected_tool"] and not item["needs_clarification"] for item in intent_checks)
                else "warning",
                summary="风控/毛利标准问题均可在不执行接口的情况下完成工具意图预检"
                if all(item["selected_expected_tool"] and not item["needs_clarification"] for item in intent_checks)
                else "存在标准问题未能稳定预检到目标工具或仍需澄清",
                evidence={"checks": intent_checks},
            ),
            self._readiness_item(
                check_id="corpus_scene_coverage",
                status="passed" if not missing_corpus_scenes and not corpus_errors else "warning",
                summary="风控/毛利业务语料均已入库"
                if not missing_corpus_scenes and not corpus_errors
                else "业务工具可用，但存在未确认入库的风控/毛利语料",
                evidence={
                    "collection_name": corpus_status.get("collection_name"),
                    "required_scenes": required_corpus_scenes,
                    "missing_scenes": missing_corpus_scenes,
                    "ingestion_guidance": corpus_ingestion_guidance,
                    "scene_status": corpus_scenes,
                    "errors": corpus_errors,
                },
            ),
            self._readiness_item(
                check_id="access_control_enabled",
                status="passed"
                if access_control.get("enabled") and access_control.get("ready")
                else ("blocked" if access_control.get("enabled") else "warning"),
                summary="访问控制已启用且 scope 就绪"
                if access_control.get("enabled") and access_control.get("ready")
                else (
                    "访问控制已启用但 scope token 未就绪"
                    if access_control.get("enabled")
                    else "接真实订单数据前建议启用访问控制 token"
                ),
                evidence={
                    "enabled": bool(access_control.get("enabled")),
                    "ready": bool(access_control.get("ready")),
                    "missing_scopes": access_control.get("missing_scopes") or [],
                },
            ),
            self._readiness_item(
                check_id="real_http_configured",
                status="passed" if tools and len(http_tools) == len(tools) else "warning",
                summary=(
                    "风控和毛利均已切到 HTTP 模式，且当前指向外部真实接口"
                    if external_http_ready
                    else (
                        "风控和毛利均已切到 HTTP 模式，当前使用进程内 fake-http 验证链路"
                        if tools and len(fake_http_tools) == len(tools)
                        else "当前仍有工具处于 mock 模式；接真实系统前需配置 Base URL"
                    )
                ),
                evidence={
                    "tool_sources": [
                        {
                            "tool_name": tool.get("tool_name"),
                            "data_source": tool.get("data_source"),
                            "integration_mode": tool.get("integration_mode"),
                            "base_url_configured": bool(tool.get("base_url_configured")),
                            "api_key_configured": bool(tool.get("api_key_configured")),
                        }
                        for tool in tools
                    ]
                },
            ),
            self._readiness_item(
                check_id="external_http_configured",
                status="passed" if external_http_ready else "warning",
                summary=(
                    "风控和毛利均已指向外部真实 HTTP 系统"
                    if external_http_ready
                    else "上线前仍需用外部真实 HTTP 系统配置补跑严格门禁"
                ),
                evidence={
                    "external_http_ready": external_http_ready,
                    "integration_modes": sorted(
                        {
                            tool.get("integration_mode")
                            for tool in tools
                            if tool.get("integration_mode")
                        }
                    ),
                    "tool_sources": [
                        {
                            "tool_name": tool.get("tool_name"),
                            "data_source": tool.get("data_source"),
                            "integration_mode": tool.get("integration_mode"),
                            "base_url_configured": bool(tool.get("base_url_configured")),
                        }
                        for tool in tools
                    ],
                },
            ),
            self._readiness_item(
                check_id="persistent_audit_enabled",
                status="passed" if persisted_audit_ready else "warning",
                summary=(
                    "JSONL 文件审计已启用，且已存在可回读的持久化审计事件"
                    if persisted_audit_ready
                    else (
                        "JSONL 文件审计已启用，但还没有可回读的持久化审计事件"
                        if audit_status.get("file_enabled")
                        else "当前仅保留内存审计；接真实系统前建议启用文件审计"
                    )
                ),
                evidence=persistent_audit_evidence,
            ),
            self._readiness_item(
                check_id="audit_traceability",
                status="passed" if traceable_events else "warning",
                summary="最近自然语言工具调用审计包含选择依据、置信度和 Audit ID"
                if traceable_events
                else "暂无可核验的自然语言工具调用审计；完成一次订单查询后再检查",
                evidence={
                    "recent_event_count": len(audit_events),
                    "traceable_event_count": len(traceable_events),
                    "latest_traceable_audit_id": traceable_events[0].get("audit_id")
                    if traceable_events
                    else None,
                    "has_selection_reason": bool(traceable_events),
                    "has_confidence": bool(traceable_events),
                },
            ),
            self._readiness_item(
                check_id="llm_intent_fallback",
                status="passed" if llm_intent.get("last_status") == "success" else "warning",
                summary=self._build_llm_intent_readiness_summary(llm_intent),
                evidence={
                    "enabled": bool(llm_intent.get("enabled")),
                    "model_configured": bool(llm_intent.get("model_configured")),
                    "min_confidence": llm_intent.get("min_confidence"),
                    "attempt_count": int(llm_intent.get("attempt_count") or 0),
                    "success_count": int(llm_intent.get("success_count") or 0),
                    "error_count": int(llm_intent.get("error_count") or 0),
                    "last_status": llm_intent.get("last_status"),
                    "last_resolution": llm_intent.get("last_resolution"),
                    "last_error_type": llm_intent.get("last_error_type"),
                    "last_attempt_at": llm_intent.get("last_attempt_at"),
                    "last_success_at": llm_intent.get("last_success_at"),
                    "last_error_at": llm_intent.get("last_error_at"),
                },
            ),
        ]

    def _build_corpus_ingestion_guidance(self, missing_scenes: List[str]) -> List[Dict[str, str]]:
        """Return safe, operator-facing import commands for missing business scenes."""
        scene_guidance = {
            "risk_rule": {
                "scene_type": "risk_rule",
                "label": "风控规则语料",
                "source_path": "data/risk_rules",
                "command": "python -m ingestion.ingest --source data/risk_rules --scene risk_rule",
            },
            "profit": {
                "scene_type": "profit",
                "label": "毛利链路语料",
                "source_path": "data/profit",
                "command": "python -m ingestion.ingest --source data/profit --scene profit",
            },
        }
        return [
            scene_guidance[scene_type]
            for scene_type in missing_scenes
            if scene_type in scene_guidance
        ]

    def _corpus_scene_status(self) -> Dict[str, Any]:
        """Return safe RAG corpus readiness metadata for business scenes."""
        scene_types = ["risk_rule", "profit"]
        collection_name = settings.milvus_collection
        try:
            from ingestion.milvus_client import get_milvus_client

            client = get_milvus_client(
                host=settings.milvus_host,
                port=settings.milvus_port,
                collection_name=collection_name,
                dimension=384,
                timeout=settings.business_tool_corpus_check_timeout,
            )
            scenes = {}
            for scene_type in scene_types:
                try:
                    rows = client.query(
                        collection_name=collection_name,
                        filter=f'scene_type == "{scene_type}"',
                        output_fields=["id", "scene_type"],
                        limit=1,
                    )
                    scenes[scene_type] = self._build_corpus_scene_status(
                        available=bool(rows),
                        sample_count=len(rows or []),
                    )
                except Exception as exc:
                    logger.warning(
                        "Corpus scene readiness check failed - scene_type=%s, error_type=%s",
                        scene_type,
                        type(exc).__name__,
                    )
                    scenes[scene_type] = self._build_corpus_scene_status(
                        available=False,
                        sample_count=0,
                        error_type=type(exc).__name__,
                    )

            return {
                "collection_name": collection_name,
                "scenes": scenes,
            }
        except Exception as exc:
            logger.warning(
                "Corpus readiness check failed - error_type=%s",
                type(exc).__name__,
            )
            return {
                "collection_name": collection_name,
                "scenes": {
                    scene_type: self._build_corpus_scene_status(
                        available=False,
                        sample_count=0,
                        error_type=type(exc).__name__,
                    )
                    for scene_type in scene_types
                },
            }

    def _build_corpus_scene_status(
        self,
        *,
        available: bool,
        sample_count: int,
        error_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build safe corpus scene metadata for readiness evidence."""
        return {
            "available": bool(available),
            "sample_count": int(sample_count or 0),
            "error_type": error_type,
        }

    def _contract_readiness_checks(self) -> List[Dict[str, Any]]:
        """Validate built-in example responses and display allowlist coverage."""
        contracts = [
            (RISK_TOOL_NAME, RISK_EXAMPLE_RESPONSE, RISK_REQUIRED_FIELDS),
            (PROFIT_TOOL_NAME, PROFIT_EXAMPLE_RESPONSE, PROFIT_REQUIRED_FIELDS),
        ]
        checks = []
        for tool_name, example_response, required_fields in contracts:
            try:
                validate_business_response(tool_name, example_response)
                example_valid = True
                diagnostic_code = None
                missing_fields: List[str] = []
                invalid_fields: List[str] = []
            except BusinessContractError as exc:
                example_valid = False
                diagnostic_code = exc.diagnostic_code
                missing_fields = exc.missing_fields
                invalid_fields = exc.invalid_fields

            allowlist = BUSINESS_TOOL_RESULT_ALLOWLIST.get(tool_name) or {}
            missing_exposed_fields = [
                field
                for field in required_fields
                if field not in allowlist
            ]
            checks.append(
                {
                    "tool_name": tool_name,
                    "contract_version": BUSINESS_TOOL_CONTRACT_VERSIONS.get(tool_name),
                    "example_valid": example_valid,
                    "diagnostic_code": diagnostic_code,
                    "missing_fields": missing_fields,
                    "invalid_fields": invalid_fields,
                    "required_fields_exposed": not missing_exposed_fields,
                    "missing_exposed_fields": missing_exposed_fields,
                }
            )
        return checks

    def _intent_precheck_readiness_checks(self) -> List[Dict[str, Any]]:
        """Return safe readiness evidence for deterministic intent prechecks."""
        scenarios = [
            {
                "scene_type": "risk_rule",
                "query": "订单 ORD12345 为什么被风控拦截？",
                "expected_tool_name": RISK_TOOL_NAME,
            },
            {
                "scene_type": "profit",
                "query": "查询订单 ORD88888 的抽成和司机收入",
                "expected_tool_name": PROFIT_TOOL_NAME,
            },
        ]
        checks = []
        for scenario in scenarios:
            intent = self.inspect_intent(
                query=scenario["query"],
                scene_type=scenario["scene_type"],
            )
            tool_name = intent.get("tool_name")
            checks.append(
                {
                    "scene_type": scenario["scene_type"],
                    "expected_tool_name": scenario["expected_tool_name"],
                    "tool_name": tool_name,
                    "selection_source": intent.get("selection_source"),
                    "confidence": intent.get("confidence"),
                    "missing_fields": intent.get("missing_fields") or [],
                    "needs_clarification": bool(intent.get("needs_clarification")),
                    "selected_expected_tool": tool_name == scenario["expected_tool_name"],
                }
            )
        return checks

    def _readiness_item(
        self,
        *,
        check_id: str,
        status: str,
        summary: str,
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        if status not in {"passed", "warning", "blocked"}:
            raise ValueError(f"Unsupported readiness status: {status}")
        return {
            "id": check_id,
            "status": status,
            "summary": summary,
            "evidence": evidence,
        }

    def _build_readiness_status_reason(
        self,
        *,
        blockers: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
    ) -> str:
        if blockers:
            return f"{len(blockers)} 个必需接入检查未通过。"
        if warnings:
            return f"{len(warnings)} 个接入建议项待处理。"
        return "业务工具接入检查已全部通过。"

    def _build_runtime_status_reason(
        self,
        *,
        enabled: bool,
        access_enabled: bool,
        missing_scopes: List[str],
    ) -> str:
        """Return a safe operator-facing readiness reason."""
        if not enabled:
            return "业务工具未启用。"
        if not access_enabled:
            return "业务工具已启用，访问控制未启用。"
        if missing_scopes:
            return f"访问控制缺少 {', '.join(missing_scopes)} scope token。"
        return "业务工具已启用，访问控制 scope 已就绪。"

    def _safe_probe_diagnostic(self, exc: Exception) -> Dict[str, Any]:
        """Expose only contract-shape probe errors that contain no payload values."""
        if isinstance(exc, BusinessContractError):
            return {
                "diagnostic": str(exc),
                "diagnostic_code": exc.diagnostic_code,
                "missing_fields": exc.missing_fields,
                "invalid_fields": exc.invalid_fields,
            }

        if not isinstance(exc, ValueError):
            return {}

        message = str(exc)
        safe_markers = (
            "API response contract violation",
            "Business API returned non-object JSON",
        )
        if any(marker in message for marker in safe_markers):
            return {"diagnostic": message}
        return {}

    def _select_tool(self, *, query: str, scene_type: str) -> Optional[ToolSelection]:
        selection = self._select_tool_by_rules(query=query, scene_type=scene_type)
        if selection is not None:
            return selection
        return self._select_tool_by_llm(query=query, scene_type=scene_type)

    def _select_tool_by_rules(
        self,
        *,
        query: str,
        scene_type: str,
    ) -> Optional[ToolSelection]:
        lowered = query.lower()
        order_id = self._extract_order_id(query)
        has_order_signal = bool(order_id) or any(
            keyword in query
            for keyword in ("订单", "链路", "拦截", "命中", "司机", "收入", "结算")
        )
        if not has_order_signal:
            return None

        if scene_type == "risk_rule" and any(
            keyword in query for keyword in ("风控", "拦截", "命中", "风险", "规则")
        ):
            return ToolSelection(
                tool=self._tools["get_risk_event_detail"],
                selection_source="rules",
                reason=self._build_selection_reason(
                    scene_type=scene_type,
                    order_id=order_id,
                    matched_signal="风控/拦截/命中/风险/规则",
                ),
                confidence=0.92 if order_id else 0.68,
                order_id=order_id,
                missing_fields=[] if order_id else ["order_id"],
            )
        if scene_type == "profit" and any(
            keyword in query for keyword in ("毛利", "抽成", "司机", "收入", "结算", "链路")
        ):
            return ToolSelection(
                tool=self._tools["get_profit_chain_detail"],
                selection_source="rules",
                reason=self._build_selection_reason(
                    scene_type=scene_type,
                    order_id=order_id,
                    matched_signal="毛利/抽成/司机/收入/结算/链路",
                ),
                confidence=0.92 if order_id else 0.68,
                order_id=order_id,
                missing_fields=[] if order_id else ["order_id"],
            )
        if scene_type == "risk_rule" and "risk" in lowered:
            return ToolSelection(
                tool=self._tools["get_risk_event_detail"],
                selection_source="rules",
                reason=self._build_selection_reason(
                    scene_type=scene_type,
                    order_id=order_id,
                    matched_signal="risk",
                ),
                confidence=0.86 if order_id else 0.62,
                order_id=order_id,
                missing_fields=[] if order_id else ["order_id"],
            )
        if scene_type == "profit" and any(word in lowered for word in ("profit", "income", "commission")):
            return ToolSelection(
                tool=self._tools["get_profit_chain_detail"],
                selection_source="rules",
                reason=self._build_selection_reason(
                    scene_type=scene_type,
                    order_id=order_id,
                    matched_signal="profit/income/commission",
                ),
                confidence=0.86 if order_id else 0.62,
                order_id=order_id,
                missing_fields=[] if order_id else ["order_id"],
            )
        return None

    def _select_tool_by_llm(self, *, query: str, scene_type: str) -> Optional[ToolSelection]:
        if not settings.enable_business_tool_llm_intent:
            return None
        if not self._should_use_llm_intent(query=query, scene_type=scene_type):
            return None

        intent = self._inspect_llm_intent(query=query, scene_type=scene_type)
        if not intent:
            return None

        tool_name = intent.get("tool_name")
        if tool_name is None:
            self._record_llm_intent_success(resolution="no_tool")
            return None

        confidence = intent.get("confidence")
        if not isinstance(confidence, (int, float)):
            self._record_llm_intent_error("invalid_confidence")
            return None
        confidence = float(confidence)

        tool = self._tools.get(str(tool_name))
        if not tool or tool.scene_type != scene_type:
            logger.info(
                "LLM tool intent rejected by scene/tool contract - scene=%s tool=%s",
                scene_type,
                tool_name,
            )
            self._record_llm_intent_error("contract_rejected")
            return None

        order_id = self._safe_intent_order_id(intent.get("order_id"))
        if not order_id:
            order_id = self._extract_order_id(query)

        missing_fields = intent.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = []
        if not order_id and "order_id" not in missing_fields:
            missing_fields = [*missing_fields, "order_id"]
        if order_id:
            missing_fields = [field for field in missing_fields if field != "order_id"]
        if confidence < settings.business_tool_llm_intent_min_confidence:
            logger.info(
                "LLM tool intent below threshold - scene=%s tool=%s confidence=%s",
                scene_type,
                tool_name,
                confidence,
            )
            if order_id and "tool_intent_confirmation" not in missing_fields:
                missing_fields = [*missing_fields, "tool_intent_confirmation"]

        resolution = "clarification_required" if missing_fields else "tool_selected"
        self._record_llm_intent_success(resolution=resolution)
        return ToolSelection(
            tool=tool,
            selection_source="llm",
            reason=self._build_llm_selection_reason(
                scene_type=scene_type,
                order_id=order_id,
            ),
            confidence=confidence,
            order_id=order_id,
            missing_fields=missing_fields,
        )

    def _build_clarification_options(self, selection: ToolSelection) -> List[str]:
        missing_fields = set(selection.missing_fields)
        if "order_id" in missing_fields:
            return [f"请补充订单号后再查询，例如：订单 ORD88888 的{selection.tool.label}。"]
        if "tool_intent_confirmation" in missing_fields:
            if selection.order_id:
                return [f"确认查询订单 {selection.order_id} 的{selection.tool.label}。"]
            return [f"请确认是否需要查询{selection.tool.label}，并补充订单号。"]
        return []

    def _safe_intent_order_id(self, order_id: Any) -> Optional[str]:
        """Accept only safe LLM-supplied path identifiers."""
        if order_id is None:
            return None
        try:
            return normalize_order_id(order_id)
        except ValueError:
            logger.info("LLM tool intent ignored invalid order_id")
            return None

    def _should_use_llm_intent(self, *, query: str, scene_type: str) -> bool:
        if scene_type not in {"risk_rule", "profit"}:
            return False
        order_id = self._extract_order_id(query)
        if order_id:
            return True
        return any(
            keyword in query
            for keyword in ("订单", "链路", "拦截", "命中", "司机", "收入", "结算", "费用", "钱")
        )

    def _inspect_llm_intent(self, *, query: str, scene_type: str) -> Optional[Dict[str, Any]]:
        self._record_llm_intent_attempt()
        try:
            client = self._get_llm_client()
            response = client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是业务系统工具路由器，只能输出 JSON。"
                            "不要解释，不要输出 Markdown。"
                        ),
                    },
                    {"role": "user", "content": self._build_llm_intent_prompt(query, scene_type)},
                ],
                temperature=0,
                max_tokens=300,
                timeout=10.0,
            )
            content = response.choices[0].message.content.strip()
            intent = self._parse_llm_intent_json(content)
            if intent is None:
                self._record_llm_intent_error("invalid_json")
                return None
            return intent
        except Exception as exc:
            self._record_llm_intent_error(type(exc).__name__)
            logger.warning(
                "LLM tool intent fallback failed - scene=%s error_type=%s",
                scene_type,
                type(exc).__name__,
            )
            return None

    def _empty_llm_intent_telemetry(self) -> Dict[str, Any]:
        return {
            "attempt_count": 0,
            "success_count": 0,
            "error_count": 0,
            "last_status": None,
            "last_resolution": None,
            "last_error_type": None,
            "last_attempt_at": None,
            "last_success_at": None,
            "last_error_at": None,
        }

    def _llm_intent_runtime_status(self) -> Dict[str, Any]:
        return dict(self._llm_intent_telemetry)

    def _record_llm_intent_attempt(self) -> None:
        self._llm_intent_telemetry["attempt_count"] += 1
        self._llm_intent_telemetry["last_attempt_at"] = self._utc_now_iso()

    def _record_llm_intent_success(self, *, resolution: str) -> None:
        now = self._utc_now_iso()
        self._llm_intent_telemetry["success_count"] += 1
        self._llm_intent_telemetry["last_status"] = "success"
        self._llm_intent_telemetry["last_resolution"] = resolution
        self._llm_intent_telemetry["last_error_type"] = None
        self._llm_intent_telemetry["last_success_at"] = now

    def _record_llm_intent_error(self, error_type: str) -> None:
        now = self._utc_now_iso()
        self._llm_intent_telemetry["error_count"] += 1
        self._llm_intent_telemetry["last_status"] = "error"
        self._llm_intent_telemetry["last_resolution"] = None
        self._llm_intent_telemetry["last_error_type"] = error_type
        self._llm_intent_telemetry["last_error_at"] = now

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_llm_intent_readiness_summary(self, llm_intent: Dict[str, Any]) -> str:
        if not llm_intent.get("enabled"):
            return "模糊问题当前主要依赖规则识别；可按需启用 LLM 兜底"
        if not llm_intent.get("model_configured"):
            return "LLM 兜底已启用，但模型尚未配置完整"
        if llm_intent.get("last_status") == "success":
            resolution = llm_intent.get("last_resolution")
            if resolution == "clarification_required":
                return "LLM 兜底已启用，最近一次真实调用成功返回澄清意图"
            if resolution == "no_tool":
                return "LLM 兜底已启用，最近一次真实调用成功返回无需调接口"
            return "LLM 兜底已启用，且已存在成功的结构化意图记录"
        if llm_intent.get("attempt_count"):
            error_type = llm_intent.get("last_error_type") or "unknown_error"
            return f"LLM 兜底已启用，但最近一次真实调用失败: {error_type}"
        return "LLM 兜底已启用，但还没有成功的真实调用记录"

    def _get_llm_client(self):
        if self.llm_client is None:
            from api.services.clarification import get_llm_client

            self.llm_client = get_llm_client()
        return self.llm_client

    def _get_llm_model(self) -> str:
        if settings.llm_provider == "minimax":
            return settings.minimax_model
        if settings.llm_provider == "openai":
            return settings.openai_model
        if settings.llm_provider == "local":
            return settings.local_llm_model
        return settings.openai_model

    def _build_llm_intent_prompt(self, query: str, scene_type: str) -> str:
        tools = [
            {
                "tool_name": tool.name,
                "scene_type": tool.scene_type,
                "description": tool.description,
                "required_fields": ["order_id"],
            }
            for tool in self._tools.values()
            if tool.scene_type == scene_type
        ]
        return (
            "判断用户问题是否需要查询业务系统接口。\n"
            "只允许选择下面 tools 中的工具；不需要工具时 tool_name 返回 null。\n"
            "如果是规则、政策、概念解释，不要选择工具。\n"
            "如果需要订单级数据但没有订单号，missing_fields 包含 order_id。\n"
            "输出 JSON 字段固定为: tool_name, order_id, confidence, reason, missing_fields。\n\n"
            f"当前场景: {scene_type}\n"
            f"tools: {json.dumps(tools, ensure_ascii=False)}\n"
            f"用户问题: {query}\n"
        )

    def _parse_llm_intent_json(self, content: str) -> Optional[Dict[str, Any]]:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return data if isinstance(data, dict) else None

    def _build_llm_selection_reason(
        self,
        *,
        scene_type: str,
        order_id: Optional[str],
    ) -> str:
        if order_id:
            order_part = f"识别到订单号 {order_id}"
        else:
            order_part = "LLM 识别到订单级问题信号"
        return (
            f"{order_part}，当前场景为 {scene_type}，"
            "LLM 意图判断: 已通过结构化字段选择工具。"
        )

    def _extract_order_id(self, query: str) -> Optional[str]:
        match = self.ORDER_ID_PATTERN.search(query)
        if not match:
            return None
        return match.group(1) or match.group(0).replace(" ", "")

    def _build_selection_reason(
        self,
        *,
        scene_type: str,
        order_id: Optional[str],
        matched_signal: str,
    ) -> str:
        order_part = f"识别到订单号 {order_id}" if order_id else "识别到订单级问题信号"
        return f"{order_part}，当前场景为 {scene_type}，命中关键词: {matched_signal}。"

    def _summarize_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        if tool_name == "get_risk_event_detail":
            rules = result.get("hit_rules") or []
            rule_names = "、".join(rule.get("rule_name", "") for rule in rules if rule.get("rule_name"))
            return (
                f"订单 {result.get('order_id')} 风控决策为 {result.get('decision')}，"
                f"风险分 {result.get('risk_score')}，命中规则: {rule_names or '无'}。"
            )
        if tool_name == "get_profit_chain_detail":
            return (
                f"订单 {result.get('order_id')} 总金额 {result.get('gross_amount')} 元，"
                f"平台抽成 {result.get('platform_commission')} 元，"
                f"司机收入 {result.get('driver_income')} 元，"
                f"平台净毛利 {result.get('platform_net_profit')} 元。"
            )
        return str(result)

    def _log_tool_audit(
        self,
        *,
        tool: ToolDefinition,
        arguments: Dict[str, Any],
        status: str,
        duration_ms: int,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        selection_source: Optional[str] = None,
        selection_reason: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> str:
        """Log a safe audit record without leaking full business payloads."""
        audit_id = f"bt-{uuid.uuid4().hex[:16]}"
        safe_arguments = self._sanitize_arguments(arguments)
        safe_selection_reason = self._sanitize_selection_reason(
            selection_reason,
            arguments=arguments,
        )
        result_keys = sorted((result or {}).keys())
        error_type = type(error).__name__ if error else None
        endpoint_template = self._get_endpoint_path(tool.name, "{order_id}")
        contract_version = BUSINESS_TOOL_CONTRACT_VERSIONS.get(tool.name)
        diagnostic = self._safe_probe_diagnostic(error) if error else {}
        audit_event = {
            "audit_id": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool.name,
            "label": tool.label,
            "scene_type": tool.scene_type,
            "contract_version": contract_version,
            "data_source": self._get_data_source(tool.name),
            "endpoint_path": endpoint_template,
            "status": status,
            "duration_ms": duration_ms,
            "arguments": safe_arguments,
            "selection_source": selection_source if isinstance(selection_source, str) else None,
            "selection_reason": safe_selection_reason,
            "confidence": confidence if isinstance(confidence, (int, float)) else None,
            "result_keys": result_keys,
            "error_type": error_type,
        }
        for key in ("diagnostic_code", "missing_fields", "invalid_fields"):
            if key in diagnostic:
                audit_event[key] = diagnostic[key]
        self._record_audit_event(audit_event)

        logger.info(
            "Business tool audit - audit_id=%s tool=%s scene=%s source=%s endpoint=%s status=%s duration_ms=%s "
            "arguments=%s selection_source=%s selection_reason=%s confidence=%s result_keys=%s error_type=%s diagnostic_code=%s",
            audit_id,
            tool.name,
            tool.scene_type,
            self._get_data_source(tool.name),
            endpoint_template,
            status,
            duration_ms,
            safe_arguments,
            selection_source,
            safe_selection_reason,
            confidence,
            result_keys,
            error_type,
            diagnostic.get("diagnostic_code"),
        )
        return audit_id

    def _record_audit_event(self, event: Dict[str, Any]) -> None:
        self._audit_events.append(event)
        if len(self._audit_events) > self.MAX_AUDIT_EVENTS:
            self._audit_events = self._audit_events[-self.MAX_AUDIT_EVENTS:]
        self._persist_audit_event(event)

    def _merge_audit_events(
        self,
        persisted_events: List[Dict[str, Any]],
        memory_events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge persisted and in-memory events, preserving oldest-to-newest order."""
        merged_by_id: Dict[str, Dict[str, Any]] = {}
        anonymous_index = 0
        for event in [*persisted_events, *memory_events]:
            audit_id = str(event.get("audit_id") or "")
            if not audit_id:
                anonymous_index += 1
                audit_id = f"anonymous-{anonymous_index}"
            merged_by_id[audit_id] = event
        return list(merged_by_id.values())

    def _load_persisted_audit_events(self, *, limit: int) -> List[Dict[str, Any]]:
        """Read recent safe audit events from the optional JSONL audit file."""
        audit_file = Path(settings.business_tool_audit_file)
        if not audit_file.is_file():
            return []

        recent_lines = deque(maxlen=max(1, min(limit, self.MAX_AUDIT_EVENTS)))
        try:
            with audit_file.open("r", encoding="utf-8") as file:
                for line in file:
                    if line.strip():
                        recent_lines.append(line)
        except OSError as exc:
            logger.warning(
                "Business tool audit file read failed - error_type=%s",
                type(exc).__name__,
            )
            return []

        events: List[Dict[str, Any]] = []
        for line in recent_lines:
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Business tool audit file skipped invalid event - error_type=%s",
                    type(exc).__name__,
                )
                continue
            event = self._normalize_audit_event(data)
            if event:
                events.append(event)
        return events

    def _normalize_audit_event(self, data: Any) -> Dict[str, Any]:
        """Keep only the safe audit event schema when reading JSONL events."""
        if not isinstance(data, dict):
            return {}

        event = {
            key: data[key]
            for key in self.AUDIT_EVENT_FIELDS
            if key in data
        }
        arguments = event.get("arguments")
        raw_arguments = arguments if isinstance(arguments, dict) else {}
        event["arguments"] = self._sanitize_arguments(raw_arguments)

        result_keys = event.get("result_keys")
        event["result_keys"] = [str(key) for key in result_keys] if isinstance(result_keys, list) else []

        selection_reason = event.get("selection_reason")
        event["selection_reason"] = self._sanitize_selection_reason(
            str(selection_reason) if selection_reason else None,
            arguments=raw_arguments,
        )

        selection_source = event.get("selection_source")
        event["selection_source"] = (
            str(selection_source)
            if selection_source in {"rules", "llm", "none", "probe"}
            else None
        )

        confidence = event.get("confidence")
        event["confidence"] = confidence if isinstance(confidence, (int, float)) else None

        error_type = event.get("error_type")
        event["error_type"] = str(error_type) if error_type else None

        contract_version = event.get("contract_version")
        event["contract_version"] = str(contract_version) if contract_version else None

        diagnostic_code = event.get("diagnostic_code")
        if diagnostic_code:
            event["diagnostic_code"] = str(diagnostic_code)
        for key in ("missing_fields", "invalid_fields"):
            fields = event.get(key)
            if isinstance(fields, list):
                event[key] = [str(field) for field in fields]
            elif key in event:
                event[key] = []
        return event

    def _persist_audit_event(self, event: Dict[str, Any]) -> None:
        if not settings.enable_business_tool_audit_file:
            return

        try:
            audit_file = Path(settings.business_tool_audit_file)
            audit_file.parent.mkdir(parents=True, exist_ok=True)
            with audit_file.open("a", encoding="utf-8") as file:
                file.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.warning(
                "Business tool audit file write failed - error_type=%s",
                type(exc).__name__,
            )

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: self._mask_value(value) if key in self.SENSITIVE_ARGUMENT_KEYS else value
            for key, value in arguments.items()
        }

    def _sanitize_selection_reason(
        self,
        reason: Optional[str],
        *,
        arguments: Dict[str, Any],
    ) -> Optional[str]:
        if not reason:
            return None

        safe_reason = str(reason)
        for key, value in arguments.items():
            if key not in self.SENSITIVE_ARGUMENT_KEYS:
                continue
            raw_value = "" if value is None else str(value)
            if raw_value:
                safe_reason = safe_reason.replace(raw_value, self._mask_value(raw_value))
        return safe_reason

    def _get_endpoint_path(self, tool_name: str, order_id: str) -> Optional[str]:
        try:
            return endpoint_path(tool_name, order_id=order_id)
        except KeyError:
            return None

    def _get_contract_metadata(self, tool_name: str) -> Dict[str, Optional[str]]:
        return {
            "endpoint_template": self._get_endpoint_path(tool_name, "{order_id}"),
            "contract_version": BUSINESS_TOOL_CONTRACT_VERSIONS.get(tool_name),
        }

    def _get_tool_base_url(self, tool_name: str) -> str:
        if tool_name == "get_risk_event_detail":
            return str(getattr(self.risk_client, "base_url", "") or "").strip()
        if tool_name == "get_profit_chain_detail":
            return str(getattr(self.profit_client, "base_url", "") or "").strip()
        return ""

    def _get_data_source(self, tool_name: str) -> str:
        return "http" if self._get_tool_base_url(tool_name) else "mock"

    def _get_integration_mode(self, tool_name: str) -> str:
        base_url = self._get_tool_base_url(tool_name)
        if not base_url:
            return "mock"
        if base_url.startswith("http://127.0.0.1:8000/api/v1/business-tools/fake-http"):
            return "fake_http"
        return "external_http"

    def _tool_runtime_status(
        self,
        *,
        tool: ToolDefinition,
        base_url: str,
        api_key: str,
    ) -> Dict[str, Any]:
        return {
            "tool_name": tool.name,
            "label": tool.label,
            "scene_type": tool.scene_type,
            "data_source": self._get_data_source(tool.name),
            "integration_mode": self._get_integration_mode(tool.name),
            "endpoint_template": self._get_endpoint_path(tool.name, "{order_id}"),
            "base_url_configured": bool((base_url or "").strip()),
            "api_key_configured": bool((api_key or "").strip()),
            "contract_available": tool.name in self.RESULT_ALLOWLIST,
        }

    def _filter_result_for_display(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        allowlist = self.RESULT_ALLOWLIST.get(tool_name)
        if not allowlist:
            return {}
        return {
            key: self._filter_allowed_value(result[key], nested_allowlist)
            for key, nested_allowlist in allowlist.items()
            if key in result
        }

    def _ignored_result_keys(
        self,
        *,
        tool_name: str,
        raw_result: Dict[str, Any],
        exposed_result: Dict[str, Any],
    ) -> List[str]:
        """Return top-level response keys that are valid but not exposed."""
        allowlist = self.RESULT_ALLOWLIST.get(tool_name) or {}
        allowed_keys = set(allowlist.keys())
        exposed_keys = set(exposed_result.keys())
        return sorted(
            key
            for key in raw_result
            if key not in allowed_keys and key not in exposed_keys
        )

    def _enrich_result_for_display(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Add derived display fields that are covered by the shared allowlist."""
        if tool_name != PROFIT_TOOL_NAME:
            return result

        if result.get("chain"):
            return {**result, "chain_source": "api"}

        chain = derive_profit_chain(result)
        if not chain:
            return result

        return {**result, "chain": chain, "chain_source": "derived"}

    def _filter_allowed_value(self, value: Any, nested_allowlist: Optional[Dict[str, Any]]) -> Any:
        if nested_allowlist is None:
            return value
        if isinstance(value, list):
            return [
                self._filter_allowed_value(item, nested_allowlist)
                for item in value
                if isinstance(item, dict)
            ]
        if isinstance(value, dict):
            return {
                key: self._filter_allowed_value(value[key], child_allowlist)
                for key, child_allowlist in nested_allowlist.items()
                if key in value
            }
        return value

    def _mask_value(self, value: Any) -> str:
        text = "" if value is None else str(value)
        if len(text) <= 4:
            return "****"
        return f"{text[:3]}***{text[-3:]}"

    def _format_chain_source(self, value: Any) -> str:
        if value == "api":
            return "接口原生链路"
        if value == "derived":
            return "自动派生链路"
        return ""

    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> str:
        lines = []
        prefix = " " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}- {key}:")
                lines.append(self._format_dict(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{prefix}- {key}:")
                for index, item in enumerate(value, start=1):
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  - item {index}:")
                        lines.append(self._format_dict(item, indent + 4))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}- {key}: {value}")
        return "\n".join(lines)


_tool_service: Optional[BusinessToolService] = None


def get_tool_service() -> BusinessToolService:
    """Get business tool service singleton."""
    global _tool_service
    if _tool_service is None:
        _tool_service = BusinessToolService()
    return _tool_service


def reset_tool_service() -> None:
    """Reset business tool service after business client settings change."""
    global _tool_service
    _tool_service = None
