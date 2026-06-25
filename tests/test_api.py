"""
API 健康检查测试
"""

import json
import sys
from types import ModuleType
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_business_tool_runtime():
    """Keep API tests independent from local .env business-tool runtime state."""
    from api.config import settings
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    business_fields = {
        "enable_business_tools": True,
        "business_tool_timeout": 5,
        "enable_business_tool_llm_intent": False,
        "business_tool_llm_intent_min_confidence": 0.75,
        "enable_business_tool_access_control": False,
        "business_tool_access_token": "",
        "business_tool_read_token": "",
        "business_tool_execute_token": "",
        "enable_business_tool_audit_file": False,
        "business_tool_audit_file": "logs/business_tool_audit.jsonl",
        "risk_api_base_url": "",
        "risk_api_key": "",
        "profit_api_base_url": "",
        "profit_api_key": "",
    }
    original_values = {
        field: getattr(settings, field) for field in business_fields
    }

    for field, value in business_fields.items():
        setattr(settings, field, value)
    reset_business_clients()
    reset_tool_service()

    try:
        yield
    finally:
        for field, value in original_values.items():
            setattr(settings, field, value)
        reset_business_clients()
        reset_tool_service()


def install_fake_conversation_agent(
    monkeypatch,
    *,
    result=None,
    stream_events=None,
    error=None,
    calls=None,
):
    """安装假的对话 Agent，隔离真实 RAG 依赖。"""

    class FakeAgent:
        def process(self, **kwargs):
            if calls is not None:
                calls.append(kwargs)
            if error is not None:
                raise error
            return result

        def process_stream(self, **kwargs):
            if calls is not None:
                calls.append(kwargs)
            if error is not None:
                raise error
            for event in stream_events or []:
                yield event

    fake_module = ModuleType("api.services.conversation_agent")
    fake_module.get_conversation_agent = lambda: FakeAgent()
    monkeypatch.setitem(sys.modules, "api.services.conversation_agent", fake_module)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check():
    """测试健康检查"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded"}
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data
    assert "api" in data["checks"]
    assert "milvus" in data["checks"]
    assert "redis" in data["checks"]


def test_ready_check():
    """测试轻量就绪检查，不依赖外部服务。"""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data
    assert "version" in data
    assert "environment" in data
    assert "checks" not in data


def test_business_tool_contracts_endpoint():
    """测试业务工具接口合同快照。"""
    response = client.get("/api/v1/business-tools/contracts")
    assert response.status_code == 200
    data = response.json()

    assert data["risk"]["tool_name"] == "get_risk_event_detail"
    assert data["integration_handoff"]["recommended_sequence"] == [
        "export_contracts",
        "validate_captured_samples",
        "fake_http_acceptance",
        "external_http_strict_gate",
        "frontend_evidence_check",
    ]
    assert data["integration_handoff"]["commands"]["external_http_strict_gate"] == (
        "make business-smoke-strict"
    )
    assert "external_http_configured" in data["integration_handoff"]["go_live_gates"]
    assert "fake_http" in data["integration_handoff"]["integration_modes"]
    assert data["prompt_contract"]["profit"]["name"] == "毛利抽成"
    assert data["prompt_contract"]["profit"]["answer_perspectives"]["finance"]["label"] == "财务口径"
    assert any(
        "Contract diagnostics" in rule for rule in data["prompt_contract"]["risk_rule"]["safety_contract"]
    )
    assert data["risk"]["contract_version"] == "v1"
    assert data["risk"]["endpoint_template"] == "/risk/events/{order_id}"
    assert data["risk"]["required_request_fields"] == ["order_id"]
    assert data["risk"]["request_json_schema"]["required"] == ["order_id"]
    assert data["risk"]["request_json_schema"]["properties"]["order_id"]["type"] == "string"
    assert data["risk"]["required_fields"] == {
        "order_id": "str",
        "decision": "str",
        "risk_score": "number",
        "hit_rules": "list",
        "recommended_action": "str",
    }
    assert data["risk"]["hit_rule_required_fields"] == {
        "rule_id": "str",
        "rule_name": "str",
        "evidence": "str",
    }
    assert data["risk"]["response_json_schema"]["required"] == [
        "order_id",
        "decision",
        "risk_score",
        "hit_rules",
        "recommended_action",
    ]
    assert (
        data["risk"]["response_json_schema"]["properties"]["hit_rules"]["items"]["required"]
        == ["rule_id", "rule_name", "evidence"]
    )
    assert data["risk"]["field_catalog"][0]["name"] == "order_id"
    assert data["risk"]["field_catalog"][1]["description"].startswith("风控系统给出的最终动作")
    assert "hit_rules" in data["risk"]["exposed_fields"]
    assert data["risk"]["example_response"]["order_id"] == "ORD12345"
    assert data["risk"]["example_response"]["hit_rules"][0]["rule_id"] == "RISK-velocity-001"

    assert data["profit"]["tool_name"] == "get_profit_chain_detail"
    assert data["profit"]["contract_version"] == "v1"
    assert data["profit"]["endpoint_template"] == "/profit/orders/{order_id}/chain"
    assert data["profit"]["required_request_fields"] == ["order_id"]
    assert data["profit"]["request_json_schema"]["required"] == ["order_id"]
    assert data["profit"]["required_fields"]["platform_net_profit"] == "number"
    assert "platform_net_profit" in data["profit"]["response_json_schema"]["required"]
    assert (
        data["profit"]["response_json_schema"]["properties"]["chain"]["items"]["required"]
        == ["node", "amount"]
    )
    assert "chain_source" not in data["profit"]["response_json_schema"]["properties"]
    assert data["profit"]["chain_step_required_fields"] == {
        "node": "str",
        "amount": "number",
    }
    assert data["profit"]["chain_step_optional_fields"] == {
        "source_field": "str",
        "role": "str",
        "tone": "str",
        "note": "str",
    }
    assert data["profit"]["chain_terminal_node"] == "平台净毛利"
    assert data["profit"]["derived_chain_steps"][0]["node"] == "乘客支付"
    assert data["profit"]["derived_chain_steps"][0]["field"] == "gross_amount"
    assert data["profit"]["derived_chain_steps"][0]["role"] == "订单收入"
    assert data["profit"]["derived_chain_steps"][-1]["node"] == "平台净毛利"
    assert data["profit"]["display_metadata_fields"] == [
        {
            "name": "chain_source",
            "label": "链路来源",
            "type": "string",
            "required": False,
            "description": "后端展示元信息，用于标记当前链路为真实接口原生返回(api)还是按最小合同自动派生(derived)。",
        }
    ]
    assert data["profit"]["field_catalog"][7]["label"] == "平台净毛利"
    assert "chain" in data["profit"]["exposed_fields"]
    assert "chain_source" in data["profit"]["exposed_fields"]
    assert data["profit"]["example_response"]["order_id"] == "ORD88888"
    assert "chain_source" not in data["profit"]["example_response"]
    assert data["profit"]["example_response"]["chain"][-1]["node"] == "平台净毛利"
    assert data["profit"]["example_response"]["chain"][-1]["note"] == "最终留存"


def test_business_tool_management_endpoints_publish_response_models():
    """测试业务工具管理接口发布稳定响应模型，避免 raw dict 契约漂移。"""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    schemas = data["components"]["schemas"]
    expected_models = {
        ("/api/v1/business-tools/contracts", "get"): "BusinessToolContractsResponse",
        ("/api/v1/business-tools/runtime-status", "get"): "BusinessToolRuntimeStatusResponse",
        ("/api/v1/business-tools/readiness", "get"): "BusinessToolReadinessResponse",
        ("/api/v1/business-tools/probe", "post"): "BusinessToolProbeResponse",
        ("/api/v1/business-tools/intent", "post"): "ToolIntent",
        ("/api/v1/business-tools/validate-response", "post"): (
            "BusinessToolValidationResponse"
        ),
        ("/api/v1/business-tools/validate-responses", "post"): (
            "BusinessToolBatchValidationResponse"
        ),
        ("/api/v1/business-tools/audit-events", "get"): "BusinessToolAuditEventsResponse",
    }

    for (path, method), model_name in expected_models.items():
        response_schema = data["paths"][path][method]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert model_name in schemas
        assert model_name in json.dumps(response_schema, ensure_ascii=False)


def test_business_tool_runtime_status_endpoint_returns_safe_snapshot(monkeypatch):
    """测试业务工具运行态自检只返回脱敏配置状态。"""
    from api.config import settings
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    monkeypatch.setattr(settings, "enable_business_tools", True)
    monkeypatch.setattr(settings, "business_tool_timeout", 9)
    monkeypatch.setattr(settings, "risk_api_base_url", "https://risk.internal.example/api")
    monkeypatch.setattr(settings, "risk_api_key", "risk-secret-key")
    monkeypatch.setattr(settings, "profit_api_base_url", "")
    monkeypatch.setattr(settings, "profit_api_key", "profit-secret-key")
    monkeypatch.setattr(settings, "enable_business_tool_audit_file", True)
    monkeypatch.setattr(settings, "business_tool_audit_file", "/var/secret/business_tool_audit.jsonl")
    monkeypatch.setattr(settings, "enable_business_tool_access_control", False)
    monkeypatch.setattr(settings, "business_tool_access_token", "business-access-secret")
    monkeypatch.setattr(settings, "business_tool_read_token", "business-read-secret")
    monkeypatch.setattr(settings, "business_tool_execute_token", "business-execute-secret")
    monkeypatch.setattr(settings, "enable_business_tool_llm_intent", True)
    monkeypatch.setattr(settings, "business_tool_llm_intent_min_confidence", 0.82)
    reset_business_clients()
    reset_tool_service()

    try:
        response = client.get("/api/v1/business-tools/runtime-status")
    finally:
        reset_business_clients()
        reset_tool_service()

    assert response.status_code == 200
    data = response.json()
    payload = json.dumps(data, ensure_ascii=False)
    assert data["status"] == "ready"
    assert data["status_reason"] == "业务工具已启用，访问控制未启用。"
    assert data["business_tools"] == {
        "enabled": True,
        "timeout_seconds": 9,
        "tool_count": 2,
    }
    assert data["access_control"]["ready"] is True
    assert data["access_control"]["full_access_configured"] is True
    assert data["access_control"]["read_configured"] is True
    assert data["access_control"]["execute_configured"] is True
    assert data["access_control"]["missing_scopes"] == []
    assert data["audit"]["file_enabled"] is True
    assert data["audit"]["file_name"] == "business_tool_audit.jsonl"
    assert data["llm_intent"]["enabled"] is True
    assert data["llm_intent"]["min_confidence"] == 0.82
    assert data["llm_intent"]["model_configured"] is True
    assert data["llm_intent"]["attempt_count"] == 0
    assert data["llm_intent"]["success_count"] == 0
    assert data["llm_intent"]["error_count"] == 0
    assert data["llm_intent"]["last_status"] is None
    assert data["llm_intent"]["last_resolution"] is None
    assert data["llm_intent"]["last_error_type"] is None
    assert data["llm_intent"]["last_attempt_at"] is None
    assert data["llm_intent"]["last_success_at"] is None
    assert data["llm_intent"]["last_error_at"] is None

    risk_tool = next(tool for tool in data["tools"] if tool["tool_name"] == "get_risk_event_detail")
    profit_tool = next(tool for tool in data["tools"] if tool["tool_name"] == "get_profit_chain_detail")
    assert risk_tool["data_source"] == "http"
    assert risk_tool["integration_mode"] == "external_http"
    assert risk_tool["base_url_configured"] is True
    assert risk_tool["api_key_configured"] is True
    assert risk_tool["endpoint_template"] == "/risk/events/{order_id}"
    assert risk_tool["contract_available"] is True
    assert profit_tool["data_source"] == "mock"
    assert profit_tool["integration_mode"] == "mock"
    assert profit_tool["base_url_configured"] is False
    assert profit_tool["api_key_configured"] is True
    assert profit_tool["endpoint_template"] == "/profit/orders/{order_id}/chain"

    assert "https://risk.internal.example" not in payload
    assert "risk-secret-key" not in payload
    assert "profit-secret-key" not in payload
    assert "business-access-secret" not in payload
    assert "business-read-secret" not in payload
    assert "business-execute-secret" not in payload
    assert "/var/secret" not in payload


def test_business_tool_readiness_endpoint_returns_safe_gates(monkeypatch):
    """测试业务工具接入检查只返回安全 gate 摘要。"""
    from api.config import settings
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import BusinessToolService, reset_tool_service

    monkeypatch.setattr(settings, "enable_business_tools", True)
    monkeypatch.setattr(settings, "risk_api_base_url", "https://risk.internal.example/api")
    monkeypatch.setattr(settings, "risk_api_key", "risk-secret-key")
    monkeypatch.setattr(settings, "profit_api_base_url", "")
    monkeypatch.setattr(settings, "profit_api_key", "profit-secret-key")
    monkeypatch.setattr(settings, "enable_business_tool_audit_file", True)
    monkeypatch.setattr(settings, "business_tool_audit_file", "/var/secret/business_tool_audit.jsonl")
    monkeypatch.setattr(settings, "enable_business_tool_access_control", False)
    monkeypatch.setattr(settings, "business_tool_access_token", "business-access-secret")
    monkeypatch.setattr(settings, "business_tool_read_token", "business-read-secret")
    monkeypatch.setattr(settings, "business_tool_execute_token", "business-execute-secret")
    monkeypatch.setattr(
        BusinessToolService,
        "_corpus_scene_status",
        lambda self: {
            "collection_name": "unified_docs",
            "scenes": {
                "risk_rule": {
                    "available": True,
                    "sample_count": 1,
                    "error_type": None,
                },
                "profit": {
                    "available": False,
                    "sample_count": 0,
                    "error_type": None,
                },
            },
        },
    )
    reset_business_clients()
    reset_tool_service()

    try:
        response = client.get("/api/v1/business-tools/readiness?limit=5")
    finally:
        reset_business_clients()
        reset_tool_service()

    assert response.status_code == 200
    data = response.json()
    payload = json.dumps(data, ensure_ascii=False)
    assert data["overall_status"] == "ready_with_warnings"
    assert data["audit_event_limit"] == 5
    assert "business_tools_enabled" in data["passed"]
    assert "contract_examples_valid" in data["passed"]
    assert "tool_contracts_available" in data["passed"]
    assert "intent_precheck" in data["passed"]
    assert "corpus_scene_coverage" in data["warnings"]
    assert "real_http_configured" in data["warnings"]
    assert "external_http_configured" in data["warnings"]
    assert "access_control_enabled" in data["warnings"]
    assert "audit_traceability" in data["warnings"]
    assert "llm_intent_fallback" in data["warnings"]
    assert not data["blockers"]

    access_item = next(item for item in data["items"] if item["id"] == "access_control_enabled")
    assert access_item["status"] == "warning"
    assert access_item["evidence"] == {
        "enabled": False,
        "ready": True,
        "missing_scopes": [],
    }
    contract_item = next(item for item in data["items"] if item["id"] == "contract_examples_valid")
    assert contract_item["status"] == "passed"
    assert contract_item["evidence"] == {
        "tools": [
            {
                "tool_name": "get_risk_event_detail",
                "contract_version": "v1",
                "example_valid": True,
                "diagnostic_code": None,
                "missing_fields": [],
                "invalid_fields": [],
                "required_fields_exposed": True,
                "missing_exposed_fields": [],
            },
            {
                "tool_name": "get_profit_chain_detail",
                "contract_version": "v1",
                "example_valid": True,
                "diagnostic_code": None,
                "missing_fields": [],
                "invalid_fields": [],
                "required_fields_exposed": True,
                "missing_exposed_fields": [],
            },
        ]
    }
    intent_item = next(item for item in data["items"] if item["id"] == "intent_precheck")
    assert intent_item["status"] == "passed"
    assert intent_item["evidence"] == {
        "checks": [
            {
                "scene_type": "risk_rule",
                "expected_tool_name": "get_risk_event_detail",
                "tool_name": "get_risk_event_detail",
                "selection_source": "rules",
                "confidence": 0.92,
                "missing_fields": [],
                "needs_clarification": False,
                "selected_expected_tool": True,
            },
            {
                "scene_type": "profit",
                "expected_tool_name": "get_profit_chain_detail",
                "tool_name": "get_profit_chain_detail",
                "selection_source": "rules",
                "confidence": 0.92,
                "missing_fields": [],
                "needs_clarification": False,
                "selected_expected_tool": True,
            },
        ]
    }
    http_item = next(item for item in data["items"] if item["id"] == "real_http_configured")
    assert http_item["evidence"]["tool_sources"][0]["tool_name"] == "get_risk_event_detail"
    assert http_item["evidence"]["tool_sources"][0]["data_source"] == "http"
    assert http_item["evidence"]["tool_sources"][0]["integration_mode"] == "external_http"
    assert http_item["evidence"]["tool_sources"][1]["data_source"] == "mock"
    assert http_item["evidence"]["tool_sources"][1]["integration_mode"] == "mock"
    external_http_item = next(
        item for item in data["items"] if item["id"] == "external_http_configured"
    )
    assert external_http_item["status"] == "warning"
    assert external_http_item["evidence"]["external_http_ready"] is False
    assert external_http_item["evidence"]["integration_modes"] == [
        "external_http",
        "mock",
    ]
    corpus_item = next(item for item in data["items"] if item["id"] == "corpus_scene_coverage")
    assert corpus_item["status"] == "warning"
    assert corpus_item["evidence"]["collection_name"] == "unified_docs"
    assert corpus_item["evidence"]["missing_scenes"] == ["profit"]
    assert corpus_item["evidence"]["ingestion_guidance"] == [
        {
            "scene_type": "profit",
            "label": "毛利链路语料",
            "source_path": "data/profit",
            "command": "python -m ingestion.ingest --source data/profit --scene profit",
        }
    ]
    assert corpus_item["evidence"]["scene_status"]["risk_rule"]["available"] is True
    assert corpus_item["evidence"]["scene_status"]["profit"]["available"] is False
    llm_item = next(item for item in data["items"] if item["id"] == "llm_intent_fallback")
    assert llm_item["status"] == "warning"
    assert llm_item["summary"] == "模糊问题当前主要依赖规则识别；可按需启用 LLM 兜底"
    assert llm_item["evidence"]["enabled"] is False
    assert llm_item["evidence"]["attempt_count"] == 0
    assert llm_item["evidence"]["success_count"] == 0
    assert llm_item["evidence"]["error_count"] == 0
    assert llm_item["evidence"]["last_status"] is None
    assert llm_item["evidence"]["last_resolution"] is None
    assert llm_item["evidence"]["last_error_type"] is None
    assert data["corpus_status"]["scenes"]["profit"]["sample_count"] == 0
    assert "risk.internal.example" not in payload
    assert "risk-secret-key" not in payload
    assert "profit-secret-key" not in payload
    assert "business-access-secret" not in payload
    assert "business-read-secret" not in payload
    assert "business-execute-secret" not in payload
    assert "/var/secret" not in payload
    assert "ORD12345" not in payload
    assert "ORD88888" not in payload


def test_business_tool_probe_endpoint_success():
    """测试业务工具探测成功响应。"""
    response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "get_profit_chain_detail"
    assert data["status"] == "success"
    assert data["endpoint_path"] == "/profit/orders/ORD88888/chain"
    assert data["endpoint_template"] == "/profit/orders/{order_id}/chain"
    assert data["contract_version"] == "v1"
    assert data["data_source"] in {"mock", "http"}
    assert data["integration_mode"] in {"mock", "fake_http", "external_http"}
    assert data["arguments"] == {"order_id": "ORD88888"}
    assert "平台净毛利" in data["summary"]
    assert data["result"]["order_id"] == "ORD88888"
    assert data["result"]["chain"][-1]["node"] == "平台净毛利"


def test_business_tool_probe_endpoint_success_for_risk_contract_metadata():
    """测试风控探测成功响应包含接口模板和合同版本。"""
    response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_risk_event_detail", "order_id": "ORD12345"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "get_risk_event_detail"
    assert data["status"] == "success"
    assert data["endpoint_path"] == "/risk/events/ORD12345"
    assert data["endpoint_template"] == "/risk/events/{order_id}"
    assert data["contract_version"] == "v1"
    assert data["arguments"] == {"order_id": "ORD12345"}
    assert data["result"]["order_id"] == "ORD12345"
    assert data["result"]["decision"] == "block"


def test_business_tool_probe_endpoint_rejects_unknown_tool():
    """测试业务工具探测拒绝未知工具。"""
    response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "unknown_tool", "order_id": "ORD88888"},
    )

    assert response.status_code == 400
    assert "Unknown business tool" in response.json()["detail"]


def test_business_tool_probe_endpoint_rejects_unsafe_order_id():
    """测试业务工具探测拒绝不安全订单号 path 参数。"""
    response = client.post(
        "/api/v1/business-tools/probe",
        json={
            "tool_name": "get_profit_chain_detail",
            "order_id": "../admin?token=secret",
        },
    )

    payload = json.dumps(response.json(), ensure_ascii=False)
    assert response.status_code == 400
    assert response.json()["detail"] == "order_id contains unsupported characters"
    assert "secret" not in payload
    assert "../admin" not in payload


def test_business_tool_probe_endpoint_preserves_contract_diagnostic(monkeypatch):
    """测试业务工具探测保留安全合同诊断字段。"""

    class FakeToolService:
        def probe(self, *, tool_name, order_id):
            return {
                "name": tool_name,
                "label": "订单毛利链路",
                "scene_type": "profit",
                "description": "按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
                "endpoint_path": f"/profit/orders/{order_id}/chain",
                "data_source": "http",
                "arguments": {"order_id": order_id},
                "status": "error",
                "duration_ms": 12,
                "summary": "订单毛利链路探测失败，请检查接口地址、鉴权和返回字段合同。",
                "result": {},
                "error_type": "BusinessContractError",
                "diagnostic": (
                    "Profit API response contract violation: "
                    "missing required fields: platform_net_profit"
                ),
                "diagnostic_code": "missing_required_fields",
                "missing_fields": ["platform_net_profit"],
                "invalid_fields": [],
            }

    business_tools_router = sys.modules["api.routers.business_tools"]
    monkeypatch.setattr(business_tools_router, "get_tool_service", lambda: FakeToolService())

    response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "BusinessContractError"
    assert (
        data["diagnostic"]
        == "Profit API response contract violation: "
        "missing required fields: platform_net_profit"
    )
    assert data["diagnostic_code"] == "missing_required_fields"
    assert data["missing_fields"] == ["platform_net_profit"]
    assert data["invalid_fields"] == []


@pytest.mark.parametrize(
    ("fake_urlopen", "expected_error_type"),
    [
        (
            lambda _req, timeout: (_ for _ in ()).throw(
                HTTPError(
                    url=(
                        "https://profit.example.test/profit/orders/"
                        "ORD88888/chain?token=secret"
                    ),
                    code=401,
                    msg="Unauthorized token=secret",
                    hdrs=None,
                    fp=None,
                )
            ),
            "ConnectionError",
        ),
        (
            lambda _req, timeout: (_ for _ in ()).throw(
                TimeoutError("timeout for ORD88888 token=secret")
            ),
            "TimeoutError",
        ),
    ],
)
def test_business_tool_probe_endpoint_wraps_http_transport_failure(
    monkeypatch,
    fake_urlopen,
    expected_error_type,
):
    """测试真实 HTTP client 失败经 probe API 后仍只返回安全降级信息。"""
    from api.config import settings
    from api.services.business_clients import reset_business_clients
    from api.services.tool_service import reset_tool_service

    monkeypatch.setattr(settings, "profit_api_base_url", "https://profit.example.test")
    monkeypatch.setattr(settings, "profit_api_key", "secret")
    monkeypatch.setattr(settings, "business_tool_timeout", 1)
    monkeypatch.setattr("api.services.business_clients.request.urlopen", fake_urlopen)
    reset_business_clients()
    reset_tool_service()

    try:
        response = client.post(
            "/api/v1/business-tools/probe",
            json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        )
    finally:
        reset_business_clients()
        reset_tool_service()

    assert response.status_code == 200
    data = response.json()
    encoded = json.dumps(data, ensure_ascii=False)
    assert data["status"] == "error"
    assert data["data_source"] == "http"
    assert data["result"] == {}
    assert data["error_type"] == expected_error_type
    assert "diagnostic" not in data
    assert "diagnostic_code" not in data
    assert "missing_fields" not in data
    assert "invalid_fields" not in data
    assert "secret" not in encoded
    assert "profit.example.test" not in encoded
    assert "Unauthorized" not in encoded
    assert "timeout for ORD88888" not in encoded


def test_business_tool_audit_events_endpoint_returns_safe_events(monkeypatch):
    """测试业务工具审计事件只返回安全摘要。"""

    class FakeToolService:
        def runtime_status(self):
            return {
                "audit": {
                    "file_enabled": True,
                    "file_configured": True,
                    "file_name": "business_tool_audit.jsonl",
                    "file_exists": True,
                    "file_readable": True,
                    "persisted_event_count": 1,
                    "memory_event_count": 1,
                    "memory_event_limit": 100,
                }
            }

        def list_audit_events(self, *, limit):
            return [
                {
                    "audit_id": "bt-testaudit0001",
                    "timestamp": "2026-06-07T00:00:00+00:00",
                    "tool_name": "get_profit_chain_detail",
                    "label": "订单毛利链路",
                    "scene_type": "profit",
                    "contract_version": "v1",
                    "data_source": "mock",
                    "endpoint_path": "/profit/orders/{order_id}/chain",
                    "status": "success",
                    "duration_ms": 12,
                    "arguments": {"order_id": "ORD***888"},
                    "selection_source": "rules",
                    "selection_reason": "识别到订单号 ORD***888，当前场景为 profit。",
                    "confidence": 0.92,
                    "result_keys": ["order_id", "platform_net_profit"],
                    "error_type": None,
                }
            ]

    business_tools_router = sys.modules["api.routers.business_tools"]
    monkeypatch.setattr(business_tools_router, "get_tool_service", lambda: FakeToolService())

    response = client.get("/api/v1/business-tools/audit-events?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["audit_status"] == {
        "file_enabled": True,
        "file_configured": True,
        "file_name": "business_tool_audit.jsonl",
        "file_exists": True,
        "file_readable": True,
        "persisted_event_count": 1,
        "memory_event_count": 1,
        "memory_event_limit": 100,
    }
    assert data["events"][0]["audit_id"] == "bt-testaudit0001"
    assert data["events"][0]["tool_name"] == "get_profit_chain_detail"
    assert data["events"][0]["contract_version"] == "v1"
    assert data["events"][0]["arguments"] == {"order_id": "ORD***888"}
    assert data["events"][0]["endpoint_path"] == "/profit/orders/{order_id}/chain"
    assert data["events"][0]["selection_source"] == "rules"
    assert data["events"][0]["selection_reason"] == "识别到订单号 ORD***888，当前场景为 profit。"
    assert data["events"][0]["confidence"] == 0.92
    assert "ORD88888" not in json.dumps(data, ensure_ascii=False)


def test_business_tool_intent_endpoint_inspects_without_executing_tool(monkeypatch):
    """测试业务工具意图预检只判断路由，不执行订单接口。"""
    calls = {"inspect": 0, "probe": 0}

    class FakeToolService:
        def inspect_intent(self, *, query, scene_type):
            calls["inspect"] += 1
            assert query == "查询订单 ORD88888 的抽成和司机收入"
            assert scene_type == "profit"
            return {
                "tool_name": "get_profit_chain_detail",
                "label": "订单毛利链路",
                "scene_type": "profit",
                "selection_source": "rules",
                "order_id": "ORD88888",
                "confidence": 0.92,
                "reason": "识别到订单号 ORD88888，当前场景为 profit。",
                "missing_fields": [],
                "needs_clarification": False,
                "clarification_options": [],
            }

        def probe(self, *, tool_name, order_id):
            calls["probe"] += 1
            raise AssertionError("intent endpoint must not execute a tool")

    business_tools_router = sys.modules["api.routers.business_tools"]
    monkeypatch.setattr(business_tools_router, "get_tool_service", lambda: FakeToolService())

    response = client.post(
        "/api/v1/business-tools/intent",
        json={
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "scene_type": "profit",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "get_profit_chain_detail"
    assert data["selection_source"] == "rules"
    assert data["order_id"] == "ORD88888"
    assert data["needs_clarification"] is False
    assert calls == {"inspect": 1, "probe": 0}


def test_business_tool_validate_response_endpoint_success():
    """测试业务工具响应样例离线校验成功。"""
    response = client.post(
        "/api/v1/business-tools/validate-response",
        json={
            "tool_name": "get_profit_chain_detail",
            "payload": {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
                "platform_net_profit": 2.33,
                "driver_phone": "13800000000",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "get_profit_chain_detail"
    assert data["contract_version"] == "v1"
    assert data["status"] == "valid"
    assert data["diagnostic_code"] is None
    assert data["missing_fields"] == []
    assert data["invalid_fields"] == []
    assert "platform_net_profit" in data["exposed_result_keys"]
    assert "chain_source" in data["exposed_result_keys"]
    assert data["ignored_result_keys"] == ["driver_phone"]
    assert "13800000000" not in json.dumps(data, ensure_ascii=False)


def test_business_tool_validate_response_endpoint_derives_chain_from_minimum_contract():
    """测试毛利最小合同样例离线校验时会暴露派生链路字段。"""
    response = client.post(
        "/api/v1/business-tools/validate-response",
        json={
            "tool_name": "get_profit_chain_detail",
            "payload": {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
                "platform_net_profit": 5.29,
                "internal_settlement_id": "settlement-secret",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    encoded = json.dumps(data, ensure_ascii=False)
    assert data["name"] == "get_profit_chain_detail"
    assert data["contract_version"] == "v1"
    assert data["status"] == "valid"
    assert data["diagnostic_code"] is None
    assert data["missing_fields"] == []
    assert data["invalid_fields"] == []
    assert data["exposed_result_keys"] == [
        "chain",
        "chain_source",
        "coupon",
        "driver_income",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "subsidy",
    ]
    assert data["ignored_result_keys"] == ["internal_settlement_id"]
    assert "settlement-secret" not in encoded


def test_business_tool_validate_response_endpoint_returns_safe_diagnostic():
    """测试业务工具响应样例离线校验返回安全合同诊断。"""
    response = client.post(
        "/api/v1/business-tools/validate-response",
        json={
            "tool_name": "get_profit_chain_detail",
            "payload": {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "invalid"
    assert data["contract_version"] == "v1"
    assert data["error_type"] == "BusinessContractError"
    assert (
        data["diagnostic"]
        == "Profit API response contract violation: "
        "missing required fields: platform_net_profit"
    )
    assert data["diagnostic_code"] == "missing_required_fields"
    assert data["missing_fields"] == ["platform_net_profit"]
    assert data["invalid_fields"] == []
    assert data["exposed_result_keys"] == []
    assert data["ignored_result_keys"] == []


def test_business_tool_validate_responses_endpoint_returns_batch_report():
    """测试批量响应样例校验返回安全聚合报告且不回显 payload。"""
    response = client.post(
        "/api/v1/business-tools/validate-responses",
        json={
            "tool_name": "get_profit_chain_detail",
            "payloads": [
                {
                    "order_id": "ORD88888",
                    "gross_amount": 128.6,
                    "platform_commission": 19.29,
                    "driver_income": 92.35,
                    "subsidy": 8.0,
                    "coupon": 6.0,
                    "platform_net_profit": 2.33,
                    "driver_phone": "13800000000",
                },
                {
                    "order_id": "ORD99999",
                    "gross_amount": 128.6,
                    "platform_commission": 19.29,
                    "driver_income": 92.35,
                    "subsidy": 8.0,
                    "coupon": 6.0,
                    "internal_settlement_id": "settlement-secret",
                },
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    encoded = json.dumps(data, ensure_ascii=False)
    assert data["name"] == "get_profit_chain_detail"
    assert data["contract_version"] == "v1"
    assert data["status"] == "invalid"
    assert data["validation_summary"] == {
        "total": 2,
        "valid_count": 1,
        "invalid_count": 1,
        "diagnostic_codes": {"missing_required_fields": 1},
        "missing_fields": ["platform_net_profit"],
        "invalid_fields": [],
        "ignored_result_keys": ["driver_phone"],
    }
    assert [item["index"] for item in data["items"]] == [0, 1]
    assert data["items"][0]["status"] == "valid"
    assert data["items"][0]["diagnostic_code"] is None
    assert "platform_net_profit" in data["items"][0]["exposed_result_keys"]
    assert data["items"][0]["ignored_result_keys"] == ["driver_phone"]
    assert data["items"][1]["status"] == "invalid"
    assert data["items"][1]["diagnostic_code"] == "missing_required_fields"
    assert data["items"][1]["missing_fields"] == ["platform_net_profit"]
    assert data["items"][1]["ignored_result_keys"] == []
    assert "ORD88888" not in encoded
    assert "ORD99999" not in encoded
    assert "13800000000" not in encoded
    assert "settlement-secret" not in encoded


def enable_business_tool_access_control(monkeypatch, token="business-access-secret"):
    """Enable the optional business tool access guard for a single test."""
    from api.config import settings

    monkeypatch.setattr(settings, "enable_business_tool_access_control", True)
    monkeypatch.setattr(settings, "business_tool_access_token", token)


def enable_scoped_business_tool_access_control(monkeypatch):
    """Enable scoped business tool tokens for a single test."""
    from api.config import settings

    enable_business_tool_access_control(monkeypatch, token="")
    monkeypatch.setattr(settings, "business_tool_read_token", "business-read-secret")
    monkeypatch.setattr(settings, "business_tool_execute_token", "business-execute-secret")


def minimal_query_result(session_id="session-sec"):
    """Return the smallest valid QueryResponse payload from a fake agent."""
    return {
        "answer": "业务查询回答",
        "sources": [],
        "retrieved_count": 0,
        "session_id": session_id,
    }


def test_business_tool_contracts_endpoint_stays_public_when_access_control_enabled(monkeypatch):
    """合同快照只读，不暴露订单数据，因此不要求业务工具 token。"""
    enable_business_tool_access_control(monkeypatch)

    response = client.get("/api/v1/business-tools/contracts")

    assert response.status_code == 200
    assert response.json()["profit"]["tool_name"] == "get_profit_chain_detail"


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("post", "/api/v1/profit/query", {"query": "查询 ORD88888 毛利"}),
        ("post", "/api/v1/profit/query-stream", {"query": "查询 ORD88888 毛利"}),
        (
            "post",
            "/api/v1/business-tools/probe",
            {"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        ),
        (
            "post",
            "/api/v1/business-tools/validate-response",
            {
                "tool_name": "get_profit_chain_detail",
                "payload": {
                    "order_id": "ORD88888",
                    "gross_amount": 128.6,
                    "platform_commission": 19.29,
                    "driver_income": 92.35,
                    "subsidy": 8.0,
                    "coupon": 6.0,
                    "platform_net_profit": 2.33,
                },
            },
        ),
        ("get", "/api/v1/business-tools/audit-events?limit=5", None),
        ("get", "/api/v1/business-tools/runtime-status", None),
        ("get", "/api/v1/business-tools/readiness?limit=5", None),
    ],
)
def test_business_tool_access_control_fails_closed_when_token_not_configured(
    monkeypatch,
    method,
    path,
    json_body,
):
    """启用访问控制但服务端未配置 token 时，订单级入口返回 503。"""
    enable_business_tool_access_control(monkeypatch, token="")

    response = getattr(client, method)(path, json=json_body) if json_body else getattr(client, method)(path)

    assert response.status_code == 503
    assert "访问控制未配置" in response.json()["detail"]


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("post", "/api/v1/risk-rules/query", {"query": "查询 ORD88888 风控"}),
        ("post", "/api/v1/profit/query", {"query": "查询 ORD88888 毛利"}),
        ("post", "/api/v1/profit/query-stream", {"query": "查询 ORD88888 毛利"}),
        (
            "post",
            "/api/v1/business-tools/probe",
            {"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        ),
        (
            "post",
            "/api/v1/business-tools/validate-response",
            {
                "tool_name": "get_profit_chain_detail",
                "payload": {
                    "order_id": "ORD88888",
                    "gross_amount": 128.6,
                    "platform_commission": 19.29,
                    "driver_income": 92.35,
                    "subsidy": 8.0,
                    "coupon": 6.0,
                    "platform_net_profit": 2.33,
                },
            },
        ),
        ("get", "/api/v1/business-tools/audit-events?limit=5", None),
        ("get", "/api/v1/business-tools/runtime-status", None),
        ("get", "/api/v1/business-tools/readiness?limit=5", None),
    ],
)
def test_business_tool_access_control_rejects_missing_or_wrong_header(
    monkeypatch,
    method,
    path,
    json_body,
):
    """启用访问控制后，缺失或错误 header 不允许查询订单级数据。"""
    enable_business_tool_access_control(monkeypatch)

    response = getattr(client, method)(path, json=json_body) if json_body else getattr(client, method)(path)
    assert response.status_code == 403
    assert "无权访问" in response.json()["detail"]

    response = (
        getattr(client, method)(
            path,
            json=json_body,
            headers={"X-Business-Tool-Token": "wrong-token"},
        )
        if json_body
        else getattr(client, method)(path, headers={"X-Business-Tool-Token": "wrong-token"})
    )
    assert response.status_code == 403


def test_business_tool_access_control_honors_read_and_execute_tokens(monkeypatch):
    """只读 token 不能执行工具，执行 token 可以执行且可读。"""
    enable_scoped_business_tool_access_control(monkeypatch)

    read_headers = {"X-Business-Tool-Token": "business-read-secret"}
    execute_headers = {"X-Business-Tool-Token": "business-execute-secret"}
    validate_body = {
        "tool_name": "get_profit_chain_detail",
        "payload": {
            "order_id": "ORD88888",
            "gross_amount": 128.6,
            "platform_commission": 19.29,
            "driver_income": 92.35,
            "subsidy": 8.0,
            "coupon": 6.0,
            "platform_net_profit": 2.33,
        },
    }

    validate_response = client.post(
        "/api/v1/business-tools/validate-response",
        json=validate_body,
        headers=read_headers,
    )
    runtime_response = client.get(
        "/api/v1/business-tools/runtime-status",
        headers=read_headers,
    )
    audit_response = client.get(
        "/api/v1/business-tools/audit-events?limit=5",
        headers=read_headers,
    )
    readiness_response = client.get(
        "/api/v1/business-tools/readiness?limit=5",
        headers=read_headers,
    )
    read_probe_response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        headers=read_headers,
    )
    read_query_response = client.post(
        "/api/v1/profit/query",
        json={"query": "查询 ORD88888 毛利"},
        headers=read_headers,
    )
    execute_probe_response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        headers=execute_headers,
    )
    execute_audit_response = client.get(
        "/api/v1/business-tools/audit-events?limit=5",
        headers=execute_headers,
    )
    execute_readiness_response = client.get(
        "/api/v1/business-tools/readiness?limit=5",
        headers=execute_headers,
    )

    assert validate_response.status_code == 200
    assert runtime_response.status_code == 200
    assert audit_response.status_code == 200
    assert readiness_response.status_code == 200
    assert read_probe_response.status_code == 403
    assert read_query_response.status_code == 403
    assert execute_probe_response.status_code == 200
    assert execute_audit_response.status_code == 200
    assert execute_readiness_response.status_code == 200


def test_business_tool_access_control_allows_query_with_correct_header(monkeypatch):
    """正确业务工具 token 允许订单级业务场景查询继续进入 agent。"""
    enable_business_tool_access_control(monkeypatch)
    calls = []
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        result=minimal_query_result(),
    )

    response = client.post(
        "/api/v1/profit/query",
        json={"query": "查询订单 ORD88888 的毛利链路"},
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "业务查询回答"
    assert calls[0]["scene_type"] == "profit"


def test_business_query_passes_explicit_answer_perspective_to_agent(monkeypatch):
    """业务查询可显式指定回答口径。"""
    enable_business_tool_access_control(monkeypatch)
    calls = []
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        result={
            **minimal_query_result(),
            "answer_perspective": "finance",
        },
    )

    response = client.post(
        "/api/v1/profit/query",
        json={
            "query": "查询订单 ORD88888 的毛利链路",
            "answer_perspective": "finance",
        },
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )

    assert response.status_code == 200
    assert response.json()["answer_perspective"] == "finance"
    assert calls[0]["scene_type"] == "profit"
    assert calls[0]["answer_perspective"] == "finance"


def test_business_tool_access_control_allows_stream_with_correct_header(monkeypatch):
    """正确业务工具 token 允许订单级 SSE 查询继续返回事件。"""
    enable_business_tool_access_control(monkeypatch)
    install_fake_conversation_agent(
        monkeypatch,
        stream_events=[
            {"type": "sources", "data": {"session_id": "session-sec", "sources": []}},
            {"type": "done", "data": {"session_id": "session-sec"}},
        ],
    )

    response = client.post(
        "/api/v1/profit/query-stream",
        json={"query": "查询订单 ORD88888 的毛利链路"},
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )

    assert response.status_code == 200
    assert "event: sources" in response.text


def test_business_tool_access_control_allows_probe_and_audit_with_correct_header(monkeypatch):
    """正确业务工具 token 允许探测和审计查询。"""
    enable_business_tool_access_control(monkeypatch)

    probe_response = client.post(
        "/api/v1/business-tools/probe",
        json={"tool_name": "get_profit_chain_detail", "order_id": "ORD88888"},
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )
    validate_response = client.post(
        "/api/v1/business-tools/validate-response",
        json={
            "tool_name": "get_profit_chain_detail",
            "payload": {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
                "platform_net_profit": 2.33,
            },
        },
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )
    audit_response = client.get(
        "/api/v1/business-tools/audit-events?limit=5",
        headers={"X-Business-Tool-Token": "business-access-secret"},
    )

    assert probe_response.status_code == 200
    assert validate_response.status_code == 200
    assert audit_response.status_code == 200


def test_business_tool_access_control_does_not_block_non_business_scene(monkeypatch):
    """非订单级场景不要求业务工具 token。"""
    enable_business_tool_access_control(monkeypatch)
    calls = []
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        result=minimal_query_result(session_id="session-model"),
    )

    response = client.post(
        "/api/v1/model_card/query",
        json={"query": "模型卡片怎么看"},
    )

    assert response.status_code == 200
    assert calls[0]["scene_type"] == "model_card"


def test_milvus_health():
    """测试 Milvus 健康检查"""
    response = client.get("/api/v1/health/milvus")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # 注意：如果 Milvus 未启动，status 会是 unhealthy


def test_redis_health():
    """测试 Redis 健康检查"""
    response = client.get("/api/v1/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # 注意：如果 Redis 未启动，status 会是 unhealthy


def test_risk_rules_query_success(monkeypatch):
    """测试查询成功响应和参数透传。"""
    calls = []
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        result={
            "answer": "白金卡单笔交易限额是 50,000 元。",
            "sources": [
                {
                    "score": 0.95,
                    "content_preview": "白金卡单笔限额：50,000 元...",
                    "rule_id": "R001",
                    "rule_name": "信用卡交易限额规则",
                }
            ],
            "retrieved_count": 1,
            "session_id": "session-123",
        },
    )

    response = client.post(
        "/api/v1/risk-rules/query",
        json={
            "query": "白金卡的单笔交易限额是多少？",
            "session_id": "session-123",
            "top_k": 3,
            "score_threshold": 0.6,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "白金卡单笔交易限额是 50,000 元。"
    assert data["retrieved_count"] == 1
    assert data["session_id"] == "session-123"
    assert data["needs_clarification"] is False
    assert data["tool_intent"] is None
    assert len(data["sources"]) == 1

    assert calls == [
        {
            "query": "白金卡的单笔交易限额是多少？",
            "session_id": "session-123",
            "scene_type": "risk_rule",
            "top_k": 3,
            "score_threshold": 0.6,
            "clarification_choice": None,
            "use_rerank": None,
            "use_bm25": None,
            "answer_perspective": None,
        }
    ]


def test_profit_query_preserves_business_tool_explainability_fields(monkeypatch):
    """测试非流式响应不会过滤业务工具可解释字段。"""
    tool_calls = [
        {
            "name": "get_profit_chain_detail",
            "label": "订单毛利链路",
            "scene_type": "profit",
            "description": "按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
            "audit_id": "bt-nonstreamaudit01",
            "endpoint_path": "/profit/orders/ORD88888/chain",
            "endpoint_template": "/profit/orders/{order_id}/chain",
            "contract_version": "v1",
            "data_source": "mock",
            "integration_mode": "mock",
            "arguments": {"order_id": "ORD88888"},
            "status": "error",
            "result": {},
            "summary": "订单毛利链路调用失败，请稍后重试或联系系统管理员。",
            "error_type": "RuntimeError",
            "duration_ms": 12,
            "selection_source": "rules",
            "selection_reason": "识别到订单号 ORD88888，当前场景为 profit。",
            "confidence": 0.92,
        }
    ]
    install_fake_conversation_agent(
        monkeypatch,
        result={
            "answer": "实时毛利接口未成功返回订单数据。",
            "sources": [],
            "retrieved_count": 0,
            "session_id": "session-tool-fields",
            "tool_calls": tool_calls,
        },
    )

    response = client.post(
        "/api/v1/profit/query",
        json={"query": "查询订单 ORD88888 的毛利链路"},
    )

    assert response.status_code == 200
    call = response.json()["tool_calls"][0]
    assert call["audit_id"] == "bt-nonstreamaudit01"
    assert call["endpoint_path"] == "/profit/orders/ORD88888/chain"
    assert call["endpoint_template"] == "/profit/orders/{order_id}/chain"
    assert call["contract_version"] == "v1"
    assert call["data_source"] == "mock"
    assert call["integration_mode"] == "mock"
    assert call["error_type"] == "RuntimeError"
    assert call["selection_source"] == "rules"
    assert call["selection_reason"] == "识别到订单号 ORD88888，当前场景为 profit。"
    assert call["confidence"] == 0.92


def test_profit_query_e2e_executes_real_business_tool_and_exposes_audit(monkeypatch):
    """测试 API 入口真实触发 Agent/业务工具/审计闭环。"""
    from tests.test_conversation_agent import (
        FakeClarificationService,
        FakeRAGService,
        FakeSessionManager,
        load_conversation_module,
    )

    business_clients = __import__(
        "api.services.business_clients",
        fromlist=["reset_business_clients"],
    )
    real_tool_module = __import__("api.services.tool_service", fromlist=["BusinessToolService"])
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tools", True)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_llm_intent", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_audit_file", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_access_control", False)
    monkeypatch.setattr(real_tool_module.settings, "profit_api_base_url", "")
    monkeypatch.setattr(real_tool_module.settings, "profit_api_key", "")
    business_clients.reset_business_clients()
    real_tool_module.reset_tool_service()
    real_tool_service = real_tool_module.BusinessToolService()

    def answer_from_tool_context(kwargs):
        return {
            "answer": f"业务系统接口数据已返回。\n{kwargs.get('tool_context', '')}",
            "sources": [{"score": 0.9, "content_preview": "毛利规则文档"}],
            "retrieved_count": 1,
        }

    module = load_conversation_module(
        monkeypatch,
        session_manager=FakeSessionManager(),
        rag_service=FakeRAGService(responder=answer_from_tool_context),
        clarification_service=FakeClarificationService(result=(False, None)),
        tool_service=real_tool_service,
    )
    agent = module.ConversationAgent()
    monkeypatch.setattr(module, "get_conversation_agent", lambda: agent)

    response = client.post(
        "/api/v1/profit/query",
        json={
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "session_id": "session-api-e2e",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-api-e2e"
    assert data["retrieved_count"] == 1
    assert "业务系统接口数据已返回" in data["answer"]
    assert data["tool_intent"]["tool_name"] == "get_profit_chain_detail"
    assert data["tool_intent"]["selection_source"] == "rules"
    assert data["tool_intent"]["needs_clarification"] is False

    call = data["tool_calls"][0]
    assert call["name"] == "get_profit_chain_detail"
    assert call["status"] == "success"
    assert call["audit_id"].startswith("bt-")
    assert call["endpoint_path"] == "/profit/orders/ORD88888/chain"
    assert call["endpoint_template"] == "/profit/orders/{order_id}/chain"
    assert call["contract_version"] == "v1"
    assert call["data_source"] == "mock"
    assert call["integration_mode"] == "mock"
    assert call["selection_source"] == "rules"
    assert call["confidence"] == 0.92
    assert call["result"]["platform_commission"] == 19.29
    assert call["result"]["driver_income"] == 92.35
    assert call["result"]["platform_net_profit"] == 2.33
    assert call["result"]["chain"][-1]["node"] == "平台净毛利"
    assert call["result"]["chain"][-1]["amount"] == 2.33
    assert call["result"]["chain"][-1]["role"] == "经营结果"
    assert call["result"]["chain_source"] == "api"
    assert "链路来源: 接口原生链路" in data["answer"]

    events = real_tool_service.list_audit_events()
    assert len(events) == 1
    assert events[0]["audit_id"] == call["audit_id"]
    assert events[0]["arguments"] == {"order_id": "ORD***888"}
    assert events[0]["endpoint_path"] == "/profit/orders/{order_id}/chain"
    assert "ORD88888" not in json.dumps(events, ensure_ascii=False)


def test_profit_query_e2e_contract_error_exposes_safe_diagnostic(monkeypatch):
    """测试自然语言查询触发工具合同错误时，API 和审计透出安全诊断字段。"""
    from api.services.business_contracts import BusinessContractError
    from tests.test_conversation_agent import (
        FakeClarificationService,
        FakeRAGService,
        FakeSessionManager,
        load_conversation_module,
    )

    business_clients = __import__(
        "api.services.business_clients",
        fromlist=["reset_business_clients"],
    )
    real_tool_module = __import__("api.services.tool_service", fromlist=["BusinessToolService"])
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tools", True)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_llm_intent", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_audit_file", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_access_control", False)
    monkeypatch.setattr(real_tool_module.settings, "profit_api_base_url", "")
    monkeypatch.setattr(real_tool_module.settings, "profit_api_key", "")
    business_clients.reset_business_clients()
    real_tool_module.reset_tool_service()
    real_tool_service = real_tool_module.BusinessToolService()

    def raise_contract_error(_order_id):
        raise BusinessContractError(
            "Profit API response contract violation: "
            "missing required fields: platform_net_profit",
            diagnostic_code="missing_required_fields",
            missing_fields=["platform_net_profit"],
        )

    real_tool_service.profit_client.get_chain_detail = raise_contract_error
    tool_def = real_tool_service._tools["get_profit_chain_detail"]
    real_tool_service._tools["get_profit_chain_detail"] = tool_def.__class__(
        name="get_profit_chain_detail",
        label="订单毛利链路",
        scene_type="profit",
        description="按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
        executor=real_tool_service.profit_client.get_chain_detail,
    )

    def answer_from_tool_context(kwargs):
        return {
            "answer": f"实时毛利接口未成功返回订单数据。\n{kwargs.get('tool_context', '')}",
            "sources": [{"score": 0.9, "content_preview": "毛利规则文档"}],
            "retrieved_count": 1,
        }

    module = load_conversation_module(
        monkeypatch,
        session_manager=FakeSessionManager(),
        rag_service=FakeRAGService(responder=answer_from_tool_context),
        clarification_service=FakeClarificationService(result=(False, None)),
        tool_service=real_tool_service,
    )
    agent = module.ConversationAgent()
    monkeypatch.setattr(module, "get_conversation_agent", lambda: agent)

    response = client.post(
        "/api/v1/profit/query",
        json={
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "session_id": "session-api-contract-error",
        },
    )

    assert response.status_code == 200
    data = response.json()
    encoded = json.dumps(data, ensure_ascii=False)
    call = data["tool_calls"][0]
    assert call["status"] == "error"
    assert call["error_type"] == "BusinessContractError"
    assert call["diagnostic_code"] == "missing_required_fields"
    assert call["missing_fields"] == ["platform_net_profit"]
    assert call["invalid_fields"] == []
    assert "合同诊断码: missing_required_fields" in data["answer"]
    assert "缺失字段: ['platform_net_profit']" in data["answer"]
    assert "ORD88888" in encoded

    business_tools_router = sys.modules["api.routers.business_tools"]
    monkeypatch.setattr(business_tools_router, "get_tool_service", lambda: real_tool_service)
    audit_response = client.get("/api/v1/business-tools/audit-events?limit=5")
    assert audit_response.status_code == 200
    audit_data = audit_response.json()
    event = audit_data["events"][0]
    assert event["audit_id"] == call["audit_id"]
    assert event["error_type"] == "BusinessContractError"
    assert event["diagnostic_code"] == "missing_required_fields"
    assert event["missing_fields"] == ["platform_net_profit"]
    assert event["invalid_fields"] == []
    assert event["arguments"] == {"order_id": "ORD***888"}
    assert "ORD88888" not in json.dumps(event, ensure_ascii=False)


def test_profit_query_e2e_derives_chain_from_minimum_contract_and_filters_sensitive_fields(
    monkeypatch,
):
    """测试 API 入口在真实工具仅返回最小合同字段时仍自动派生链路并过滤敏感字段。"""
    from api.services.business_contracts import derive_profit_chain
    from tests.test_conversation_agent import (
        FakeClarificationService,
        FakeRAGService,
        FakeSessionManager,
        load_conversation_module,
    )

    business_clients = __import__(
        "api.services.business_clients",
        fromlist=["reset_business_clients"],
    )
    real_tool_module = __import__("api.services.tool_service", fromlist=["BusinessToolService"])
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tools", True)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_llm_intent", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_audit_file", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_access_control", False)
    monkeypatch.setattr(real_tool_module.settings, "profit_api_base_url", "")
    monkeypatch.setattr(real_tool_module.settings, "profit_api_key", "")
    business_clients.reset_business_clients()
    real_tool_module.reset_tool_service()
    real_tool_service = real_tool_module.BusinessToolService()

    def get_chain_without_explicit_chain(order_id):
        return {
            "order_id": order_id,
            "gross_amount": 128.6,
            "platform_commission": 19.29,
            "driver_income": 92.35,
            "subsidy": 8.0,
            "coupon": 6.0,
            "platform_net_profit": 5.29,
            "driver_phone": "13800000000",
            "internal_settlement_id": "settlement-secret",
            "driver_income_detail": {
                "base_fare": 70.0,
                "distance_fee": 22.35,
                "driver_id_card": "hidden-id-card",
            },
        }

    real_tool_service.profit_client.get_chain_detail = get_chain_without_explicit_chain
    tool_def = real_tool_service._tools["get_profit_chain_detail"]
    real_tool_service._tools["get_profit_chain_detail"] = tool_def.__class__(
        name="get_profit_chain_detail",
        label="订单毛利链路",
        scene_type="profit",
        description="按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
        executor=real_tool_service.profit_client.get_chain_detail,
    )

    def answer_from_tool_context(kwargs):
        return {
            "answer": f"业务系统接口数据已返回。\n{kwargs.get('tool_context', '')}",
            "sources": [{"score": 0.9, "content_preview": "毛利规则文档"}],
            "retrieved_count": 1,
        }

    module = load_conversation_module(
        monkeypatch,
        session_manager=FakeSessionManager(),
        rag_service=FakeRAGService(responder=answer_from_tool_context),
        clarification_service=FakeClarificationService(result=(False, None)),
        tool_service=real_tool_service,
    )
    agent = module.ConversationAgent()
    monkeypatch.setattr(module, "get_conversation_agent", lambda: agent)

    response = client.post(
        "/api/v1/profit/query",
        json={
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "session_id": "session-api-derived-chain",
        },
    )

    assert response.status_code == 200
    data = response.json()
    encoded = json.dumps(data, ensure_ascii=False)
    assert data["session_id"] == "session-api-derived-chain"
    assert data["retrieved_count"] == 1
    assert data["tool_intent"]["tool_name"] == "get_profit_chain_detail"
    assert data["tool_intent"]["selection_source"] == "rules"
    assert data["tool_intent"]["needs_clarification"] is False
    assert "13800000000" not in encoded
    assert "settlement-secret" not in encoded
    assert "hidden-id-card" not in encoded

    call = data["tool_calls"][0]
    assert call["name"] == "get_profit_chain_detail"
    assert call["status"] == "success"
    assert call["endpoint_template"] == "/profit/orders/{order_id}/chain"
    assert call["contract_version"] == "v1"
    assert call["data_source"] == "mock"
    assert call["integration_mode"] == "mock"
    assert call["selection_source"] == "rules"
    assert call["result"] == {
        "order_id": "ORD88888",
        "gross_amount": 128.6,
        "platform_commission": 19.29,
        "driver_income": 92.35,
        "subsidy": 8.0,
        "coupon": 6.0,
        "platform_net_profit": 5.29,
        "chain_source": "derived",
        "driver_income_detail": {
            "base_fare": 70.0,
            "distance_fee": 22.35,
        },
        "chain": derive_profit_chain(
            {
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "subsidy": 8.0,
                "coupon": 6.0,
                "platform_net_profit": 5.29,
            }
        ),
    }
    assert "driver_phone" not in call["result"]
    assert "internal_settlement_id" not in call["result"]
    assert "driver_id_card" not in json.dumps(call["result"], ensure_ascii=False)
    assert call["result"]["chain"][-1]["node"] == "平台净毛利"
    assert call["result"]["chain"][-1]["amount"] == 5.29
    assert "链路来源: 自动派生链路" in data["answer"]
    assert "平台净毛利" in data["answer"]

    events = real_tool_service.list_audit_events()
    assert len(events) == 1
    assert events[0]["audit_id"] == call["audit_id"]
    assert events[0]["arguments"] == {"order_id": "ORD***888"}
    assert events[0]["endpoint_path"] == "/profit/orders/{order_id}/chain"
    assert events[0]["result_keys"] == [
        "chain",
        "chain_source",
        "coupon",
        "driver_income",
        "driver_income_detail",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "subsidy",
    ]
    assert "ORD88888" not in json.dumps(events, ensure_ascii=False)
    assert "settlement-secret" not in json.dumps(events, ensure_ascii=False)


def test_risk_rules_query_clarification_response(monkeypatch):
    """测试澄清响应结构。"""
    tool_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "selection_source": "rules",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号，当前场景为 profit，命中关键词: 司机/收入/结算/链路。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询，例如：订单 ORD88888 的订单毛利链路。"],
    }
    install_fake_conversation_agent(
        monkeypatch,
        result={
            "answer": "我判断这个问题需要查询订单毛利链路，但还缺少订单号。",
            "sources": [],
            "retrieved_count": 0,
            "session_id": "session-clarify",
            "needs_clarification": True,
            "clarification_options": tool_intent["clarification_options"],
            "tool_intent": tool_intent,
        },
    )

    response = client.post(
        "/api/v1/risk-rules/query",
        json={
            "query": "限额是多少？",
            "clarification_choice": "白金卡单笔限额",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert data["clarification_options"] == tool_intent["clarification_options"]
    assert data["tool_intent"]["tool_name"] == "get_profit_chain_detail"
    assert data["tool_intent"]["selection_source"] == "rules"
    assert data["tool_intent"]["missing_fields"] == ["order_id"]
    assert data["tool_intent"]["confidence"] == 0.68
    assert data["session_id"] == "session-clarify"


def test_scene_query_stream_includes_business_tool_payload(monkeypatch):
    """测试 SSE sources 事件透出业务工具调用信息。"""
    calls = []
    tool_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "selection_source": "rules",
        "order_id": "ORD88888",
        "confidence": 0.92,
        "reason": "识别到订单号 ORD88888，当前场景为 profit。",
        "missing_fields": [],
        "needs_clarification": False,
        "clarification_options": [],
    }
    tool_calls = [
        {
            "name": "get_profit_chain_detail",
            "label": "订单毛利链路",
            "scene_type": "profit",
            "audit_id": "bt-streamaudit01",
            "selection_source": "rules",
            "arguments": {"order_id": "ORD88888"},
            "status": "success",
            "summary": "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元。",
            "result": {
                "order_id": "ORD88888",
                "chain": [{"node": "乘客支付", "amount": 128.6}],
            },
        }
    ]
    install_fake_conversation_agent(
        monkeypatch,
        calls=calls,
        stream_events=[
            {
                "type": "progress",
                "data": {
                    "session_id": "session-stream",
                    "stage": "tool",
                    "message": "正在调用订单毛利链路。",
                },
            },
            {
                "type": "sources",
                "data": {
                    "session_id": "session-stream",
                    "sources": [],
                    "retrieved_count": 0,
                    "answer_perspective": "finance",
                    "tool_calls": tool_calls,
                    "tool_intent": tool_intent,
                },
            },
            {"type": "chunk", "data": "毛利链路回答"},
            {"type": "done", "data": {"session_id": "session-stream"}},
        ],
    )

    response = client.post(
        "/api/v1/profit/query-stream",
        json={
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "session_id": "session-stream",
            "answer_perspective": "finance",
        },
    )

    assert response.status_code == 200
    text = response.text
    assert "event: progress" in text
    assert "event: sources" in text
    assert "event: chunk" in text
    progress_line = next(
        line
        for index, line in enumerate(text.splitlines())
        if line.startswith("data: {") and text.splitlines()[index - 1] == "event: progress"
    )
    progress_data = json.loads(progress_line.removeprefix("data: "))
    assert progress_data["stage"] == "tool"
    lines = text.splitlines()
    sources_line = next(
        line
        for index, line in enumerate(lines)
        if line.startswith("data: {") and lines[index - 1] == "event: sources"
    )
    sources_data = json.loads(sources_line.removeprefix("data: "))
    assert sources_data["answer_perspective"] == "finance"
    assert sources_data["tool_calls"] == tool_calls
    assert sources_data["tool_intent"] == tool_intent
    assert calls == [
        {
            "query": "查询订单 ORD88888 的抽成和司机收入",
            "session_id": "session-stream",
            "scene_type": "profit",
            "top_k": None,
            "score_threshold": None,
            "clarification_choice": None,
            "use_rerank": None,
            "use_bm25": None,
            "answer_perspective": "finance",
        }
    ]


def test_scene_query_stream_masks_internal_error_details(monkeypatch):
    """测试 SSE error 事件不透出内部异常原文。"""
    install_fake_conversation_agent(
        monkeypatch,
        error=RuntimeError("database password leaked"),
    )

    response = client.post(
        "/api/v1/profit/query-stream",
        json={"query": "查询订单 ORD88888 的抽成和司机收入"},
    )

    assert response.status_code == 200
    text = response.text
    assert "event: error" in text
    assert "database password leaked" not in text

    error_line = next(line for line in text.splitlines() if line.startswith("data: {"))
    error_data = json.loads(error_line.removeprefix("data: "))
    assert error_data["error"] == "流式查询失败，请稍后重试或联系系统管理员。"
    assert error_data["error_type"] == "RuntimeError"
    assert error_data["request_id"]


@pytest.mark.parametrize(
    ("error", "status_code", "detail_prefix", "raw_detail"),
    [
        (ConnectionError("Milvus unavailable"), 503, "服务暂时不可用", "Milvus unavailable"),
        (TimeoutError("LLM timeout"), 504, "请求超时", "LLM timeout"),
        (ValueError("bad input"), 400, "请求参数错误", "bad input"),
        (Exception("unexpected"), 500, "查询失败", "unexpected"),
    ],
)
def test_risk_rules_query_error_mapping(
    monkeypatch,
    error,
    status_code,
    detail_prefix,
    raw_detail,
):
    """测试异常到 HTTP 状态码的映射。"""
    install_fake_conversation_agent(monkeypatch, error=error)

    response = client.post(
        "/api/v1/risk-rules/query",
        json={"query": "测试查询"},
    )

    assert response.status_code == status_code
    detail = response.json()["detail"]
    assert detail.startswith(detail_prefix)
    assert raw_detail not in detail
    assert "请求ID:" in detail
