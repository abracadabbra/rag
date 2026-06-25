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
    use_rerank: Optional[bool] = Field(None, description="是否使用精排（默认按配置）")
    use_bm25: Optional[bool] = Field(None, description="是否使用BM25粗排（默认按配置）")
    answer_perspective: Optional[str] = Field(
        None,
        description="回答口径，如 finance/operations/technical/strategy/balanced",
        max_length=32,
    )


class SourceDocument(BaseModel):
    """来源文档"""
    score: float = Field(..., description="相似度分数")
    content_preview: str = Field(..., description="内容预览")
    scene_type: Optional[str] = Field(None, description="来源文档所属场景")
    rule_id: Optional[str] = Field(None, description="规则ID")
    rule_name: Optional[str] = Field(None, description="规则名称")
    file_path: Optional[str] = Field(None, description="文件路径")
    chunk_index: Optional[int] = Field(None, description="文本块索引")
    source_type: Optional[str] = Field(None, description="来源类型: vector, bm25, rerank")


class RetrievalMetadata(BaseModel):
    """检索元数据"""
    vector_count: int = Field(0, description="向量检索结果数")
    bm25_count: int = Field(0, description="BM25 结果数")
    final_count: int = Field(0, description="最终返回数")
    used_rerank: bool = Field(False, description="是否使用了精排")
    used_bm25: bool = Field(False, description="是否使用了 BM25")


class ToolCall(BaseModel):
    """业务工具调用结果"""
    name: str = Field(..., description="工具名称")
    label: str = Field(..., description="工具展示名称")
    scene_type: str = Field(..., description="适用场景")
    description: str = Field("", description="工具说明")
    audit_id: Optional[str] = Field(None, description="业务工具审计追踪ID")
    endpoint_path: Optional[str] = Field(None, description="业务工具接口路径")
    endpoint_template: Optional[str] = Field(None, description="业务工具接口路径模板")
    contract_version: Optional[str] = Field(None, description="业务工具接口合同版本")
    data_source: Optional[str] = Field(None, description="业务工具数据源: mock/http")
    integration_mode: Optional[str] = Field(
        None,
        description="业务工具接入模式: mock/fake_http/external_http",
    )
    selection_source: Optional[str] = Field(
        None,
        description="工具选择来源: rules/llm/probe",
    )
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    status: str = Field(..., description="调用状态: success/error")
    result: Dict[str, Any] = Field(default_factory=dict, description="工具返回的结构化数据")
    summary: str = Field("", description="工具结果摘要")
    error_type: Optional[str] = Field(None, description="安全错误类型，仅包含异常类名")
    diagnostic: Optional[str] = Field(None, description="安全合同诊断文本，仅用于响应字段合同错误")
    diagnostic_code: Optional[str] = Field(None, description="安全合同诊断码，仅用于响应字段合同错误")
    missing_fields: Optional[List[str]] = Field(None, description="合同诊断中的缺失字段")
    invalid_fields: Optional[List[str]] = Field(None, description="合同诊断中的异常字段")
    duration_ms: Optional[int] = Field(None, description="工具调用耗时（毫秒）")
    selection_reason: Optional[str] = Field(None, description="工具选择原因")
    confidence: Optional[float] = Field(None, description="工具选择置信度")


class BusinessToolProbeResponse(ToolCall):
    """业务工具探测响应"""


class BusinessToolValidationResponse(BaseModel):
    """业务工具响应样例校验结果"""

    name: str = Field(..., description="工具名称")
    label: str = Field(..., description="工具展示名称")
    scene_type: str = Field(..., description="适用场景")
    contract_version: Optional[str] = Field(None, description="本次校验使用的接口合同版本")
    status: str = Field(..., description="校验状态: valid/invalid")
    duration_ms: int = Field(..., description="校验耗时（毫秒）")
    summary: str = Field(..., description="校验摘要")
    exposed_result_keys: List[str] = Field(default_factory=list, description="可展示结果字段")
    ignored_result_keys: List[str] = Field(
        default_factory=list,
        description="响应中存在但不会进入前端或 Prompt 的顶层字段",
    )
    error_type: Optional[str] = Field(None, description="安全错误类型，仅包含异常类名")
    diagnostic: Optional[str] = Field(None, description="安全合同诊断文本")
    diagnostic_code: Optional[str] = Field(None, description="安全合同诊断码")
    missing_fields: List[str] = Field(default_factory=list, description="合同诊断中的缺失字段")
    invalid_fields: List[str] = Field(default_factory=list, description="合同诊断中的异常字段")


