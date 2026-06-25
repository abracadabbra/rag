"""
对话 Agent 单元测试
"""

import importlib
import sys
from types import ModuleType, SimpleNamespace


class FakeBaseMessage:
    def __init__(self, content):
        self.content = content


class FakeHumanMessage(FakeBaseMessage):
    pass


class FakeAIMessage(FakeBaseMessage):
    pass


class FakeCompiledGraph:
    def __init__(self, workflow, end_sentinel):
        self.workflow = workflow
        self.end_sentinel = end_sentinel

    def invoke(self, state):
        current = self.workflow.entry_point

        while True:
            state = self.workflow.nodes[current](state)

            if current in self.workflow.conditional_edges:
                router, mapping = self.workflow.conditional_edges[current]
                current = mapping[router(state)]
                continue

            next_node = self.workflow.edges.get(current, self.end_sentinel)
            if next_node == self.end_sentinel:
                return state
            current = next_node


class FakeStateGraph:
    def __init__(self, *_args, **_kwargs):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None

    def add_node(self, name, handler):
        self.nodes[name] = handler

    def set_entry_point(self, name):
        self.entry_point = name

    def add_edge(self, source, target):
        self.edges[source] = target

    def add_conditional_edges(self, source, router, mapping):
        self.conditional_edges[source] = (router, mapping)

    def compile(self):
        return FakeCompiledGraph(self, "__END__")


class FakeSession:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}


class FakeSessionManager:
    def __init__(self, history=None, metadata=None):
        self.created_sessions = []
        self.extended_sessions = []
        self.saved_messages = []
        self.history = history or {}
        self.metadata_by_session = metadata or {}

    def create_session(self):
        session_id = f"session-{len(self.created_sessions) + 1}"
        self.created_sessions.append(session_id)
        self.metadata_by_session.setdefault(session_id, {})
        return session_id

    def extend_ttl(self, session_id):
        self.extended_sessions.append(session_id)
        return True

    def get_conversation_history(self, session_id, limit=None):
        messages = list(self.history.get(session_id, []))
        if limit is not None:
            messages = messages[-limit:]
        return messages

    def get_session(self, session_id):
        return FakeSession(metadata=self.metadata_by_session.get(session_id, {}))

    def add_message(self, session_id, role, content, metadata=None):
        self.saved_messages.append(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata,
            }
        )
        if metadata:
            self.metadata_by_session.setdefault(session_id, {}).update(metadata)
        return True


class FakeRAGService:
    def __init__(self, responder=None):
        self.calls = []
        self.responder = responder or self._default_response

    def _default_response(self, kwargs):
        return {
            "answer": f"answer for {kwargs['query']}",
            "sources": [{"score": 0.9, "content_preview": "preview"}],
            "retrieved_count": 1,
        }

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return self.responder(kwargs)

    def query_stream(self, **kwargs):
        self.calls.append(kwargs)
        yield {
            "type": "sources",
            "data": {
                "sources": [{"score": 0.9, "content_preview": "preview"}],
                "retrieved_count": 1,
                "retrieval_metadata": None,
            },
        }
        yield {"type": "chunk", "data": f"answer for {kwargs['query']}"}
        yield {"type": "done", "data": {}}


class FakeClarificationService:
    def __init__(self, result=(False, None)):
        self.calls = []
        self.result = result

    def needs_clarification(self, **kwargs):
        self.calls.append(kwargs)
        needs_clarification, options = self.result
        return needs_clarification, options or []


