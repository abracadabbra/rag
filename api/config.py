"""
RAG 系统配置管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # ==================== 应用配置 ====================
    app_name: str = "RAG System"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # ==================== API 配置 ====================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ==================== Milvus 配置 ====================
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_user: str = ""
    milvus_password: str = ""
    milvus_collection: str = "unified_docs"

    # ==================== Redis 配置 ====================
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_session_ttl: int = 1800  # 30分钟

    # ==================== LLM 配置 ====================
    # MiniMax (通过 aicodee 代理)
    minimax_api_key: str = ""
    minimax_api_base: str = "https://v2.aicodee.com/v1"
    minimax_model: str = "MiniMax-M2.7-highspeed"

    # OpenAI (备选)
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # 本地 LLM
    local_llm_enabled: bool = False
    local_llm_base_url: str = "http://localhost:11434"
    local_llm_model: str = "qwen2.5:72b"

    # 当前使用的 LLM Provider: minimax / openai / local
    llm_provider: str = "minimax"

    # ==================== Embedding 配置 ====================
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32

    # OpenAI Embedding
    use_openai_embedding: bool = False
    openai_embedding_model: str = "text-embedding-3-small"

    # Sentence Transformer Embedding
    use_sentence_transformer: bool = False
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    # ==================== 检索配置 ====================
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.7
    retrieval_metric_type: str = "IP"

    # Rerank
    enable_rerank: bool = False
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_top_k: int = 3

    # BM25 粗排
    enable_bm25: bool = False
    bm25_index_dir: str = "data/bm25_index"

    # ==================== 缓存配置 ====================
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 小时

    # ==================== 开发配置 ====================
    use_mock_data: bool = False

    # ==================== 日志配置 ====================
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/rag_system.log"

    # ==================== 监控配置 ====================
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "rag-system"

    enable_metrics: bool = False
    metrics_port: int = 9090

    # ==================== 数据摄入配置 ====================
    chunk_size: int = 500
    chunk_overlap: int = 50
    supported_formats: list[str] = ["md", "pdf", "docx", "txt"]

    # ==================== 业务系统 API ====================
    simulation_api_base_url: str = ""
    simulation_api_key: str = ""
    simulation_api_timeout: int = 30

    profit_db_host: str = "localhost"
    profit_db_port: int = 5432
    profit_db_name: str = "profit_db"
    profit_db_user: str = "profit_user"
    profit_db_password: str = ""

    # ==================== 安全配置 ====================
    enable_auth: bool = False
    api_key: str = ""
    jwt_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
