"""
Frontend business tool display contract tests.

These checks keep the Vue display contract aligned with backend `tool_calls`
without adding a frontend test runner dependency.
"""

from pathlib import Path


QA_VIEW = Path("frontend/src/components/QAView.vue")
BUSINESS_TOOL_COMPONENT = Path("frontend/src/components/BusinessToolCallList.vue")
PROFIT_TOOL_COMPONENT = Path("frontend/src/components/ProfitToolInsights.vue")
PROFIT_ANALYSIS_COMPONENT = Path("frontend/src/components/ProfitAnalysisPanel.vue")
PROFIT_CHAIN_COMPONENT = Path("frontend/src/components/ProfitChainTimeline.vue")
RISK_TOOL_COMPONENT = Path("frontend/src/components/RiskToolInsights.vue")
API_SERVICE = Path("frontend/src/services/api.js")
API_SETTINGS = Path("frontend/src/views/ApiSettings.vue")
PROFIT_QA = Path("frontend/src/views/ProfitQA.vue")
RISK_QA = Path("frontend/src/views/RiskRulesQA.vue")
BUSINESS_TOOL_QUICKSTART_DOC = Path("docs/BUSINESS_TOOL_QUICKSTART.md")
BUSINESS_TOOLS_DOC = Path("docs/BUSINESS_TOOLS.md")
ENV_EXAMPLE = Path(".env.example")
README = Path("README.md")


def test_qa_view_mounts_business_tool_component():
    source = QA_VIEW.read_text(encoding="utf-8")

    assert "import BusinessToolCallList from './BusinessToolCallList.vue'" in source
    assert "<BusinessToolCallList" in source
    assert ':tool-calls="msg.tool_calls || []"' in source
    assert ':tool-intent="msg.tool_intent"' in source
    assert "showToolIntent(msg)" not in source
    assert 'v-if="msg.tool_calls?.length"' not in source


def test_business_tool_component_keeps_shared_tool_call_shell():
    source = BUSINESS_TOOL_COMPONENT.read_text(encoding="utf-8")

    assert "import ProfitToolInsights from './ProfitToolInsights.vue'" in source
    assert "import RiskToolInsights from './RiskToolInsights.vue'" in source
    assert "<ProfitToolInsights :call=\"call\" :anchor-prefix=\"callAnchorPrefix(call)\" />" in source
    assert "<RiskToolInsights :call=\"call\" :panel-id=\"riskEvidenceAnchorId(call)\" />" in source
    assert "系统接口调用" in source
    assert "tool-call-list" in source
    assert "tool-call-item" in source
    assert "call.duration_ms" in source
    assert "call.audit_id" in source
    assert "审计ID" in source
    assert "接口降级提示" in source
    assert "call.status === 'error'" in source
    assert "call.error_type" in source
    assert "call.diagnostic" in source
    assert "call.diagnostic_code" in source
    assert "call.missing_fields" in source
    assert "call.invalid_fields" in source
    assert "formatDiagnosticCode(call.diagnostic_code)" in source
    assert "缺失字段" in source
    assert "异常字段" in source
    assert "tool-degrade-diagnostic" in source
    assert "稍后重试，或在 API 设置中使用接口探测和响应样例校验" in source
    assert "tool-degrade" in source
    assert "call.status === 'success' ? '成功' : '失败'" in source
    assert "call.selection_reason" in source
    assert "formatConfidence(call.confidence)" in source
    assert "toolIntentStateLabel(toolIntent)" in source
    assert "toolIntentActionHint(toolIntent)" in source
    assert "formatIntentMissingField(field)" in source
    assert "toolIntent.clarification_options[0]" in source
    assert "formatSelectionSource(toolIntent.selection_source)" in source
    assert "call.selection_source" in source
    assert "decisionTimeline.length" in source
    assert "buildDecisionTimeline(props.toolIntent, primaryCall.value)" in source
    assert "工具决策时间线" in source
    assert "item.targets?.length" in source
    assert "@click=\"jumpToTarget(target.id)\"" in source
    assert "ProfitToolInsights :call=\"call\" :anchor-prefix=\"callAnchorPrefix(call)\"" in source
    assert "RiskToolInsights :call=\"call\" :panel-id=\"riskEvidenceAnchorId(call)\"" in source
    assert "profit-analysis" not in source
    assert "risk-evidence" not in source
    assert "profit-chain" not in source
    assert "profitExecutiveSummary(call)" not in source
    assert "riskExecutiveSummary(call)" not in source