class FakeToolService:
    def __init__(self, tool_calls=None, tool_context="", tool_intent=None):
        self.calls = []
        self.intent_calls = []
        self.execute_intent_calls = []
        self.tool_calls = tool_calls or []
        self.tool_context = tool_context
        self.tool_intent = tool_intent or {
            "tool_name": None,
            "label": None,
            "scene_type": "risk_rule",
            "selection_source": "none",
            "order_id": None,
            "confidence": 0.0,
            "reason": "未识别到需要调用业务系统接口的订单级问题。",
            "missing_fields": [],
            "needs_clarification": False,
            "clarification_options": [],
        }

    def inspect_intent(self, **kwargs):
        self.intent_calls.append(kwargs)
        return self.tool_intent

    def maybe_execute(self, **kwargs):
        self.calls.append(kwargs)
        return self.tool_calls

    def execute_intent(self, intent):
        self.execute_intent_calls.append(intent)
        if (
            intent.get("needs_clarification")
            or intent.get("missing_fields")
            or not intent.get("tool_name")
            or not intent.get("order_id")
        ):
            return []
        return self.tool_calls

    def format_tool_context(self, tool_calls):
        if not tool_calls:
            return ""
        return self.tool_context or "formatted tool context"


def load_conversation_module(
    monkeypatch,
    *,
    session_manager,
    rag_service,
    clarification_service,
    tool_service,
):
    """在无 langgraph/langchain_core 依赖下加载 conversation_agent 模块。"""

    fake_messages_module = ModuleType("langchain_core.messages")
    fake_messages_module.BaseMessage = FakeBaseMessage
    fake_messages_module.HumanMessage = FakeHumanMessage
    fake_messages_module.AIMessage = FakeAIMessage
    fake_langchain_core = ModuleType("langchain_core")
    fake_langchain_core.messages = fake_messages_module

    fake_graph_module = ModuleType("langgraph.graph")
    fake_graph_module.StateGraph = FakeStateGraph
    fake_graph_module.END = "__END__"
    fake_langgraph = ModuleType("langgraph")
    fake_langgraph.graph = fake_graph_module

    fake_session_module = ModuleType("api.services.session_manager")
    fake_session_module.get_session_manager = lambda: session_manager

    fake_rag_module = ModuleType("api.services.rag_service")
    fake_rag_module.get_rag_service = lambda: rag_service

    fake_clarification_module = ModuleType("api.services.clarification")
    fake_clarification_module.get_clarification_service = lambda: clarification_service

    fake_tool_module = ModuleType("api.services.tool_service")
    fake_tool_module.get_tool_service = lambda: tool_service

    monkeypatch.setitem(sys.modules, "langchain_core", fake_langchain_core)
    monkeypatch.setitem(sys.modules, "langchain_core.messages", fake_messages_module)
    monkeypatch.setitem(sys.modules, "langgraph", fake_langgraph)
    monkeypatch.setitem(sys.modules, "langgraph.graph", fake_graph_module)
    monkeypatch.setitem(sys.modules, "api.services.session_manager", fake_session_module)
    monkeypatch.setitem(sys.modules, "api.services.rag_service", fake_rag_module)
    monkeypatch.setitem(sys.modules, "api.services.clarification", fake_clarification_module)
    monkeypatch.setitem(sys.modules, "api.services.tool_service", fake_tool_module)
    monkeypatch.delitem(sys.modules, "api.services.conversation_agent", raising=False)

    return importlib.import_module("api.services.conversation_agent")


def create_agent(
    monkeypatch,
    *,
    history=None,
    metadata=None,
    rag_responder=None,
    clarification_result=(False, None),
    tool_calls=None,
    tool_context="",
    tool_intent=None,
):
    session_manager = FakeSessionManager(history=history, metadata=metadata)
    rag_service = FakeRAGService(responder=rag_responder)
    clarification_service = FakeClarificationService(result=clarification_result)
    tool_service = FakeToolService(
        tool_calls=tool_calls,
        tool_context=tool_context,
        tool_intent=tool_intent,
    )

    module = load_conversation_module(
        monkeypatch,
        session_manager=session_manager,
        rag_service=rag_service,
        clarification_service=clarification_service,
        tool_service=tool_service,
    )

    agent = module.ConversationAgent()
    return agent, session_manager, rag_service, clarification_service, module, tool_service


