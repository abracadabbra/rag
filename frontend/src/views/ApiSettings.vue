<template>
  <div class="api-settings">
    <header class="header">
      <router-link to="/" class="back-btn">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M12 4L6 9l6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </router-link>
      <div class="title-group">
        <h1>API 设置</h1>
        <span class="subtitle">配置大语言模型服务</span>
      </div>
    </header>

    <div class="content">
      <div class="settings-card">
        <h2>LLM 提供商</h2>
        <div class="form-group">
          <label>当前提供商</label>
          <select v-model="form.llm_provider" class="select-input">
            <option value="minimax">MiniMax</option>
            <option value="openai">OpenAI</option>
            <option value="local">本地 LLM</option>
          </select>
        </div>
      </div>

      <div v-if="form.llm_provider === 'minimax'" class="settings-card">
        <h2>MiniMax API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.minimax_api_key" type="password" placeholder="sk-..." class="text-input" />
          <span class="hint">从 MiniMax 控制台获取 API Key</span>
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.minimax_api_base" type="text" placeholder="https://topapi.link/v1" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.minimax_model" type="text" placeholder="MiniMax-M2.7-highspeed" class="text-input" />
        </div>
      </div>

      <div v-if="form.llm_provider === 'openai'" class="settings-card">
        <h2>OpenAI API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.openai_api_key" type="password" placeholder="sk-..." class="text-input" />
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.openai_api_base" type="text" placeholder="https://api.openai.com/v1" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.openai_model" type="text" placeholder="gpt-4-turbo-preview" class="text-input" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Temperature</label>
            <input v-model.number="form.openai_temperature" type="number" min="0" max="2" step="0.1" class="text-input small" />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input v-model.number="form.openai_max_tokens" type="number" min="1" max="32000" class="text-input small" />
          </div>
        </div>
      </div>

      <div v-if="form.llm_provider === 'local'" class="settings-card">
        <h2>本地 LLM</h2>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.local_llm_base_url" type="text" placeholder="http://localhost:11434" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.local_llm_model" type="text" placeholder="qwen2.5:72b" class="text-input" />
        </div>
      </div>

      <div class="settings-card">
        <h2>业务系统接口</h2>
        <label class="toggle-row">
          <input v-model="form.enable_business_tools" type="checkbox" />
          <span>启用风控/毛利业务工具</span>
        </label>
        <label class="toggle-row">
          <input v-model="form.enable_business_tool_access_control" type="checkbox" />
          <span>启用订单级工具访问控制</span>
        </label>
        <div class="form-group">
          <label>调用超时（秒）</label>
          <input
            v-model.number="form.business_tool_timeout"
            type="number"
            min="1"
            max="60"
            step="1"
            class="text-input small"
          />
          <span class="hint">Base URL 留空时使用本地 mock 数据</span>
        </div>
        <div class="form-group">
          <label>风控 API Base URL</label>
          <input v-model="form.risk_api_base_url" type="text" placeholder="https://risk.example.com/api" class="text-input" />
        </div>
        <div class="form-group">
          <label>风控 API Key</label>
          <input v-model="form.risk_api_key" type="password" placeholder="Bearer token" class="text-input" />
        </div>
        <div class="form-group">
          <label>毛利 API Base URL</label>
          <input v-model="form.profit_api_base_url" type="text" placeholder="https://profit.example.com/api" class="text-input" />
        </div>
        <div class="form-group">
          <label>毛利 API Key</label>
          <input v-model="form.profit_api_key" type="password" placeholder="Bearer token" class="text-input" />
        </div>
        <div class="form-group">
          <label>服务端访问 Token</label>
          <input v-model="form.business_tool_access_token" type="password" placeholder="X-Business-Tool-Token" class="text-input" />
          <span class="hint">写入后端期望的 token；空值不会覆盖已有配置</span>
        </div>
        <div class="form-group">
          <label>只读 Token</label>
          <input v-model="form.business_tool_read_token" type="password" placeholder="审计读取 / 响应样例校验" class="text-input" />
          <span class="hint">只能访问审计读取和响应样例校验；空值不会覆盖已有配置</span>
        </div>
        <div class="form-group">
          <label>执行 Token</label>
          <input v-model="form.business_tool_execute_token" type="password" placeholder="订单查询 / SSE / 接口探测" class="text-input" />
          <span class="hint">允许订单查询、SSE 和接口探测，也可访问只读入口</span>
        </div>
        <label class="toggle-row">
          <input v-model="form.enable_business_tool_audit_file" type="checkbox" />
          <span>启用 JSONL 文件审计</span>
        </label>
        <div class="form-group">
          <label>审计文件路径</label>
          <input
            v-model="form.business_tool_audit_file"
            type="text"
            placeholder="logs/business_tool_audit.jsonl"
            class="text-input"
          />
          <span class="hint">用于持久化脱敏后的业务工具调用审计；建议使用仓库内相对路径</span>
        </div>
        <div class="form-group">
          <label>本浏览器请求 Token</label>
          <input
            v-model="businessToolRequestToken"
            type="password"
            placeholder="当前标签页用于 X-Business-Tool-Token"
            class="text-input"
            @input="syncBusinessToolRequestToken"
          />
          <span class="hint">仅保存在当前浏览器会话，用于订单级查询、探测和审计请求</span>
        </div>
        <div class="probe-section">
          <div class="intent-inspect-section">
            <label>工具意图预检</label>
            <div class="intent-inspect-grid">
              <select v-model="intentInspectSceneType" class="select-input">
                <option value="risk_rule">风控场景</option>
                <option value="profit">毛利场景</option>
              </select>
              <input
                v-model="intentInspectQuery"
                type="text"
                placeholder="例如：查询订单 ORD88888 的抽成和司机收入"
                class="text-input"
              />
              <button
                class="btn secondary"
                :disabled="loading || intentInspectLoading || !intentInspectQuery.trim()"
                @click="runIntentInspect"
              >
                {{ intentInspectLoading ? '预检中...' : '预检意图' }}
              </button>
            </div>
            <span class="hint">只判断会不会选风控/毛利工具，不调用真实订单接口</span>
            <div v-if="intentInspectError" class="probe-result error-text">{{ intentInspectError }}</div>
            <div v-if="intentInspectResult" class="probe-result">
              <div class="probe-result-header">
                <span>{{ intentInspectResult.label || intentInspectResult.tool_name || '未选择工具' }}</span>
                <strong :class="intentInspectResult.needs_clarification ? 'invalid' : 'valid'">
                  {{ intentInspectStateLabel(intentInspectResult) }}
                </strong>
              </div>
              <p>{{ intentInspectResult.reason }}</p>
              <div class="probe-meta">
                <span>来源：{{ formatSelectionSource(intentInspectResult.selection_source) }}</span>
                <span>置信度：{{ formatAuditConfidence(intentInspectResult.confidence) }}</span>
                <span>订单号：{{ intentInspectResult.order_id || '-' }}</span>
              </div>
              <div
                v-if="intentInspectResult.missing_fields?.length || intentInspectResult.clarification_options?.length"
                class="probe-diagnostic-details"
              >
                <span v-if="intentInspectResult.missing_fields?.length">
                  待补充：{{ intentInspectResult.missing_fields.join('、') }}
                </span>
                <span v-if="intentInspectResult.clarification_options?.length">
                  提示：{{ intentInspectResult.clarification_options[0] }}
                </span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>接口探测订单号</label>
            <input v-model="probeOrderId" type="text" placeholder="ORD88888" class="text-input" />
            <span class="hint">
              订单号格式：字母/数字开头，仅允许字母、数字、_、-，最多 128 位；当前合同 {{ probeOrderIdPatternText() }}；Base URL 留空时探测 mock 数据
            </span>
            <span v-if="probeOrderIdError()" class="hint error-text">{{ probeOrderIdError() }}</span>
          </div>
          <div class="probe-actions">
            <button
              class="btn secondary"
              :disabled="loading || probeLoading || !isProbeOrderIdValid(probeOrderId)"
              @click="runProbe('get_risk_event_detail')"
            >
              {{ probeLoading === 'get_risk_event_detail' ? '探测中...' : '测试风控接口' }}
            </button>
            <button
              class="btn secondary"
              :disabled="loading || probeLoading || !isProbeOrderIdValid(probeOrderId)"
              @click="runProbe('get_profit_chain_detail')"
            >
              {{ probeLoading === 'get_profit_chain_detail' ? '探测中...' : '测试毛利接口' }}
            </button>
          </div>
          <div v-if="probeError" class="probe-result error-text">{{ probeError }}</div>
          <div v-if="probeResult" class="probe-result">
            <div class="probe-result-header">
              <span>{{ probeResult.label }}</span>
              <strong :class="probeResult.status">{{ probeResult.status === 'success' ? '成功' : '失败' }}</strong>
            </div>
            <p>{{ probeResult.summary }}</p>
            <p v-if="probeResult.diagnostic" class="probe-diagnostic">
              合同诊断：{{ probeResult.diagnostic }}
            </p>
            <div v-if="hasProbeDiagnosticDetails(probeResult)" class="probe-diagnostic-details">
              <span v-if="probeResult.diagnostic_code">
                类型：{{ formatDiagnosticCode(probeResult.diagnostic_code) }}
              </span>
              <span v-if="probeResult.missing_fields?.length">
                缺失字段：{{ probeResult.missing_fields.join('、') }}
              </span>
              <span v-if="probeResult.invalid_fields?.length">
                异常字段：{{ probeResult.invalid_fields.join('、') }}
              </span>
            </div>
            <div class="probe-meta">
              <span>来源：{{ formatDataSource(probeResult.data_source) }}</span>
              <span>模式：{{ formatIntegrationMode(probeResult.integration_mode) }}</span>
              <span>耗时：{{ probeResult.duration_ms }}ms</span>
              <span>接口：{{ probeResult.endpoint_path }}</span>
            </div>
          </div>
          <div class="response-validation-section">
            <label>响应样例校验</label>
            <textarea
              v-model="validatePayloadText"
              class="text-input json-input"
              rows="8"
              spellcheck="false"
            ></textarea>
            <div class="probe-actions">
              <button
                class="btn secondary"
                :disabled="!businessContracts?.risk?.example_response"
                @click="fillValidationPayload('risk')"
              >
                填入风控示例
              </button>
              <button
                class="btn secondary"
                :disabled="!businessContracts?.profit?.example_response"
                @click="fillValidationPayload('profit')"
              >
                填入毛利示例
              </button>
              <button
                class="btn secondary"
                :disabled="loading || validateLoading"
                @click="runResponseValidation('get_risk_event_detail')"
              >
                {{ validateLoading === 'get_risk_event_detail' ? '校验中...' : '校验风控响应' }}
              </button>
              <button
                class="btn secondary"
                :disabled="loading || validateLoading"
                @click="runResponseValidation('get_profit_chain_detail')"
              >
                {{ validateLoading === 'get_profit_chain_detail' ? '校验中...' : '校验毛利响应' }}
              </button>
            </div>
            <div v-if="validateError" class="probe-result error-text">{{ validateError }}</div>
            <div v-if="validateResult" class="probe-result">
              <div class="probe-result-header">
                <span>{{ validateResult.label }}</span>
                <strong :class="validateResult.status">
                  {{ validateResult.status === 'valid' ? '通过' : '未通过' }}
                </strong>
              </div>
              <p>{{ validateResult.summary }}</p>
              <p v-if="validateResult.diagnostic" class="probe-diagnostic">
                合同诊断：{{ validateResult.diagnostic }}
              </p>
              <div v-if="hasProbeDiagnosticDetails(validateResult)" class="probe-diagnostic-details">
                <span v-if="validateResult.diagnostic_code">
                  类型：{{ formatDiagnosticCode(validateResult.diagnostic_code) }}
                </span>
                <span v-if="validateResult.missing_fields?.length">
                  缺失字段：{{ validateResult.missing_fields.join('、') }}
                </span>
                <span v-if="validateResult.invalid_fields?.length">
                  异常字段：{{ validateResult.invalid_fields.join('、') }}
                </span>
              </div>
              <div class="probe-meta">
                <span>耗时：{{ validateResult.duration_ms }}ms</span>
                <span>可展示字段：{{ formatResultKeys(validateResult.exposed_result_keys) }}</span>
                <span v-if="validateResult.ignored_result_keys?.length">
                  未展示字段：{{ formatResultKeys(validateResult.ignored_result_keys) }}
                </span>
              </div>
            </div>
            <label>
              批量响应样例 JSON
              <textarea
                v-model="batchValidatePayloadText"
                class="json-textarea compact"
                placeholder='粘贴 JSON 数组，或 {"payloads":[...]}'
                rows="7"
                spellcheck="false"
              ></textarea>
            </label>
            <div class="probe-actions">
              <button
                class="btn secondary"
                :disabled="!businessContracts?.risk?.example_response"
                @click="fillBatchValidationPayload('risk')"
              >
                批量填入风控示例
              </button>
              <button
                class="btn secondary"
                :disabled="!businessContracts?.profit?.example_response"
                @click="fillBatchValidationPayload('profit')"
              >
                批量填入毛利示例
              </button>
              <button
                class="btn secondary"
                :disabled="loading || batchValidateLoading"
                @click="runBatchResponseValidation('get_risk_event_detail')"
              >
                {{ batchValidateLoading === 'get_risk_event_detail' ? '批量校验中...' : '批量校验风控' }}
              </button>
              <button
                class="btn secondary"
                :disabled="loading || batchValidateLoading"
                @click="runBatchResponseValidation('get_profit_chain_detail')"
              >
                {{ batchValidateLoading === 'get_profit_chain_detail' ? '批量校验中...' : '批量校验毛利' }}
              </button>
            </div>
            <div v-if="batchValidateError" class="probe-result error-text">{{ batchValidateError }}</div>
            <div v-if="batchValidateResult" class="probe-result">
              <div class="probe-result-header">
                <span>{{ batchValidateResult.label }}批量校验</span>
                <strong :class="batchValidateResult.status">
                  {{ batchValidateResult.status === 'valid' ? '全部通过' : '存在异常' }}
                </strong>
              </div>
              <p>{{ batchValidateResult.summary }}</p>
              <div class="batch-validation-summary">
                <span>总数：{{ batchValidateResult.validation_summary?.total || 0 }}</span>
                <span>通过：{{ batchValidateResult.validation_summary?.valid_count || 0 }}</span>
                <span>失败：{{ batchValidateResult.validation_summary?.invalid_count || 0 }}</span>
                <span>诊断：{{ formatDiagnosticCounts(batchValidateResult.validation_summary?.diagnostic_codes) }}</span>
                <span v-if="batchValidateResult.validation_summary?.ignored_result_keys?.length">
                  未展示字段：{{ formatResultKeys(batchValidateResult.validation_summary.ignored_result_keys) }}
                </span>
              </div>
              <div
                v-if="hasBatchValidationDetails(batchValidateResult)"
                class="probe-diagnostic-details"
              >
                <span v-if="batchValidateResult.validation_summary?.missing_fields?.length">
                  缺失字段：{{ batchValidateResult.validation_summary.missing_fields.join('、') }}
                </span>
                <span v-if="batchValidateResult.validation_summary?.invalid_fields?.length">
                  异常字段：{{ batchValidateResult.validation_summary.invalid_fields.join('、') }}
                </span>
              </div>
              <div class="batch-validation-items">
                <div
                  v-for="item in batchValidatePreviewItems(batchValidateResult)"
                  :key="item.index"
                  class="batch-validation-item"
                  :class="item.status"
                >
                  <strong>#{{ item.index + 1 }} {{ item.status === 'valid' ? '通过' : '未通过' }}</strong>
                  <span>{{ batchValidationItemSummary(item) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="settings-card workbench-card">
        <div class="workbench-header">
          <div class="workbench-header-copy">
            <h2>接入检查工作台</h2>
            <p>按工具汇总合同版本、接入模式、最近探测、样例校验和脱敏审计，方便快速判断哪一段链路需要处理。</p>
          </div>
          <div class="workbench-header-actions">
            <div class="workbench-overall">
              <span>总体门禁</span>
              <strong :class="businessToolReadiness?.overall_status || 'idle'">
                {{ workbenchOverallStatusLabel() }}
              </strong>
              <small>{{ workbenchOverallStatusHint() }}</small>
            </div>
            <div class="workbench-action-buttons">
              <button
                class="btn secondary compact"
                :disabled="workbenchLoading()"
                @click="refreshBusinessWorkbench"
              >
                {{ workbenchLoading() ? '刷新中...' : '刷新总览' }}
              </button>
              <button
                type="button"
                class="btn secondary compact"
                :disabled="workbenchLoading() || !canDownloadBusinessAcceptancePack()"
                @click="downloadBusinessAcceptancePack"
              >
                导出验收包
              </button>
            </div>
          </div>
        </div>
        <div v-if="acceptancePackDownloadMessage" class="workbench-download-hint">
          {{ acceptancePackDownloadMessage }}
        </div>

        <div class="workbench-grid">
          <section
            v-for="tool in businessWorkbenchTools"
            :key="tool.tool_name"
            class="workbench-tool-card"
            :class="toolWorkbenchTone(tool.tool_name)"
          >
            <div class="workbench-tool-head">
              <div class="workbench-tool-title">
                <span>{{ tool.label }}</span>
                <p>{{ tool.description }}</p>
              </div>
              <div class="contract-badges workbench-badges">
                <code>{{ tool.tool_name }}</code>
                <em>{{ toolContractVersion(tool.contract_key) }}</em>
              </div>
            </div>

            <div class="workbench-runtime-row">
              <div class="workbench-runtime-main">
                <span>接入模式</span>
                <strong>{{ toolRuntimeMode(tool.tool_name) }}</strong>
                <small>{{ toolRuntimeHint(tool.tool_name) }}</small>
              </div>
              <div class="workbench-runtime-state">
                <span>合同</span>
                <strong>{{ toolContractState(tool.contract_key, tool.tool_name) }}</strong>
              </div>
            </div>

            <div class="workbench-signal-grid">
              <div class="workbench-signal-item">
                <span>最近探测</span>
                <strong>{{ toolProbeState(tool.tool_name) }}</strong>
                <small>{{ toolProbeHint(tool.tool_name) }}</small>
              </div>
              <div class="workbench-signal-item">
                <span>样例校验</span>
                <strong>{{ toolValidationState(tool.tool_name) }}</strong>
                <small>{{ toolValidationHint(tool.tool_name) }}</small>
              </div>
              <div class="workbench-signal-item">
                <span>最近审计</span>
                <strong>{{ toolAuditState(tool.tool_name) }}</strong>
                <small>{{ toolAuditHint(tool.tool_name) }}</small>
              </div>
              <div class="workbench-signal-item">
                <span>字段暴露</span>
                <strong>{{ toolContractExposure(tool.contract_key) }}</strong>
                <small>{{ toolContractHint(tool.contract_key) }}</small>
              </div>
            </div>

            <div class="workbench-action-row">
              <button
                type="button"
                class="btn secondary compact"
                :disabled="loading || probeLoading || !isProbeOrderIdValid(probeOrderId)"
                @click="runProbe(tool.tool_name)"
              >
                {{ probeLoading === tool.tool_name ? '探测中...' : '探测接口' }}
              </button>
              <button
                type="button"
                class="btn secondary compact"
                :disabled="loading || validateLoading || !toolContract(tool.contract_key)?.example_response"
                @click="runExampleValidation(tool.contract_key, tool.tool_name)"
              >
                {{ validateLoading === tool.tool_name ? '校验中...' : '校验示例' }}
              </button>
            </div>

            <div v-if="latestAuditEventByToolName(tool.tool_name)" class="workbench-audit-foot">
              <span>追因摘要</span>
              <small>
                {{ toolAuditFootnote(tool.tool_name) }}
              </small>
            </div>
          </section>
        </div>
      </div>

      <div class="settings-card runtime-card">
        <h2>业务工具运行态</h2>
        <div
          v-if="businessRuntimeStatus"
          class="safety-check"
          aria-label="业务工具接入安全检查"
        >
          <div
            v-for="item in safetyCheckItems()"
            :key="item.label"
            class="safety-check-item"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.hint }}</small>
          </div>
        </div>
        <div class="runtime-toolbar">
          <span>只展示模式、配置状态和合同可用性，不返回 URL、Token 或 API Key</span>
          <button class="btn secondary compact" :disabled="runtimeLoading" @click="loadRuntimeStatus">
            {{ runtimeLoading ? '刷新中...' : '刷新' }}
          </button>
        </div>
        <div v-if="readinessLoading" class="runtime-empty">接入检查加载中...</div>
        <div v-else-if="readinessError" class="runtime-empty error-text">{{ readinessError }}</div>
        <div v-else-if="businessToolReadiness" class="readiness-panel">
          <div class="readiness-head">
            <div>
              <span>接入门禁</span>
              <strong :class="businessToolReadiness.overall_status">
                {{ formatReadinessStatus(businessToolReadiness.overall_status) }}
              </strong>
            </div>
            <small>{{ businessToolReadiness.status_reason }}</small>
          </div>
          <div class="readiness-counts">
            <span>通过 {{ businessToolReadiness.passed?.length || 0 }}</span>
            <span>警告 {{ businessToolReadiness.warnings?.length || 0 }}</span>
            <span>阻塞 {{ businessToolReadiness.blockers?.length || 0 }}</span>
            <span>审计 {{ businessToolReadiness.audit_event_count || 0 }}/{{ businessToolReadiness.audit_event_limit || 0 }}</span>
          </div>
          <div class="readiness-list">
            <div
              v-for="item in businessToolReadiness.items || []"
              :key="item.id"
              class="readiness-item"
              :class="item.status"
            >
              <div class="readiness-item-head">
                <span>{{ formatReadinessItemLabel(item.id) }}</span>
                <strong>{{ formatReadinessItemStatus(item.status) }}</strong>
              </div>
              <p>{{ item.summary }}</p>
              <small>{{ formatReadinessEvidence(item.id, item.evidence) }}</small>
              <div
                v-if="readinessCorpusGuidance(item).length"
                class="corpus-guidance"
              >
                <div
                  v-for="guide in readinessCorpusGuidance(item)"
                  :key="guide.scene_type"
                  class="corpus-guide"
                >
                  <span>{{ guide.label }}</span>
                  <div class="corpus-guide-command">
                    <code>{{ guide.command }}</code>
                    <button
                      type="button"
                      class="copy-command-button"
                      :aria-label="`复制${guide.label}导入命令`"
                      @click="copyCorpusCommand(guide)"
                    >
                      {{ copiedCorpusCommand === guide.command ? '已复制' : '复制' }}
                    </button>
                  </div>
                  <small
                    v-if="corpusCopyError === guide.command"
                    class="corpus-copy-state error-text"
                  >
                    复制失败，请手动选择命令
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="runtimeLoading" class="runtime-empty">运行态加载中...</div>
        <div v-else-if="runtimeError" class="runtime-empty error-text">{{ runtimeError }}</div>
        <div v-else-if="businessRuntimeStatus" class="runtime-status">
          <div class="runtime-summary">
            <span>整体状态</span>
            <strong :class="businessRuntimeStatus.status">
              {{ formatRuntimeStatus(businessRuntimeStatus.status) }}
            </strong>
          </div>
          <div class="runtime-reason">
            <span>{{ businessRuntimeStatus.status_reason || '暂无状态原因' }}</span>
            <strong v-if="businessRuntimeStatus.access_control?.missing_scopes?.length">
              缺少 {{ formatMissingScopes(businessRuntimeStatus.access_control.missing_scopes) }}
            </strong>
          </div>
          <div class="runtime-grid">
            <div class="runtime-cell">
              <span>业务工具</span>
              <strong>{{ businessRuntimeStatus.business_tools?.enabled ? '已启用' : '已停用' }}</strong>
              <small>超时 {{ businessRuntimeStatus.business_tools?.timeout_seconds }}s · {{ businessRuntimeStatus.business_tools?.tool_count || 0 }} 个工具</small>
            </div>
            <div class="runtime-cell">
              <span>访问控制</span>
              <strong>{{ businessRuntimeStatus.access_control?.enabled ? '已启用' : '未启用' }}</strong>
              <small>
                读 {{ formatReady(businessRuntimeStatus.access_control?.read_scope_ready) }} ·
                执行 {{ formatReady(businessRuntimeStatus.access_control?.execute_scope_ready) }}
              </small>
            </div>
            <div class="runtime-cell">
              <span>审计</span>
              <strong>{{ businessRuntimeStatus.audit?.file_enabled ? '文件审计开启' : '内存审计' }}</strong>
              <small>{{ businessRuntimeStatus.audit?.memory_event_count || 0 }}/{{ businessRuntimeStatus.audit?.memory_event_limit || 0 }} 条 · {{ businessRuntimeStatus.audit?.file_name || '未配置文件名' }}</small>
            </div>
            <div class="runtime-cell">
              <span>LLM 兜底</span>
              <strong>{{ businessRuntimeStatus.llm_intent?.enabled ? '已启用' : '未启用' }}</strong>
              <small>{{ formatLlmIntentRuntimeSummary(businessRuntimeStatus.llm_intent) }}</small>
              <small>
                尝试 {{ businessRuntimeStatus.llm_intent?.attempt_count || 0 }} 次 ·
                成功 {{ businessRuntimeStatus.llm_intent?.success_count || 0 }} 次 ·
                失败 {{ businessRuntimeStatus.llm_intent?.error_count || 0 }} 次
              </small>
            </div>
          </div>
          <div class="runtime-token-row">
            <span>全量 Token：{{ formatConfigured(businessRuntimeStatus.access_control?.full_access_configured) }}</span>
            <span>只读 Token：{{ formatConfigured(businessRuntimeStatus.access_control?.read_configured) }}</span>
            <span>执行 Token：{{ formatConfigured(businessRuntimeStatus.access_control?.execute_configured) }}</span>
          </div>
          <div class="runtime-tool-list">
            <div
              v-for="tool in businessRuntimeStatus.tools || []"
              :key="tool.tool_name"
              class="runtime-tool"
            >
              <div class="runtime-tool-head">
                <span>{{ tool.label }}</span>
                <strong>{{ formatDataSource(tool.data_source) }}</strong>
              </div>
              <div class="runtime-tool-meta">
                <span>接口：{{ tool.endpoint_template }}</span>
                <span>模式：{{ formatIntegrationMode(tool.integration_mode) }}</span>
                <span>Base URL：{{ formatConfigured(tool.base_url_configured) }}</span>
                <span>API Key：{{ formatConfigured(tool.api_key_configured) }}</span>
                <span>合同：{{ formatReady(tool.contract_available) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="runtime-empty">暂无运行态数据</div>
      </div>

      <div class="settings-card audit-card">
        <h2>业务工具审计</h2>
        <div class="audit-toolbar">
          <span>最近调用摘要仅展示脱敏参数、选择来源、选择依据、置信度、接口模板、耗时、来源和结果字段名</span>
          <button class="btn secondary compact" :disabled="auditLoading" @click="loadAuditEvents">
            {{ auditLoading ? '刷新中...' : '刷新' }}
          </button>
        </div>
        <div class="audit-filter-row" aria-label="业务工具审计筛选">
          <label>
            工具
            <select v-model="auditToolFilter" class="select-input compact-select">
              <option value="all">全部工具</option>
              <option value="get_risk_event_detail">风控接口</option>
              <option value="get_profit_chain_detail">毛利接口</option>
            </select>
          </label>
          <label>
            状态
            <select v-model="auditStatusFilter" class="select-input compact-select">
              <option value="all">全部状态</option>
              <option value="success">成功</option>
              <option value="error">失败</option>
            </select>
          </label>
          <label>
            选择来源
            <select v-model="auditSelectionSourceFilter" class="select-input compact-select">
              <option value="all">全部来源</option>
              <option value="rules">规则命中</option>
              <option value="llm">LLM 兜底</option>
              <option value="probe">手动探测</option>
              <option value="none">未触发</option>
            </select>
          </label>
          <button
            type="button"
            class="btn secondary compact"
            :disabled="!hasAuditFilters()"
            @click="clearAuditFilters"
          >
            清除筛选
          </button>
        </div>
        <div v-if="businessAuditStatus" class="audit-status">
          <span>文件审计：{{ businessAuditStatus.file_enabled ? '已启用' : '未启用' }}</span>
          <span>回读：{{ businessAuditStatus.file_readable ? '可用' : '未回读' }}</span>
          <span>落盘：{{ businessAuditStatus.persisted_event_count || 0 }} 条</span>
          <span>内存：{{ businessAuditStatus.memory_event_count || 0 }}/{{ businessAuditStatus.memory_event_limit || 0 }}</span>
          <span>当前筛选：{{ filteredBusinessAuditEvents().length }}/{{ businessAuditEvents.length }}</span>
        </div>
        <div v-if="auditLoading" class="audit-empty">审计加载中...</div>
        <div v-else-if="auditError" class="audit-empty error-text">{{ auditError }}</div>
        <div v-else-if="filteredBusinessAuditEvents().length" class="audit-list">
          <div
            v-for="event in filteredBusinessAuditEvents()"
            :key="`${event.timestamp}-${event.tool_name}-${event.duration_ms}`"
            class="audit-event"
          >
            <div class="audit-event-head">
              <span>{{ event.label || event.tool_name }}</span>
              <strong :class="event.status">{{ event.status === 'success' ? '成功' : '失败' }}</strong>
            </div>
            <div class="audit-meta">
              <span>{{ formatAuditTime(event.timestamp) }}</span>
              <span>审计ID：{{ event.audit_id || '-' }}</span>
              <span>合同：{{ event.contract_version || '未标版本' }}</span>
              <span>来源：{{ formatDataSource(event.data_source) }}</span>
              <span>耗时：{{ event.duration_ms }}ms</span>
            </div>
            <div class="audit-meta">
              <span>接口：{{ event.endpoint_path || '-' }}</span>
              <span>参数：{{ formatAuditArguments(event.arguments) }}</span>
            </div>
            <div
              v-if="event.selection_reason || (event.confidence !== undefined && event.confidence !== null)"
              class="audit-selection"
            >
              <span v-if="event.selection_source">来源：{{ formatSelectionSource(event.selection_source) }}</span>
              <span v-if="event.selection_reason">依据：{{ event.selection_reason }}</span>
              <span v-if="event.confidence !== undefined && event.confidence !== null">
                置信度：{{ formatAuditConfidence(event.confidence) }}
              </span>
            </div>
            <div class="audit-meta">
              <span>结果字段：{{ formatResultKeys(event.result_keys) }}</span>
              <span v-if="event.error_type">错误类型：{{ event.error_type }}</span>
            </div>
            <div
              v-if="event.diagnostic_code || event.missing_fields?.length || event.invalid_fields?.length"
              class="audit-selection"
            >
              <span v-if="event.diagnostic_code">
                合同诊断：{{ formatDiagnosticCode(event.diagnostic_code) }}
              </span>
              <span v-if="event.missing_fields?.length">
                缺失字段：{{ event.missing_fields.join('、') }}
              </span>
              <span v-if="event.invalid_fields?.length">
                异常字段：{{ event.invalid_fields.join('、') }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="audit-empty">
          {{ businessAuditEvents.length ? '当前筛选下暂无业务工具调用记录' : '暂无业务工具调用记录' }}
        </div>
      </div>

      <div class="settings-card">
        <h2>业务工具意图识别</h2>
        <label class="toggle-row">
          <input v-model="form.enable_business_tool_llm_intent" type="checkbox" />
          <span>规则未命中时启用 LLM 兜底识别</span>
        </label>
        <div class="form-group">
          <label>最低置信度</label>
          <input
            v-model.number="form.business_tool_llm_intent_min_confidence"
            type="number"
            min="0"
            max="1"
            step="0.01"
            class="text-input small"
          />
          <span class="hint">仅影响 LLM 兜底识别；低于阈值时不会调用业务接口或发起缺字段澄清</span>
        </div>
      </div>

      <div class="settings-card business-contract-card">
        <div class="contract-card-head">
          <h2>业务接口合同</h2>
          <button
            type="button"
            class="btn secondary compact"
            :disabled="contractsLoading || !businessContracts"
            @click="downloadBusinessContracts"
          >
            导出 JSON
          </button>
        </div>
        <div v-if="contractDownloadMessage" class="contract-download-hint">
          {{ contractDownloadMessage }}
        </div>
        <div v-if="contractsLoading" class="contract-empty">合同加载中...</div>
        <div v-else-if="contractsError" class="contract-empty error-text">{{ contractsError }}</div>
        <div v-else-if="businessContracts" class="contract-list">
          <div
            v-if="businessContracts.integration_handoff"
            class="contract-panel contract-panel-wide"
          >
            <div class="contract-header">
              <span>真实系统联调交接</span>
              <div class="contract-badges">
                <em>integration_handoff</em>
              </div>
            </div>
            <div class="contract-section">
              <strong>联调顺序</strong>
              <div class="field-chip-list handoff-step-list">
                <span
                  v-for="step in businessContracts.integration_handoff.recommended_sequence || []"
                  :key="`handoff-step-${step}`"
                  class="field-chip"
                >
                  {{ formatHandoffStep(step) }}
                </span>
              </div>
            </div>
            <div class="contract-section">
              <strong>可复制命令</strong>
              <div class="handoff-command-list">
                <div
                  v-for="item in handoffCommandEntries(businessContracts.integration_handoff.commands)"
                  :key="`handoff-command-${item.name}`"
                  class="handoff-command-item"
                >
                  <span>{{ formatHandoffStep(item.name) }}</span>
                  <code>{{ item.command }}</code>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>上线门禁</strong>
              <div class="field-chip-list optional-chip-list">
                <span
                  v-for="gate in businessContracts.integration_handoff.go_live_gates || []"
                  :key="`handoff-gate-${gate}`"
                  class="field-chip optional"
                >
                  {{ formatReadinessItemLabel(gate) }}<em>{{ gate }}</em>
                </span>
              </div>
            </div>
            <div class="contract-section">
              <strong>模式语义</strong>
              <div class="field-catalog-list">
                <div
                  v-for="item in handoffModeEntries(businessContracts.integration_handoff.integration_modes)"
                  :key="`handoff-mode-${item.mode}`"
                  class="field-catalog-item"
                >
                  <div class="field-catalog-head">
                    <span>{{ formatIntegrationMode(item.mode) }}</span>
                    <code>{{ item.mode }}</code>
                  </div>
                  <p>{{ item.description }}</p>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>安全说明</strong>
              <div class="handoff-note-list">
                <span
                  v-for="note in businessContracts.integration_handoff.safety_notes || []"
                  :key="`handoff-note-${note}`"
                >
                  {{ note }}
                </span>
              </div>
            </div>
          </div>

          <div
            v-for="scene in promptContractEntries(businessContracts.prompt_contract)"
            :key="`prompt-contract-${scene.scene_type}`"
            class="contract-panel"
          >
            <div class="contract-header">
              <span>回答口径合同</span>
              <div class="contract-badges">
                <code>{{ scene.scene_type }}</code>
                <em>{{ scene.name }}</em>
              </div>
            </div>
            <div class="contract-section">
              <strong>适用场景</strong>
              <p>{{ scene.focus }}</p>
            </div>
            <div class="contract-section">
              <strong>回答要求</strong>
              <div class="field-chip-list">
                <span
                  v-for="requirement in scene.requirements || []"
                  :key="`prompt-requirement-${scene.scene_type}-${requirement}`"
                  class="field-chip"
                >
                  {{ requirement }}
                </span>
              </div>
            </div>
            <div class="contract-section">
              <strong>建议输出段落</strong>
              <div class="field-chip-list optional-chip-list">
                <span
                  v-for="section in scene.answer_structure || []"
                  :key="`prompt-answer-structure-${scene.scene_type}-${section}`"
                  class="field-chip optional"
                >
                  {{ section }}
                </span>
              </div>
            </div>
            <div class="contract-section">
              <strong>回答口径</strong>
              <div class="field-catalog-list">
                <div
                  v-for="perspective in answerPerspectiveEntries(scene.answer_perspectives)"
                  :key="`prompt-perspective-${scene.scene_type}-${perspective.key}`"
                  class="field-catalog-item"
                >
                  <div class="field-catalog-head">
                    <span>{{ perspective.label }}</span>
                    <code>{{ perspective.key }}</code>
                  </div>
                  <p>{{ perspective.instruction }}</p>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>安全说明</strong>
              <div class="handoff-note-list">
                <span
                  v-for="note in scene.safety_contract || []"
                  :key="`prompt-safety-${scene.scene_type}-${note}`"
                >
                  {{ note }}
                </span>
              </div>
            </div>
          </div>

          <div class="contract-panel">
            <div class="contract-header">
              <span>风控事件详情</span>
              <div class="contract-badges">
                <code>{{ businessContracts.risk.tool_name }}</code>
                <em>{{ businessContracts.risk.contract_version || '未标版本' }}</em>
              </div>
            </div>
            <div class="contract-section">
              <strong>接口路径</strong>
              <p>{{ businessContracts.risk.endpoint_template }}</p>
            </div>
            <div class="contract-section">
              <strong>请求字段</strong>
              <p>{{ businessContracts.risk.required_request_fields.join('、') }}</p>
            </div>
            <div class="contract-section">
              <strong>请求 Schema</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.risk.request_json_schema) }}</pre>
            </div>
            <div class="contract-section">
              <strong>必填字段</strong>
              <div class="field-chip-list">
                <span v-for="field in contractFieldEntries(businessContracts.risk.required_fields)" :key="`risk-${field.name}`" class="field-chip">
                  {{ field.name }}<em>{{ field.type }}</em>
                </span>
              </div>
            </div>
            <div v-if="businessContracts.risk.field_catalog?.length" class="contract-section">
              <strong>字段语义</strong>
              <div class="field-catalog-list">
                <div
                  v-for="field in businessContracts.risk.field_catalog"
                  :key="`risk-catalog-${field.name}`"
                  class="field-catalog-item"
                >
                  <div class="field-catalog-head">
                    <span>{{ field.label }}</span>
                    <code>{{ field.name }}</code>
                  </div>
                  <div class="field-catalog-meta">
                    <em>{{ field.type }}</em>
                    <em>{{ field.required ? '必填' : '可选' }}</em>
                  </div>
                  <p>{{ field.description }}</p>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>命中规则字段</strong>
              <div class="field-chip-list">
                <span v-for="field in contractFieldEntries(businessContracts.risk.hit_rule_required_fields)" :key="`risk-rule-${field.name}`" class="field-chip">
                  {{ field.name }}<em>{{ field.type }}</em>
                </span>
              </div>
            </div>
            <div class="contract-section">
              <strong>允许展示字段</strong>
              <p>{{ businessContracts.risk.exposed_fields.join('、') }}</p>
            </div>
            <div class="contract-section">
              <strong>响应 Schema</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.risk.response_json_schema) }}</pre>
            </div>
            <div class="contract-section">
              <strong>示例响应</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.risk.example_response) }}</pre>
            </div>
          </div>

          <div class="contract-panel">
            <div class="contract-header">
              <span>订单毛利链路</span>
              <div class="contract-badges">
                <code>{{ businessContracts.profit.tool_name }}</code>
                <em>{{ businessContracts.profit.contract_version || '未标版本' }}</em>
              </div>
            </div>
            <div class="contract-section">
              <strong>接口路径</strong>
              <p>{{ businessContracts.profit.endpoint_template }}</p>
            </div>
            <div class="contract-section">
              <strong>请求字段</strong>
              <p>{{ businessContracts.profit.required_request_fields.join('、') }}</p>
            </div>
            <div class="contract-section">
              <strong>请求 Schema</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.profit.request_json_schema) }}</pre>
            </div>
            <div class="contract-section">
              <strong>必填字段</strong>
              <div class="field-chip-list">
                <span v-for="field in contractFieldEntries(businessContracts.profit.required_fields)" :key="`profit-${field.name}`" class="field-chip">
                  {{ field.name }}<em>{{ field.type }}</em>
                </span>
              </div>
            </div>
            <div v-if="businessContracts.profit.field_catalog?.length" class="contract-section">
              <strong>字段语义</strong>
              <div class="field-catalog-list">
                <div
                  v-for="field in businessContracts.profit.field_catalog"
                  :key="`profit-catalog-${field.name}`"
                  class="field-catalog-item"
                >
                  <div class="field-catalog-head">
                    <span>{{ field.label }}</span>
                    <code>{{ field.name }}</code>
                  </div>
                  <div class="field-catalog-meta">
                    <em>{{ field.type }}</em>
                    <em>{{ field.required ? '必填' : '可选' }}</em>
                  </div>
                  <p>{{ field.description }}</p>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>链路节点字段</strong>
              <div class="field-chip-list">
                <span v-for="field in contractFieldEntries(businessContracts.profit.chain_step_required_fields)" :key="`profit-chain-${field.name}`" class="field-chip">
                  {{ field.name }}<em>{{ field.type }}</em>
                </span>
              </div>
              <div
                v-if="contractFieldEntries(businessContracts.profit.chain_step_optional_fields).length"
                class="field-chip-list optional-chip-list"
              >
                <span
                  v-for="field in contractFieldEntries(businessContracts.profit.chain_step_optional_fields)"
                  :key="`profit-chain-optional-${field.name}`"
                  class="field-chip optional"
                >
                  {{ field.name }}<em>{{ field.type }} · 可选</em>
                </span>
              </div>
              <p>链路终点：{{ businessContracts.profit.chain_terminal_node }}</p>
            </div>
            <div v-if="businessContracts.profit.derived_chain_steps?.length" class="contract-section">
              <strong>自动派生链路</strong>
              <div class="derived-step-list">
                <div
                  v-for="step in businessContracts.profit.derived_chain_steps"
                  :key="`profit-derived-${step.node}-${step.field}`"
                  class="derived-step-item"
                >
                  <div class="derived-step-head">
                    <span>{{ step.node }}</span>
                    <code>{{ step.field }}</code>
                  </div>
                  <div class="derived-step-meta">
                    <em>{{ step.role || '链路节点' }}</em>
                    <em>{{ step.sign > 0 ? '正向流入' : '负向扣减' }}</em>
                    <em>{{ step.required ? '必填' : '可选' }}</em>
                  </div>
                  <p>{{ step.note || '无补充说明' }}</p>
                </div>
              </div>
            </div>
            <div v-if="businessContracts.profit.display_metadata_fields?.length" class="contract-section">
              <strong>展示元信息</strong>
              <p class="contract-note">这些字段由后端在合同校验通过后补充，用于解释展示，不要求上游接口原样返回。</p>
              <div class="field-catalog-list">
                <div
                  v-for="field in businessContracts.profit.display_metadata_fields"
                  :key="`profit-display-${field.name}`"
                  class="field-catalog-item"
                >
                  <div class="field-catalog-head">
                    <span>{{ field.label }}</span>
                    <code>{{ field.name }}</code>
                  </div>
                  <div class="field-catalog-meta">
                    <em>{{ field.type }}</em>
                    <em>{{ field.required ? '必填' : '后端补充' }}</em>
                  </div>
                  <p>{{ field.description }}</p>
                </div>
              </div>
            </div>
            <div class="contract-section">
              <strong>允许展示字段</strong>
              <p>{{ businessContracts.profit.exposed_fields.join('、') }}</p>
            </div>
            <div class="contract-section">
              <strong>响应 Schema</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.profit.response_json_schema) }}</pre>
            </div>
            <div class="contract-section">
              <strong>示例响应</strong>
              <pre class="contract-json">{{ formatJson(businessContracts.profit.example_response) }}</pre>
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2"/>
          <path d="M9 6v3M9 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ error }}</span>
      </div>

      <div v-if="success" class="success-banner">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2"/>
          <path d="M6 9l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>配置已保存到 .env 文件</span>
      </div>

      <div class="actions">
        <button @click="loadSettings" class="btn secondary" :disabled="loading">重置</button>
        <button @click="saveSettings" class="btn primary" :disabled="loading">
          {{ loading ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  getBusinessToolRequestToken,
  getBusinessToolAuditEvents,
  getBusinessToolContracts,
  getBusinessToolReadiness,
  getBusinessToolRuntimeStatus,
  getLlmSettings,
  inspectBusinessToolIntent,
  probeBusinessTool,
  setBusinessToolRequestToken,
  updateLlmSettings,
  validateBusinessToolResponse,
  validateBusinessToolResponses
} from '../services/api.js'

const loading = ref(false)
const error = ref(null)
const success = ref(false)
const contractsLoading = ref(false)
const contractsError = ref(null)
const businessContracts = ref(null)
const contractDownloadMessage = ref('')
const acceptancePackDownloadMessage = ref('')
const runtimeLoading = ref(false)
const runtimeError = ref(null)
const businessRuntimeStatus = ref(null)
const readinessLoading = ref(false)
const readinessError = ref(null)
const businessToolReadiness = ref(null)
const copiedCorpusCommand = ref('')
const corpusCopyError = ref('')
const auditLoading = ref(false)
const auditError = ref(null)
const businessAuditEvents = ref([])
const businessAuditStatus = ref(null)
const auditToolFilter = ref('all')
const auditStatusFilter = ref('all')
const auditSelectionSourceFilter = ref('all')
const intentInspectSceneType = ref('profit')
const intentInspectQuery = ref('查询订单 ORD88888 的抽成和司机收入')
const intentInspectLoading = ref(false)
const intentInspectResult = ref(null)
const intentInspectError = ref(null)
const probeOrderId = ref('ORD88888')
const probeLoading = ref(null)
const probeResult = ref(null)
const probeResultsByTool = ref({})
const probeError = ref(null)
const validatePayloadText = ref('')
const validateLoading = ref(null)
const validateResult = ref(null)
const validationResultsByTool = ref({})
const validateError = ref(null)
const batchValidatePayloadText = ref('')
const batchValidateLoading = ref(null)
const batchValidateResult = ref(null)
const batchValidationResultsByTool = ref({})
const batchValidateError = ref(null)
const businessToolRequestToken = ref('')
const businessWorkbenchTools = [
  {
    contract_key: 'risk',
    tool_name: 'get_risk_event_detail',
    label: '风控接口',
    description: '检查订单风控事件、命中规则和建议动作的接入状态。',
  },
  {
    contract_key: 'profit',
    tool_name: 'get_profit_chain_detail',
    label: '毛利接口',
    description: '检查抽成、补贴、司机收入和钱流链路的接入状态。',
  },
]

const DEFAULT_VALIDATE_PAYLOAD = {
  order_id: 'ORD88888',
  gross_amount: 128.6,
  platform_commission: 19.29,
  driver_income: 92.35,
  subsidy: 8.0,
  coupon: 6.0,
  platform_net_profit: 2.33,
}

const ORDER_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/

const form = reactive({
  llm_provider: 'minimax',
  minimax_api_key: '',
  minimax_api_base: '',
  minimax_model: '',
  openai_api_key: '',
  openai_api_base: '',
  openai_model: '',
  openai_temperature: 0.7,
  openai_max_tokens: 2000,
  local_llm_base_url: '',
  local_llm_model: '',
  enable_business_tools: true,
  business_tool_timeout: 5,
  risk_api_base_url: '',
  risk_api_key: '',
  profit_api_base_url: '',
  profit_api_key: '',
  enable_business_tool_llm_intent: false,
  business_tool_llm_intent_min_confidence: 0.75,
  enable_business_tool_access_control: false,
  business_tool_access_token: '',
  business_tool_read_token: '',
  business_tool_execute_token: '',
  enable_business_tool_audit_file: false,
  business_tool_audit_file: 'logs/business_tool_audit.jsonl',
})

const businessToolFields = [
  'enable_business_tools',
  'business_tool_timeout',
  'risk_api_base_url',
  'risk_api_key',
  'profit_api_base_url',
  'profit_api_key',
  'enable_business_tool_llm_intent',
  'business_tool_llm_intent_min_confidence',
  'enable_business_tool_access_control',
  'business_tool_access_token',
  'business_tool_read_token',
  'business_tool_execute_token',
  'enable_business_tool_audit_file',
  'business_tool_audit_file',
]

const fieldsByProvider = {
  minimax: ['llm_provider', 'minimax_api_key', 'minimax_api_base', 'minimax_model', ...businessToolFields],
  openai: ['llm_provider', 'openai_api_key', 'openai_api_base', 'openai_model', 'openai_temperature', 'openai_max_tokens', ...businessToolFields],
  local: ['llm_provider', 'local_llm_base_url', 'local_llm_model', ...businessToolFields],
}

const requiredByProvider = {
  minimax: [],
  openai: [],
  local: ['local_llm_base_url', 'local_llm_model'],
}

const secretFields = new Set([
  'minimax_api_key',
  'openai_api_key',
  'risk_api_key',
  'profit_api_key',
  'business_tool_access_token',
  'business_tool_read_token',
  'business_tool_execute_token',
])

const loadSettings = async () => {
  loading.value = true
  error.value = null
  success.value = false
  try {
    const data = await getLlmSettings()
    form.llm_provider = data.llm_provider || 'minimax'
    form.minimax_api_key = ''
    form.minimax_api_base = data.minimax_api_base || ''
    form.minimax_model = data.minimax_model || ''
    form.openai_api_key = ''
    form.openai_api_base = data.openai_api_base || ''
    form.openai_model = data.openai_model || ''
    form.openai_temperature = parseFloat(data.openai_temperature) || 0.7
    form.openai_max_tokens = parseInt(data.openai_max_tokens) || 2000
    form.local_llm_base_url = data.local_llm_base_url || ''
    form.local_llm_model = data.local_llm_model || ''
    form.enable_business_tools = parseBoolean(data.enable_business_tools, true)
    form.business_tool_timeout = parseInt(data.business_tool_timeout) || 5
    form.risk_api_base_url = data.risk_api_base_url || ''
    form.risk_api_key = ''
    form.profit_api_base_url = data.profit_api_base_url || ''
    form.profit_api_key = ''
    form.enable_business_tool_llm_intent = parseBoolean(data.enable_business_tool_llm_intent)
    form.business_tool_llm_intent_min_confidence = parseFloat(data.business_tool_llm_intent_min_confidence) || 0.75
    form.enable_business_tool_access_control = parseBoolean(data.enable_business_tool_access_control)
    form.business_tool_access_token = ''
    form.business_tool_read_token = ''
    form.business_tool_execute_token = ''
    form.enable_business_tool_audit_file = parseBoolean(data.enable_business_tool_audit_file)
    form.business_tool_audit_file = data.business_tool_audit_file || 'logs/business_tool_audit.jsonl'
  } catch (e) {
    error.value = e.message || '加载配置失败'
  } finally {
    loading.value = false
  }
}

const loadBusinessContracts = async () => {
  contractsLoading.value = true
  contractsError.value = null
  contractDownloadMessage.value = ''
  acceptancePackDownloadMessage.value = ''
  try {
    businessContracts.value = await getBusinessToolContracts()
  } catch (e) {
    contractsError.value = e.message || '加载业务接口合同失败'
  } finally {
    contractsLoading.value = false
  }
}

const loadRuntimeStatus = async () => {
  syncBusinessToolRequestToken()
  runtimeLoading.value = true
  runtimeError.value = null
  acceptancePackDownloadMessage.value = ''
  try {
    businessRuntimeStatus.value = await getBusinessToolRuntimeStatus()
  } catch (e) {
    runtimeError.value = e.message || '加载业务工具运行态失败'
  } finally {
    runtimeLoading.value = false
  }
}

const loadReadiness = async () => {
  syncBusinessToolRequestToken()
  readinessLoading.value = true
  readinessError.value = null
  acceptancePackDownloadMessage.value = ''
  try {
    businessToolReadiness.value = await getBusinessToolReadiness(20)
  } catch (e) {
    readinessError.value = e.message || '加载业务工具接入检查失败'
  } finally {
    readinessLoading.value = false
  }
}

const loadAuditEvents = async () => {
  auditLoading.value = true
  auditError.value = null
  try {
    const data = await getBusinessToolAuditEvents(20)
    businessAuditEvents.value = data.events || []
    businessAuditStatus.value = data.audit_status || null
  } catch (e) {
    auditError.value = e.message || '加载业务工具审计失败'
  } finally {
    auditLoading.value = false
  }
}

const refreshBusinessWorkbench = async () => {
  await Promise.all([
    loadBusinessContracts(),
    loadRuntimeStatus(),
    loadReadiness(),
    loadAuditEvents(),
  ])
}

const runIntentInspect = async () => {
  syncBusinessToolRequestToken()
  intentInspectLoading.value = true
  intentInspectError.value = null
  intentInspectResult.value = null
  try {
    intentInspectResult.value = await inspectBusinessToolIntent({
      query: intentInspectQuery.value.trim(),
      scene_type: intentInspectSceneType.value,
    })
  } catch (e) {
    intentInspectError.value = e.message || '业务工具意图预检失败'
  } finally {
    intentInspectLoading.value = false
  }
}

const runProbe = async (toolName) => {
  syncBusinessToolRequestToken()
  const validationError = probeOrderIdError()
  if (validationError) {
    probeError.value = validationError
    probeResult.value = null
    return
  }
  probeLoading.value = toolName
  probeError.value = null
  probeResult.value = null
  try {
    probeResult.value = await probeBusinessTool({
      tool_name: toolName,
      order_id: probeOrderId.value.trim(),
    })
    probeResultsByTool.value = {
      ...probeResultsByTool.value,
      [toolName]: probeResult.value,
    }
    await loadAuditEvents()
    await loadReadiness()
  } catch (e) {
    probeError.value = e.message || '接口探测失败'
  } finally {
    probeLoading.value = null
  }
}

const runResponseValidation = async (toolName) => {
  syncBusinessToolRequestToken()
  validateLoading.value = toolName
  validateError.value = null
  validateResult.value = null
  try {
    const payload = JSON.parse(validatePayloadText.value)
    validateResult.value = await validateBusinessToolResponse({
      tool_name: toolName,
      payload,
    })
    validationResultsByTool.value = {
      ...validationResultsByTool.value,
      [toolName]: validateResult.value,
    }
  } catch (e) {
    validateError.value = e instanceof SyntaxError
      ? '响应样例不是合法 JSON'
      : (e.message || '响应样例校验失败')
  } finally {
    validateLoading.value = null
  }
}

const runBatchResponseValidation = async (toolName) => {
  syncBusinessToolRequestToken()
  batchValidateLoading.value = toolName
  batchValidateError.value = null
  batchValidateResult.value = null
  try {
    const payloads = parseBatchValidationPayloads(batchValidatePayloadText.value)
    batchValidateResult.value = await validateBusinessToolResponses({
      tool_name: toolName,
      payloads,
    })
    batchValidationResultsByTool.value = {
      ...batchValidationResultsByTool.value,
      [toolName]: batchValidateResult.value,
    }
    validationResultsByTool.value = {
      ...validationResultsByTool.value,
      [toolName]: batchValidateResult.value,
    }
  } catch (e) {
    batchValidateError.value = e instanceof SyntaxError
      ? '批量响应样例不是合法 JSON'
      : (e.message || '批量响应样例校验失败')
  } finally {
    batchValidateLoading.value = null
  }
}

const fillValidationPayload = (contractKey) => {
  const sample = businessContracts.value?.[contractKey]?.example_response
  if (!sample) return
  validatePayloadText.value = JSON.stringify(sample, null, 2)
  validateError.value = null
  validateResult.value = null
}

const fillBatchValidationPayload = (contractKey) => {
  const sample = businessContracts.value?.[contractKey]?.example_response
  if (!sample) return
  batchValidatePayloadText.value = JSON.stringify([sample], null, 2)
  batchValidateError.value = null
  batchValidateResult.value = null
}

const runExampleValidation = async (contractKey, toolName) => {
  fillValidationPayload(contractKey)
  if (!validatePayloadText.value) return
  await runResponseValidation(toolName)
}

const validate = () => {
  const provider = form.llm_provider
  const required = requiredByProvider[provider] || []
  for (const field of required) {
    if (!form[field] || !form[field].toString().trim()) {
      return `${field} 为必填项`
    }
  }
  if (provider === 'openai') {
    if (form.openai_temperature < 0 || form.openai_temperature > 2) return 'Temperature 必须在 0-2 之间'
    if (form.openai_max_tokens < 1 || form.openai_max_tokens > 32000) return 'Max Tokens 必须在 1-32000 之间'
  }
  if (
    form.business_tool_llm_intent_min_confidence < 0 ||
    form.business_tool_llm_intent_min_confidence > 1
  ) {
    return '业务工具最低置信度必须在 0-1 之间'
  }
  if (form.business_tool_timeout < 1 || form.business_tool_timeout > 60) {
    return '业务接口调用超时必须在 1-60 秒之间'
  }
  if (form.enable_business_tool_audit_file && !String(form.business_tool_audit_file || '').trim()) {
    return '启用文件审计时必须提供审计文件路径'
  }
  return null
}

const saveSettings = async () => {
  error.value = null
  success.value = false
  const validationError = validate()
  if (validationError) { error.value = validationError; return }
  loading.value = true
  const provider = form.llm_provider
  const fields = fieldsByProvider[provider] || fieldsByProvider.minimax
  const updates = {}
  for (const key of fields) {
    if (secretFields.has(key) && !form[key]) continue
    updates[key] = form[key]
  }
  try {
    await updateLlmSettings(updates)
    if (!businessToolRequestToken.value && form.business_tool_access_token) {
      businessToolRequestToken.value = form.business_tool_access_token
    }
    syncBusinessToolRequestToken()
    success.value = true
    await loadRuntimeStatus()
    await loadReadiness()
    await loadAuditEvents()
    setTimeout(() => { success.value = false }, 3000)
  } catch (e) {
    error.value = e.message || '保存配置失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  businessToolRequestToken.value = getBusinessToolRequestToken()
  validatePayloadText.value = JSON.stringify(DEFAULT_VALIDATE_PAYLOAD, null, 2)
  loadSettings()
  loadBusinessContracts()
  loadRuntimeStatus()
  loadReadiness()
  loadAuditEvents()
})

function syncBusinessToolRequestToken() {
  setBusinessToolRequestToken(businessToolRequestToken.value)
}

function isProbeOrderIdValid(value = '') {
  return probeOrderIdPattern().test(String(value || '').trim())
}

function probeOrderIdError() {
  const value = String(probeOrderId.value || '').trim()
  if (!value) return '请先输入订单号'
  if (!isProbeOrderIdValid(value)) return '订单号只能包含字母、数字、_、-，且不能以符号开头'
  return ''
}

function probeOrderIdPattern() {
  const contractPattern = businessContracts.value?.risk?.request_json_schema?.properties?.order_id?.pattern
  if (typeof contractPattern !== 'string' || !contractPattern.trim()) return ORDER_ID_PATTERN
  try {
    return new RegExp(contractPattern)
  } catch {
    return ORDER_ID_PATTERN
  }
}

function probeOrderIdPatternText() {
  return `/${probeOrderIdPattern().source}/`
}

function parseBoolean(value, defaultValue = false) {
  if (typeof value === 'boolean') return value
  if (value === undefined || value === null || value === '') return defaultValue
  return String(value).toLowerCase() === 'true'
}

function contractFieldEntries(fields = {}) {
  return Object.entries(fields).map(([name, type]) => ({ name, type }))
}

function promptContractEntries(promptContracts = {}) {
  return Object.entries(promptContracts || {}).map(([scene_type, contract]) => ({
    scene_type,
    ...contract,
  }))
}

function answerPerspectiveEntries(answerPerspectives = {}) {
  return Object.entries(answerPerspectives || {}).map(([key, perspective]) => ({
    key,
    ...perspective,
  }))
}

function formatJson(value = {}) {
  return JSON.stringify(value || {}, null, 2)
}

function downloadJsonFile(filename, value) {
  const content = `${formatJson(value)}\n`
  const blob = new Blob([content], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  try {
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}

function downloadBusinessContracts() {
  contractDownloadMessage.value = ''
  if (!businessContracts.value) {
    contractsError.value = '业务接口合同尚未加载'
    return
  }

  downloadJsonFile('business_tool_contracts.json', businessContracts.value)
  contractDownloadMessage.value = '已生成 business_tool_contracts.json'
}

function canDownloadBusinessAcceptancePack() {
  return Boolean(businessContracts.value && businessToolReadiness.value && businessRuntimeStatus.value)
}

function downloadBusinessAcceptancePack() {
  acceptancePackDownloadMessage.value = ''
  if (!canDownloadBusinessAcceptancePack()) {
    readinessError.value = '请先刷新接入检查工作台'
    return
  }

  downloadJsonFile('business_tool_acceptance_pack_frontend.json', buildBusinessAcceptancePack())
  acceptancePackDownloadMessage.value = '已生成 business_tool_acceptance_pack_frontend.json'
}

function buildBusinessAcceptancePack() {
  const readiness = businessToolReadiness.value || {}
  return {
    generated_at: new Date().toISOString(),
    status: businessAcceptancePackStatus(readiness.overall_status),
    acceptance_scope: [
      'contract_snapshot',
      'runtime_status',
      'readiness_gates',
      'integration_workbench',
      'safe_audit_summary',
      'prompt_contract',
    ],
    contracts: businessContracts.value,
    prompt_contract: businessContracts.value?.prompt_contract || {},
    readiness_summary: {
      overall_status: readiness.overall_status,
      passed: readiness.passed || [],
      warnings: readiness.warnings || [],
      blockers: readiness.blockers || [],
    },
    readiness_items: readiness.items || [],
    safe_frontend_evidence: {
      runtime_status: businessRuntimeStatus.value,
      workbench_tools: businessWorkbenchTools.map(tool => businessAcceptanceToolEvidence(tool)),
      audit: {
        status: businessAuditStatus.value,
        event_count: businessAuditEvents.value?.length || 0,
        audit_ids: (businessAuditEvents.value || [])
          .map(event => event.audit_id)
          .filter(Boolean)
          .slice(0, 10),
      },
    },
    integration_handoff: {
      go_live_allowed: readiness.overall_status === 'ready',
      must_fix_before_real_order_traffic: readiness.blockers || [],
      should_fix_before_production: readiness.warnings || [],
      recommended_next_actions: businessAcceptanceRecommendedActions(readiness),
    },
    source_commands: {
      contract_export: 'make business-contracts',
      acceptance_pack: 'make business-acceptance-pack',
      local_smoke: 'make business-smoke',
      strict_gate: 'make business-smoke-strict',
      llm_fallback_acceptance: 'make business-llm-acceptance',
    },
  }
}

function businessAcceptancePackStatus(overallStatus) {
  if (overallStatus === 'ready') return 'accepted'
  if (overallStatus === 'blocked') return 'blocked'
  return 'needs_attention'
}

function businessAcceptanceToolEvidence(tool) {
  const probe = latestProbeResultByToolName(tool.tool_name)
  const validation = latestValidationResultByToolName(tool.tool_name)
  const audit = latestAuditEventByToolName(tool.tool_name)
  return {
    tool_name: tool.tool_name,
    contract_key: tool.contract_key,
    contract_version: toolContractVersion(tool.contract_key),
    runtime_mode: toolRuntimeMode(tool.tool_name),
    contract_state: toolContractState(tool.contract_key, tool.tool_name),
    latest_probe: probe ? {
      status: probe.status,
      data_source: probe.data_source,
      integration_mode: probe.integration_mode,
      diagnostic_code: probe.diagnostic_code || null,
      missing_fields: probe.missing_fields || [],
      invalid_fields: probe.invalid_fields || [],
      audit_id: probe.audit_id || null,
    } : null,
    latest_validation: validation ? {
      status: validation.status,
      diagnostic_code: validation.diagnostic_code || null,
      missing_fields: validation.missing_fields || [],
      invalid_fields: validation.invalid_fields || [],
      exposed_result_keys: validation.exposed_result_keys || [],
      ignored_result_keys: validation.ignored_result_keys || [],
      validation_summary: validation.validation_summary || null,
    } : null,
    latest_audit: audit ? {
      status: audit.status,
      selection_source: audit.selection_source || null,
      data_source: audit.data_source || null,
      diagnostic_code: audit.diagnostic_code || null,
      audit_id: audit.audit_id || null,
    } : null,
  }
}

function businessAcceptanceRecommendedActions(readiness = {}) {
  const active = new Set([...(readiness.blockers || []), ...(readiness.warnings || [])])
  const actionByGate = {
    real_http_configured: '配置 RISK_API_BASE_URL / PROFIT_API_BASE_URL，并用非生产订单号重新跑验收。',
    external_http_configured: '使用外部真实风控/毛利 Base URL 和非生产订单号补跑严格门禁。',
    access_control_enabled: '启用 ENABLE_BUSINESS_TOOL_ACCESS_CONTROL，并配置只读/执行 Token。',
    persistent_audit_enabled: '启用 JSONL 或等价持久审计，并确认 audit_id 可回查。',
    captured_sample_validation: '提供真实风控/毛利响应样例，用响应样例校验或 RISK_RESPONSE_FILE / PROFIT_RESPONSE_FILE 离线校验。',
    audit_traceability: '完成一次自然语言订单查询，确认 tool_calls.audit_id 能在脱敏审计中关联。',
    llm_intent_fallback: '如果生产依赖模糊问题识别，配置有效 LLM 凭证并运行 make business-llm-acceptance。',
    corpus_scene_coverage: '导入风控/毛利业务语料后刷新 readiness，确保解释可引用规则文档。',
    probe_endpoints: '使用接口探测定位真实接口响应、鉴权、超时或合同字段问题。',
    intent_precheck: '检查标准风控/毛利提示是否能在不执行接口的情况下选中目标工具。',
  }
  const actions = [...active].sort().map(gate => actionByGate[gate]).filter(Boolean)
  return actions.length ? actions : ['当前前端接入状态已满足 go-live gate；进入小流量真实订单验证。']
}

function formatDataSource(source) {
  if (source === 'mock') return 'Mock 数据'
  if (source === 'http') return '真实接口'
  return source || '未知'
}

function formatIntegrationMode(mode) {
  if (mode === 'mock') return 'Mock 模式'
  if (mode === 'fake_http') return '进程内 fake-http 验证'
  if (mode === 'external_http') return '外部真实 HTTP'
  return mode || '未知'
}

function formatRuntimeStatus(status) {
  const labels = {
    ready: '就绪',
    disabled: '已停用',
    misconfigured: '配置异常',
  }
  return labels[status] || status || '未知'
}

function formatReadinessStatus(status) {
  const labels = {
    ready: '就绪',
    ready_with_warnings: '有警告',
    blocked: '阻塞',
  }
  return labels[status] || status || '未知'
}

function formatReadinessItemStatus(status) {
  const labels = {
    passed: '通过',
    warning: '警告',
    blocked: '阻塞',
  }
  return labels[status] || status || '未知'
}

function formatReadinessItemLabel(id) {
  const labels = {
    business_tools_enabled: '业务工具开关',
    contract_examples_valid: '合同自检',
    tool_contracts_available: '接口合同',
    intent_precheck: '意图预检',
    corpus_scene_coverage: '业务语料',
    access_control_enabled: '访问控制',
    real_http_configured: '真实接口',
    external_http_configured: '外部系统',
    persistent_audit_enabled: '持久审计',
    audit_traceability: '审计追因',
    llm_intent_fallback: 'LLM 兜底',
  }
  return labels[id] || id
}

function formatToolName(toolName) {
  if (toolName === 'get_risk_event_detail') return '风控'
  if (toolName === 'get_profit_chain_detail') return '毛利'
  return toolName || '未知工具'
}

function formatReadinessEvidence(id, evidence = {}) {
  if (id === 'real_http_configured') {
    const tools = Array.isArray(evidence.tool_sources) ? evidence.tool_sources : []
    if (!tools.length) return '-'
    return tools
      .map(tool => `${formatToolName(tool.tool_name)}=${formatIntegrationMode(tool.integration_mode || 'mock')}`)
      .join('；')
  }
  if (id === 'external_http_configured') {
    const modes = Array.isArray(evidence.integration_modes) ? evidence.integration_modes : []
    return evidence.external_http_ready
      ? '风控和毛利均为外部真实 HTTP'
      : `当前模式：${modes.length ? modes.map(formatIntegrationMode).join('、') : '未配置'}`
  }
  if (id === 'corpus_scene_coverage') {
    const missing = Array.isArray(evidence.missing_scenes) ? evidence.missing_scenes : []
    return missing.length ? `缺少场景：${missing.join('、')}` : '风控和毛利语料都已覆盖'
  }
  if (id === 'intent_precheck') {
    const checks = Array.isArray(evidence.checks) ? evidence.checks : []
    if (!checks.length) return '-'
    return checks
      .map(check => `${formatToolName(check.expected_tool_name)}=${check.selected_expected_tool ? '已命中' : '未命中'}(${formatSelectionSource(check.selection_source)})`)
      .join('；')
  }
  if (id === 'persistent_audit_enabled') {
    return `${evidence.persisted_event_count || 0} 条已落盘；${evidence.file_readable ? '可回读' : '未回读'}`
  }
  if (id === 'audit_traceability') {
    return `最近 ${evidence.traceable_event_count || 0} 条可追因；最新审计ID=${evidence.latest_traceable_audit_id || '-'}`
  }
  if (id === 'access_control_enabled') {
    const missingScopes = Array.isArray(evidence.missing_scopes) ? evidence.missing_scopes : []
    return evidence.enabled
      ? `访问控制已启用；${missingScopes.length ? `缺少 ${formatMissingScopes(missingScopes)}` : 'scope 已就绪'}`
      : '未启用订单级访问控制'
  }
  if (id === 'llm_intent_fallback') {
    if (!evidence.enabled) return '当前未启用 LLM 兜底'
    if (!evidence.model_configured) return '已启用但模型尚未配置完整'
    if (evidence.last_status === 'success') {
      return `最近成功：${formatLlmIntentResolution(evidence.last_resolution)}；成功 ${evidence.success_count || 0}/${evidence.attempt_count || 0} 次`
    }
    if (evidence.attempt_count) {
      return `最近失败：${evidence.last_error_type || '-'}；失败 ${evidence.error_count || 0}/${evidence.attempt_count || 0} 次`
    }
    return '已启用但尚无成功的真实调用记录'
  }
  const entries = Object.entries(evidence || {})
    .filter(([key]) => key !== 'ingestion_guidance')
  if (!entries.length) return '-'
  return entries
    .map(([key, value]) => `${key}=${formatEvidenceValue(value)}`)
    .join('，')
}

function readinessCorpusGuidance(item = {}) {
  if (item.id !== 'corpus_scene_coverage') return []
  const guidance = item.evidence?.ingestion_guidance || []
  return Array.isArray(guidance) ? guidance : []
}

async function copyCorpusCommand(guide = {}) {
  const command = String(guide.command || '').trim()
  if (!command) return
  try {
    await writeClipboardText(command)
    copiedCorpusCommand.value = command
    corpusCopyError.value = ''
    setTimeout(() => {
      if (copiedCorpusCommand.value === command) copiedCorpusCommand.value = ''
    }, 2000)
  } catch (_e) {
    copiedCorpusCommand.value = ''
    corpusCopyError.value = command
  }
}

async function writeClipboardText(text) {
  if (copyWithTextarea(text)) return
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  throw new Error('copy_failed')
}

function copyWithTextarea(text) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.top = '0'
  textarea.style.left = '0'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  try {
    return document.execCommand('copy')
  } finally {
    document.body.removeChild(textarea)
  }
}

function formatEvidenceValue(value) {
  if (Array.isArray(value)) return JSON.stringify(value)
  if (value && typeof value === 'object') return JSON.stringify(value)
  if (value === true) return 'true'
  if (value === false) return 'false'
  return value ?? '-'
}

function formatConfigured(value) {
  return value ? '已配置' : '未配置'
}

function formatReady(value) {
  return value ? '可用' : '不可用'
}

function formatMissingScopes(scopes = []) {
  const labels = {
    read: '只读 Token',
    execute: '执行 Token',
  }
  return scopes.map(scope => labels[scope] || scope).join('、')
}

function formatLlmIntentRuntimeSummary(llmIntent = {}) {
  const threshold = llmIntent?.min_confidence ?? '-'
  if (!llmIntent?.enabled) {
    return `阈值 ${threshold} · 当前按规则路由`
  }
  if (!llmIntent?.model_configured) {
    return `阈值 ${threshold} · 模型未配置完整`
  }
  if (llmIntent?.last_status === 'success') {
    return `阈值 ${threshold} · 最近成功：${formatLlmIntentResolution(llmIntent.last_resolution)}`
  }
  if (llmIntent?.attempt_count) {
    return `阈值 ${threshold} · 最近失败：${llmIntent.last_error_type || 'unknown_error'}`
  }
  return `阈值 ${threshold} · 尚无真实调用记录`
}

function formatLlmIntentResolution(resolution) {
  const labels = {
    tool_selected: '已选工具',
    clarification_required: '需要澄清',
    no_tool: '无需调接口',
  }
  return labels[resolution] || resolution || '未知结果'
}

function hasProbeDiagnosticDetails(result = {}) {
  return Boolean(
    result.diagnostic_code ||
    result.missing_fields?.length ||
    result.invalid_fields?.length
  )
}

function formatDiagnosticCode(code) {
  const labels = {
    missing_required_fields: '缺少必填字段',
    invalid_field_types: '字段类型不匹配',
    invalid_hit_rules: '风控命中规则格式异常',
    invalid_chain: '毛利链路格式异常',
    non_object_json: '接口未返回 JSON 对象',
  }
  return labels[code] || code
}

function formatAuditTime(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return timestamp
  return date.toLocaleString()
}

function formatAuditArguments(argumentsValue = {}) {
  const entries = Object.entries(argumentsValue || {})
  if (!entries.length) return '-'
  return entries.map(([key, value]) => `${key}=${value}`).join('，')
}

function formatSelectionSource(value) {
  if (value === 'rules') return '规则命中'
  if (value === 'llm') return 'LLM 兜底'
  if (value === 'probe') return '手动探测'
  if (value === 'none') return '未触发'
  return value || '-'
}

function formatAuditConfidence(value) {
  if (typeof value !== 'number') return '-'
  return `${Math.round(value * 100)}%`
}

function intentInspectStateLabel(intent = {}) {
  if (intent.needs_clarification) return '待澄清'
  if (intent.tool_name) return '可执行'
  return '不调用'
}

function formatResultKeys(keys = []) {
  return Array.isArray(keys) && keys.length ? keys.join('、') : '-'
}

function parseBatchValidationPayloads(text) {
  const parsed = JSON.parse(text)
  const payloads = Array.isArray(parsed)
    ? parsed
    : (Array.isArray(parsed?.payloads) ? parsed.payloads : null)
  if (!payloads || !payloads.length) {
    throw new Error('批量响应样例必须是 JSON 数组，或包含 payloads 数组')
  }
  return payloads
}

function hasBatchValidationDetails(result = {}) {
  const summary = result.validation_summary || {}
  return Boolean(
    summary.missing_fields?.length ||
    summary.invalid_fields?.length ||
    summary.ignored_result_keys?.length
  )
}

function formatDiagnosticCounts(counts = {}) {
  const entries = Object.entries(counts || {})
  if (!entries.length) return '-'
  return entries
    .map(([code, count]) => `${formatDiagnosticCode(code)} ${count}`)
    .join('、')
}

function batchValidatePreviewItems(result = {}) {
  return Array.isArray(result.items) ? result.items.slice(0, 5) : []
}

function batchValidationItemSummary(item = {}) {
  if (item.diagnostic_code) return formatDiagnosticCode(item.diagnostic_code)
  if (item.ignored_result_keys?.length) return `未展示：${formatResultKeys(item.ignored_result_keys)}`
  if (item.exposed_result_keys?.length) return `字段：${formatResultKeys(item.exposed_result_keys)}`
  return item.summary || '-'
}

function filteredBusinessAuditEvents() {
  return (businessAuditEvents.value || []).filter(event => {
    if (auditToolFilter.value !== 'all' && event.tool_name !== auditToolFilter.value) return false
    if (auditStatusFilter.value !== 'all' && event.status !== auditStatusFilter.value) return false
    if (auditSelectionSourceFilter.value !== 'all') {
      const source = event.selection_source || 'none'
      if (source !== auditSelectionSourceFilter.value) return false
    }
    return true
  })
}

function hasAuditFilters() {
  return (
    auditToolFilter.value !== 'all' ||
    auditStatusFilter.value !== 'all' ||
    auditSelectionSourceFilter.value !== 'all'
  )
}

function clearAuditFilters() {
  auditToolFilter.value = 'all'
  auditStatusFilter.value = 'all'
  auditSelectionSourceFilter.value = 'all'
}

function workbenchLoading() {
  return Boolean(
    contractsLoading.value ||
    runtimeLoading.value ||
    readinessLoading.value ||
    auditLoading.value
  )
}

function workbenchOverallStatusLabel() {
  const status = businessToolReadiness.value?.overall_status
  if (!status) return '待检查'
  return formatReadinessStatus(status)
}

function workbenchOverallStatusHint() {
  return businessToolReadiness.value?.status_reason || '刷新后查看接入门禁、探测和审计摘要。'
}

function runtimeToolByName(toolName) {
  const tools = businessRuntimeStatus.value?.tools || []
  return tools.find(tool => tool.tool_name === toolName) || null
}

function latestAuditEventByToolName(toolName) {
  const events = businessAuditEvents.value || []
  return events.find(event => event.tool_name === toolName) || null
}

function latestProbeResultByToolName(toolName) {
  return probeResultsByTool.value?.[toolName] || null
}

function latestValidationResultByToolName(toolName) {
  return validationResultsByTool.value?.[toolName] || null
}

function toolContract(contractKey) {
  return businessContracts.value?.[contractKey] || null
}

function handoffCommandEntries(commands = {}) {
  return Object.entries(commands || {}).map(([name, command]) => ({ name, command }))
}

function handoffModeEntries(modes = {}) {
  return Object.entries(modes || {}).map(([mode, description]) => ({ mode, description }))
}

function formatHandoffStep(step) {
  const labels = {
    export_contracts: '导出合同',
    validate_captured_samples: '校验真实样例',
    fake_http_acceptance: 'fake-http 验收',
    external_http_strict_gate: '外部系统门禁',
    frontend_evidence_check: '前端证据检查',
  }
  return labels[step] || step
}

function toolContractVersion(contractKey) {
  return toolContract(contractKey)?.contract_version || '未标版本'
}

function toolRuntimeMode(toolName) {
  const tool = runtimeToolByName(toolName)
  if (!tool) return '待检查'
  return formatIntegrationMode(tool.integration_mode)
}

function toolRuntimeHint(toolName) {
  const tool = runtimeToolByName(toolName)
  if (!tool) return '运行态尚未返回该工具的接入信息。'
  return [
    formatDataSource(tool.data_source),
    `Base URL ${formatConfigured(tool.base_url_configured)}`,
    `API Key ${formatConfigured(tool.api_key_configured)}`,
  ].join(' · ')
}

function toolContractState(contractKey, toolName) {
  const tool = runtimeToolByName(toolName)
  if (tool?.contract_available === false) return '不可用'
  return toolContract(contractKey) ? '可用' : '待加载'
}

function toolContractExposure(contractKey) {
  const contract = toolContract(contractKey)
  const count = contract?.exposed_fields?.length || 0
  return count ? `${count} 个字段` : '待加载'
}

function toolContractHint(contractKey) {
  const contract = toolContract(contractKey)
  if (!contract) return '合同快照未加载完成。'
  const requestFieldCount = contract.required_request_fields?.length || 0
  const responseFieldCount = contract.exposed_fields?.length || 0
  return `请求 ${requestFieldCount} 项 · 展示 ${responseFieldCount} 项`
}

function toolProbeState(toolName) {
  const result = latestProbeResultByToolName(toolName)
  if (!result) return '未探测'
  return result.status === 'success' ? '成功' : '失败'
}

function toolProbeHint(toolName) {
  const result = latestProbeResultByToolName(toolName)
  if (!result) return '使用上面的接口探测按钮生成最新结果。'
  if (result.diagnostic) return `合同诊断：${result.diagnostic}`
  return `${formatDataSource(result.data_source)} · ${formatIntegrationMode(result.integration_mode)} · ${result.duration_ms}ms`
}

function toolValidationState(toolName) {
  const result = latestValidationResultByToolName(toolName)
  if (!result) return '未校验'
  return result.status === 'valid' ? '通过' : '未通过'
}

function toolValidationHint(toolName) {
  const result = latestValidationResultByToolName(toolName)
  if (!result) return '可用合同示例或自定义 JSON 做离线校验。'
  if (result.validation_summary) {
    const summary = result.validation_summary
    const ignoredCount = summary.ignored_result_keys?.length || 0
    return `批量：${summary.valid_count || 0}/${summary.total || 0} 通过${
      ignoredCount ? ` · 忽略 ${ignoredCount} 个字段` : ''
    }`
  }
  if (result.diagnostic) return `合同诊断：${result.diagnostic}`
  if (result.ignored_result_keys?.length) {
    return `字段：${formatResultKeys(result.exposed_result_keys)} · 未展示：${formatResultKeys(result.ignored_result_keys)}`
  }
  return `字段：${formatResultKeys(result.exposed_result_keys)}`
}

function toolAuditState(toolName) {
  const event = latestAuditEventByToolName(toolName)
  if (!event) return '暂无记录'
  return event.status === 'success' ? '成功' : '失败'
}

function toolAuditHint(toolName) {
  const event = latestAuditEventByToolName(toolName)
  if (!event) return '接口探测或真实查询后会出现脱敏审计。'
  if (event.diagnostic_code) return `合同诊断：${formatDiagnosticCode(event.diagnostic_code)}`
  const selection = event.selection_source
    ? formatSelectionSource(event.selection_source)
    : '未触发'
  return `${selection} · ${formatDataSource(event.data_source)} · ${event.duration_ms}ms`
}

function toolAuditFootnote(toolName) {
  const event = latestAuditEventByToolName(toolName)
  if (!event) return ''
  const parts = [
    formatAuditTime(event.timestamp),
    `参数 ${formatAuditArguments(event.arguments)}`,
    `结果 ${formatResultKeys(event.result_keys)}`,
  ]
  if (event.selection_reason) parts.push(`依据 ${event.selection_reason}`)
  return parts.join(' · ')
}

function toolWorkbenchTone(toolName) {
  const runtimeTool = runtimeToolByName(toolName)
  const probe = latestProbeResultByToolName(toolName)
  const validation = latestValidationResultByToolName(toolName)
  const audit = latestAuditEventByToolName(toolName)

  if (
    runtimeTool?.contract_available === false ||
    probe?.status === 'error' ||
    validation?.status === 'invalid' ||
    audit?.status === 'error'
  ) {
    return 'warn'
  }
  if (runtimeTool || probe || validation || audit) return 'safe'
  return 'neutral'
}

function safetyCheckItems() {
  const status = businessRuntimeStatus.value || {}
  const events = businessAuditEvents.value || []
  const failedEvents = events.filter(event => event.status === 'error')
  const httpTools = (status.tools || []).filter(tool => tool.data_source === 'http')
  const configuredHttpTools = httpTools.filter(tool => tool.base_url_configured)
  const fakeHttpTools = httpTools.filter(tool => tool.integration_mode === 'fake_http')
  const externalHttpTools = httpTools.filter(tool => tool.integration_mode === 'external_http')
  const accessReady = Boolean(status.access_control?.ready)
  const auditReady = Boolean(status.audit?.file_enabled || status.audit?.memory_event_limit)
  const persistedAuditCount = status.audit?.persisted_event_count || 0
  const persistedAuditReadable = Boolean(status.audit?.file_readable)
  const failureRate = events.length ? failedEvents.length / events.length : 0
  const corpusCoverage = readinessItemById('corpus_scene_coverage')
  const missingCorpusScenes = corpusCoverage?.evidence?.missing_scenes || []

  return [
    {
      label: '业务语料',
      value: missingCorpusScenes.length ? `缺 ${missingCorpusScenes.length} 个场景` : '已覆盖',
      hint: corpusCoverage?.summary || '检查风控/毛利语料是否已入库',
      tone: corpusCoverage?.status === 'passed' ? 'safe' : 'warn',
    },
    {
      label: '访问控制',
      value: status.access_control?.enabled ? '已启用' : '未启用',
      hint: status.access_control?.enabled
        ? `读 ${formatReady(status.access_control?.read_scope_ready)} · 执行 ${formatReady(status.access_control?.execute_scope_ready)}`
        : '真实订单接入前建议启用',
      tone: accessReady && status.access_control?.enabled ? 'safe' : 'warn',
    },
    {
      label: '审计记录',
      value: status.audit?.file_enabled ? '文件审计' : '内存审计',
      hint: status.audit?.file_enabled
        ? `${persistedAuditCount} 条已落盘 · ${persistedAuditReadable ? '可回读' : '未回读'}`
        : `${status.audit?.memory_event_count || 0}/${status.audit?.memory_event_limit || 0} 条最近记录`,
      tone: status.audit?.file_enabled ? (persistedAuditReadable ? 'safe' : 'warn') : (auditReady ? 'safe' : 'warn'),
    },
    {
      label: '真实接口',
      value: httpTools.length
        ? (
          externalHttpTools.length === httpTools.length
            ? '外部 HTTP'
            : (fakeHttpTools.length === httpTools.length ? 'fake-http 验证' : `${configuredHttpTools.length}/${httpTools.length} 已配置`)
        )
        : 'Mock 模式',
      hint: httpTools.length
        ? (
          externalHttpTools.length === httpTools.length
            ? '当前所有业务工具都在走外部真实 HTTP'
            : (fakeHttpTools.length === httpTools.length ? '当前所有业务工具都在走进程内 fake-http 验证链路' : '部分工具仍未切到 HTTP 模式')
        )
        : 'Base URL 留空不会调用外部系统',
      tone: httpTools.length && configuredHttpTools.length !== httpTools.length
        ? 'warn'
        : (httpTools.length ? 'safe' : 'neutral'),
    },
    {
      label: '最近调用',
      value: events.length ? `${events.length - failedEvents.length}/${events.length} 成功` : '暂无调用',
      hint: events.length ? `失败率 ${(failureRate * 100).toFixed(0)}%` : '探测后会生成脱敏审计',
      tone: failedEvents.length ? 'warn' : 'safe',
    },
  ]
}

function readinessItemById(id) {
  const items = businessToolReadiness.value?.items || []
  return items.find(item => item.id === id)
}
</script>

<style scoped>
.api-settings {
  width: 100%;
  min-width: 0;
  max-width: 640px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.api-settings *,
.api-settings *::before,
.api-settings *::after {
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(14, 19, 34, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: var(--text-muted);
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.title-group h1 {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.settings-card {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 20px;
}

.settings-card h2 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
  letter-spacing: -0.01em;
}

.form-group {
  margin-bottom: 14px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.text-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-surface);
  transition: all 0.2s;
  font-family: var(--font-body);
}

.text-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--glow);
}

.text-input::placeholder {
  color: var(--text-muted);
}

.text-input.small {
  width: 140px;
}

.json-input {
  min-height: 180px;
  resize: vertical;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
}

.select-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-surface);
  cursor: pointer;
  font-family: var(--font-body);
}