def test_business_tool_component_maps_backend_tool_call_fields_to_visible_chips():
    source = BUSINESS_TOOL_COMPONENT.read_text(encoding="utf-8")

    assert "return Boolean(intent?.tool_name)" in source
    assert "if (missingFields.includes('tool_intent_confirmation'))" in source
    assert "等待你确认后再调用接口" in source
    assert "if (missingFields.includes('order_id'))" in source
    assert "等待补充订单号" in source
    assert "return '执行确认'" in source
    assert "return '订单号'" in source
    assert "return '规则命中'" in source
    assert "return 'LLM 兜底'" in source
    assert "命中依据" in source
    assert "选择来源" in source
    assert "建议补充" in source
    assert "下一状态" in source
    assert "title: '意图识别'" in source
    assert "title: '信息补齐'" in source
    assert "title: '接口执行'" in source
    assert "title: '结果返回'" in source
    assert "state: '等待输入'" in source
    assert "state: '待执行'" in source
    assert "state: '未返回'" in source
    assert "state: call.status === 'success' ? '执行成功' : '执行失败'" in source
    assert "state: call.status === 'success' ? '已返回' : '已降级'" in source
    assert "待补充：" in source
    assert "补齐后会自动进入接口调用" in source
    assert "label: '查看钱流链路'" in source
    assert "label: '查看毛利拆解'" in source
    assert "label: '查看命中证据'" in source
    assert "id: `${callAnchorPrefix(call)}-chain`" in source
    assert "id: `${callAnchorPrefix(call)}-analysis`" in source
    assert "return prefix ? `${prefix}-risk` : ''" in source
    assert "element.scrollIntoView({ behavior: 'smooth', block: 'nearest' })" in source
    assert "formatDataSource(call.data_source)" in source
    assert "if (value === 'mock') return 'Mock 数据'" in source
    assert "if (value === 'http') return '真实接口'" in source
    assert "call.contract_version" in source
    assert "call.endpoint_template" in source
    assert "合同版本" in source
    assert "接口模板" in source
    assert "call.endpoint_path" in source
    assert "call.audit_id" in source
    assert "result.order_id || args.order_id" in source

    assert "call?.name === 'get_risk_event_detail'" in source
    assert "result.decision" in source
    assert "result.risk_score" in source
    assert "result.risk_level" in source

    assert "call?.name === 'get_profit_chain_detail'" in source
    assert "result.gross_amount" in source
    assert "result.platform_commission" in source
    assert "result.driver_income" in source
    assert "result.platform_net_profit" in source
    assert "result.chain_source" in source
    assert "formatChainSource(result.chain_source)" in source
    assert "链路来源" in source
    assert "return '接口原生链路'" in source
    assert "return '自动派生链路'" in source
    assert "return labels[value] || value" in source
    assert "missing_required_fields: '缺少必填字段'" in source


def test_profit_tool_component_renders_profit_analysis_and_chain_sections():
    source = PROFIT_TOOL_COMPONENT.read_text(encoding="utf-8")

    assert "import ProfitAnalysisPanel from './ProfitAnalysisPanel.vue'" in source
    assert "import ProfitChainTimeline from './ProfitChainTimeline.vue'" in source
    assert "<ProfitAnalysisPanel" in source
    assert "<ProfitChainTimeline" in source
    assert ":panel-id=\"profitAnalysisAnchorId\"" in source
    assert ":panel-id=\"profitChainAnchorId\"" in source
    assert "analysisModel" in source
    assert "chainViewModel" in source
    assert "hasProfitAnalysis" in source
    assert "hasProfitChain" in source
    assert "profitHeadline()" in source
    assert "profitSummaryText()" in source
    assert "profitTopDrivers()" in source
    assert "profitChainStepTone(step)" in source
    assert "profitChainStepRole(step)" in source
    assert "profitChainStepRatio(step)" in source
    assert "profitChainStepFormulaTag(step)" in source
    assert "profitChainStepNote(step)" in source
    assert "profitChainSourceLabel()" in source
    assert "sourceLabel: profitChainSourceLabel()" in source
    assert "formulaAudit: profitFormulaAudit()" in source
    assert "function profitFormulaAudit()" in source
    assert "commission - subsidy - coupon - safeChannelFee" in source
    assert "与接口净毛利一致" in source
    assert "与接口净毛利不一致" in source
    assert "未返回渠道费时按 0 参与核对" in source
    assert "formatSignedDelta(delta)" in source
    assert "function roundMoney(value)" in source
    assert "formatChainAmount(step.amount)" in source
    assert "result?.chain_source" in source
    assert "return '接口原生链路'" in source
    assert "return '自动派生链路'" in source

    assert "result.subsidy" in source
    assert "result.coupon" in source
    assert "result.channel_fee" in source
    assert "props.call?.result?.chain" in source
    assert "step?.tone" in source
    assert "step?.role" in source
    assert "step?.note" in source
    assert "buildProfitDriver('平台补贴'" in source
    assert "buildProfitDriver('用户优惠'" in source
    assert "buildProfitDriver('渠道成本'" in source
    assert "buildProfitDriver('平台抽成'" in source


def test_profit_analysis_component_renders_profit_summary_kpis_and_formula():
    source = PROFIT_ANALYSIS_COMPONENT.read_text(encoding="utf-8")

    assert ":id=\"panelId\"" in source
    assert "panelId: { type: String, default: '' }" in source
    assert "毛利拆解" in source
    assert "profit-analysis" in source
    assert "业务结论" in source
    assert "profit-summary-card" in source
    assert "profit-summary-head" in source
    assert "profit-driver-list" in source
    assert "profit-driver-chip" in source
    assert "profit-kpi-grid" in source
    assert "profit-kpi" in source
    assert "毛利公式" in source
    assert "profit-equation" in source
    assert "profit-ledger" in source
    assert "profit-signals" in source