def test_process_creates_session_and_runs_retrieval_path(monkeypatch):
    agent, session_manager, rag_service, clarification_service, _module, _tool_service = create_agent(monkeypatch)

    result = agent.process(query="白金卡单笔限额是多少？")

    assert result["session_id"] == "session-1"
    assert result["answer"] == "answer for 白金卡单笔限额是多少？"
    assert result["retrieved_count"] == 1
    assert result["needs_clarification"] is False
    assert session_manager.created_sessions == ["session-1"]
    assert len(rag_service.calls) == 2
    assert rag_service.calls[0]["score_threshold"] == 0.5
    assert rag_service.calls[1]["query"] == "白金卡单笔限额是多少？"
    assert clarification_service.calls[0]["query"] == "白金卡单笔限额是多少？"
    assert session_manager.saved_messages[0]["role"] == "user"
    assert session_manager.saved_messages[1]["role"] == "assistant"


def test_process_existing_session_extends_ttl_and_enhances_query(monkeypatch):
    history = {
        "session-existing": [
            SimpleNamespace(role="user", content="白金卡单笔限额是多少？"),
            SimpleNamespace(role="assistant", content="50,000 元。"),
        ]
    }
    agent, session_manager, rag_service, _clarification_service, _module, _tool_service = create_agent(
        monkeypatch,
        history=history,
    )

    result = agent.process(query="日累计呢？", session_id="session-existing")

    assert result["session_id"] == "session-existing"
    assert session_manager.extended_sessions == ["session-existing"]
    assert len(rag_service.calls) == 2
    assert rag_service.calls[1]["query"] == "上下文：白金卡单笔限额是多少？\n当前问题：日累计呢？"


def test_process_passes_answer_perspective_to_rag_and_session_metadata(monkeypatch):
    agent, session_manager, rag_service, _clarification_service, _module, _tool_service = create_agent(monkeypatch)

    result = agent.process(
        query="订单 ORD88888 的补贴是否异常",
        scene_type="profit",
        answer_perspective="finance",
    )

    assert result["session_id"] == "session-1"
    assert result["answer_perspective"] == "finance"
    assert rag_service.calls[0]["answer_perspective"] == "finance"
    assert rag_service.calls[1]["answer_perspective"] == "finance"
    assert session_manager.saved_messages[1]["metadata"]["answer_perspective"] == "finance"


def test_process_executes_business_tool_and_passes_context(monkeypatch):
    tool_calls = [
        {
            "name": "get_profit_chain_detail",
            "label": "订单毛利链路",
            "scene_type": "profit",
            "description": "按订单查询链路",
            "arguments": {"order_id": "ORD12345"},
            "status": "success",
            "result": {"order_id": "ORD12345"},
            "summary": "订单 ORD12345 平台抽成 19.29 元。",
        }
    ]
    agent, _session_manager, rag_service, _clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        tool_calls=tool_calls,
        tool_context="订单 ORD12345 的毛利链路数据",
        tool_intent={
            "tool_name": "get_profit_chain_detail",
            "label": "订单毛利链路",
            "scene_type": "profit",
            "selection_source": "rules",
            "order_id": "ORD12345",
            "confidence": 0.92,
            "reason": "识别到订单号 ORD12345，当前场景为 profit。",
            "missing_fields": [],
            "needs_clarification": False,
            "clarification_options": [],
        },
    )

    result = agent.process(query="查询订单 ORD12345 的抽成和司机收入", scene_type="profit")

    assert result["tool_calls"] == tool_calls
    assert rag_service.calls[1]["tool_context"] == "订单 ORD12345 的毛利链路数据"
    assert tool_service.calls == []
    assert tool_service.execute_intent_calls == [result["tool_intent"]]


