"""
会话管理路由
提供会话列表、创建、删除等 API
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from api.services.session_manager import get_session_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionSummaryResponse(BaseModel):
    """会话摘要响应"""
    session_id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str
    scene_type: Optional[str] = None


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionSummaryResponse]
    total: int


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    session_id: Optional[str] = None
    scene_type: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    message: str


class DeleteSessionResponse(BaseModel):
    """删除会话响应"""
    success: bool
    message: str


class UpdateTitleRequest(BaseModel):
    """更新标题请求"""
    title: str


@router.get("/", response_model=SessionListResponse, summary="获取会话列表")
async def list_sessions(limit: int = 50, offset: int = 0):
    """
    获取当前所有会话列表

    Query 参数:
    - limit: 返回数量限制（默认 50）
    - offset: 偏移量（默认 0）
    """
    try:
        manager = get_session_manager()
        sessions = manager.list_sessions(limit=limit, offset=offset)

        return SessionListResponse(
            sessions=[
                SessionSummaryResponse(
                    session_id=s.session_id,
                    title=s.title,
                    message_count=s.message_count,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    scene_type=s.scene_type
                )
                for s in sessions
            ],
            total=len(sessions)
        )
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/", response_model=CreateSessionResponse, summary="创建会话")
async def create_session(request: CreateSessionRequest = None):
    """
    创建新会话

    Request body:
    - session_id: 可选的会话 ID（不提供则自动生成）
    - scene_type: 场景类型
    """
    try:
        manager = get_session_manager()
        session_id = request.session_id if request else None
        new_session_id = manager.create_session(session_id=session_id)

        # 如果提供了 scene_type，更新元数据
        if request and request.scene_type:
            manager.update_metadata(new_session_id, {"scene_type": request.scene_type})

        return CreateSessionResponse(
            session_id=new_session_id,
            message="会话创建成功"
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.delete("/{session_id}", response_model=DeleteSessionResponse, summary="删除会话")
async def delete_session(session_id: str):
    """删除指定会话"""
    try:
        manager = get_session_manager()
        success = manager.delete_session(session_id)

        if success:
            return DeleteSessionResponse(success=True, message="会话删除成功")
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.patch("/{session_id}/title", response_model=DeleteSessionResponse, summary="更新会话标题")
async def update_session_title(session_id: str, request: UpdateTitleRequest):
    """更新会话标题"""
    try:
        manager = get_session_manager()
        success = manager.update_session_title(session_id, request.title)

        if success:
            return DeleteSessionResponse(success=True, message="标题更新成功")
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新标题失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新标题失败: {str(e)}")


@router.get("/{session_id}", summary="获取会话详情")
async def get_session(session_id: str):
    """获取指定会话的完整信息"""
    try:
        manager = get_session_manager()
        state = manager.get_session(session_id)

        if not state:
            raise HTTPException(status_code=404, detail="会话不存在")

        return {
            "session_id": state.session_id,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp
                }
                for m in state.messages
            ],
            "metadata": state.metadata,
            "created_at": state.created_at,
            "updated_at": state.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")