def test_profit_chain_component_renders_money_flow_timeline_contract():
    source = PROFIT_CHAIN_COMPONENT.read_text(encoding="utf-8")

    assert ":id=\"panelId\"" in source
    assert "panelId: { type: String, default: '' }" in source
    assert "订单钱流链路" in source
    assert "profit-chain" in source
    assert "profit-chain-head" in source
    assert "profit-chain-source" in source
    assert "毛利口径说明" in source
    assert "公式核对" in source
    assert "profit-formula-audit" in source
    assert "formula-audit-head" in source
    assert "formula-audit-row" in source
    assert "formula-audit-part" in source
    assert "chainView.formulaAudit.statusLabel" in source
    assert "chainView.formulaAudit.note" in source
    assert "chainView.formulaAudit.parts" in source
    assert "profit-chain-track" in source
    assert "chain-node-role" in source
    assert "chain-node-label" in source
    assert "chain-node-amount" in source
    assert "chain-node-ratio" in source
    assert "chain-node-formula" in source
    assert "chain-node-note" in source
    assert "chain-arrow" in source


def test_risk_tool_component_renders_risk_summary_and_rule_evidence():
    source = RISK_TOOL_COMPONENT.read_text(encoding="utf-8")

    assert ":id=\"panelId\"" in source
    assert "panelId: { type: String, default: '' }" in source
    assert "risk-evidence" in source
    assert "hasRiskEvidence" in source
    assert "props.call?.name !== 'get_risk_event_detail'" in source
    assert "riskExecutiveSummary()" in source
    assert "risk-summary-card" in source
    assert "风控结论" in source
    assert "risk-summary-head" in source
    assert "risk-signal-list" in source
    assert "risk-signal-chip" in source
    assert "riskEvidenceMeter" in source
    assert "buildRiskEvidenceMeter()" in source
    assert "证据完整度" in source
    assert "coveragePercent" in source
    assert "coverageLabel" in source
    assert "risk-meter-grid" in source
    assert "risk-meter-item" in source
    assert "riskSummaryText()" in source
    assert "riskSummarySignals()" in source
    assert "riskDecisionLabel()" in source
    assert "riskDecisionTone()" in source
    assert "formatRiskDecision(result.decision)" in source
    assert "formatRiskLevel(result.risk_level)" in source
    assert "result.recommended_action" in source
    assert "formatDataSource(props.call?.data_source)" in source
    assert "props.call?.result?.hit_rules" in source
    assert "label: '来源'" in source
    assert "if (value === 'http') return '真实接口'" in source
    assert "if (value === 'mock') return 'Mock 数据'" in source
    assert "建议拦截" in source
    assert "建议复核" in source
    assert "建议放行" in source
    assert "命中 1 条规则" not in source
    assert "命中规则证据" in source
    assert "<template v-if=\"riskRules().length\">" in source
    assert "risk-rule-empty" in source
    assert "当前接口未返回命中规则，按系统决策、风险分和建议动作解释。" in source
    assert "rule.rule_name" in source
    assert "rule.evidence" in source


def test_qa_view_keeps_order_id_clarification_input_path():
    source = QA_VIEW.read_text(encoding="utf-8")

    assert "pendingClarification" in source
    assert "isOrderIdClarification(pendingClarification)" in source
    assert "clarification-input-card" in source
    assert 'placeholder="输入订单号，例如 ORD88888"' in source
    assert "handleClarificationInputSubmit" in source
    assert "missingFields.includes('order_id')" in source


def test_business_qa_view_exposes_answer_perspective_controls():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    qa_source = QA_VIEW.read_text(encoding="utf-8")
    profit_source = PROFIT_QA.read_text(encoding="utf-8")
    risk_source = RISK_QA.read_text(encoding="utf-8")

    assert "answer_perspective" in api_source
    assert "answerPerspectives" in qa_source
    assert "selectedAnswerPerspective" in qa_source
    assert "perspective-tabs" in qa_source
    assert "perspective-tab" in qa_source
    assert "answer-perspective-chip" in qa_source
    assert "stream-progress" in qa_source
    assert "setMessageProgress" in qa_source
    assert "clearMessageProgress" in qa_source
    assert "formatAnswerPerspective" in qa_source
    assert "aria-label=\"回答口径\"" in qa_source
    assert "onProgress" in api_source
    assert "eventType === 'progress'" in api_source
    assert "answer_perspective: selectedAnswerPerspective.value || null" in qa_source
    assert "data.answer_perspective || selectedAnswerPerspective.value || null" in qa_source
    assert "answer_perspective: msg.metadata?.answer_perspective || null" in qa_source

    assert ':answerPerspectives="answerPerspectives"' in profit_source
    assert "finance" in profit_source
    assert "operations" in profit_source
    assert "technical" in profit_source
    assert ':answerPerspectives="answerPerspectives"' in risk_source
    assert "strategy" in risk_source
    assert "operations" in risk_source
    assert "technical" in risk_source


def test_qa_view_uses_lightweight_ready_check_for_connection_status():
    source = QA_VIEW.read_text(encoding="utf-8")

    assert "import { checkReady" in source
    assert "await checkReady()" in source
    assert "checkHealth" not in source