def test_process_e2e_executes_real_profit_tool_and_records_safe_audit(monkeypatch):
    business_clients_module = importlib.import_module("api.services.business_clients")
    real_tool_module = importlib.import_module("api.services.tool_service")
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tools", True)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_llm_intent", False)
    monkeypatch.setattr(real_tool_module.settings, "enable_business_tool_audit_file", False)
    monkeypatch.setattr(real_tool_module.settings, "profit_api_base_url", "")
    monkeypatch.setattr(real_tool_module.settings, "profit_api_key", "")
    business_clients_module.reset_business_clients()
    real_tool_module.reset_tool_service()
    real_tool_service = real_tool_module.BusinessToolService()

    def answer_from_tool_context(kwargs):
        tool_context = kwargs.get("tool_context", "")
        return {
            "answer": f"业务系统接口数据已返回。\n{tool_context}",
            "sources": [{"score": 0.9, "content_preview": "毛利规则文档"}],
            "retrieved_count": 1,
        }

    session_manager = FakeSessionManager()
    rag_service = FakeRAGService(responder=answer_from_tool_context)
    clarification_service = FakeClarificationService(result=(False, None))
    module = load_conversation_module(
        monkeypatch,
        session_manager=session_manager,
        rag_service=rag_service,
        clarification_service=clarification_service,
        tool_service=real_tool_service,
    )
    agent = module.ConversationAgent()

    result = agent.process(
        query="查询订单 ORD88888 的抽成和司机收入",
        scene_type="profit",
    )

    assert result["retrieved_count"] == 1
    assert result["tool_intent"]["tool_name"] == "get_profit_chain_detail"
    assert result["tool_intent"]["selection_source"] == "rules"
    assert result["tool_intent"]["needs_clarification"] is False

    tool_call = result["tool_calls"][0]
    assert tool_call["name"] == "get_profit_chain_detail"
    assert tool_call["status"] == "success"
    assert tool_call["audit_id"].startswith("bt-")
    assert tool_call["endpoint_path"] == "/profit/orders/ORD88888/chain"
    assert tool_call["data_source"] == "mock"
    assert tool_call["arguments"] == {"order_id": "ORD88888"}
    assert tool_call["selection_source"] == "rules"
    assert tool_call["confidence"] == 0.92
    assert (
        "命中关键词: 毛利/抽成/司机/收入/结算/链路"
        in tool_call["selection_reason"]
    )
    assert tool_call["result"]["platform_commission"] == 19.29
    assert tool_call["result"]["driver_income"] == 92.35
    assert tool_call["result"]["platform_net_profit"] == 2.33
    assert tool_call["result"]["chain"][-1]["node"] == "平台净毛利"
    assert tool_call["result"]["chain"][-1]["amount"] == 2.33
    assert tool_call["result"]["chain"][-1]["role"] == "经营结果"

    assert len(rag_service.calls) == 2
    final_rag_call = rag_service.calls[1]
    assert final_rag_call["scene_type"] == "profit"
    assert "【工具 1】订单毛利链路" in final_rag_call["tool_context"]
    assert "接口路径: /profit/orders/ORD88888/chain" in final_rag_call["tool_context"]
    assert "链路来源: 接口原生链路" in final_rag_call["tool_context"]
    assert "- platform_net_profit: 2.33" in final_rag_call["tool_context"]
    assert "业务系统接口数据已返回" in result["answer"]

    audit_events = real_tool_service.list_audit_events()
    assert len(audit_events) == 1
    assert audit_events[0]["audit_id"] == tool_call["audit_id"]
    assert audit_events[0]["arguments"] == {"order_id": "ORD***888"}
    assert audit_events[0]["endpoint_path"] == "/profit/orders/{order_id}/chain"
    assert audit_events[0]["result_keys"] == [
        "chain",
        "chain_source",
        "channel_fee",
        "commission_rate",
        "coupon",
        "driver_income",
        "driver_income_detail",
        "gross_amount",
        "order_id",
        "platform_commission",
        "platform_net_profit",
        "settlement_status",
        "subsidy",
    ]
    assert "ORD88888" not in str(audit_events[0])

    assert session_manager.saved_messages[1]["metadata"]["tool_calls"] == result["tool_calls"]
    assert session_manager.saved_messages[1]["metadata"]["tool_intent"] == result["tool_intent"]