class BusinessToolBatchValidationItem(BaseModel):
    """业务工具批量响应样例校验条目"""

    index: int = Field(..., description="样例在请求 payloads 中的序号，从 0 开始")
    status: str = Field(..., description="校验状态: valid/invalid")
    duration_ms: int = Field(..., description="单条样例校验耗时（毫秒）")
    summary: str = Field(..., description="单条样例校验摘要")
    exposed_result_keys: List[str] = Field(default_factory=list, description="可展示结果字段")
    ignored_result_keys: List[str] = Field(
        default_factory=list,
        description="响应中存在但不会进入前端或 Prompt 的顶层字段",
    )
    error_type: Optional[str] = Field(None, description="安全错误类型，仅包含异常类名")
    diagnostic: Optional[str] = Field(None, description="安全合同诊断文本")
    diagnostic_code: Optional[str] = Field(None, description="安全合同诊断码")
    missing_fields: List[str] = Field(default_factory=list, description="合同诊断中的缺失字段")
    invalid_fields: List[str] = Field(default_factory=list, description="合同诊断中的异常字段")


class BusinessToolBatchValidationSummary(BaseModel):
    """业务工具批量响应样例校验摘要"""

    total: int = Field(..., description="样例总数")
    valid_count: int = Field(..., description="校验通过数量")
    invalid_count: int = Field(..., description="校验失败数量")
    diagnostic_codes: Dict[str, int] = Field(default_factory=dict, description="诊断码计数")
    missing_fields: List[str] = Field(default_factory=list, description="本批次出现过的缺失字段")
    invalid_fields: List[str] = Field(default_factory=list, description="本批次出现过的异常字段")
    ignored_result_keys: List[str] = Field(
        default_factory=list,
        description="本批次出现过但不会进入前端或 Prompt 的顶层字段",
    )


class BusinessToolBatchValidationResponse(BaseModel):
    """业务工具批量响应样例校验结果"""

    name: str = Field(..., description="工具名称")
    label: str = Field(..., description="工具展示名称")
    scene_type: str = Field(..., description="适用场景")
    contract_version: Optional[str] = Field(None, description="本次校验使用的接口合同版本")
    status: str = Field(..., description="批量校验状态: valid/invalid")
    duration_ms: int = Field(..., description="批量校验总耗时（毫秒）")
    summary: str = Field(..., description="批量校验摘要")
    validation_summary: BusinessToolBatchValidationSummary = Field(..., description="批量校验聚合摘要")
    items: List[BusinessToolBatchValidationItem] = Field(default_factory=list, description="逐条校验结果")


class BusinessToolAuditStatus(BaseModel):
    """业务工具审计存储状态"""

    file_enabled: bool = Field(False, description="是否启用文件审计")
    file_configured: bool = Field(False, description="是否配置审计文件")
    file_name: Optional[str] = Field(None, description="审计文件名")
    file_exists: bool = Field(False, description="审计文件是否存在")
    file_readable: bool = Field(False, description="审计文件是否可读")
    persisted_event_count: int = Field(0, description="持久化审计事件数量")
    memory_event_count: int = Field(0, description="内存审计事件数量")
    memory_event_limit: int = Field(0, description="内存审计事件上限")