def test_api_settings_renders_business_tool_contract_snapshot():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    settings_source = API_SETTINGS.read_text(encoding="utf-8")

    assert "getBusinessToolContracts" in api_source
    assert "business-tools/contracts" in api_source
    assert "getBusinessToolContracts" in settings_source
    assert "业务接口合同" in settings_source
    assert "导出 JSON" in settings_source
    assert "downloadBusinessContracts" in settings_source
    assert "business_tool_contracts.json" in settings_source
    assert "new Blob" in settings_source
    assert "URL.createObjectURL" in settings_source
    assert "URL.revokeObjectURL" in settings_source
    assert "contractDownloadMessage" in settings_source
    assert "endpoint_template" in settings_source
    assert "required_request_fields" in settings_source
    assert "businessContracts.risk.required_fields" in settings_source
    assert "businessContracts.risk.contract_version" in settings_source
    assert "businessContracts.risk.hit_rule_required_fields" in settings_source
    assert "businessContracts.risk.field_catalog" in settings_source
    assert "businessContracts.risk.request_json_schema" in settings_source
    assert "businessContracts.risk.response_json_schema" in settings_source
    assert "businessContracts.risk.example_response" in settings_source
    assert "businessContracts.profit.required_fields" in settings_source
    assert "businessContracts.profit.contract_version" in settings_source
    assert "businessContracts.profit.chain_step_required_fields" in settings_source
    assert "businessContracts.profit.chain_step_optional_fields" in settings_source
    assert "businessContracts.profit.chain_terminal_node" in settings_source
    assert "businessContracts.profit.derived_chain_steps" in settings_source
    assert "businessContracts.profit.display_metadata_fields" in settings_source
    assert "businessContracts.profit.field_catalog" in settings_source
    assert "businessContracts.profit.request_json_schema" in settings_source
    assert "businessContracts.profit.response_json_schema" in settings_source
    assert "businessContracts.profit.example_response" in settings_source
    assert "businessContracts.integration_handoff" in settings_source
    assert "businessContracts.prompt_contract" in settings_source
    assert "promptContractEntries" in settings_source
    assert "answerPerspectiveEntries" in settings_source
    assert "回答口径合同" in settings_source
    assert "建议输出段落" in settings_source
    assert "安全说明" in settings_source
    assert "真实系统联调交接" in settings_source
    assert "recommended_sequence" in settings_source
    assert "handoffCommandEntries" in settings_source
    assert "handoffModeEntries" in settings_source
    assert "go_live_gates" in settings_source
    assert "integration_modes" in settings_source
    assert "safety_notes" in settings_source
    assert "external_http_strict_gate" in settings_source
    assert "外部系统门禁" in settings_source
    assert "自动派生链路" in settings_source
    assert "展示元信息" in settings_source
    assert "这些字段由后端在合同校验通过后补充" in settings_source
    assert "后端补充" in settings_source
    assert "字段语义" in settings_source
    assert "field-catalog-list" in settings_source
    assert "derived-step-list" in settings_source
    assert "正向流入" in settings_source
    assert "负向扣减" in settings_source
    assert "optional-chip-list" in settings_source
    assert "请求 Schema" in settings_source
    assert "响应 Schema" in settings_source
    assert "示例响应" in settings_source
    assert "formatJson" in settings_source
    assert "contract-json" in settings_source
    assert "contract-badges" in settings_source
    assert "businessContracts.profit.exposed_fields" in settings_source
    assert "'prompt_contract'" in settings_source