def test_process_clarifies_missing_order_id_for_tool_intent(monkeypatch):
    tool_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号，当前场景为 profit，命中关键词: 司机/收入/结算/链路。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询，例如：订单 ORD88888 的订单毛利链路。"],
    }
    (
        agent,
        session_manager,
        rag_service,
        clarification_service,
        _module,
        tool_service,
    ) = create_agent(monkeypatch, tool_intent=tool_intent)

    result = agent.process(query="查询司机收入和结算链路", scene_type="profit")

    assert result["needs_clarification"] is True
    assert result["answer"].startswith("我判断这个问题需要查询订单毛利链路")
    assert result["clarification_options"] == tool_intent["clarification_options"]
    assert result["tool_intent"] == tool_intent
    assert result["tool_calls"] == []
    assert rag_service.calls == []
    assert clarification_service.calls == []
    assert tool_service.calls == []
    assert tool_service.execute_intent_calls == []
    assert tool_service.intent_calls[0]["query"] == "查询司机收入和结算链路"
    assert session_manager.saved_messages[1]["metadata"]["tool_calls"] == []


def test_process_clarifies_low_confidence_tool_intent(monkeypatch):
    tool_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": "ORD88888",
        "confidence": 0.62,
        "reason": "识别到订单号 ORD88888，当前场景为 profit，LLM 意图判断: 可能是订单资金问题。",
        "missing_fields": ["tool_intent_confirmation"],
        "needs_clarification": True,
        "clarification_options": ["确认查询订单 ORD88888 的订单毛利链路。"],
    }
    (
        agent,
        _session_manager,
        rag_service,
        clarification_service,
        _module,
        tool_service,
    ) = create_agent(monkeypatch, tool_intent=tool_intent)

    result = agent.process(query="看看订单 ORD88888 的钱是怎么分的", scene_type="profit")

    assert result["needs_clarification"] is True
    assert result["answer"] == "我不确定这个问题是否需要查询订单毛利链路。确认查询订单 ORD88888 的订单毛利链路。"
    assert result["clarification_options"] == tool_intent["clarification_options"]
    assert result["tool_intent"] == tool_intent
    assert result["tool_calls"] == []
    assert rag_service.calls == []
    assert clarification_service.calls == []
    assert tool_service.calls == []
    assert tool_service.execute_intent_calls == []


def test_check_clarification_rebuilds_order_tool_query_from_session_intent(monkeypatch):
    previous_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
    }
    agent, _session_manager, rag_service, clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        metadata={"session-1": {"tool_intent": previous_intent}},
    )

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "",
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_count": 0,
        "scene_type": "profit",
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
        "clarification_choice": "ORD88888",
    }

    updated = agent._check_clarification(state)

    assert updated["query"] == "订单 ORD88888 的订单毛利链路"
    assert updated["needs_clarification"] is False
    assert tool_service.intent_calls[0]["query"] == "订单 ORD88888 的订单毛利链路"
    assert rag_service.calls == []
    assert clarification_service.calls == []


def test_check_clarification_keeps_asking_when_order_id_remains_missing(monkeypatch):
    previous_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
    }
    unresolved_intent = {
        **previous_intent,
        "reason": "仍缺少有效订单号。",
        "clarification_options": ["请补充有效订单号，例如 ORD88888。"],
    }
    agent, _session_manager, rag_service, clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        metadata={"session-1": {"tool_intent": previous_intent}},
        tool_intent=unresolved_intent,
    )

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "",
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_count": 0,
        "scene_type": "profit",
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
        "clarification_choice": "没有订单号",
    }

    updated = agent._check_clarification(state)

    assert updated["needs_clarification"] is True
    assert updated["clarification_options"] == unresolved_intent["clarification_options"]
    assert updated["tool_intent"] == unresolved_intent
    assert updated["answer"].startswith("我判断这个问题需要查询订单毛利链路")
    assert tool_service.intent_calls[0]["query"] == "订单 没有订单号 的订单毛利链路"
    assert rag_service.calls == []
    assert clarification_service.calls == []


