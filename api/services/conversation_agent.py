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


class ConversationAgent:
    """对话 Agent"""

    def __init__(self):
        """初始化对话 Agent"""
        self.session_manager = get_session_manager()
        self.rag_service = get_rag_service()
        self.clarification_service = get_clarification_service()
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
                "continue": "retrieve_context"  # 不需要澄清，继续检索
            }
        )

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
        use_bm25: bool = None
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
            "clarification_choice": clarification_choice
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
                "needs_clarification": final_state.get("needs_clarification", False),
                "clarification_options": final_state.get("clarification_options", [])
            }

        except Exception as e:
            logger.error(f"对话处理失败 - session_id: {session_id}, error: {e}", exc_info=True)
            raise

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

    def _check_clarification(self, state: ConversationState) -> ConversationState:
        """检查是否需要澄清"""
        query = state["query"]
        clarification_choice = state.get("clarification_choice")

        # 如果用户已经提供了澄清选择，跳过检查
        if clarification_choice:
            logger.debug(f"用户已提供澄清选择 - choice: {clarification_choice}")
            # 将选择合并到查询中
            state["query"] = f"{clarification_choice} {query}"
            state["needs_clarification"] = False
            return state

        # 先做一次快速检索，获取候选文档
        try:
            result = self.rag_service.query(
                query=query,
                scene_type=state["scene_type"],
                top_k=self._top_k,
                score_threshold=0.5,  # 使用较低的阈值以获取更多候选
                use_rerank=self._use_rerank,
                use_bm25=self._use_bm25
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
            use_bm25=self._use_bm25
        )

        # 更新状态
        state["answer"] = result.get("answer", "")
        state["sources"] = result.get("sources", [])
        state["retrieved_count"] = result.get("retrieved_count", 0)

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
                "scene_type": state["scene_type"]
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
