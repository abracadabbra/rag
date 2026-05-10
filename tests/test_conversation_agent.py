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


class FakeSessionManager:
    def __init__(self, history=None):
        self.created_sessions = []
        self.extended_sessions = []
        self.saved_messages = []
        self.history = history or {}

    def create_session(self):
        session_id = f"session-{len(self.created_sessions) + 1}"
        self.created_sessions.append(session_id)
        return session_id

    def extend_ttl(self, session_id):
        self.extended_sessions.append(session_id)
        return True

    def get_conversation_history(self, session_id, limit=None):
        messages = list(self.history.get(session_id, []))
        if limit is not None:
            messages = messages[-limit:]
        return messages

    def add_message(self, session_id, role, content, metadata=None):
        self.saved_messages.append(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata,
            }
        )
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


class FakeClarificationService:
    def __init__(self, result=(False, None)):
        self.calls = []
        self.result = result

    def needs_clarification(self, **kwargs):
        self.calls.append(kwargs)
        needs_clarification, options = self.result
        return needs_clarification, options or []


def load_conversation_module(
    monkeypatch,
    *,
    session_manager,
    rag_service,
    clarification_service,
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

    monkeypatch.setitem(sys.modules, "langchain_core", fake_langchain_core)
    monkeypatch.setitem(sys.modules, "langchain_core.messages", fake_messages_module)
    monkeypatch.setitem(sys.modules, "langgraph", fake_langgraph)
    monkeypatch.setitem(sys.modules, "langgraph.graph", fake_graph_module)
    monkeypatch.setitem(sys.modules, "api.services.session_manager", fake_session_module)
    monkeypatch.setitem(sys.modules, "api.services.rag_service", fake_rag_module)
    monkeypatch.setitem(sys.modules, "api.services.clarification", fake_clarification_module)
    monkeypatch.delitem(sys.modules, "api.services.conversation_agent", raising=False)

    return importlib.import_module("api.services.conversation_agent")


def create_agent(monkeypatch, *, history=None, rag_responder=None, clarification_result=(False, None)):
    session_manager = FakeSessionManager(history=history)
    rag_service = FakeRAGService(responder=rag_responder)
    clarification_service = FakeClarificationService(result=clarification_result)

    module = load_conversation_module(
        monkeypatch,
        session_manager=session_manager,
        rag_service=rag_service,
        clarification_service=clarification_service,
    )

    agent = module.ConversationAgent()
    return agent, session_manager, rag_service, clarification_service, module


def test_process_creates_session_and_runs_retrieval_path(monkeypatch):
    agent, session_manager, rag_service, clarification_service, _module = create_agent(monkeypatch)

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
    agent, session_manager, rag_service, _clarification_service, _module = create_agent(
        monkeypatch,
        history=history,
    )

    result = agent.process(query="日累计呢？", session_id="session-existing")

    assert result["session_id"] == "session-existing"
    assert session_manager.extended_sessions == ["session-existing"]
    assert len(rag_service.calls) == 2
    assert rag_service.calls[1]["query"] == "上下文：白金卡单笔限额是多少？\n当前问题：日累计呢？"


def test_check_clarification_merges_user_choice_and_skips_services(monkeypatch):
    agent, _session_manager, rag_service, clarification_service, _module = create_agent(monkeypatch)

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


def test_check_clarification_sets_prompt_when_service_requests_it(monkeypatch):
    agent, _session_manager, rag_service, clarification_service, _module = create_agent(
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
    agent, session_manager, _rag_service, _clarification_service, _module = create_agent(monkeypatch)

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
            },
        },
    ]