class BusinessToolAuditEvent(BaseModel):
    """业务工具审计事件安全摘要"""

    audit_id: Optional[str] = Field(None, description="审计追踪ID")
    timestamp: Optional[str] = Field(None, description="事件时间")
    tool_name: Optional[str] = Field(None, description="工具名称")
    label: Optional[str] = Field(None, description="工具展示名称")
    scene_type: Optional[str] = Field(None, description="适用场景")
    contract_version: Optional[str] = Field(None, description="调用时使用的接口合同版本")
    data_source: Optional[str] = Field(None, description="业务工具数据源: mock/http")
    endpoint_path: Optional[str] = Field(None, description="脱敏后的接口路径模板")
    status: Optional[str] = Field(None, description="调用状态: success/error")
    duration_ms: Optional[int] = Field(None, description="调用耗时（毫秒）")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="脱敏后的工具参数")
    selection_source: Optional[str] = Field(None, description="工具选择来源")
    selection_reason: Optional[str] = Field(None, description="脱敏后的工具选择依据")
    confidence: Optional[float] = Field(None, description="工具选择置信度")
    result_keys: List[str] = Field(default_factory=list, description="结果字段名列表")
    error_type: Optional[str] = Field(None, description="安全错误类型，仅包含异常类名")
    diagnostic_code: Optional[str] = Field(None, description="安全合同诊断码")
    missing_fields: List[str] = Field(default_factory=list, description="合同诊断中的缺失字段")
    invalid_fields: List[str] = Field(default_factory=list, description="合同诊断中的异常字段")


class BusinessToolAuditEventsResponse(BaseModel):
    """最近业务工具审计事件响应"""

    events: List[BusinessToolAuditEvent] = Field(default_factory=list, description="最近审计事件")
    limit: int = Field(..., description="本次返回上限")
    audit_status: BusinessToolAuditStatus = Field(..., description="审计存储状态")


class BusinessToolFieldCatalogItem(BaseModel):
    """业务工具字段目录项"""

    name: str = Field(..., description="字段名")
    label: str = Field(..., description="字段展示名")
    type: str = Field(..., description="字段类型标签")
    required: bool = Field(..., description="是否属于接口必填或展示必需字段")
    description: str = Field(..., description="字段说明")


class ProfitDerivedChainStep(BaseModel):
    """毛利自动派生链路节点定义"""

    node: str = Field(..., description="链路节点名称")
    field: str = Field(..., description="来源金额字段")
    sign: int = Field(..., description="金额方向: 1 收入/留存, -1 成本")
    required: bool = Field(..., description="该节点来源字段是否为必填")
    role: str = Field(..., description="业务角色")
    tone: str = Field(..., description="前端展示语气")
    note: str = Field(..., description="节点说明")


class RiskBusinessToolContract(BaseModel):
    """风控业务工具接口合同快照"""

    tool_name: str = Field(..., description="工具名称")
    contract_version: str = Field(..., description="接口合同版本")
    endpoint_template: str = Field(..., description="接口路径模板")
    required_request_fields: List[str] = Field(default_factory=list, description="必填请求字段")
    request_json_schema: Dict[str, Any] = Field(default_factory=dict, description="请求 JSON Schema")
    required_fields: Dict[str, str] = Field(default_factory=dict, description="必填响应字段类型")
    hit_rule_required_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="命中规则数组中每项必填字段类型",
    )
    field_catalog: List[BusinessToolFieldCatalogItem] = Field(
        default_factory=list,
        description="字段目录",
    )
    response_json_schema: Dict[str, Any] = Field(default_factory=dict, description="响应 JSON Schema")
    example_response: Dict[str, Any] = Field(default_factory=dict, description="示例响应")
    exposed_fields: List[str] = Field(default_factory=list, description="允许展示字段")


