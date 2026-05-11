"""
仿真解读查询路由
"""

import uuid
import logging

from fastapi import APIRouter, HTTPException

from api.models import QueryRequest, QueryResponse, ErrorResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        500: {"model": ErrorResponse, "description": "服务器错误"}
    },
    summary="仿真解读问答",
    description="基于 RAG 检索仿真结果文档并生成解读"
)
async def query_simulation(request: QueryRequest):
    """
    仿真解读问答
    """
    request_id = str(uuid.uuid4())

    logger.info(
        f"[{request_id}] 收到仿真解读请求 - Query: {request.query[:50]}..., "
        f"Session: {request.session_id}"
    )

    try:
        import time
        start_time = time.time()

        from api.services.conversation_agent import get_conversation_agent

        agent = get_conversation_agent()

        result = agent.process(
            query=request.query,
            session_id=request.session_id,
            scene_type="simulation",
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            clarification_choice=request.clarification_choice
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"[{request_id}] 查询成功 - Retrieved: {result['retrieved_count']}, "
            f"Time: {elapsed_ms}ms"
        )

        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            retrieved_count=result["retrieved_count"],
            session_id=result["session_id"],
            needs_clarification=result.get("needs_clarification", False),
            clarification_options=result.get("clarification_options", [])
        )

    except ConnectionError as e:
        logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"服务暂时不可用: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] 查询失败 - Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
