"""
通用场景查询路由 — 合并风控规则、模型卡片、仿真解读、毛利抽成
"""

import uuid
import time
import json
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from api.models import QueryRequest, QueryResponse, ErrorResponse
from api.security.business_tools import BUSINESS_TOOL_TOKEN_HEADER, require_business_tool_access

router = APIRouter()
logger = logging.getLogger(__name__)

SCENE_META = {
    "risk_rule": {"label": "风控规则", "route": "risk-rules"},
    "model_card": {"label": "模型卡片", "route": "model-cards"},
    "simulation": {"label": "仿真解读", "route": "simulation"},
    "profit": {"label": "毛利抽成", "route": "profit"},
}

SCENE_ALIASES = {
    "risk-rules": "risk_rule",
    "model-cards": "model_card",
}


def normalize_scene_type(scene_type: str) -> str:
    """Normalize legacy route names to canonical scene keys."""
    return SCENE_ALIASES.get(scene_type, scene_type)


@router.post(
    "/{scene_type}/query",
    response_model=QueryResponse,
    responses={500: {"model": ErrorResponse, "description": "服务器错误"}},
    summary="场景问答",
    description="基于 RAG 检索指定场景文档并生成答案"
)
async def query_scene(
    scene_type: str,
    request: QueryRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    scene_type = normalize_scene_type(scene_type)
    meta = SCENE_META.get(scene_type)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"未知场景类型: {scene_type}，支持: {list(SCENE_META.keys())}"
        )
    require_business_tool_access(
        scene_type=scene_type,
        token=x_business_tool_token,
        scope="execute",
    )

    request_id = str(uuid.uuid4())
    label = meta["label"]

    logger.info(
        f"[{request_id}] {label}查询 - Query: {request.query[:50]}..., "
        f"Session: {request.session_id}, TopK: {request.top_k}"
    )

    try:
        start_time = time.time()

        from api.services.conversation_agent import get_conversation_agent
        agent = get_conversation_agent()

        result = await run_in_threadpool(
            agent.process,
            query=request.query,
            session_id=request.session_id,
            scene_type=scene_type,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            clarification_choice=request.clarification_choice,
            use_rerank=request.use_rerank,
            use_bm25=request.use_bm25,
            answer_perspective=request.answer_perspective,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"[{request_id}] {label}查询成功 - Retrieved: {result['retrieved_count']}, "
            f"Session: {result['session_id']}, Time: {elapsed_ms}ms"
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
        raise HTTPException(
            status_code=503,
            detail=f"服务暂时不可用，请稍后重试或联系系统管理员。请求ID: {request_id}",
        )
    except TimeoutError as e:
        logger.error(f"[{request_id}] 请求超时 - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=504,
            detail=f"请求超时，请稍后重试或联系系统管理员。请求ID: {request_id}",
        )
    except ValueError as e:
        logger.error(f"[{request_id}] 参数错误 - {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"请求参数错误，请检查输入后重试。请求ID: {request_id}",
        )
    except Exception as e:
        logger.error(f"[{request_id}] {label}查询失败 - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询失败，请稍后重试或联系系统管理员。请求ID: {request_id}",
        )


@router.post(
    "/{scene_type}/query-stream",
    summary="场景问答 (SSE 流式)",
    description="流式返回答案，逐步推送文本块"
)
async def query_scene_stream(
    scene_type: str,
    request: QueryRequest,
    x_business_tool_token: Optional[str] = Header(
        default=None,
        alias=BUSINESS_TOOL_TOKEN_HEADER,
    ),
):
    scene_type = normalize_scene_type(scene_type)
    meta = SCENE_META.get(scene_type)
    if not meta:
        raise HTTPException(status_code=404, detail=f"未知场景类型: {scene_type}")
    require_business_tool_access(
        scene_type=scene_type,
        token=x_business_tool_token,
        scope="execute",
    )

    request_id = str(uuid.uuid4())
    label = meta["label"]

    logger.info(f"[{request_id}] {label}流式查询 - Query: {request.query[:50]}...")

    async def event_generator():
        try:
            from api.services.conversation_agent import get_conversation_agent
            agent = get_conversation_agent()

            generator = agent.process_stream(
                query=request.query,
                session_id=request.session_id,
                scene_type=scene_type,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
                clarification_choice=request.clarification_choice,
                use_rerank=request.use_rerank,
                use_bm25=request.use_bm25,
                answer_perspective=request.answer_perspective,
            )
            async for event in iterate_in_threadpool(generator):
                event_type = event["type"]
                data = json.dumps(event["data"], ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"

        except Exception as e:
            logger.error(f"[{request_id}] 流式查询失败: {e}", exc_info=True)
            error_data = json.dumps(
                {
                    "error": "流式查询失败，请稍后重试或联系系统管理员。",
                    "error_type": type(e).__name__,
                    "request_id": request_id,
                },
                ensure_ascii=False,
            )
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