def test_api_settings_exposes_business_tool_probe_controls():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    settings_source = API_SETTINGS.read_text(encoding="utf-8")

    assert "probeBusinessTool" in api_source
    assert "business-tools/probe" in api_source
    assert "inspectBusinessToolIntent" in api_source
    assert "business-tools/intent" in api_source
    assert "validateBusinessToolResponse" in api_source
    assert "business-tools/validate-response" in api_source
    assert "validateBusinessToolResponses" in api_source
    assert "business-tools/validate-responses" in api_source
    assert "probeBusinessTool" in settings_source
    assert "inspectBusinessToolIntent" in settings_source
    assert "validateBusinessToolResponse" in settings_source
    assert "validateBusinessToolResponses" in settings_source
    assert "接口探测订单号" in settings_source
    assert "工具意图预检" in settings_source
    assert "只判断会不会选风控/毛利工具，不调用真实订单接口" in settings_source
    assert "intentInspectQuery" in settings_source
    assert "intentInspectSceneType" in settings_source
    assert "runIntentInspect" in settings_source
    assert "intentInspectStateLabel" in settings_source
    assert "测试风控接口" in settings_source
    assert "测试毛利接口" in settings_source
    assert "响应样例校验" in settings_source
    assert "填入风控示例" in settings_source
    assert "填入毛利示例" in settings_source
    assert "校验风控响应" in settings_source
    assert "校验毛利响应" in settings_source
    assert "批量响应样例 JSON" in settings_source
    assert "批量填入风控示例" in settings_source
    assert "批量填入毛利示例" in settings_source
    assert "批量校验风控" in settings_source
    assert "批量校验毛利" in settings_source
    assert "validatePayloadText" in settings_source
    assert "batchValidatePayloadText" in settings_source
    assert "fillValidationPayload" in settings_source
    assert "fillBatchValidationPayload" in settings_source
    assert "runResponseValidation" in settings_source
    assert "runBatchResponseValidation" in settings_source
    assert "parseBatchValidationPayloads" in settings_source
    assert "formatDiagnosticCounts" in settings_source
    assert "batchValidatePreviewItems" in settings_source
    assert "batchValidationItemSummary" in settings_source
    assert "probeResultsByTool" in settings_source
    assert "validationResultsByTool" in settings_source
    assert "batchValidationResultsByTool" in settings_source
    assert "[toolName]: probeResult.value" in settings_source
    assert "[toolName]: validateResult.value" in settings_source
    assert "[toolName]: batchValidateResult.value" in settings_source
    assert "return probeResultsByTool.value?.[toolName] || null" in settings_source
    assert "return validationResultsByTool.value?.[toolName] || null" in settings_source
    assert "exposed_result_keys" in settings_source
    assert "ignored_result_keys" in settings_source
    assert "未展示字段" in settings_source
    assert "忽略 ${ignoredCount} 个字段" in settings_source
    assert "validation_summary" in settings_source
    assert "batch-validation-summary" in settings_source
    assert "batch-validation-item" in settings_source
    assert "get_risk_event_detail" in settings_source
    assert "get_profit_chain_detail" in settings_source
    assert "probeResult.diagnostic" in settings_source
    assert "probeResult.diagnostic_code" in settings_source
    assert "probeResult.missing_fields" in settings_source
    assert "probeResult.invalid_fields" in settings_source
    assert "probeResult.integration_mode" in settings_source
    assert "formatIntegrationMode(probeResult.integration_mode)" in settings_source
    assert "formatIntegrationMode(result.integration_mode)" in settings_source
    assert "合同诊断" in settings_source
    assert "缺失字段" in settings_source
    assert "异常字段" in settings_source
    assert "hasProbeDiagnosticDetails" in settings_source
    assert "formatDiagnosticCode" in settings_source
    assert "missing_required_fields" in settings_source
    assert "invalid_field_types" in settings_source
    assert "invalid_hit_rules" in settings_source
    assert "invalid_chain" in settings_source
    assert "non_object_json" in settings_source
    assert "ORDER_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/" in settings_source
    assert "isProbeOrderIdValid" in settings_source
    assert "probeOrderIdError" in settings_source
    assert "probeOrderIdPattern" in settings_source
    assert "probeOrderIdPatternText" in settings_source
    assert "request_json_schema?.properties?.order_id?.pattern" in settings_source
    assert "new RegExp(contractPattern)" in settings_source
    assert "return ORDER_ID_PATTERN" in settings_source
    assert ":disabled=\"loading || probeLoading || !isProbeOrderIdValid(probeOrderId)\"" in settings_source
    assert "const validationError = probeOrderIdError()" in settings_source
    assert "probeError.value = validationError" in settings_source
    assert "订单号格式：字母/数字开头，仅允许字母、数字、_、-，最多 128 位" in settings_source
    assert "当前合同 {{ probeOrderIdPatternText() }}" in settings_source
    assert "订单号只能包含字母、数字、_、-，且不能以符号开头" in settings_source


