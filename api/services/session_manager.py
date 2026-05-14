"""
会话管理器
负责会话的创建、恢复、保存和过期管理
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field

try:
    import redis
except ModuleNotFoundError:  # pragma: no cover - 仅在依赖未安装的轻量环境触发
    redis = None

from api.config import settings

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """对话消息"""
    role: str  # user / assistant
    content: str
    timestamp: str


class SessionState(BaseModel):
    """会话状态"""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class SessionSummary(BaseModel):
    """会话摘要"""
    session_id: str
    title: str = ""
    message_count: int = 0
    created_at: str
    updated_at: str
    scene_type: Optional[str] = None


class SessionManager:
    """会话管理器"""

    SESSIONS_INDEX_KEY = "sessions:index"

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        ttl: Optional[int] = None,
    ):
        """初始化会话管理器"""
        self.redis_client = redis_client or get_redis_client()
        self.ttl = ttl if ttl is not None else settings.redis_session_ttl

        logger.info(
            f"会话管理器初始化完成 - Redis: {settings.redis_host}:{settings.redis_port}, "
            f"TTL: {self.ttl}s"
        )

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        创建新会话

        Args:
            session_id: 可选的会话 ID，不提供则自动生成

        Returns:
            会话 ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        now = datetime.utcnow().isoformat()
        state = SessionState(
            session_id=session_id,
            messages=[],
            metadata={},
            created_at=now,
            updated_at=now
        )

        self._save_state(session_id, state)
        self._add_to_index(session_id, state)
        logger.info(f"创建新会话 - session_id: {session_id}")

        return session_id

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        获取会话状态

        Args:
            session_id: 会话 ID

        Returns:
            会话状态，不存在则返回 None
        """
        key = self._get_key(session_id)
        data = self.redis_client.get(key)

        if not data:
            logger.warning(f"会话不存在或已过期 - session_id: {session_id}")
            return None

        try:
            state = SessionState.model_validate_json(data)
            logger.debug(f"恢复会话 - session_id: {session_id}, messages: {len(state.messages)}")
            return state
        except Exception as e:
            logger.error(f"解析会话状态失败 - session_id: {session_id}, error: {e}")
            return None

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加消息到会话

        Args:
            session_id: 会话 ID
            role: 角色（user / assistant）
            content: 消息内容
            metadata: 可选的元数据

        Returns:
            是否成功
        """
        state = self.get_session(session_id)
        if not state:
            logger.error(f"无法添加消息，会话不存在 - session_id: {session_id}")
            return False

        # 添加消息
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        state.messages.append(message)

        # 更新元数据
        if metadata:
            state.metadata.update(metadata)

        # 更新时间戳
        state.updated_at = datetime.utcnow().isoformat()

        # 保存状态
        self._save_state(session_id, state)
        logger.debug(
            f"添加消息 - session_id: {session_id}, role: {role}, "
            f"content_length: {len(content)}"
        )

        return True

    def update_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        更新会话元数据

        Args:
            session_id: 会话 ID
            metadata: 元数据

        Returns:
            是否成功
        """
        state = self.get_session(session_id)
        if not state:
            logger.error(f"无法更新元数据，会话不存在 - session_id: {session_id}")
            return False

        state.metadata.update(metadata)
        state.updated_at = datetime.utcnow().isoformat()

        self._save_state(session_id, state)
        logger.debug(f"更新元数据 - session_id: {session_id}, metadata: {metadata}")

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        key = self._get_key(session_id)
        result = self.redis_client.delete(key)

        if result:
            logger.info(f"删除会话 - session_id: {session_id}")
        else:
            logger.warning(f"删除会话失败，会话不存在 - session_id: {session_id}")

        return bool(result)

    def extend_ttl(self, session_id: str) -> bool:
        """
        延长会话过期时间

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        key = self._get_key(session_id)
        result = self.redis_client.expire(key, self.ttl)

        if result:
            logger.debug(f"延长会话 TTL - session_id: {session_id}, ttl: {self.ttl}s")
        else:
            logger.warning(f"延长 TTL 失败，会话不存在 - session_id: {session_id}")

        return bool(result)

    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        获取对话历史

        Args:
            session_id: 会话 ID
            limit: 限制返回的消息数量（最近的 N 条）

        Returns:
            消息列表
        """
        state = self.get_session(session_id)
        if not state:
            return []

        messages = state.messages
        if limit and limit > 0:
            messages = messages[-limit:]

        return messages

    def _get_key(self, session_id: str) -> str:
        """生成 Redis key"""
        return f"session:{session_id}"

    def _add_to_index(self, session_id: str, state: SessionState):
        """将会话添加到索引"""
        summary = SessionSummary(
            session_id=session_id,
            title=state.metadata.get("title", "") or self._generate_title(state),
            message_count=len(state.messages),
            created_at=state.created_at,
            updated_at=state.updated_at,
            scene_type=state.metadata.get("scene_type")
        )
        self.redis_client.hset(self.SESSIONS_INDEX_KEY, session_id, summary.model_dump_json())
        self.redis_client.expire(self.SESSIONS_INDEX_KEY, self.ttl)

    def _remove_from_index(self, session_id: str):
        """从索引中移除会话"""
        self.redis_client.hdel(self.SESSIONS_INDEX_KEY, session_id)

    def _generate_title(self, state: SessionState) -> str:
        """生成会话标题（基于第一条用户消息）"""
        for msg in state.messages:
            if msg.role == "user":
                return msg.content[:50] + ("..." if len(msg.content) > 50 else "")
        return "新会话"

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[SessionSummary]:
        """
        获取会话列表

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            会话摘要列表
        """
        all_sessions = self.redis_client.hgetall(self.SESSIONS_INDEX_KEY)

        sessions = []
        for session_id, data in all_sessions.items():
            try:
                summary = SessionSummary.model_validate_json(data)
                sessions.append(summary)
            except Exception as e:
                logger.warning(f"解析会话摘要失败: {session_id}, {e}")

        # 按 updated_at 倒序
        sessions.sort(key=lambda x: x.updated_at, reverse=True)

        return sessions[offset:offset + limit]

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        key = self._get_key(session_id)
        result = self.redis_client.delete(key)
        self._remove_from_index(session_id)

        if result:
            logger.info(f"删除会话 - session_id: {session_id}")
        else:
            logger.warning(f"删除会话失败，会话不存在 - session_id: {session_id}")

        return bool(result)

    def update_session_title(self, session_id: str, title: str) -> bool:
        """更新会话标题"""
        state = self.get_session(session_id)
        if not state:
            return False

        state.metadata["title"] = title
        state.updated_at = datetime.utcnow().isoformat()
        self._save_state(session_id, state)
        self._add_to_index(session_id, state)
        return True

    def _save_state(self, session_id: str, state: SessionState):
        """保存会话状态到 Redis"""
        key = self._get_key(session_id)
        data = state.model_dump_json()

        self.redis_client.setex(key, self.ttl, data)


# 全局单例
_redis_client: Optional[Any] = None
_session_manager: Optional[SessionManager] = None


def get_redis_client() -> Any:
    """获取 Redis 客户端单例"""
    global _redis_client
    if _redis_client is None:
        if redis is None:
            raise ModuleNotFoundError("redis package is not installed")
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True,
        )
    return _redis_client


def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