class ProfitBusinessToolContract(BaseModel):
    """毛利业务工具接口合同快照"""

    tool_name: str = Field(..., description="工具名称")
    contract_version: str = Field(..., description="接口合同版本")
    endpoint_template: str = Field(..., description="接口路径模板")
    required_request_fields: List[str] = Field(default_factory=list, description="必填请求字段")
    request_json_schema: Dict[str, Any] = Field(default_factory=dict, description="请求 JSON Schema")
    required_fields: Dict[str, str] = Field(default_factory=dict, description="必填响应字段类型")
    chain_step_required_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="钱流链路节点必填字段类型",
    )
    chain_step_optional_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="钱流链路节点可选字段类型",
    )
    chain_terminal_node: str = Field(..., description="钱流链路终点节点")
    derived_chain_steps: List[ProfitDerivedChainStep] = Field(
        default_factory=list,
        description="后端可自动派生的钱流链路节点定义",
    )
    display_metadata_fields: List[BusinessToolFieldCatalogItem] = Field(
        default_factory=list,
        description="后端展示元信息字段",
    )
    field_catalog: List[BusinessToolFieldCatalogItem] = Field(
        default_factory=list,
        description="字段目录",
    )
    response_json_schema: Dict[str, Any] = Field(default_factory=dict, description="响应 JSON Schema")
    example_response: Dict[str, Any] = Field(default_factory=dict, description="示例响应")
    exposed_fields: List[str] = Field(default_factory=list, description="允许展示字段")


class BusinessToolContractsResponse(BaseModel):
    """风控/毛利业务工具接口合同快照响应"""

    integration_handoff: Dict[str, Any] = Field(
        default_factory=dict,
        description="真实系统联调顺序、命令、上线门禁和安全说明",
    )
    prompt_contract: Dict[str, Any] = Field(
        default_factory=dict,
        description="业务场景回答口径、视角和安全提示合同",
    )
    risk: RiskBusinessToolContract = Field(..., description="风控工具合同")
    profit: ProfitBusinessToolContract = Field(..., description="毛利工具合同")


class BusinessToolRuntimeConfigStatus(BaseModel):
    """业务工具基础运行配置状态"""

    enabled: bool = Field(False, description="业务工具是否启用")
    timeout_seconds: int = Field(0, description="业务工具调用超时时间")
    tool_count: int = Field(0, description="业务工具数量")


class BusinessToolAccessControlStatus(BaseModel):
    """业务工具访问控制运行状态"""

    enabled: bool = Field(False, description="是否启用访问控制")
    ready: bool = Field(False, description="访问控制是否就绪")
    full_access_configured: bool = Field(False, description="是否配置全权限 token")
    read_configured: bool = Field(False, description="是否配置只读 token")
    execute_configured: bool = Field(False, description="是否配置执行 token")
    read_scope_ready: bool = Field(False, description="只读 scope 是否就绪")
    execute_scope_ready: bool = Field(False, description="执行 scope 是否就绪")
    missing_scopes: List[str] = Field(default_factory=list, description="缺失的 scope")


class BusinessToolLlmIntentRuntimeStatus(BaseModel):
    """业务工具 LLM 意图兜底运行状态"""

    enabled: bool = Field(False, description="是否启用 LLM 意图兜底")
    min_confidence: float = Field(0.0, description="LLM 意图最低执行置信度")
    model_configured: bool = Field(False, description="LLM 模型是否已配置")
    attempt_count: int = Field(0, description="意图识别尝试次数")
    success_count: int = Field(0, description="意图识别成功次数")
    error_count: int = Field(0, description="意图识别失败次数")
    last_status: Optional[str] = Field(None, description="最近一次意图识别状态")
    last_resolution: Optional[str] = Field(None, description="最近一次成功解析结果")
    last_error_type: Optional[str] = Field(None, description="最近一次失败类型")
    last_attempt_at: Optional[str] = Field(None, description="最近一次尝试时间")
    last_success_at: Optional[str] = Field(None, description="最近一次成功时间")
    last_error_at: Optional[str] = Field(None, description="最近一次失败时间")


class BusinessToolRuntimeToolStatus(BaseModel):
    """单个业务工具运行态摘要"""

    tool_name: str = Field(..., description="工具名称")
    label: str = Field(..., description="工具展示名称")
    scene_type: str = Field(..., description="适用场景")
    data_source: str = Field(..., description="业务工具数据源: mock/http")
    integration_mode: str = Field(..., description="业务工具接入模式: mock/fake_http/external_http")
    endpoint_template: str = Field(..., description="脱敏接口路径模板")
    base_url_configured: bool = Field(False, description="是否配置 Base URL")
    api_key_configured: bool = Field(False, description="是否配置 API Key")
    contract_available: bool = Field(False, description="接口合同是否可用")