def test_api_settings_exposes_business_tool_runtime_status():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    settings_source = API_SETTINGS.read_text(encoding="utf-8")

    assert "getBusinessToolRuntimeStatus" in api_source
    assert "business-tools/runtime-status" in api_source
    assert "getBusinessToolReadiness" in api_source
    assert "business-tools/readiness" in api_source
    assert "headers: withBusinessToolToken()" in api_source
    assert "getBusinessToolRuntimeStatus" in settings_source
    assert "getBusinessToolReadiness" in settings_source
    assert "接入检查工作台" in settings_source
    assert "按工具汇总合同版本、接入模式、最近探测、样例校验和脱敏审计" in settings_source
    assert "businessWorkbenchTools" in settings_source
    assert "refreshBusinessWorkbench" in settings_source
    assert "workbenchOverallStatusLabel()" in settings_source
    assert "workbenchOverallStatusHint()" in settings_source
    assert "导出验收包" in settings_source
    assert "downloadBusinessAcceptancePack" in settings_source
    assert "buildBusinessAcceptancePack" in settings_source
    assert "business_tool_acceptance_pack_frontend.json" in settings_source
    assert "integration_handoff" in settings_source
    assert "recommended_next_actions" in settings_source
    assert "go_live_allowed" in settings_source
    assert "must_fix_before_real_order_traffic" in settings_source
    assert "should_fix_before_production" in settings_source
    assert "safe_frontend_evidence" in settings_source
    assert "businessAcceptanceRecommendedActions" in settings_source
    assert "businessAcceptanceToolEvidence" in settings_source
    assert "downloadJsonFile" in settings_source
    assert "toolWorkbenchTone(tool.tool_name)" in settings_source
    assert "toolContractVersion(tool.contract_key)" in settings_source
    assert "toolRuntimeMode(tool.tool_name)" in settings_source
    assert "toolRuntimeHint(tool.tool_name)" in settings_source
    assert "toolContractState(tool.contract_key, tool.tool_name)" in settings_source
    assert "toolProbeState(tool.tool_name)" in settings_source
    assert "toolValidationState(tool.tool_name)" in settings_source
    assert "toolAuditState(tool.tool_name)" in settings_source
    assert "toolContractExposure(tool.contract_key)" in settings_source
    assert "toolAuditFootnote(tool.tool_name)" in settings_source
    assert "if (event.diagnostic_code) return `合同诊断：${formatDiagnosticCode(event.diagnostic_code)}`" in settings_source
    assert "runExampleValidation(tool.contract_key, tool.tool_name)" in settings_source
    assert "@click=\"runProbe(tool.tool_name)\"" in settings_source
    assert "探测接口" in settings_source
    assert "校验示例" in settings_source
    assert "workbench-action-row" in settings_source
    assert "const runExampleValidation = async (contractKey, toolName)" in settings_source
    assert "latestAuditEventByToolName(tool.tool_name)" in settings_source
    assert "workbench-grid" in settings_source
    assert "workbench-tool-card" in settings_source
    assert "workbench-signal-grid" in settings_source
    assert "最近探测" in settings_source
    assert "样例校验" in settings_source
    assert "最近审计" in settings_source
    assert "字段暴露" in settings_source
    assert "追因摘要" in settings_source
    assert "业务工具运行态" in settings_source
    assert "接入门禁" in settings_source
    assert "只展示模式、配置状态和合同可用性" in settings_source
    assert "businessRuntimeStatus" in settings_source
    assert "businessToolReadiness" in settings_source
    assert "loadRuntimeStatus" in settings_source
    assert "loadReadiness" in settings_source
    assert "loadAuditEvents" in settings_source
    assert "formatRuntimeStatus" in settings_source
    assert "formatReadinessStatus" in settings_source
    assert "formatReadinessItemStatus" in settings_source
    assert "formatReadinessItemLabel" in settings_source
    assert "formatReadinessEvidence" in settings_source
    assert "formatIntegrationMode" in settings_source
    assert "formatConfigured" in settings_source
    assert "formatReady" in settings_source
    assert "formatMissingScopes" in settings_source
    assert "businessRuntimeStatus.status_reason" in settings_source
    assert "businessRuntimeStatus.access_control?.missing_scopes" in settings_source
    assert "businessRuntimeStatus.access_control?.read_scope_ready" in settings_source
    assert "businessRuntimeStatus.access_control?.execute_scope_ready" in settings_source
    assert "tool.endpoint_template" in settings_source
    assert "tool.integration_mode" in settings_source
    assert "tool.base_url_configured" in settings_source
    assert "tool.api_key_configured" in settings_source
    assert "tool.contract_available" in settings_source
    assert "业务工具接入安全检查" in settings_source
    assert "safetyCheckItems" in settings_source
    assert "safety-check" in settings_source
    assert "访问控制" in settings_source
    assert "审计记录" in settings_source
    assert "真实接口" in settings_source
    assert "fake-http 验证" in settings_source
    assert "进程内 fake-http 验证" in settings_source
    assert "外部真实 HTTP" in settings_source
    assert "最近调用" in settings_source
    assert "失败率" in settings_source
    assert "audit_traceability" in settings_source
    assert "intent_precheck" in settings_source
    assert "external_http_configured" in settings_source
    assert "意图预检" in settings_source
    assert "外部系统" in settings_source
    assert "enable_business_tool_audit_file" in settings_source
    assert "business_tool_audit_file" in settings_source
    assert "启用 JSONL 文件审计" in settings_source
    assert "审计文件路径" in settings_source
    assert "persisted_event_count" in settings_source
    assert "file_readable" in settings_source
    assert "llm_intent_fallback" in settings_source
    assert "contract_examples_valid" in settings_source
    assert "corpus_scene_coverage" in settings_source
    assert "业务语料" in settings_source
    assert "readinessItemById" in settings_source
    assert "missing_scenes" in settings_source
    assert "合同自检" in settings_source
    assert "businessToolReadiness.audit_event_count" in settings_source
    assert "readinessCorpusGuidance" in settings_source
    assert "ingestion_guidance" in settings_source
    assert "corpus-guidance" in settings_source
    assert "corpus-guide" in settings_source
    assert "copyCorpusCommand" in settings_source
    assert "writeClipboardText" in settings_source
    assert "copiedCorpusCommand" in settings_source
    assert "corpusCopyError" in settings_source
    assert "copy-command-button" in settings_source
    assert "corpus-guide-command" in settings_source
    assert "复制失败，请手动选择命令" in settings_source
    assert "runtime-card" in settings_source
    assert "readiness-panel" in settings_source
    assert "readiness-item" in settings_source
    assert "runtime-tool-list" in settings_source