def test_check_clarification_rebuilds_low_confidence_tool_confirmation(monkeypatch):
    previous_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": "ORD88888",
        "confidence": 0.62,
        "reason": "LLM 低置信度工具意图。",
        "missing_fields": ["tool_intent_confirmation"],
        "needs_clarification": True,
        "clarification_options": ["确认查询订单 ORD88888 的订单毛利链路。"],
    }
    agent, _session_manager, rag_service, clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        metadata={"session-1": {"tool_intent": previous_intent}},
    )

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "",
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_count": 0,
        "scene_type": "profit",
        "needs_clarification": True,
        "clarification_options": ["确认查询订单 ORD88888 的订单毛利链路。"],
        "clarification_choice": "确认查询订单 ORD88888 的订单毛利链路。",
    }

    updated = agent._check_clarification(state)

    assert updated["query"] == "订单 ORD88888 的订单毛利链路"
    assert updated["needs_clarification"] is False
    assert tool_service.intent_calls[0]["query"] == "订单 ORD88888 的订单毛利链路"
    assert rag_service.calls == []
    assert clarification_service.calls == []


def test_check_clarification_merges_user_choice_and_skips_services(monkeypatch):
    agent, _session_manager, rag_service, clarification_service, _module, _tool_service = create_agent(monkeypatch)

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "限额是多少？",
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_count": 0,
        "scene_type": "risk_rule",
        "needs_clarification": True,
        "clarification_options": ["白金卡单笔限额"],
        "clarification_choice": "白金卡单笔限额",
    }

    updated = agent._check_clarification(state)

    assert updated["query"] == "白金卡单笔限额 限额是多少？"
    assert updated["needs_clarification"] is False
    assert rag_service.calls == []
    assert clarification_service.calls == []


def test_process_stream_saves_tool_intent_before_order_id_clarification(monkeypatch):
    tool_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号，当前场景为 profit。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询，例如：订单 ORD88888 的订单毛利链路。"],
    }
    agent, session_manager, rag_service, clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        tool_intent=tool_intent,
    )

    events = list(agent.process_stream(query="查询司机收入和结算链路", scene_type="profit"))

    assert events[0] == {
        "type": "progress",
        "data": {
            "session_id": "session-1",
            "stage": "intent",
            "message": "正在识别是否需要查询业务系统。",
        },
    }
    clarification_event = next(event for event in events if event["type"] == "clarification")
    assert clarification_event == {
        "type": "clarification",
        "data": {
            "options": tool_intent["clarification_options"],
            "session_id": "session-1",
            "answer": "我判断这个问题需要查询订单毛利链路，但还缺少订单号。请补充订单号后再查询，例如：订单 ORD88888 的订单毛利链路。",
            "answer_perspective": None,
            "tool_intent": tool_intent,
        },
    }
    assert session_manager.saved_messages[0]["content"] == "查询司机收入和结算链路"
    assert session_manager.saved_messages[1]["metadata"]["tool_intent"] == tool_intent
    assert session_manager.metadata_by_session["session-1"]["tool_intent"] == tool_intent
    assert rag_service.calls == []
    assert clarification_service.calls == []
    assert tool_service.calls == []
    assert tool_service.execute_intent_calls == []


def test_process_stream_uses_request_retrieval_options_not_stale_agent_state(monkeypatch):
    agent, _session_manager, rag_service, _clarification_service, _module, _tool_service = create_agent(monkeypatch)
    agent._top_k = 99
    agent._score_threshold = 0.01

    events = list(
        agent.process_stream(
            query="白金卡单笔限额是多少？",
            scene_type="risk_rule",
            top_k=3,
            score_threshold=0.66,
        )
    )

    assert events[-1] == {"type": "done", "data": {"session_id": "session-1"}}
    assert rag_service.calls[0]["top_k"] == 3
    assert rag_service.calls[0]["score_threshold"] == 0.5
    assert rag_service.calls[1]["top_k"] == 3
    assert rag_service.calls[1]["score_threshold"] == 0.66


