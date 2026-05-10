"""
RAG 服务模块
负责检索和生成答案
"""

import logging
import time
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection
from openai import OpenAI

from api.config import settings
from ingestion.embeddings import embed_query
from api.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 服务"""

    def __init__(self):
        """初始化 RAG 服务"""
        try:
            # 连接 Milvus
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            self.collection = Collection(settings.milvus_collection)
            self.collection.load()

            logger.info(
                f"Milvus 连接成功 - Collection: {settings.milvus_collection}"
            )
        except Exception as e:
            logger.error(f"Milvus 连接失败: {e}", exc_info=True)
            raise ConnectionError(f"无法连接到 Milvus: {e}")

        try:
            # 初始化 LLM
            self.llm_client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base
            )

            logger.info(f"LLM 客户端初始化成功 - Model: {settings.openai_model}")
        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {e}", exc_info=True)
            raise ConnectionError(f"无法初始化 LLM 客户端: {e}")

        # 初始化缓存服务
        self.cache_service = get_cache_service()

        print(f"✅ RAG 服务初始化完成")
        print(f"   Milvus Collection: {settings.milvus_collection}")
        print(f"   LLM Model: {settings.openai_model}")
        print(f"   Cache Enabled: {settings.cache_enabled}")
        logger.info(
            f"RAG 服务初始化完成 - Collection: {settings.milvus_collection}, "
            f"Model: {settings.openai_model}, Cache: {settings.cache_enabled}"
        )

    def query(
        self,
        query: str,
        scene_type: str,
        top_k: int = None,
        score_threshold: float = None
    ) -> Dict[str, Any]:
        """
        执行 RAG 查询

        Args:
            query: 用户问题
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值

        Returns:
            查询结果，包含 answer 和 sources
        """
        top_k = top_k or settings.retrieval_top_k
        score_threshold = score_threshold or settings.retrieval_score_threshold

        # 0. 检查缓存
        cached_result = self.cache_service.get(
            query=query,
            scene_type=scene_type,
            top_k=top_k,
            score_threshold=score_threshold
        )
        if cached_result:
            logger.info(f"缓存命中 - query: {query[:50]}...")
            return cached_result

        # 1. 生成查询向量
        embed_start = time.time()
        query_vector = embed_query(query)
        embed_time_ms = int((time.time() - embed_start) * 1000)
        logger.debug(f"Embedding 生成耗时: {embed_time_ms}ms")

        # 2. 检索相关文档
        retrieval_start = time.time()
        search_params = {
            "metric_type": settings.retrieval_metric_type,
            "params": {"nprobe": 10}
        }

        try:
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=f'scene_type == "{scene_type}"',
                output_fields=["content", "metadata", "scene_type"]
            )
        except Exception as e:
            logger.error(f"Milvus 检索失败: {e}", exc_info=True)
            raise ConnectionError(f"向量检索失败: {e}")

        retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
        logger.debug(f"向量检索耗时: {retrieval_time_ms}ms, 返回结果数: {len(results[0])}")

        # 3. 过滤低分文档
        retrieved_docs = []
        for hit in results[0]:
            if hit.score >= score_threshold:
                retrieved_docs.append({
                    "content": hit.entity.get("content"),
                    "metadata": hit.entity.get("metadata"),
                    "score": hit.score
                })

        logger.info(
            f"检索完成 - 原始结果: {len(results[0])}, "
            f"过滤后: {len(retrieved_docs)} (阈值: {score_threshold})"
        )

        if not retrieved_docs:
            result = {
                "answer": "抱歉，我没有找到相关的信息。请尝试换一种方式提问。",
                "sources": [],
                "retrieved_count": 0
            }
            # 不缓存空结果
            return result

        # 4. 构建 Prompt
        context = self._build_context(retrieved_docs)
        prompt = self._build_prompt(query, context, scene_type)

        # 5. 调用 LLM 生成答案
        llm_start = time.time()
        answer = self._generate_answer(prompt)
        llm_time_ms = int((time.time() - llm_start) * 1000)
        logger.info(f"LLM 生成耗时: {llm_time_ms}ms")

        # 6. 构建结果
        result = {
            "answer": answer,
            "sources": self._format_sources(retrieved_docs),
            "retrieved_count": len(retrieved_docs)
        }

        # 7. 写入缓存
        self.cache_service.set(
            query=query,
            scene_type=scene_type,
            top_k=top_k,
            score_threshold=score_threshold,
            result=result
        )

        return result

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []

        for i, doc in enumerate(docs, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")

            # 添加文档来源信息
            source_info = f"【文档 {i}】"
            if metadata.get("rule_id"):
                source_info += f" 规则ID: {metadata['rule_id']}"
            if metadata.get("rule_name"):
                source_info += f" | {metadata['rule_name']}"

            context_parts.append(f"{source_info}\n{content}")

        return "\n\n---\n\n".join(context_parts)

    def _build_prompt(self, query: str, context: str, scene_type: str) -> str:
        """构建 Prompt"""
        scene_names = {
            "risk_rule": "风控规则",
            "model_card": "模型卡片",
            "simulation": "仿真结果",
            "profit": "毛利抽成"
        }

        scene_name = scene_names.get(scene_type, scene_type)

        prompt = f"""你是一个专业的{scene_name}问答助手。请基于以下文档内容回答用户的问题。

## 文档内容

{context}

## 用户问题

{query}

## 回答要求

1. 准确引用文档中的信息，不要编造内容
2. 如果文档中没有相关信息，明确告知用户
3. 回答要简洁明了，重点突出
4. 如果涉及多个规则或文档，请分点说明
5. 在回答末尾注明信息来源（文档编号）

请开始回答："""

        return prompt

    def _generate_answer(self, prompt: str) -> str:
        """调用 LLM 生成答案"""
        try:
            response = self.llm_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
                timeout=30.0
            )

            # 记录 Token 消耗
            usage = response.usage
            logger.info(
                f"LLM Token 消耗 - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}"
            )

            return response.choices[0].message.content

        except TimeoutError as e:
            logger.error(f"LLM 调用超时: {e}")
            raise TimeoutError(f"LLM 响应超时，请稍后重试")
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            # 检查是否是 API Key 问题
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                raise ConnectionError(f"OpenAI API 认证失败，请检查 API Key")
            raise ConnectionError(f"LLM 调用失败: {e}")

    def _format_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化来源信息"""
        sources = []

        for doc in docs:
            metadata = doc.get("metadata", {})
            source = {
                "score": round(doc.get("score", 0), 4),
                "content_preview": doc.get("content", "")[:200] + "..."
            }

            # 添加元数据
            if metadata.get("rule_id"):
                source["rule_id"] = metadata["rule_id"]
            if metadata.get("rule_name"):
                source["rule_name"] = metadata["rule_name"]
            if metadata.get("source"):
                source["file_path"] = metadata["source"]
            if metadata.get("chunk_index") is not None:
                source["chunk_index"] = metadata["chunk_index"]

            sources.append(source)

        return sources


# 全局单例
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