def test_api_settings_exposes_business_tool_access_control_settings():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    settings_source = API_SETTINGS.read_text(encoding="utf-8")

    assert "BUSINESS_TOOL_TOKEN_HEADER = 'X-Business-Tool-Token'" in api_source
    assert "BUSINESS_TOOL_REQUEST_TOKEN_KEY" in api_source
    assert "getBusinessToolRequestToken" in api_source
    assert "setBusinessToolRequestToken" in api_source
    assert "businessSceneHeaders(sceneType" in api_source
    assert "withBusinessToolToken({ 'Content-Type': 'application/json' })" in api_source
    assert "business-tools/contracts" in api_source
    assert "enable_business_tool_access_control" in settings_source
    assert "business_tool_access_token" in settings_source
    assert "business_tool_read_token" in settings_source
    assert "business_tool_execute_token" in settings_source
    assert "启用订单级工具访问控制" in settings_source
    assert "服务端访问 Token" in settings_source
    assert "只读 Token" in settings_source
    assert "执行 Token" in settings_source
    assert "本浏览器请求 Token" in settings_source
    assert "X-Business-Tool-Token" in settings_source
    assert "businessToolRequestToken" in settings_source
    assert "syncBusinessToolRequestToken" in settings_source
    assert "'business_tool_access_token'" in settings_source
    assert "'business_tool_read_token'" in settings_source
    assert "'business_tool_execute_token'" in settings_source
    assert "secretFields" in settings_source


def test_api_settings_exposes_business_tool_audit_events():
    api_source = API_SERVICE.read_text(encoding="utf-8")
    settings_source = API_SETTINGS.read_text(encoding="utf-8")

    assert "getBusinessToolAuditEvents" in api_source
    assert "business-tools/audit-events" in api_source
    assert "getBusinessToolAuditEvents" in settings_source
    assert "业务工具审计" in settings_source
    assert "最近调用摘要仅展示脱敏参数" in settings_source
    assert "选择来源" in settings_source
    assert "选择依据" in settings_source
    assert "置信度" in settings_source
    assert "businessAuditEvents" in settings_source
    assert "businessAuditStatus" in settings_source
    assert "auditToolFilter" in settings_source
    assert "auditStatusFilter" in settings_source
    assert "auditSelectionSourceFilter" in settings_source
    assert "filteredBusinessAuditEvents()" in settings_source
    assert "hasAuditFilters()" in settings_source
    assert "clearAuditFilters" in settings_source
    assert "业务工具审计筛选" in settings_source
    assert "全部工具" in settings_source
    assert "全部状态" in settings_source
    assert "全部来源" in settings_source
    assert "清除筛选" in settings_source
    assert "当前筛选" in settings_source
    assert "当前筛选下暂无业务工具调用记录" in settings_source
    assert "loadAuditEvents" in settings_source
    assert "formatAuditArguments" in settings_source
    assert "formatAuditConfidence" in settings_source
    assert "formatResultKeys" in settings_source
    assert "data.audit_status" in settings_source
    assert "audit-status" in settings_source
    assert "persisted_event_count" in settings_source
    assert "file_readable" in settings_source
    assert "event.audit_id" in settings_source
    assert "审计ID" in settings_source
    assert "event.contract_version" in settings_source
    assert "合同：" in settings_source
    assert "event.endpoint_path" in settings_source
    assert "event.duration_ms" in settings_source
    assert "event.selection_source" in settings_source
    assert "event.selection_reason" in settings_source
    assert "event.confidence" in settings_source
    assert "event.error_type" in settings_source
    assert "event.diagnostic_code" in settings_source
    assert "event.missing_fields" in settings_source
    assert "event.invalid_fields" in settings_source
    assert "formatDiagnosticCode(event.diagnostic_code)" in settings_source
    assert "formatSelectionSource(event.selection_source)" in settings_source


def test_business_tools_doc_describes_profit_analysis_display_contract():
    source = BUSINESS_TOOLS_DOC.read_text(encoding="utf-8")
    quickstart = BUSINESS_TOOL_QUICKSTART_DOC.read_text(encoding="utf-8")

    assert "毛利拆解" in source
    assert "公式核对" in source
    assert "platform_commission - subsidy - coupon - channel_fee = calculated_net_profit" in source
    assert "与接口净毛利一致" in source
    assert "与接口净毛利不一致" in source
    assert "driver_income" in source
    assert "not counted again" in source
    assert "platform net-profit" in source
    assert "display_metadata_fields" in source
    assert "not part of the upstream HTTP response contract" in source
    assert "Tool-intent precheck status before or alongside execution" in source
    assert "integration workbench" in source
    assert "latest probe result, latest offline response validation result" in source
    assert "safe diagnostic codes plus missing/invalid field names" in source
    assert "BusinessToolRuntimeStatusResponse" in source
    assert "BusinessToolReadinessResponse" in source
    assert "BusinessToolProbeResponse" in source
    assert "BusinessToolValidationResponse" in source
    assert "BusinessToolBatchValidationResponse" in source
    assert "BusinessToolAuditEventsResponse" in source
    assert "/openapi.json" in source
    assert "selection_source" in source
    assert "意图识别 -> 信息补齐 -> 接口执行 -> 结果返回" in source
    assert "KPI blocks" in source
    assert "revenue/cost/net-profit ledger" in source
    assert "negative or low net margin" in source
    assert "discount erosion" in source
    assert "high channel fee" in source
    assert "公式核对" in quickstart
    assert "与接口净毛利一致" in quickstart


