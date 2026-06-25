"""
毛利抽成查询路由
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from starlette.concurrency import run_in_threadpool

from api.models import QueryRequest, QueryResponse, ErrorResponse
from api.security.business_tools import BUSINESS_TOOL_TOKEN_HEADER, require_business_tool_access

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        500: {"model": ErrorResponse, "description": "服务器错误"}
    },
    summary="毛利抽成问答",
    description="基于 RAG 检索毛利抽成规则并生成答案"
)
async def query_profit(
    request: QueryRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    """
    毛利抽成问答
    """
    request_id = str(uuid.uuid4())
    require_business_tool_access(
        scene_type="profit",
        token=x_business_tool_token,
        scope="execute",
    )

    logger.info(
        f"[{request_id}] 收到毛利抽成请求 - Query: {request.query[:50]}..., "
        f"Session: {request.session_id}"
    )

    try:
        import time
        start_time = time.time()

        from api.services.conversation_agent import get_conversation_agent

        agent = get_conversation_agent()

        result = await run_in_threadpool(
            agent.process,
            query=request.query,
            session_id=request.session_id,
            scene_type="profit",
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            clarification_choice=request.clarification_choice,
            use_rerank=request.use_rerank,
            use_bm25=request.use_bm25,
            answer_perspective=request.answer_perspective,
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
            answer_perspective=result.get("answer_perspective"),
            needs_clarification=result.get("needs_clarification", False),
            clarification_options=result.get("clarification_options", []),
            retrieval_metadata=result.get("retrieval_metadata"),
            tool_calls=result.get("tool_calls", []),
            tool_intent=result.get("tool_intent"),
        )

    except ConnectionError as e:
        logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"服务暂时不可用: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] 查询失败 - Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