.select-input:focus {
  outline: none;
  border-color: var(--accent);
}

.compact-select {
  min-width: 128px;
  padding: 7px 10px;
  border-radius: 8px;
  font-size: 12px;
}

.hint {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.form-row {
  display: flex;
  gap: 14px;
}

.form-row .form-group {
  flex: 1;
}

.toggle-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.toggle-row input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.error-banner,
.success-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  animation: fadeSlideIn 0.3s ease;
}

.error-banner {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.success-banner {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #10b981;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 4px;
}

.btn {
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-family: var(--font-display);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--accent);
  color: var(--bg-base);
}

.btn.primary:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: 0 4px 16px var(--glow);
}

.btn.secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.btn.secondary:hover:not(:disabled) {
  border-color: var(--border-default);
  color: var(--text-primary);
}

.btn.compact {
  padding: 7px 12px;
  font-size: 12px;
}

.workbench-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workbench-card h2 {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.workbench-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.workbench-header-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.workbench-header-copy p {
  margin: 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.workbench-header-actions {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.workbench-action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.workbench-action-buttons .btn {
  white-space: nowrap;
}

.workbench-download-hint {
  margin-top: -6px;
  font-size: 12px;
  color: var(--accent);
}

.workbench-overall {
  min-width: 160px;
  padding: 10px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--bg-surface);
}

.workbench-overall span,
.workbench-overall strong,
.workbench-overall small {
  display: block;
}

.workbench-overall span {
  color: var(--text-muted);
  font-size: 11px;
  margin-bottom: 4px;
}

.workbench-overall strong {
  color: var(--text-primary);
  font-size: 13px;
  margin-bottom: 4px;
}

.workbench-overall strong.ready {
  color: #10b981;
}

.workbench-overall strong.ready_with_warnings {
  color: #f59e0b;
}

.workbench-overall strong.blocked {
  color: #ef4444;
}

.workbench-overall strong.idle {
  color: var(--text-secondary);
}

.workbench-overall small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.45;
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.workbench-tool-card {
  min-width: 0;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}

.workbench-tool-card.safe {
  border-color: rgba(16, 185, 129, 0.18);
}

.workbench-tool-card.warn {
  border-color: rgba(245, 158, 11, 0.24);
}

.workbench-tool-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.workbench-tool-title {
  min-width: 0;
}

.workbench-tool-title span {
  display: block;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 5px;
}

.workbench-tool-title p {
  margin: 0;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.workbench-badges {
  max-width: 48%;
}

.workbench-runtime-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 96px;
  gap: 10px;
  margin-bottom: 12px;
}

.workbench-runtime-main,
.workbench-runtime-state,
.workbench-signal-item,
.workbench-audit-foot {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
}

.workbench-runtime-main span,
.workbench-runtime-main strong,
.workbench-runtime-main small,
.workbench-runtime-state span,
.workbench-runtime-state strong,
.workbench-signal-item span,
.workbench-signal-item strong,
.workbench-signal-item small,
.workbench-audit-foot span,
.workbench-audit-foot small {
  display: block;
}

.workbench-runtime-main span,
.workbench-runtime-state span,
.workbench-signal-item span,
.workbench-audit-foot span {
  color: var(--text-muted);
  font-size: 11px;
  margin-bottom: 4px;
}

.workbench-runtime-main strong,
.workbench-runtime-state strong,
.workbench-signal-item strong {
  color: var(--text-primary);
  font-size: 12px;
  margin-bottom: 4px;
}

.workbench-runtime-main small,
.workbench-signal-item small,
.workbench-audit-foot small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.workbench-signal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.workbench-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.workbench-audit-foot {
  margin-top: 10px;
}

.probe-section {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
}

.probe-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.intent-inspect-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.intent-inspect-section label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.intent-inspect-grid {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.response-validation-section {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.response-validation-section label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.probe-result {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  font-size: 12px;
  color: var(--text-secondary);
}

.probe-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.probe-result-header span {
  font-weight: 600;
  color: var(--text-primary);
}

.probe-result-header strong {
  font-size: 12px;
}

.probe-result-header strong.success {
  color: #10b981;
}

.probe-result-header strong.valid {
  color: #10b981;
}

.probe-result-header strong.error {
  color: #ef4444;
}

.probe-result-header strong.invalid {
  color: #ef4444;
}

.probe-result p {
  margin: 0 0 8px;
  line-height: 1.6;
}

.probe-diagnostic {
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.08);
  color: #f87171;
  word-break: break-word;
}

.probe-diagnostic-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.probe-diagnostic-details span {
  padding: 5px 8px;
  border-radius: 8px;
  background: var(--bg-elevated);
  border: 1px solid rgba(239, 68, 68, 0.16);
  color: var(--text-secondary);
}

.batch-validation-summary,
.batch-validation-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.batch-validation-summary span,
.batch-validation-item {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
}

.batch-validation-item {
  min-width: 160px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.batch-validation-item strong {
  font-size: 12px;
}

.batch-validation-item.valid strong {
  color: #10b981;
}

.batch-validation-item.invalid strong {
  color: #ef4444;
}

.probe-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--text-muted);
}

.safety-check {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.safety-check-item {
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
}

.safety-check-item span,
.safety-check-item strong,
.safety-check-item small {
  display: block;
}

.safety-check-item span {
  color: var(--text-muted);
  font-size: 11px;
  margin-bottom: 4px;
}

.safety-check-item strong {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 3px;
}

.safety-check-item small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.safety-check-item.safe {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(16, 185, 129, 0.055);
}

.safety-check-item.safe strong {
  color: #10b981;
}

.safety-check-item.warn {
  border-color: rgba(245, 158, 11, 0.2);
  background: rgba(245, 158, 11, 0.065);
}

.safety-check-item.warn strong {
  color: #f59e0b;
}

.safety-check-item.neutral strong {
  color: var(--text-secondary);
}

.runtime-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 12px;
}

.runtime-empty {
  font-size: 13px;
  color: var(--text-muted);
}

.readiness-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.readiness-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--bg-surface);
}