def test_business_tool_quickstart_covers_real_http_integration_flow():
    source = BUSINESS_TOOL_QUICKSTART_DOC.read_text(encoding="utf-8")

    assert "业务工具真实接入 Quickstart" in source
    assert "风控接口最小合同" in source
    assert "毛利接口最小合同" in source
    assert "chain_source` 不是上游接口必填字段" in source
    assert "ENABLE_BUSINESS_TOOLS=true" in source
    assert "RISK_API_BASE_URL=https://risk.example.com/api" in source
    assert "PROFIT_API_BASE_URL=https://profit.example.com/api" in source
    assert "mock" in source
    assert "fake_http" in source
    assert "external_http" in source
    assert "/api/v1/business-tools/probe" in source
    assert "/api/v1/business-tools/intent" in source
    assert "/api/v1/business-tools/validate-response" in source
    assert "/api/v1/business-tools/validate-responses" in source
    assert "/api/v1/business-tools/runtime-status" in source
    assert "/api/v1/business-tools/readiness" in source
    assert "BusinessToolRuntimeStatusResponse" in source
    assert "BusinessToolReadinessResponse" in source
    assert "BusinessToolProbeResponse" in source
    assert "BusinessToolValidationResponse" in source
    assert "BusinessToolBatchValidationResponse" in source
    assert "BusinessToolAuditEventsResponse" in source
    assert "/openapi.json" in source
    assert "接入检查工作台" in source
    assert "按工具分别保留最近一次探测和样例校验结果" in source
    assert "批量汇总真实样例诊断" in source
    assert "tool_calls" in source
    assert "订单钱流链路" in source
    assert "接口降级提示" in source


def test_readme_keeps_business_tool_integration_entrypoint_aligned():
    readme = README.read_text(encoding="utf-8")
    doc = BUSINESS_TOOLS_DOC.read_text(encoding="utf-8")
    quickstart = BUSINESS_TOOL_QUICKSTART_DOC.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "多场景 RAG + 风控/毛利业务工具接入验证" in readme
    assert "[docs/BUSINESS_TOOLS.md](./docs/BUSINESS_TOOLS.md)" in readme
    assert "[docs/BUSINESS_TOOL_QUICKSTART.md](./docs/BUSINESS_TOOL_QUICKSTART.md)" in readme
    assert "## 业务工具接入" in readme
    assert "风控和毛利订单级业务工具" in readme
    assert "低置信度或缺订单号时只提示澄清，不直接调用接口" in readme
    assert "如果你现在要接真实风控/毛利系统" in readme
    assert "| 阶段 1 | MVP 单场景（风控规则） | 2-3周 | ✅ 已完成 |" in readme
    assert "| 阶段 2 | 多轮对话 + 会话管理 | 2周 | ✅ 已完成基础能力 |" in readme
    assert "已支持多场景与业务工具接入验证" in readme
    assert "### 已完成能力摘要" in readme

    for setting in [
        "ENABLE_BUSINESS_TOOLS=true",
        "ENABLE_BUSINESS_TOOL_LLM_INTENT=false",
        "ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false",
        "ENABLE_BUSINESS_TOOL_AUDIT_FILE=false",
        "RISK_API_BASE_URL=",
        "RISK_API_KEY=",
        "PROFIT_API_BASE_URL=",
        "PROFIT_API_KEY=",
    ]:
        assert setting in readme
        assert setting in env_example
        assert setting in doc
        if setting != "ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false":
            assert setting in quickstart or setting.endswith("=")

    for endpoint in [
        "/api/v1/business-tools/contracts",
        "/api/v1/business-tools/runtime-status",
        "/api/v1/business-tools/readiness",
        "/api/v1/business-tools/intent",
        "/api/v1/business-tools/probe",
        "/api/v1/business-tools/validate-response",
        "/api/v1/business-tools/validate-responses",
        "/api/v1/business-tools/audit-events",
    ]:
        assert endpoint in readme
        assert endpoint in doc

    for readme_term, doc_term in [
        ("API 设置", "API 设置"),
        ("tool_calls", "tool_calls"),
        ("审计 ID", "Audit ID"),
        ("接口降级提示", "接口降级提示"),
        ("error_type", "error_type"),
    ]:
        assert readme_term in readme
        assert doc_term in doc


def test_env_example_contains_business_tool_runtime_settings():
    source = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "ENABLE_BUSINESS_TOOLS=true" in source
    assert "BUSINESS_TOOL_TIMEOUT=5" in source
    assert "ENABLE_BUSINESS_TOOL_LLM_INTENT=false" in source
    assert "BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE=0.75" in source
    assert "ENABLE_BUSINESS_TOOL_AUDIT_FILE=false" in source
    assert "BUSINESS_TOOL_AUDIT_FILE=logs/business_tool_audit.jsonl" in source
    assert "ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false" in source
    assert "BUSINESS_TOOL_ACCESS_TOKEN=" in source
    assert "BUSINESS_TOOL_READ_TOKEN=" in source
    assert "BUSINESS_TOOL_EXECUTE_TOKEN=" in source
    assert "RISK_API_BASE_URL=" in source
    assert "RISK_API_KEY=" in source
    assert "PROFIT_API_BASE_URL=" in source
    assert "PROFIT_API_KEY=" in source
