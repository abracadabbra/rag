"""
风控规则查询路由
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
    summary="风控规则问答",
    description="基于 RAG 检索风控规则文档并生成答案"
)
async def query_risk_rules(request: QueryRequest):
    """
    风控规则问答

    ## 请求示例

    ```json
    {
        "query": "白金卡的单笔交易限额是多少？",
        "session_id": null,
        "top_k": 5,
        "score_threshold": 0.7
    }
    ```

    ## 响应示例

    ```json
    {
        "answer": "根据规则 R001，白金卡的单笔交易限额是 50,000 元...",
        "sources": [
            {
                "score": 0.95,
                "content_preview": "白金卡单笔限额：50,000 元...",
                "rule_id": "R001",
                "rule_name": "信用卡单笔交易限额规则"
            }
        ],
        "retrieved_count": 3,
        "session_id": null
    }
    ```
    """
    # 生成请求 ID
    request_id = str(uuid.uuid4())

    logger.info(
        f"[{request_id}] 收到查询请求 - Query: {request.query[:50]}..., "
        f"Session: {request.session_id}, TopK: {request.top_k}"
    )

    try:
        import time
        start_time = time.time()

        # 获取对话 Agent
        from api.services.conversation_agent import get_conversation_agent

        agent = get_conversation_agent()

        # 执行查询（支持多轮对话和澄清机制）
        result = agent.process(
            query=request.query,
            session_id=request.session_id,
            scene_type="risk_rule",
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            clarification_choice=request.clarification_choice,
            use_rerank=request.use_rerank,
            use_bm25=request.use_bm25
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"[{request_id}] 查询成功 - Retrieved: {result['retrieved_count']}, "
            f"Session: {result['session_id']}, Time: {elapsed_ms}ms"
        )

        # 返回响应
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            retrieved_count=result["retrieved_count"],
            session_id=result["session_id"],
            needs_clarification=result.get("needs_clarification", False),
            clarification_options=result.get("clarification_options", []),
            retrieval_metadata=result.get("retrieval_metadata")
        )

    except ConnectionError as e:
        logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"服务暂时不可用，请稍后重试: {str(e)}"
        )
    except TimeoutError as e:
        logger.error(f"[{request_id}] 请求超时 - {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=504,
            detail=f"请求超时，请稍后重试: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"[{request_id}] 参数错误 - {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"请求参数错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[{request_id}] 查询失败 - Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )
