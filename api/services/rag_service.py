"""
RAG 服务模块
负责检索和生成答案
支持: 向量检索 + BM25 粗排 + BGE-reranker 精排
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI

from api.config import settings
from ingestion.embeddings import embed_query
from ingestion.milvus_client import get_milvus_client
from api.services.cache_service import get_cache_service
from api.services.bm25_service import get_bm25_indexer, compute_bm25_scores_dynamic
from api.services.rerank_service import get_reranker
from api.services.hybrid_search import reciprocal_rank_fusion, hybrid_search
from api.routers.config import get_hot_config
from api.services.prompt_templates import build_scene_prompt

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 服务"""

    def _connect_milvus(self):
        """连接 Milvus（支持 Server 和 Lite 自动切换）"""
        try:
            from ingestion.embeddings import get_embedding_generator
            gen = get_embedding_generator()
            test_vec = gen.embed_query("test")
            dimension = len(test_vec)

            self.milvus_client = get_milvus_client(
                host=settings.milvus_host,
                port=settings.milvus_port,
                collection_name=settings.milvus_collection,
                dimension=dimension
            )
            self.collection_name = settings.milvus_collection

            logger.info(
                f"Milvus 连接成功 - Collection: {settings.milvus_collection}"
            )
        except Exception as e:
            logger.error(f"Milvus 连接失败: {e}", exc_info=True)
            raise ConnectionError(f"无法连接到 Milvus: {e}")

    def __init__(self):
        """初始化 RAG 服务"""
        self._connect_milvus()
        self.cache_service = get_cache_service()

        try:
            # 初始化 LLM（根据配置的 provider）
            if settings.llm_provider == "minimax":
                self.llm_client = OpenAI(
                    api_key=settings.minimax_api_key,
                    base_url=settings.minimax_api_base
                )
                self.llm_model = settings.minimax_model
                logger.info(f"MiniMax LLM 客户端初始化 - Model: {self.llm_model}")
            elif settings.llm_provider == "openai":
                self.llm_client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_api_base
                )
                self.llm_model = settings.openai_model
                logger.info(f"OpenAI LLM 客户端初始化 - Model: {self.llm_model}")
            elif settings.llm_provider == "local":
                self.llm_client = OpenAI(
                    api_key="dummy",  # 本地模型不需要真实 key
                    base_url=settings.local_llm_base_url
                )
                self.llm_model = settings.local_llm_model
                logger.info(f"本地 LLM 客户端初始化 - Model: {self.llm_model}")
            else:
                raise ValueError(f"未知的 LLM Provider: {settings.llm_provider}")
        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {e}", exc_info=True)
            raise ConnectionError(f"无法初始化 LLM 客户端: {e}")

        print(f"✅ RAG 服务初始化完成")
        print(f"   Milvus Collection: {settings.milvus_collection}")
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   LLM Model: {self.llm_model}")
        print(f"   Cache Enabled: {settings.cache_enabled}")
        logger.info(
            f"RAG 服务初始化完成 - Collection: {settings.milvus_collection}, "
            f"Provider: {settings.llm_provider}, Model: {self.llm_model}, Cache: {settings.cache_enabled}"
        )

    def query(
        self,
        query: str,
        scene_type: str,
        top_k: int = None,
        score_threshold: float = None,
        use_rerank: bool = None,
        use_bm25: bool = None,
        tool_context: str = "",
        answer_perspective: str = None,
    ) -> Dict[str, Any]:
        """
        执行 RAG 查询

        Args:
            query: 用户问题
            scene_type: 场景类型
            top_k: 返回文档数量
            score_threshold: 相似度阈值
            use_rerank: 是否使用精排（None=按配置）
            use_bm25: 是否使用 BM25 粗排（None=按配置）
            tool_context: 业务工具返回的结构化上下文
            answer_perspective: 显式回答口径；None 时自动推断

        Returns:
            查询结果，包含 answer 和 sources
        """
        top_k = top_k or get_hot_config("retrieval_top_k") or settings.retrieval_top_k
        score_threshold = score_threshold or get_hot_config("retrieval_score_threshold") or settings.retrieval_score_threshold
        use_rerank = use_rerank if use_rerank is not None else (get_hot_config("enable_rerank") if get_hot_config("enable_rerank") is not None else settings.enable_rerank)
        use_bm25 = use_bm25 if use_bm25 is not None else (get_hot_config("enable_bm25") if get_hot_config("enable_bm25") is not None else getattr(settings, 'enable_bm25', False))

        # 0. 检查缓存
        if not tool_context:
            cached_result = self.cache_service.get(
                query=query,
                scene_type=scene_type,
                top_k=top_k,
                score_threshold=score_threshold,
                answer_perspective=answer_perspective,
            )
            if cached_result:
                logger.info(f"缓存命中 - query: {query[:50]}...")
                return cached_result

        # 1. 生成查询向量
        embed_start = time.time()
        query_vector = embed_query(query)
        embed_time_ms = int((time.time() - embed_start) * 1000)
        total_start = embed_start  # 记录总开始时间

        # 2. 向量检索
        vector_search_start = time.time()
        search_params = {
            "metric_type": settings.retrieval_metric_type,
            "params": {"nprobe": 10}
        }

        try:
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k * 5 if use_rerank else top_k * 2,
                output_fields=["content", "metadata", "scene_type"],
                search_params={"metric_type": settings.retrieval_metric_type}
            )
        except Exception as e:
            logger.error(f"Milvus 检索失败: {e}", exc_info=True)
            raise ConnectionError(f"向量检索失败: {e}")

        vector_search_time_ms = int((time.time() - vector_search_start) * 1000)

        # 转换为统一格式
        vector_docs = []
        for hit in results[0]:
            entity = hit.get("entity", hit)
            vector_docs.append({
                "content": entity.get("content"),
                "metadata": self._normalize_metadata(entity.get("metadata", {})),
                "scene_type": entity.get("scene_type"),
                "score": hit.get("distance", 0),
                "id": hit.get("id")
            })

        # 过滤 scene_type，避免跨业务场景引用来源文档
        vector_docs = self._filter_docs_by_scene(vector_docs, scene_type)

        # 初始化各阶段耗时变量
        bm25_time_ms = 0
        fusion_time_ms = 0
        rerank_time_ms = 0
        llm_time_ms = 0

        # 3. BM25 粗排（可选）
        bm25_docs = []
        if use_bm25:
            bm25_start = time.time()
            try:
                bm25_indexer = get_bm25_indexer()
                bm25_results = bm25_indexer.search(
                    query=query,
                    scene_type=scene_type,
                    top_k=top_k * 3
                )
                bm25_docs = bm25_results
                bm25_time_ms = int((time.time() - bm25_start) * 1000)
                logger.debug(f"BM25 检索耗时: {bm25_time_ms}ms, 返回结果数: {len(bm25_docs)}")
            except Exception as e:
                logger.warning(f"BM25 检索失败: {e}")

        # 4. 混合检索融合（向量 + BM25）
        if bm25_docs:
            # 使用 RRF 融合
            fusion_start = time.time()
            fused_docs = reciprocal_rank_fusion([vector_docs, bm25_docs], k=60)

            # 过滤低于阈值的文档
            retrieved_docs = []
            for doc in fused_docs:
                # 使用向量分数或混合分数判断
                score = doc.get("rrf_score", doc.get("score", 0))
                if score >= score_threshold * 0.01:  # RRF 阈值大幅放宽
                    retrieved_docs.append(doc)

            fusion_time_ms = int((time.time() - fusion_start) * 1000)
            logger.debug(f"混合融合耗时: {fusion_time_ms}ms, 融合后结果数: {len(retrieved_docs)}")
        else:
            # 仅向量检索 - 不过滤，返回所有
            retrieved_docs = vector_docs

        logger.info(
            f"粗排完成 - 向量结果: {len(vector_docs)}, BM25结果: {len(bm25_docs)}, "
            f"融合后: {len(retrieved_docs)}"
        )

        if not retrieved_docs and not tool_context:
            result = {
                "answer": "抱歉，我没有找到相关的信息。请尝试换一种方式提问。",
                "sources": [],
                "retrieved_count": 0,
                "retrieval_metadata": {
                    "vector_count": len(vector_docs),
                    "bm25_count": len(bm25_docs),
                    "final_count": 0,
                    "used_rerank": bool(use_rerank and rerank_time_ms > 0),
                    "used_bm25": bool(use_bm25 and bm25_docs)
                }
            }
            total_time_ms = int((time.time() - total_start) * 1000)
            logger.info(
                f"查询完成（无结果）- 总耗时: {total_time_ms}ms, "
                f"各阶段: embedding={embed_time_ms}ms, 向量检索={vector_search_time_ms}ms, "
                f"BM25={bm25_time_ms}ms, 融合={fusion_time_ms}ms"
            )
            return result

        # 5. 精排（可选）- BGE Reranker
        rerank_top_k = get_hot_config("rerank_top_k") or settings.rerank_top_k
        if use_rerank and len(retrieved_docs) > 1:
            rerank_start = time.time()
            try:
                reranker = get_reranker()
                reranked_docs = reranker.rerank(
                    query=query,
                    documents=retrieved_docs,
                    top_k=rerank_top_k
                )
                retrieved_docs = reranked_docs

                rerank_time_ms = int((time.time() - rerank_start) * 1000)
                logger.info(f"精排完成 - 输入: {len(retrieved_docs)}, 输出: {len(reranked_docs)}, 耗时: {rerank_time_ms}ms")
            except Exception as e:
                logger.warning(f"精排失败: {e}")

        # 限制最终返回数量
        retrieved_docs = retrieved_docs[:top_k]

        # 6. 构建 Prompt
        context = self._build_context(retrieved_docs)
        prompt = self._build_prompt(
            query,
            context,
            scene_type,
            tool_context=tool_context,
            answer_perspective=answer_perspective,
        )

        # 7. 调用 LLM 生成答案
        llm_start = time.time()
        try:
            answer = self._generate_answer(prompt)
        except (ConnectionError, TimeoutError) as exc:
            if not tool_context:
                raise
            logger.warning(
                "LLM generation failed after business tool context; using fallback answer - error_type=%s",
                type(exc).__name__,
            )
            answer = self._build_tool_context_fallback_answer(tool_context)
        llm_time_ms = int((time.time() - llm_start) * 1000)

        # 8. 构建结果
        result = {
            "answer": answer,
            "sources": self._format_sources(retrieved_docs),
            "retrieved_count": len(retrieved_docs),
            "retrieval_metadata": {
                "vector_count": len(vector_docs),
                "bm25_count": len(bm25_docs),
                "final_count": len(retrieved_docs),
                "used_rerank": bool(use_rerank and rerank_time_ms > 0),
                "used_bm25": bool(use_bm25 and bm25_docs)
            }
        }

        # 9. 写入缓存
        if not tool_context:
            self.cache_service.set(
                query=query,
                scene_type=scene_type,
                top_k=top_k,
                score_threshold=score_threshold,
                result=result,
                answer_perspective=answer_perspective,
            )

        # 10. 记录完整耗时
        total_time_ms = int((time.time() - total_start) * 1000)
        retrieval_time_ms = vector_search_time_ms + bm25_time_ms + fusion_time_ms + rerank_time_ms

        logger.info(
            f"查询完成 - 总耗时: {total_time_ms}ms, "
            f"各阶段: embedding={embed_time_ms}ms, "
            f"检索={retrieval_time_ms}ms (向量={vector_search_time_ms}, BM25={bm25_time_ms}, 融合={fusion_time_ms}, 精排={rerank_time_ms}), "
            f"LLM={llm_time_ms}ms"
        )

        return result

    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []

        for i, doc in enumerate(docs, 1):
            metadata = self._normalize_metadata(doc.get("metadata", {}))
            content = doc.get("content", "")

            # 添加文档来源信息
            source_info = f"【文档 {i}】"
            if metadata.get("rule_id"):
                source_info += f" 规则ID: {metadata['rule_id']}"
            if metadata.get("rule_name"):
                source_info += f" | {metadata['rule_name']}"

            context_parts.append(f"{source_info}\n{content}")

        return "\n\n---\n\n".join(context_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        scene_type: str,
        tool_context: str = "",
        answer_perspective: str = None,
    ) -> str:
        """构建 Prompt"""
        return build_scene_prompt(
            query=query,
            context=context,
            scene_type=scene_type,
            tool_context=tool_context,
            answer_perspective=answer_perspective,
        )

    def _generate_answer_stream(self, prompt: str):
        """调用 LLM 流式生成答案，逐块 yield"""
        try:
            stream = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
                timeout=30.0,
                stream=True
            )

            full_answer = ""
            for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None)
                if content:
                    full_answer += content
                    yield content

            logger.info(f"LLM 流式生成完成 - length: {len(full_answer)}")

        except TimeoutError as e:
            logger.error(f"LLM 流式调用超时: {e}")
            raise TimeoutError(f"LLM 响应超时，请稍后重试")
        except Exception as e:
            logger.error(f"LLM 流式调用失败: {e}", exc_info=True)
            raise ConnectionError(f"LLM 调用失败: {e}")

    def query_stream(
        self,
        query: str,
        scene_type: str = "risk_rule",
        top_k: int = None,
        score_threshold: float = None,
        use_rerank: bool = None,
        use_bm25: bool = None,
        tool_context: str = "",
        answer_perspective: str = None,
    ):
        """
        流式 RAG 查询 — 检索完成后逐块 yield 答案

        Yields:
            dict: {"type": "sources", "data": {...}} 或 {"type": "chunk", "data": "..."}
        """
        top_k = top_k or get_hot_config("retrieval_top_k") or settings.retrieval_top_k
        score_threshold = score_threshold or get_hot_config("retrieval_score_threshold") or settings.retrieval_score_threshold
        use_rerank = use_rerank if use_rerank is not None else (get_hot_config("enable_rerank") if get_hot_config("enable_rerank") is not None else settings.enable_rerank)
        use_bm25 = use_bm25 if use_bm25 is not None else (get_hot_config("enable_bm25") if get_hot_config("enable_bm25") is not None else getattr(settings, 'enable_bm25', False))

        # 1-6: 检索流程与 query() 相同
        query_vector = embed_query(query)

        vector_docs = []
        bm25_docs = []
        try:
            results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[query_vector],
                limit=top_k * 5 if use_rerank else top_k * 2,
                output_fields=["content", "metadata", "scene_type"],
                search_params={"metric_type": settings.retrieval_metric_type}
            )
            if results and results[0]:
                for hit in results[0]:
                    entity = hit.get("entity", {})
                    doc = {
                        "content": entity.get("content", ""),
                        "metadata": self._normalize_metadata(entity.get("metadata", {})),
                        "scene_type": entity.get("scene_type", ""),
                        "score": hit.get("distance", 0)
                    }
                    vector_docs.append(doc)
        except Exception as e:
            logger.error(f"Milvus 检索失败: {e}")
            raise ConnectionError(f"向量检索失败: {e}")

        vector_docs = self._filter_docs_by_scene(vector_docs, scene_type)
        retrieved_docs = list(vector_docs)

        # BM25
        if use_bm25:
            try:
                from api.services.bm25_service import get_bm25_service
                bm25_svc = get_bm25_service()
                bm25_results = bm25_svc.search(query=query, scene_type=scene_type, top_k=top_k * 2)
                bm25_docs = bm25_results
                if bm25_docs:
                    from api.services.hybrid_search import get_hybrid_search
                    hybrid = get_hybrid_search()
                    retrieved_docs = hybrid.reciprocal_rank_fusion(vector_docs, bm25_docs, top_k=top_k * 3)
                    retrieved_docs = self._filter_docs_by_scene(retrieved_docs, scene_type)
            except Exception as e:
                logger.warning(f"BM25 检索失败: {e}")

        # Rerank
        if use_rerank and len(retrieved_docs) > top_k:
            try:
                from api.services.rerank_service import get_rerank_service
                reranker = get_rerank_service()
                reranked = reranker.rerank(query=query, documents=retrieved_docs, top_k=top_k)
                if reranked:
                    retrieved_docs = self._filter_docs_by_scene(reranked, scene_type)
            except Exception as e:
                logger.warning(f"精排失败: {e}")

        retrieved_docs = retrieved_docs[:top_k]

        # 构建 prompt
        context = self._build_context(retrieved_docs)
        prompt = self._build_prompt(
            query,
            context,
            scene_type,
            tool_context=tool_context,
            answer_perspective=answer_perspective,
        )

        # 先 yield 来源信息
        sources = self._format_sources(retrieved_docs)
        yield {
            "type": "sources",
            "data": {
                "sources": sources,
                "retrieved_count": len(retrieved_docs),
                "retrieval_metadata": {
                    "vector_count": len(vector_docs),
                    "bm25_count": len(bm25_docs),
                    "final_count": len(retrieved_docs),
                    "used_rerank": bool(use_rerank and retrieved_docs != vector_docs),
                    "used_bm25": bool(use_bm25 and bm25_docs)
                }
            }
        }

        # 流式生成答案
        try:
            for chunk_text in self._generate_answer_stream(prompt):
                yield {"type": "chunk", "data": chunk_text}
        except (ConnectionError, TimeoutError) as exc:
            if not tool_context:
                raise
            logger.warning(
                "LLM stream failed after business tool context; using fallback answer - error_type=%s",
                type(exc).__name__,
            )
            yield {
                "type": "chunk",
                "data": self._build_tool_context_fallback_answer(tool_context),
            }

        yield {"type": "done", "data": ""}

    def _generate_answer(self, prompt: str) -> str:
        """调用 LLM 生成答案"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
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
            metadata = self._normalize_metadata(doc.get("metadata", {}))

            # 判断来源类型
            if "rerank_score" in doc:
                source_type = "rerank"
            elif "rrf_score" in doc:
                source_type = "bm25"
            else:
                source_type = "vector"

            source = {
                "score": round(doc.get("rerank_score") or doc.get("rrf_score") or doc.get("score", 0), 4),
                "content_preview": doc.get("content", "")[:200] + "...",
                "source_type": source_type
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
            if doc.get("scene_type"):
                source["scene_type"] = doc["scene_type"]

            sources.append(source)

        return sources

    def _filter_docs_by_scene(
        self,
        docs: List[Dict[str, Any]],
        scene_type: str,
    ) -> List[Dict[str, Any]]:
        """Keep only documents that explicitly belong to the requested scene."""
        return [doc for doc in docs if doc.get("scene_type") == scene_type]

    def corpus_scene_status(self, scene_types: List[str]) -> Dict[str, Any]:
        """Return safe corpus availability metadata for requested scenes."""
        scene_status: Dict[str, Any] = {}
        for scene_type in scene_types:
            try:
                rows = self.milvus_client.query(
                    collection_name=self.collection_name,
                    filter=f'scene_type == "{scene_type}"',
                    output_fields=["id", "scene_type"],
                    limit=1,
                )
                count = len(rows or [])
                scene_status[scene_type] = {
                    "available": count > 0,
                    "sample_count": count,
                    "error_type": None,
                }
            except Exception as exc:
                logger.warning(
                    "Corpus scene readiness check failed - scene_type=%s, error_type=%s",
                    scene_type,
                    type(exc).__name__,
                )
                scene_status[scene_type] = {
                    "available": False,
                    "sample_count": 0,
                    "error_type": type(exc).__name__,
                }

        return {
            "collection_name": self.collection_name,
            "scenes": scene_status,
        }

    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Normalize metadata from Milvus/BM25 into a dict."""
        if isinstance(metadata, dict):
            return metadata
        if isinstance(metadata, str):
            try:
                parsed = json.loads(metadata)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _build_tool_context_fallback_answer(self, tool_context: str) -> str:
        """Return a useful answer when business data exists but the LLM is unavailable."""
        source_summary = ""
        if "链路来源: 接口原生链路" in tool_context:
            source_summary = "当前钱流链路来源：接口原生链路。\n"
        elif "链路来源: 自动派生链路" in tool_context:
            source_summary = "当前钱流链路来源：自动派生链路。\n"
        formula_summary = self._extract_profit_formula_audit_summary(tool_context)
        risk_summary = self._extract_risk_evidence_summary(tool_context)

        return (
            "业务系统接口数据已返回，但 LLM 暂时不可用，以下为可验证的系统接口摘要。\n\n"
            f"{source_summary}"
            f"{formula_summary}"
            f"{risk_summary}"
            f"{tool_context}\n\n"
            "请以系统接口数据为准；文档解释和更完整的自然语言分析可在 LLM 恢复后重新生成。"
        )

    def _extract_profit_formula_audit_summary(self, tool_context: str) -> str:
        """Surface the profit formula check near the top of fallback answers."""
        for line in (tool_context or "").splitlines():
            line = line.strip()
            if line.startswith("毛利公式核对:"):
                return f"毛利公式核对结果：{line.removeprefix('毛利公式核对:').strip()}\n"
        return ""

    def _extract_risk_evidence_summary(self, tool_context: str) -> str:
        """Surface the risk evidence summary near the top of fallback answers."""
        for line in (tool_context or "").splitlines():
            line = line.strip()
            if line.startswith("风控证据摘要:"):
                return f"风控证据摘要结果：{line.removeprefix('风控证据摘要:').strip()}\n"
        return ""


# 全局单例
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