.readiness-head div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.readiness-head span {
  color: var(--text-muted);
  font-size: 11px;
}

.readiness-head strong {
  color: var(--text-primary);
  font-size: 14px;
}

.readiness-head strong.ready {
  color: #10b981;
}

.readiness-head strong.ready_with_warnings {
  color: #f59e0b;
}

.readiness-head strong.blocked {
  color: #ef4444;
}

.readiness-head small {
  max-width: 55%;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
  text-align: right;
  overflow-wrap: anywhere;
}

.readiness-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--text-muted);
  font-size: 11px;
}

.readiness-counts span {
  padding: 5px 8px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}

.readiness-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.readiness-item {
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
}

.readiness-item.passed {
  border-color: rgba(16, 185, 129, 0.18);
}

.readiness-item.warning {
  border-color: rgba(245, 158, 11, 0.2);
}

.readiness-item.blocked {
  border-color: rgba(239, 68, 68, 0.2);
}

.readiness-item-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.readiness-item-head span {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
}

.readiness-item-head strong {
  color: var(--text-muted);
  font-size: 11px;
}

.readiness-item.passed .readiness-item-head strong {
  color: #10b981;
}

.readiness-item.warning .readiness-item-head strong {
  color: #f59e0b;
}

.readiness-item.blocked .readiness-item-head strong {
  color: #ef4444;
}