class BusinessToolRuntimeStatusResponse(BaseModel):
    """业务工具运行态自检响应"""

    status: str = Field(..., description="运行态状态: ready/disabled/misconfigured")
    status_reason: str = Field(..., description="运行态说明")
    business_tools: BusinessToolRuntimeConfigStatus = Field(..., description="基础配置状态")
    access_control: BusinessToolAccessControlStatus = Field(..., description="访问控制状态")
    audit: BusinessToolAuditStatus = Field(..., description="审计状态")
    llm_intent: BusinessToolLlmIntentRuntimeStatus = Field(..., description="LLM 意图兜底状态")
    tools: List[BusinessToolRuntimeToolStatus] = Field(default_factory=list, description="工具运行态列表")


class BusinessToolCorpusSceneStatus(BaseModel):
    """业务语料场景可用性"""

    available: bool = Field(False, description="该场景语料是否可用")
    sample_count: int = Field(0, description="抽样命中的语料数量")
    error_type: Optional[str] = Field(None, description="安全错误类型，仅包含异常类名")


class BusinessToolCorpusStatus(BaseModel):
    """业务语料接入状态"""

    collection_name: str = Field(..., description="Milvus collection 名称")
    scenes: Dict[str, BusinessToolCorpusSceneStatus] = Field(
        default_factory=dict,
        description="按场景聚合的语料状态",
    )


class BusinessToolReadinessItem(BaseModel):
    """业务工具接入检查项"""

    id: str = Field(..., description="检查项 ID")
    status: str = Field(..., description="检查状态: passed/warning/blocked")
    summary: str = Field(..., description="检查摘要")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="安全检查证据")


class BusinessToolReadinessResponse(BaseModel):
    """业务工具接入检查响应"""

    overall_status: str = Field(..., description="整体接入状态: ready/ready_with_warnings/blocked")
    status_reason: str = Field(..., description="整体接入说明")
    passed: List[str] = Field(default_factory=list, description="已通过检查项 ID")
    warnings: List[str] = Field(default_factory=list, description="建议处理检查项 ID")
    blockers: List[str] = Field(default_factory=list, description="阻塞检查项 ID")
    items: List[BusinessToolReadinessItem] = Field(default_factory=list, description="检查项详情")
    audit_event_count: int = Field(0, description="本次检查读取的审计事件数量")
    audit_event_limit: int = Field(0, description="本次检查读取的审计事件上限")
    corpus_status: BusinessToolCorpusStatus = Field(..., description="业务语料接入状态")


class ToolIntent(BaseModel):
    """业务工具意图预判结果"""
    tool_name: Optional[str] = Field(None, description="候选工具名称")
    label: Optional[str] = Field(None, description="候选工具展示名称")
    scene_type: str = Field(..., description="适用场景")
    selection_source: str = Field("none", description="工具选择来源: none/rules/llm")
    order_id: Optional[str] = Field(None, description="识别到的订单号")
    confidence: float = Field(0.0, description="工具意图置信度")
    reason: str = Field("", description="工具意图判断原因")
    missing_fields: List[str] = Field(default_factory=list, description="缺失的必要字段")
    needs_clarification: bool = Field(False, description="是否需要用户补充信息")
    clarification_options: List[str] = Field(default_factory=list, description="澄清提示")


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str = Field(..., description="生成的答案")
    sources: List[SourceDocument] = Field(default_factory=list, description="来源文档列表")
    retrieved_count: int = Field(..., description="检索到的文档数量")
    session_id: str = Field(..., description="会话ID")
    answer_perspective: Optional[str] = Field(None, description="本次回答口径")
    needs_clarification: bool = Field(False, description="是否需要澄清")
    clarification_options: List[str] = Field(default_factory=list, description="澄清选项列表")
    retrieval_metadata: Optional[RetrievalMetadata] = Field(None, description="检索元数据")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="业务系统工具调用列表")
    tool_intent: Optional[ToolIntent] = Field(None, description="业务工具意图预判结果")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
