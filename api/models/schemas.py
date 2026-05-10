"""
API 数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="用户问题", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, description="会话ID（用于多轮对话）")
    top_k: Optional[int] = Field(None, description="返回文档数量", ge=1, le=20)
    score_threshold: Optional[float] = Field(None, description="相似度阈值", ge=0.0, le=1.0)
    clarification_choice: Optional[str] = Field(None, description="用户选择的澄清选项")


class SourceDocument(BaseModel):
    """来源文档"""
    score: float = Field(..., description="相似度分数")
    content_preview: str = Field(..., description="内容预览")
    rule_id: Optional[str] = Field(None, description="规则ID")
    rule_name: Optional[str] = Field(None, description="规则名称")
    file_path: Optional[str] = Field(None, description="文件路径")
    chunk_index: Optional[int] = Field(None, description="文本块索引")


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str = Field(..., description="生成的答案")
    sources: List[SourceDocument] = Field(default_factory=list, description="来源文档列表")
    retrieved_count: int = Field(..., description="检索到的文档数量")
    session_id: str = Field(..., description="会话ID")
    needs_clarification: bool = Field(False, description="是否需要澄清")
    clarification_options: List[str] = Field(default_factory=list, description="澄清选项列表")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