def test_process_stream_passes_answer_perspective_to_rag_and_session_metadata(monkeypatch):
    agent, session_manager, rag_service, _clarification_service, _module, _tool_service = create_agent(monkeypatch)

    events = list(
        agent.process_stream(
            query="订单 ORD88888 的补贴是否异常",
            scene_type="profit",
            answer_perspective="operations",
        )
    )

    assert events[-1] == {"type": "done", "data": {"session_id": "session-1"}}
    progress_stages = [event["data"]["stage"] for event in events if event["type"] == "progress"]
    assert progress_stages == ["intent", "retrieve", "tool", "generate"]
    sources_event = next(event for event in events if event["type"] == "sources")
    assert sources_event["data"]["answer_perspective"] == "operations"
    assert rag_service.calls[0]["answer_perspective"] == "operations"
    assert rag_service.calls[1]["answer_perspective"] == "operations"
    assert session_manager.saved_messages[1]["metadata"]["answer_perspective"] == "operations"


def test_process_stream_continues_order_id_clarification_with_profit_tool(monkeypatch):
    previous_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号，当前场景为 profit。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
    }
    resolved_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
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
            "arguments": {"order_id": "ORD88888"},
            "status": "success",
            "duration_ms": 8,
            "selection_reason": "识别到订单号 ORD88888，当前场景为 profit。",
            "confidence": 0.92,
            "summary": "订单 ORD88888 总金额 128.6 元，平台抽成 19.29 元，司机收入 92.35 元。",
            "result": {
                "order_id": "ORD88888",
                "gross_amount": 128.6,
                "platform_commission": 19.29,
                "driver_income": 92.35,
                "platform_net_profit": 2.33,
                "chain": [
                    {"node": "乘客支付", "amount": 128.6},
                    {"node": "平台抽成", "amount": 19.29},
                ],
            },
        }
    ]
    agent, session_manager, rag_service, _clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        metadata={"session-1": {"tool_intent": previous_intent}},
        tool_intent=resolved_intent,
        tool_calls=tool_calls,
        tool_context="订单 ORD88888 的毛利链路数据",
    )

    events = list(
        agent.process_stream(
            query="",
            session_id="session-1",
            scene_type="profit",
            clarification_choice="ORD88888",
        )
    )

    progress_stages = [event["data"]["stage"] for event in events if event["type"] == "progress"]
    assert progress_stages == ["intent", "tool", "generate"]
    sources_event = next(event for event in events if event["type"] == "sources")
    chunk_event = next(event for event in events if event["type"] == "chunk")
    assert sources_event["data"]["session_id"] == "session-1"
    assert sources_event["data"]["tool_calls"] == tool_calls
    assert sources_event["data"]["tool_intent"] == resolved_intent
    assert chunk_event == {
        "type": "chunk",
        "data": "answer for 订单 ORD88888 的订单毛利链路",
    }
    assert events[-1] == {"type": "done", "data": {"session_id": "session-1"}}
    assert tool_service.intent_calls[0]["query"] == "订单 ORD88888 的订单毛利链路"
    assert tool_service.calls == []
    assert tool_service.execute_intent_calls == [resolved_intent]
    assert rag_service.calls[0]["query"] == "订单 ORD88888 的订单毛利链路"
    assert rag_service.calls[0]["tool_context"] == "订单 ORD88888 的毛利链路数据"
    assert session_manager.saved_messages[0] == {
        "session_id": "session-1",
        "role": "user",
        "content": "ORD88888",
        "metadata": None,
    }
    assert session_manager.saved_messages[1]["metadata"]["tool_calls"] == tool_calls
    assert session_manager.saved_messages[1]["metadata"]["tool_intent"] == resolved_intent


