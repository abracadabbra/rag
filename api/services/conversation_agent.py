"""
对话 Agent
基于 LangGraph 实现多轮对话
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from api.config import settings
from api.services.session_manager import get_session_manager
from api.services.rag_service import get_rag_service
from api.services.clarification import get_clarification_service
from api.services.tool_service import get_tool_service

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """对话状态"""
    session_id: str
    messages: List[BaseMessage]  # 对话历史
    query: str  # 当前问题
    context: str  # 检索到的上下文
    answer: str  # 生成的答案
    sources: List[Dict[str, Any]]  # 来源文档
    retrieved_count: int  # 检索到的文档数量
    scene_type: str  # 场景类型
    needs_clarification: bool  # 是否需要澄清
    clarification_options: List[str]  # 澄清选项
    clarification_choice: Optional[str]  # 用户选择的澄清选项
    retrieval_metadata: Optional[Dict[str, Any]]  # 检索元数据
    tool_calls: List[Dict[str, Any]]  # 业务工具调用结果
    tool_context: str  # 注入 Prompt 的工具上下文
    tool_intent: Optional[Dict[str, Any]]  # 工具意图预判结果
    answer_perspective: Optional[str]  # 显式回答口径


class ConversationAgent:
    """对话 Agent"""

    def __init__(self):
        """初始化对话 Agent"""
        self.session_manager = get_session_manager()
        self.rag_service = get_rag_service()
        self.clarification_service = get_clarification_service()
        self.tool_service = get_tool_service()
        self.graph = self._build_graph()
        # 存储检索参数（不通过 LangGraph state 传递）
        self._top_k = None
        self._score_threshold = None
        self._use_rerank = None
        self._use_bm25 = None

        logger.info("对话 Agent 初始化完成")

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(ConversationState)

        # 添加节点
        workflow.add_node("load_history", self._load_history)
        workflow.add_node("check_clarification", self._check_clarification)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("save_state", self._save_state)

        # 定义边
        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "check_clarification")

        # 条件路由：是否需要澄清
        workflow.add_conditional_edges(
            "check_clarification",
            self._should_clarify,
            {
                "clarify": "save_state",  # 需要澄清，直接保存状态并返回
                "continue": "execute_tools"  # 不需要澄清，继续工具选择
            }
        )

        workflow.add_edge("execute_tools", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_answer")
        workflow.add_edge("generate_answer", "save_state")
        workflow.add_edge("save_state", END)

        return workflow.compile()

    def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        scene_type: str = "risk_rule",
        top_k: int = None,
        score_threshold: float = None,
        clarification_choice: Optional[str] = None,
        use_rerank: bool = None,
        use_bm25: bool = None,
        answer_perspective: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户查询

        Args:
            query: 用户问题
            session_id: 会话 ID（可选）
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值
            clarification_choice: 用户选择的澄清选项
            use_rerank: 是否使用精排（None=按配置）
            use_bm25: 是否使用 BM25 粗排（None=按配置）
            answer_perspective: 显式回答口径

        Returns:
            查询结果
        """
        # 创建或恢复会话
        if not session_id:
            session_id = self.session_manager.create_session()
            logger.info(f"创建新会话 - session_id: {session_id}")
        else:
            # 延长会话 TTL
            self.session_manager.extend_ttl(session_id)

        # 初始化状态
        initial_state: ConversationState = {
            "session_id": session_id,
            "messages": [],
            "query": query,
            "context": "",
            "answer": "",
            "sources": [],
            "retrieved_count": 0,
            "scene_type": scene_type,
            "needs_clarification": False,
            "clarification_options": [],
            "clarification_choice": clarification_choice,
            "retrieval_metadata": None,
            "tool_calls": [],
            "tool_context": "",
            "tool_intent": None,
            "answer_perspective": answer_perspective,
        }

        # 存储检索参数（不通过 LangGraph state 传递）
        self._top_k = top_k or settings.retrieval_top_k
        self._score_threshold = score_threshold or settings.retrieval_score_threshold
        self._use_rerank = use_rerank
        self._use_bm25 = use_bm25

        # 执行工作流
        try:
            final_state = self.graph.invoke(initial_state)

            return {
                "answer": final_state["answer"],
                "sources": final_state["sources"],
                "retrieved_count": final_state["retrieved_count"],
                "session_id": session_id,
                "answer_perspective": final_state.get("answer_perspective"),
                "needs_clarification": final_state.get("needs_clarification", False),
                "clarification_options": final_state.get("clarification_options", []),
                "retrieval_metadata": final_state.get("retrieval_metadata"),
                "tool_calls": final_state.get("tool_calls", []),
                "tool_intent": final_state.get("tool_intent"),
            }

        except Exception as e:
            logger.error(f"对话处理失败 - session_id: {session_id}, error: {e}", exc_info=True)
            raise

    def process_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        scene_type: str = "risk_rule",
        top_k: int = None,
        score_threshold: float = None,
        clarification_choice: Optional[str] = None,
        use_rerank: bool = None,
        use_bm25: bool = None,
        answer_perspective: Optional[str] = None,
    ):
        """
        流式处理用户查询

        Yields:
            dict: {"type": "sources"|"chunk"|"done"|"clarification", "data": ...}
        """
        if not session_id:
            session_id = self.session_manager.create_session()
        else:
            self.session_manager.extend_ttl(session_id)

        yield {
            "type": "progress",
            "data": {
                "session_id": session_id,
                "stage": "intent",
                "message": "正在识别是否需要查询业务系统。",
            },
        }

        stream_top_k = top_k or settings.retrieval_top_k
        stream_score_threshold = score_threshold or settings.retrieval_score_threshold

        # 加载历史
        history = self.session_manager.get_conversation_history(session_id, limit=10)
        messages = []
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # 检查澄清
        effective_query = query
        tool_intent = None
        if clarification_choice:
            effective_query = self._build_clarified_query(
                session_id=session_id,
                clarification_choice=clarification_choice,
                query=query,
                scene_type=scene_type,
            )
            tool_intent = self.tool_service.inspect_intent(
                query=effective_query,
                scene_type=scene_type,
            )
            if tool_intent.get("needs_clarification"):
                answer = self._build_tool_intent_clarification_answer(tool_intent)
                self.session_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=query or clarification_choice or effective_query,
                )
                self.session_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    metadata={
                        "retrieved_count": 0,
                        "scene_type": scene_type,
                        "tool_calls": [],
                        "tool_intent": tool_intent,
                        "answer_perspective": answer_perspective,
                    },
                )
                yield {
                    "type": "clarification",
                    "data": {
                        "options": tool_intent.get("clarification_options", []),
                        "session_id": session_id,
                        "answer": answer,
                        "answer_perspective": answer_perspective,
                        "tool_intent": tool_intent,
                    },
                }
                return
        else:
            tool_intent = self.tool_service.inspect_intent(query=query, scene_type=scene_type)
            if tool_intent.get("needs_clarification"):
                answer = self._build_tool_intent_clarification_answer(tool_intent)
                self.session_manager.add_message(session_id=session_id, role="user", content=query)
                self.session_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    metadata={
                        "retrieved_count": 0,
                        "scene_type": scene_type,
                        "tool_calls": [],
                        "tool_intent": tool_intent,
                        "answer_perspective": answer_perspective,
                    },
                )
                yield {
                    "type": "clarification",
                    "data": {
                        "options": tool_intent.get("clarification_options", []),
                        "session_id": session_id,
                        "answer": answer,
                        "answer_perspective": answer_perspective,
                        "tool_intent": tool_intent,
                    },
                }
                return

            # 快速预检索
            yield {
                "type": "progress",
                "data": {
                    "session_id": session_id,
                    "stage": "retrieve",
                    "message": "正在检索规则文档，判断是否需要补充问题。",
                },
            }
            try:
                pre_result = self.rag_service.query(
                    query=query, scene_type=scene_type,
                    top_k=stream_top_k, score_threshold=0.5,
                    use_rerank=use_rerank, use_bm25=use_bm25,
                    answer_perspective=answer_perspective,
                )
                pre_docs = pre_result.get("sources", [])
            except Exception:
                pre_docs = []

            conv_history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    conv_history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    conv_history.append({"role": "assistant", "content": msg.content})

            needs_clarification, options = self.clarification_service.needs_clarification(
                query=query, conversation_history=conv_history, retrieved_docs=pre_docs
            )

            if needs_clarification and options:
                yield {
                    "type": "clarification",
                    "data": {
                        "options": options,
                        "session_id": session_id,
                        "answer_perspective": answer_perspective,
                    },
                }
                return

        # 增强查询
        enhanced_query = effective_query
        if messages:
            recent = messages[-2:]
            ctx_parts = [m.content for m in recent if isinstance(m, HumanMessage)]
            if ctx_parts:
                enhanced_query = f"上下文：{' '.join(ctx_parts)}\n当前问题：{effective_query}"

        # 流式 RAG 查询
        full_answer = ""
        sources_data = None

        if tool_intent is None:
            tool_intent = self.tool_service.inspect_intent(
                query=effective_query,
                scene_type=scene_type,
            )
        yield {
            "type": "progress",
            "data": {
                "session_id": session_id,
                "stage": "tool",
                "message": (
                    f"正在调用{tool_intent.get('label') or '业务系统接口'}。"
                    if tool_intent.get("tool_name")
                    else "未命中业务接口，继续检索知识库。"
                ),
            },
        }
        tool_calls = self.tool_service.execute_intent(tool_intent)
        tool_context = self.tool_service.format_tool_context(tool_calls)

        yield {
            "type": "progress",
            "data": {
                "session_id": session_id,
                "stage": "generate",
                "message": (
                    "已获取业务接口数据，正在结合规则文档生成解释。"
                    if tool_calls
                    else "正在结合规则文档生成回答。"
                ),
            },
        }

        for event in self.rag_service.query_stream(
            query=enhanced_query, scene_type=scene_type,
            top_k=stream_top_k, score_threshold=stream_score_threshold,
            use_rerank=use_rerank, use_bm25=use_bm25,
            tool_context=tool_context,
            answer_perspective=answer_perspective,
        ):
            if event["type"] == "sources":
                sources_data = event["data"]
                sources_data["session_id"] = session_id
                sources_data["answer_perspective"] = answer_perspective
                sources_data["tool_calls"] = tool_calls
                sources_data["tool_intent"] = tool_intent
                yield event
            elif event["type"] == "chunk":
                full_answer += event["data"]
                yield event
            elif event["type"] == "done":
                break

        # 保存会话
        self.session_manager.add_message(
            session_id=session_id,
            role="user",
            content=query or clarification_choice or effective_query,
        )
        self.session_manager.add_message(
            session_id=session_id, role="assistant", content=full_answer,
            metadata={
                "retrieved_count": sources_data.get("retrieved_count", 0) if sources_data else 0,
                "scene_type": scene_type,
                "tool_calls": tool_calls,
                "tool_intent": tool_intent,
                "answer_perspective": answer_perspective,
            }
        )

        yield {"type": "done", "data": {"session_id": session_id}}

    def _load_history(self, state: ConversationState) -> ConversationState:
        """加载对话历史"""
        session_id = state["session_id"]

        # 获取历史消息（最近 10 条）
        history = self.session_manager.get_conversation_history(
            session_id,
            limit=10
        )

        # 转换为 LangChain 消息格式
        messages = []
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        state["messages"] = messages

        logger.debug(
            f"加载对话历史 - session_id: {session_id}, "
            f"history_count: {len(messages)}"
        )

        return state

    def _execute_tools(self, state: ConversationState) -> ConversationState:
        """选择并执行业务工具。"""
        tool_intent = state.get("tool_intent")
        if tool_intent:
            tool_calls = self.tool_service.execute_intent(tool_intent)
        else:
            tool_calls = self.tool_service.maybe_execute(
                query=state["query"],
                scene_type=state["scene_type"],
            )
        state["tool_calls"] = tool_calls
        state["tool_context"] = self.tool_service.format_tool_context(tool_calls)

        if tool_calls:
            logger.info(
                "业务工具调用完成 - session_id: %s, tools: %s",
                state["session_id"],
                [call.get("name") for call in tool_calls],
            )

        return state

    def _check_clarification(self, state: ConversationState) -> ConversationState:
        """检查是否需要澄清"""
        query = state["query"]
        clarification_choice = state.get("clarification_choice")

        # 如果用户已经提供了澄清选择，跳过检查
        if clarification_choice:
            logger.debug(f"用户已提供澄清选择 - choice: {clarification_choice}")
            # 将选择合并到查询中
            state["query"] = self._build_clarified_query(
                session_id=state["session_id"],
                clarification_choice=clarification_choice,
                query=query,
                scene_type=state["scene_type"],
            )
            state["tool_intent"] = self.tool_service.inspect_intent(
                query=state["query"],
                scene_type=state["scene_type"],
            )
            if state["tool_intent"].get("needs_clarification"):
                state["needs_clarification"] = True
                state["clarification_options"] = state["tool_intent"].get(
                    "clarification_options",
                    [],
                )
                state["answer"] = self._build_tool_intent_clarification_answer(
                    state["tool_intent"],
                )
                return state

            state["needs_clarification"] = False
            state["clarification_options"] = []
            return state

        tool_intent = self.tool_service.inspect_intent(
            query=query,
            scene_type=state["scene_type"],
        )
        state["tool_intent"] = tool_intent
        if tool_intent.get("needs_clarification"):
            state["needs_clarification"] = True
            state["clarification_options"] = tool_intent.get("clarification_options", [])
            state["answer"] = self._build_tool_intent_clarification_answer(tool_intent)
            logger.info(
                "工具意图缺少必要字段 - session_id: %s, tool: %s, missing: %s",
                state["session_id"],
                tool_intent.get("tool_name"),
                tool_intent.get("missing_fields"),
            )
            return state

        # 先做一次快速检索，获取候选文档
        try:
            result = self.rag_service.query(
                query=query,
                scene_type=state["scene_type"],
                top_k=self._top_k,
                score_threshold=0.5,  # 使用较低的阈值以获取更多候选
                use_rerank=self._use_rerank,
                use_bm25=self._use_bm25,
                answer_perspective=state.get("answer_perspective"),
            )
            retrieved_docs = result.get("sources", [])
        except Exception as e:
            logger.error(f"预检索失败: {e}")
            retrieved_docs = []

        # 转换对话历史格式
        conversation_history = []
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                conversation_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                conversation_history.append({"role": "assistant", "content": msg.content})

        # 判断是否需要澄清
        needs_clarification, options = self.clarification_service.needs_clarification(
            query=query,
            conversation_history=conversation_history,
            retrieved_docs=retrieved_docs
        )

        if needs_clarification and options:
            state["needs_clarification"] = True
            state["clarification_options"] = options
            state["answer"] = "请问您想查询以下哪个方面的信息？"
            logger.info(
                f"需要澄清 - session_id: {state['session_id']}, "
                f"options: {options}"
            )
        else:
            state["needs_clarification"] = False
            state["clarification_options"] = []

        return state

    def _build_tool_intent_clarification_answer(self, tool_intent: Dict[str, Any]) -> str:
        """Build a concise clarification answer for incomplete tool intent."""
        label = tool_intent.get("label") or tool_intent.get("tool_name") or "业务接口"
        options = tool_intent.get("clarification_options") or ["请补充订单号后再查询。"]
        missing_fields = set(tool_intent.get("missing_fields") or [])
        if "tool_intent_confirmation" in missing_fields:
            return f"我不确定这个问题是否需要查询{label}。{options[0]}"
        return f"我判断这个问题需要查询{label}，但还缺少订单号。{options[0]}"

    def _build_clarified_query(
        self,
        *,
        session_id: str,
        clarification_choice: str,
        query: str,
        scene_type: str,
    ) -> str:
        """Rebuild a query after the user fills a missing clarification value."""
        choice = (clarification_choice or "").strip()
        current_query = (query or "").strip()
        previous_intent = self._get_session_tool_intent(session_id)

        if (
            previous_intent
            and previous_intent.get("scene_type") == scene_type
        ):
            missing_fields = set(previous_intent.get("missing_fields") or [])
            label = previous_intent.get("label") or previous_intent.get("tool_name") or "业务接口"
            if "order_id" in missing_fields:
                return f"订单 {choice} 的{label}"
            if "tool_intent_confirmation" in missing_fields and previous_intent.get("order_id"):
                return f"订单 {previous_intent['order_id']} 的{label}"

        if current_query:
            return f"{choice} {current_query}".strip()
        return choice

    def _get_session_tool_intent(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Read the latest session-level tool intent when the manager supports it."""
        get_session = getattr(self.session_manager, "get_session", None)
        if not callable(get_session):
            return None

        try:
            session = get_session(session_id)
        except Exception as exc:
            logger.debug("读取会话工具意图失败 - session_id: %s, error: %s", session_id, exc)
            return None

        metadata = getattr(session, "metadata", {}) if session else {}
        tool_intent = metadata.get("tool_intent") if isinstance(metadata, dict) else None
        return tool_intent if isinstance(tool_intent, dict) else None

    def _should_clarify(self, state: ConversationState) -> str:
        """判断是否需要澄清（路由函数）"""
        if state.get("needs_clarification", False):
            return "clarify"
        return "continue"

    def _retrieve_context(self, state: ConversationState) -> ConversationState:
        """检索相关文档"""
        query = state["query"]
        scene_type = state["scene_type"]

        # 如果有对话历史，构建增强查询
        enhanced_query = query
        if state["messages"]:
            # 简单策略：将最近的用户问题和当前问题拼接
            recent_messages = state["messages"][-2:]  # 最近 2 条
            context_parts = [msg.content for msg in recent_messages if isinstance(msg, HumanMessage)]
            if context_parts:
                enhanced_query = f"上下文：{' '.join(context_parts)}\n当前问题：{query}"

        logger.debug(f"增强查询 - original: {query}, enhanced: {enhanced_query}")

        # 调用 RAG 服务检索
        result = self.rag_service.query(
            query=enhanced_query,
            scene_type=scene_type,
            top_k=self._top_k,
            score_threshold=self._score_threshold,
            use_rerank=self._use_rerank,
            use_bm25=self._use_bm25,
            tool_context=state.get("tool_context", ""),
            answer_perspective=state.get("answer_perspective"),
        )

        # 更新状态
        state["answer"] = result.get("answer", "")
        state["sources"] = result.get("sources", [])
        state["retrieved_count"] = result.get("retrieved_count", 0)
        state["retrieval_metadata"] = result.get("retrieval_metadata")

        logger.debug(
            f"检索完成 - session_id: {state['session_id']}, "
            f"retrieved_count: {state['retrieved_count']}"
        )

        return state

    def _generate_answer(self, state: ConversationState) -> ConversationState:
        """生成答案"""
        # RAG 服务已经在 retrieve_context 阶段生成了答案
        # 这里只需要确保答案存在

        if not state.get("answer"):
            logger.warning("未找到预生成的答案，使用默认回复")
            state["answer"] = "抱歉，我无法回答这个问题。"

        logger.debug(
            f"答案生成完成 - session_id: {state['session_id']}, "
            f"answer_length: {len(state['answer'])}"
        )

        return state

    def _save_state(self, state: ConversationState) -> ConversationState:
        """保存会话状态"""
        session_id = state["session_id"]
        query = state["query"]
        answer = state["answer"]

        # 保存用户消息
        self.session_manager.add_message(
            session_id=session_id,
            role="user",
            content=query
        )

        # 保存助手消息
        self.session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            metadata={
                "retrieved_count": state["retrieved_count"],
                "scene_type": state["scene_type"],
                "tool_calls": state.get("tool_calls", []),
                "tool_intent": state.get("tool_intent"),
                "answer_perspective": state.get("answer_perspective"),
            }
        )

        logger.debug(f"保存会话状态 - session_id: {session_id}")

        return state


# 全局单例
_conversation_agent: Optional[ConversationAgent] = None


def get_conversation_agent() -> ConversationAgent:
    """获取对话 Agent 单例"""
    global _conversation_agent
    if _conversation_agent is None:
        _conversation_agent = ConversationAgent()
    return _conversation_agent


def reset_conversation_agent() -> None:
    """Reset conversation agent so runtime service dependencies are rebuilt."""
    global _conversation_agent
    _conversation_agent = None
