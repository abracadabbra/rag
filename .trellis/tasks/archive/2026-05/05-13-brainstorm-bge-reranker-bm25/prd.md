# brainstorm: BGE-reranker 精排 + BM25 粗排接入

## Goal

在现有 RAG 系统中接入 BGE-reranker 精排模块 + BM25 粗排/混合检索，提升检索质量。

## What I already know

* 现有 RAG 流程: Embedding → Milvus ANN search → score_threshold 过滤 → LLM
* 后端: FastAPI + LangChain + Milvus + Redis
* 现有 Embedding: sentence-transformers / FlagEmbedding
* 精排候选: BGE-reranker-v1.5（本地部署，与现有 FlagEmbedding 生态一致）
* 粗排方案: BM25 混合检索补充向量检索

## Assumptions (temporary)

* BGE-reranker 将本地部署，不走 API
* BM25 使用 rank_bm25 库实现
* 混合检索策略：向量检索 + BM25 分数融合

## Open Questions

* ~~BM25 索引策略~~ → **预构建 + 动态计算 fallback**

## Requirements (evolving)

* [ ] BGE-reranker 精排模块封装（配置已预留: rerank_model, rerank_top_k）
* [ ] BM25 预构建索引（文档摄入时建立，存储到本地文件）
* [ ] BM25 动态计算 fallback（查询时实时计算）
* [ ] 混合检索策略：向量检索 + BM25 分数融合（RRF）
* [ ] RAG 查询流程改造：向量检索 → 混合粗排 → 精排 → LLM
* [ ] 配置项: enable_rerank, enable_bm25, rerank_top_k, bm25_top_k, fusion_weight

## Acceptance Criteria (evolving)

* [ ] 精排模块可独立调用，返回重排序后的文档
* [ ] BM25 预构建索引在文档摄入时生成
* [ ] 查询时 BM25 + 向量检索结果通过 RRF 融合
* [ ] 混合检索结果 > 单一向量检索（人工抽检）
* [ ] 可通过配置开关切换: enable_rerank, enable_bm25
* [ ] 精排延迟 < 500ms（20 个候选文档）

## Definition of Done (team quality bar)

* 代码实现完整（精排 + BM25 + 混合检索）
* 单元测试覆盖核心逻辑
* 集成到现有 rag_service.py，不破坏现有流程
* 可通过配置开关切换是否启用

## Out of Scope (explicit)

* ColBERT 等更复杂的粗排方案
* 多阶段级联检索（暂只做两层：混合粗排 → 精排）
* 精排模型的微调训练

## Decision (ADR-lite)

**Context**: 需要在现有 RAG 流程中加入粗排和精排，提升检索质量
**Decision**: BM25 预构建索引为主，动态计算为 fallback；精排用 BGE-reranker
**Consequences**: 需要新增 BM25 索引存储；查询流程增加 2 个阶段

## Technical Notes

* 已有配置: `enable_rerank`, `rerank_model: BAAI/bge-reranker-v2-m3`, `rerank_top_k: 3`
* 现有 Embedding: FlagEmbedding BGEM3FlagModel
* BGE-reranker: https://huggingface.co/BAAI/bge-reranker-v2-m3
* rank_bm25: https://github.com/dorianbrown/rank_bm25
* 相关文件:
  - `api/services/rag_service.py` - 现有 RAG 流程
  - `ingestion/embeddings.py` - Embedding 相关
  - `api/config.py` - 配置管理