def test_process_stream_keeps_asking_when_order_id_clarification_is_invalid(monkeypatch):
    previous_intent = {
        "tool_name": "get_profit_chain_detail",
        "label": "订单毛利链路",
        "scene_type": "profit",
        "order_id": None,
        "confidence": 0.68,
        "reason": "识别到订单级问题信号，当前场景为 profit。",
        "missing_fields": ["order_id"],
        "needs_clarification": True,
        "clarification_options": ["请补充订单号后再查询。"],
    }
    unresolved_intent = {
        **previous_intent,
        "reason": "仍缺少有效订单号。",
        "clarification_options": ["请补充有效订单号，例如 ORD88888。"],
    }
    agent, session_manager, rag_service, _clarification_service, _module, tool_service = create_agent(
        monkeypatch,
        metadata={"session-1": {"tool_intent": previous_intent}},
        tool_intent=unresolved_intent,
    )

    events = list(
        agent.process_stream(
            query="",
            session_id="session-1",
            scene_type="profit",
            clarification_choice="没有订单号",
        )
    )

    assert [event["type"] for event in events] == ["progress", "clarification"]
    clarification_event = events[-1]
    assert clarification_event["data"]["options"] == unresolved_intent["clarification_options"]
    assert clarification_event["data"]["tool_intent"] == unresolved_intent
    assert clarification_event["data"]["answer"].startswith("我判断这个问题需要查询订单毛利链路")
    assert tool_service.intent_calls[0]["query"] == "订单 没有订单号 的订单毛利链路"
    assert tool_service.execute_intent_calls == []
    assert rag_service.calls == []
    assert session_manager.saved_messages[-1]["metadata"]["tool_intent"] == unresolved_intent


def test_check_clarification_sets_prompt_when_service_requests_it(monkeypatch):
    agent, _session_manager, rag_service, clarification_service, _module, _tool_service = create_agent(
        monkeypatch,
        clarification_result=(True, ["白金卡单笔限额", "白金卡日累计限额"]),
    )

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "限额呢？",
        "context": "",
        "answer": "",
        "sources": [],
        "retrieved_count": 0,
        "scene_type": "risk_rule",
        "needs_clarification": False,
        "clarification_options": [],
        "clarification_choice": None,
        "top_k": 5,
        "score_threshold": 0.7,
    }

    updated = agent._check_clarification(state)

    assert updated["needs_clarification"] is True
    assert updated["clarification_options"] == ["白金卡单笔限额", "白金卡日累计限额"]
    assert updated["answer"] == "请问您想查询以下哪个方面的信息？"
    assert rag_service.calls[0]["score_threshold"] == 0.5
    assert clarification_service.calls[0]["retrieved_docs"] == [{"score": 0.9, "content_preview": "preview"}]


def test_save_state_persists_user_and_assistant_messages(monkeypatch):
    agent, session_manager, _rag_service, _clarification_service, _module, _tool_service = create_agent(monkeypatch)

    state = {
        "session_id": "session-1",
        "messages": [],
        "query": "白金卡限额",
        "context": "",
        "answer": "白金卡限额是 50,000 元。",
        "sources": [],
        "retrieved_count": 2,
        "scene_type": "risk_rule",
        "needs_clarification": False,
        "clarification_options": [],
        "clarification_choice": None,
    }

    agent._save_state(state)

    assert session_manager.saved_messages == [
        {
            "session_id": "session-1",
            "role": "user",
            "content": "白金卡限额",
            "metadata": None,
        },
        {
            "session_id": "session-1",
            "role": "assistant",
            "content": "白金卡限额是 50,000 元。",
            "metadata": {
                "retrieved_count": 2,
                "scene_type": "risk_rule",
                "tool_calls": [],
                "tool_intent": None,
                "answer_perspective": None,
            },
        },
    ]