.readiness-item p {
  margin: 0 0 6px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.5;
}

.readiness-item small {
  display: block;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.corpus-guidance {
  display: grid;
  gap: 7px;
  margin-top: 9px;
}

.corpus-guide {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 8px;
  border: 1px solid rgba(245, 158, 11, 0.16);
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.06);
}

.corpus-guide span {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.corpus-guide-command {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.corpus-guide-command code {
  display: block;
  width: 100%;
  min-width: 0;
  color: var(--text-primary);
  font-size: 10px;
  line-height: 1.5;
  white-space: normal;
  overflow-wrap: anywhere;
}

.copy-command-button {
  flex: 0 0 auto;
  min-height: 24px;
  padding: 4px 8px;
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.copy-command-button:hover {
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.18);
}

.corpus-copy-state {
  color: var(--text-muted);
  font-size: 10px;
}

.runtime-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.runtime-summary,
.runtime-reason,
.runtime-cell,
.runtime-tool {
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  background: var(--bg-surface);
}

.runtime-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
}

.runtime-summary span,
.runtime-cell span,
.runtime-tool-head span {
  color: var(--text-secondary);
  font-size: 12px;
}

.runtime-summary strong {
  font-size: 13px;
}

.runtime-summary strong.ready {
  color: #10b981;
}

.runtime-summary strong.disabled {
  color: var(--text-muted);
}

.runtime-summary strong.misconfigured {
  color: #f59e0b;
}

.runtime-reason {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  color: var(--text-muted);
  font-size: 12px;
}

.runtime-reason strong {
  color: #f59e0b;
  white-space: nowrap;
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.runtime-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  min-width: 0;
}

.runtime-cell strong {
  color: var(--text-primary);
  font-size: 13px;
}

.runtime-cell small {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.runtime-token-row,
.runtime-tool-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.runtime-token-row span,
.runtime-tool-meta span {
  overflow-wrap: anywhere;
}

.runtime-tool-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.runtime-tool {
  padding: 12px;
}

.runtime-tool-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.runtime-tool-head span {
  color: var(--text-primary);
  font-weight: 600;
}

.runtime-tool-head strong {
  color: var(--accent);
  font-size: 12px;
}

.audit-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 12px;
}

.audit-filter-row {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.audit-filter-row label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  color: var(--text-muted);
  font-size: 11px;
}

.audit-status {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 12px;
}

.audit-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audit-event {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
}

.audit-event-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.audit-event-head span {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.audit-event-head strong {
  font-size: 12px;
}

.audit-event-head strong.success {
  color: #10b981;
}

.audit-event-head strong.error {
  color: #ef4444;
}

.audit-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.audit-meta span {
  overflow-wrap: anywhere;
}

.audit-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.audit-selection span {
  overflow-wrap: anywhere;
}

.audit-empty {
  font-size: 13px;
  color: var(--text-muted);
}

.contract-empty {
  font-size: 13px;
  color: var(--text-muted);
}

.contract-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.contract-card-head h2 {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.contract-download-hint {
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--accent);
}

.error-text {
  color: #ef4444;
}

.contract-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.contract-panel {
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 14px;
  background: var(--bg-surface);
}

.contract-panel-wide {
  background: color-mix(in srgb, var(--bg-surface) 92%, var(--accent) 8%);
}

.contract-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.contract-header span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.contract-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.contract-badges code,
.contract-badges em {
  padding: 3px 6px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--bg-elevated);
  font-family: var(--font-mono);
  font-size: 11px;
  font-style: normal;
  line-height: 1.4;
  overflow-wrap: anywhere;
}

.contract-badges code {
  color: var(--accent);
}

.contract-badges em {
  color: var(--text-muted);
}

.contract-section {
  margin-top: 12px;
}

.contract-section strong {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.contract-section p {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.7;
  margin: 0;
}

.contract-json {
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.handoff-command-list,
.handoff-note-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.handoff-command-item {
  display: grid;
  grid-template-columns: minmax(120px, 0.35fr) minmax(0, 1fr);
  gap: 10px;
  align-items: start;
  padding: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-elevated);
}

.handoff-command-item span {
  color: var(--text-muted);
  font-size: 12px;
}

.handoff-command-item code {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.handoff-note-list span {
  padding: 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.field-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.handoff-step-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
}

.field-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}

.handoff-step-list .field-chip {
  min-width: 0;
  justify-content: center;
  text-align: center;
  white-space: normal;
  overflow-wrap: anywhere;
}

.field-chip em {
  font-style: normal;
  color: var(--accent);
}

.field-catalog-list,
.derived-step-list {
  display: grid;
  gap: 12px;
}

.field-catalog-item,
.derived-step-item {
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 12px;
  background: var(--bg-elevated);
}

.field-catalog-head,
.derived-step-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.field-catalog-head span,
.derived-step-head span {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.field-catalog-head code,
.derived-step-head code {
  color: var(--accent);
  font-family: var(--font-mono);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.field-catalog-meta,
.derived-step-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-bottom: 8px;
}

.field-catalog-meta em,
.derived-step-meta em {
  color: var(--text-muted);
  font-size: 11px;
  font-style: normal;
}

.field-catalog-item p,
.derived-step-item p {
  margin: 0;
}

.optional-chip-list {
  margin-top: 8px;
}

.field-chip.optional em {
  color: var(--text-muted);
}

@media (max-width: 720px) {
  .content {
    padding: 18px 14px;
  }

  .workbench-header,
  .workbench-header-actions,
  .workbench-grid,
  .workbench-runtime-row,
  .workbench-signal-grid,
  .safety-check,
  .readiness-list,
  .runtime-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .workbench-header-actions {
    width: 100%;
  }

  .workbench-overall,
  .workbench-badges,
  .workbench-action-buttons,
  .workbench-header-actions .btn {
    width: 100%;
    max-width: none;
  }

  .handoff-command-item {
    grid-template-columns: 1fr;
  }

  .readiness-head,
  .runtime-toolbar,
  .audit-toolbar,
  .audit-filter-row,
  .contract-card-head,
  .contract-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .contract-card-head .btn {
    width: 100%;
  }

  .audit-filter-row,
  .audit-filter-row label,
  .audit-filter-row .compact-select,
  .audit-filter-row .btn {
    width: 100%;
  }

  .workbench-action-row .btn {
    flex: 1 1 140px;
  }

  .readiness-head small {
    max-width: none;
    text-align: left;
  }
}
</style>
