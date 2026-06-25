# Business Tools Contract

This document defines the runtime contract for business-system tools used by the
RAG assistant. The goal is to keep real risk/profit system integration stable
without changing the agent, prompt, or frontend display contract.

The machine-readable source of truth lives in
`api/services/business_contracts.py`. Business clients use it for HTTP response
validation, and `BusinessToolService` uses the same module for prompt/frontend
allowlisting. Update that module first when real-system fields change, then
update this document and the contract tests in the same change.

Runtime contract snapshots are also exposed at:

```text
GET /api/v1/business-tools/contracts
```

The same snapshot can be exported without starting the API:

```bash
make business-contracts

# Optional custom path or compact JSON
make business-contracts BUSINESS_CONTRACT_OUTPUT_FILE=/tmp/business_tool_contracts.json
make business-contracts BUSINESS_CONTRACT_COMPACT=1
```

Both the endpoint and export CLI are read-only and do not call risk/profit
systems. Use either during real-system integration to verify endpoint templates,
request fields, required response fields, primitive type labels, exposed fields,
and the profit chain terminal node. The snapshot also includes
`request_json_schema`, `response_json_schema`, `example_response`, and any
backend-added `display_metadata_fields` for each tool, so integrators can
compare or validate a real response against the expected shape without reading
this document manually. It also includes a top-level `integration_handoff`
section with the recommended integration sequence, copyable commands,
`go_live_gates`, integration-mode semantics, and safety notes for real-system
owners. `display_metadata_fields` are explicitly not part of the upstream HTTP response contract;
they document fields added by this backend after response validation and before
prompt/frontend exposure. Each tool snapshot includes a manual
`contract_version` such as `v1`; bump it in
`api/services/business_contracts.py` whenever a required field, response schema,
or display allowlist changes in a way that external systems must coordinate.

The JSON schemas are intentionally permissive about extra response fields
(`additionalProperties=true`): real systems may return operational columns, but
only allowlisted fields are passed to prompts, frontend views, and safe audit
summaries.

Configured business tools can also be probed without LLM routing:

```text
POST /api/v1/business-tools/probe
{
  "tool_name": "get_profit_chain_detail",
  "order_id": "ORD88888"
}
```

The probe executes the selected tool against the current mock or HTTP client,
validates the response contract, filters the result through the same display
allowlist, writes the same safe audit log, and returns status, endpoint, data
source, integration mode, contract version, endpoint template, duration,
`audit_id`, summary, and allowlisted result fields. Unknown
tools return a 400 error; integration failures return a normal probe payload with
`status=error` and an error type, without raw exception details. Contract-shape
failures such as missing required fields or non-object JSON also include a safe
`diagnostic` string plus structured fields so integrators can fix response
fields without exposing network, authentication, or runtime exception details.
The structured probe diagnostics are:

- `diagnostic_code`: stable machine-readable category, such as
  `missing_required_fields`, `invalid_field_types`, `invalid_hit_rules`,
  `invalid_chain`, `invalid_json`, or `non_object_json`.
- `missing_fields`: required response fields that were absent.
- `invalid_fields`: fields or nested chain/rule entries whose type or shape did
  not match the contract.

Runtime, network, authentication, and unexpected implementation errors do not
include these diagnostic fields.

The request `order_id` is also validated before rendering an endpoint path. It
must match `^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$`; path separators, query-string
characters, whitespace, and empty values are rejected before any business-system
call is attempted. This keeps probe requests and LLM-derived tool intents from
turning an order id into a different URL path.

Before pointing the application at a real system, integrators can validate a
captured response sample without calling any business API:

```text
POST /api/v1/business-tools/validate-response
{
  "tool_name": "get_profit_chain_detail",
  "payload": {
    "order_id": "ORD88888",
    "gross_amount": 128.6,
    "platform_commission": 19.29,
    "driver_income": 92.35,
    "subsidy": 8.0,
    "coupon": 6.0,
    "platform_net_profit": 2.33
  }
}
```

The validation route reuses the same response-contract checks as the HTTP
clients, but it never returns the submitted payload values. Successful responses
include the allowlisted `exposed_result_keys` plus `ignored_result_keys`, a
top-level field-name list for values accepted from the real system but not
exposed to prompts or frontend views. Failed responses include the same safe
contract diagnostics as probe failures.

The repository also includes editable captured-response templates that
integrators can fill with real-system output and validate fully offline:

```bash
examples/business_tool_samples/risk_response.sample.json
examples/business_tool_samples/profit_response.sample.json

make business-validate-samples

make business-validate-samples \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json \
  BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation.json
```

`make business-validate-samples` calls
`scripts/validate_business_response_samples.py`, reuses the same local response
contract validator as the HTTP clients, and does not call risk/profit APIs or
depend on `RISK_API_BASE_URL` / `PROFIT_API_BASE_URL`. Its JSON report is safe
for CI logs and handoff comments: it returns status, diagnostic codes, missing
fields, invalid fields, and exposed result keys, but never echoes the complete
payload, order ids, money values, phone numbers, stack traces, or raw business
response bodies.

For handoffs with multiple captured real-system samples, use the batch route:

```text
POST /api/v1/business-tools/validate-responses
{
  "tool_name": "get_profit_chain_detail",
  "payloads": [
    { "...": "first captured response object" },
    { "...": "second captured response object" }
  ]
}
```

The batch response returns `validation_summary` plus indexed item results. It
counts valid/invalid samples, aggregates diagnostic codes and missing/invalid
field names, aggregates ignored top-level field names for valid samples, and
still never echoes submitted order ids, money values, phone numbers, or raw
payload values.

Operators can inspect the current business-tool runtime mode without calling
external risk/profit systems:

```text
GET /api/v1/business-tools/runtime-status
GET /api/v1/business-tools/readiness?limit=20
```

The management endpoints publish stable Pydantic/OpenAPI response models, so
frontend code, smoke scripts, and external integrators can validate against the
same contract instead of relying on raw dictionary shapes:

- `BusinessToolRuntimeStatusResponse` for `runtime-status`
- `BusinessToolReadinessResponse` for `readiness`
- `BusinessToolProbeResponse` for `probe`
- `BusinessToolValidationResponse` for `validate-response`
- `BusinessToolBatchValidationResponse` for `validate-responses`
- `BusinessToolAuditEventsResponse` for `audit-events`

The `readiness` model deliberately keeps each gate's `evidence` as a safe object
because different gates expose different non-sensitive proof fields. Its top
level fields, item envelope, corpus status, and runtime status dependencies are
typed and visible in `/openapi.json`.

`runtime-status` returns safe configuration metadata: whether business tools are
enabled, the configured timeout, whether each tool is in `mock` or `http` mode,
endpoint templates, whether base URLs/API keys/tokens are configured, audit
mode, LLM intent fallback settings, whether contracts are available, the safe
`status_reason`, and any missing read/execute access scopes.

`readiness` returns safe integration gates derived from runtime status and
recent sanitized audit metadata. It reports `overall_status`, passed/warning/
blocked gate IDs, and per-gate safe evidence for checks such as contract
availability, built-in example response validity, display allowlist coverage,
access control, real HTTP configuration, persistent audit, audit traceability,
LLM intent fallback readiness, and whether risk/profit business corpus scenes
have at least one indexed document. It does not call external business systems
and does not return API base URLs, API keys, shared tokens, audit file
directories, order IDs, selection-reason text, or business payload values. When
business corpus scenes are missing, the `corpus_scene_coverage` evidence includes
safe import guidance such as `source_path` and the matching `python -m
ingestion.ingest` command. Use these read-only endpoints for operational checks, and use `probe`
only when you intentionally want to execute a selected business tool with an
order id.

For offline development or CI smoke checks where embedding model files are not
available, run corpus ingestion with `USE_DETERMINISTIC_EMBEDDING=true`. This
mode produces stable local vectors so readiness gates can verify corpus coverage;
do not use it for production semantic retrieval quality.

## Runtime Switches

Configure these values in `.env`:

```env
ENABLE_BUSINESS_TOOLS=true
BUSINESS_TOOL_TIMEOUT=5
BUSINESS_TOOL_CORPUS_CHECK_TIMEOUT=1.0
ENABLE_BUSINESS_TOOL_LLM_INTENT=false
BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE=0.75
ENABLE_BUSINESS_TOOL_AUDIT_FILE=false
BUSINESS_TOOL_AUDIT_FILE=logs/business_tool_audit.jsonl
ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false
BUSINESS_TOOL_ACCESS_TOKEN=
BUSINESS_TOOL_READ_TOKEN=
BUSINESS_TOOL_EXECUTE_TOKEN=

RISK_API_BASE_URL=
RISK_API_KEY=

PROFIT_API_BASE_URL=
PROFIT_API_KEY=
```

Business tool runtime and API endpoint values can also be edited from the
frontend `API 设置` page. Empty API key inputs are skipped when saving, so an
existing key in `.env` is not overwritten by a masked or blank value. Runtime
settings are also applied to the current backend process and business tool
clients are rebuilt after saving, so switching between mock and HTTP mode does
not require an immediate restart. Audit file settings are `.env`-only
operational settings.

- `ENABLE_BUSINESS_TOOLS=false` disables all business tool execution.
- `BUSINESS_TOOL_CORPUS_CHECK_TIMEOUT` limits the read-only readiness corpus
  coverage probe so the settings page does not wait on an unavailable Milvus
  server.
- `ENABLE_BUSINESS_TOOL_LLM_INTENT=true` enables optional LLM intent fallback
  only when deterministic rules do not select a tool.
- `BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE` is the minimum confidence required
  before an LLM-selected tool can run or ask for missing fields.
- Live fallback acceptance is intentionally opt-in because it calls the
  configured model provider. Run
  `make business-llm-acceptance ORDER_ID=ORD88888 BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE=/tmp/business_llm_acceptance.json`
  after credentials are valid; the report must show `status=ok` and
  `selection_source=llm` before relying on ambiguous natural-language tool
  routing in production.
- `ENABLE_BUSINESS_TOOL_AUDIT_FILE=true` appends safe audit events to JSONL.
- `BUSINESS_TOOL_AUDIT_FILE` controls the JSONL path used when file audit is
  enabled.
- `ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=true` requires a shared token before
  exposing order-level business tool data.
- `BUSINESS_TOOL_ACCESS_TOKEN` is the full-access compatibility token. It works
  for both read and execute scopes.
- `BUSINESS_TOOL_READ_TOKEN` allows read-only business endpoints such as audit
  event reads and response sample validation.
- `BUSINESS_TOOL_EXECUTE_TOKEN` allows order-level queries, SSE, and tool probes;
  it also works on read-only endpoints.
- When access control is enabled but no token is configured for the requested
  scope, protected endpoints return 503 so the deployment fails closed.
- Empty `RISK_API_BASE_URL` / `PROFIT_API_BASE_URL` keeps deterministic mock data.
- Non-empty API base URLs switch clients to HTTP mode.
- `runtime-status.tools[*].data_source` continues to report `mock` or `http` for
  backward compatibility. `runtime-status.tools[*].integration_mode` adds the
  finer-grained runtime label: `mock`, `fake_http`, or `external_http`.
- API keys are sent as `Authorization: Bearer <token>` when configured.

When access control is enabled, clients must send:

```text
X-Business-Tool-Token: <BUSINESS_TOOL_ACCESS_TOKEN>
```

Protected endpoints are:

- Execute scope: `POST /api/v1/risk-rules/query`
- Execute scope: `POST /api/v1/profit/query`
- Execute scope: `POST /api/v1/{scene_type}/query` for `risk_rule` and `profit`
- Execute scope: `POST /api/v1/{scene_type}/query-stream` for `risk_rule` and
  `profit`
- Execute scope: `POST /api/v1/business-tools/probe`
- Read scope: `POST /api/v1/business-tools/validate-response`
- Read scope: `GET /api/v1/business-tools/audit-events`
- Read scope: `GET /api/v1/business-tools/runtime-status`
- Read scope: `GET /api/v1/business-tools/readiness`

`GET /api/v1/business-tools/contracts` stays public because it is read-only and
does not call risk/profit systems or reveal order-level data. Non-business
scenes such as model cards and simulation also stay available without this
header.

For local UI integration, `API 设置` includes a `本浏览器请求 Token` field. It
stores the value in `sessionStorage` for the current browser tab and attaches it
as `X-Business-Tool-Token` to order-level risk/profit queries, SSE queries,
business tool probes, response sample validation, and audit-event reads. It is not stored in `.env` and is
cleared when the browser session ends. The separate `服务端访问 Token` field
writes the backend's expected token.

## Tool Selection

The router uses a conservative two-stage selector:

1. Use deterministic rules first. This is the default and lowest-risk path.
2. If rules do not select a tool and `ENABLE_BUSINESS_TOOL_LLM_INTENT=true`,
   ask the LLM for structured intent JSON.
3. Execute the tool only when the selected tool matches the current scene, the
   confidence meets the configured threshold, and required fields are present.

Both `tool_intent` and executed `tool_calls` expose `selection_source` so the
frontend and audit views can distinguish deterministic `rules` routing from
`llm` fallback. Manual `/business-tools/probe` calls use `probe`.
The same selection metadata is injected into prompt context as `选择来源`,
`选择依据`, and `选择置信度`; scene prompts instruct the model to briefly explain
why a business interface was queried when these fields are present. This keeps
the generated answer aligned with the frontend decision timeline and the safe
audit record. API and audit payloads keep the stable machine values
`rules`/`llm`/`probe`/`none`, while prompt context renders them as human-readable
labels such as `规则命中`, `LLM 兜底`, and `手动探测`.

| Scene | Tool | Trigger |
| --- | --- | --- |
| `risk_rule` | `get_risk_event_detail` | Order id plus risk wording such as `风控`, `拦截`, `命中`, `风险`, `规则` |
| `profit` | `get_profit_chain_detail` | Order id plus profit wording such as `毛利`, `抽成`, `司机`, `收入`, `结算`, `链路` |

LLM fallback output is treated as an untrusted proposal. The backend rejects it
when:

- `tool_name` is not one of the registered tools.
- The tool does not belong to the current scene.
- The model returns malformed JSON.
- The model's free-text `reason` is not echoed into prompt context or frontend
  display. `selection_reason` is rebuilt from verified structured fields only.

When the LLM proposes a valid scene/tool and order id but `confidence` is below
`BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE`, the backend does not execute the
tool. It returns a `tool_intent` with
`missing_fields=["tool_intent_confirmation"]` and asks the user to confirm the
order-level lookup first. This keeps ambiguous prompts from silently calling
real business systems while still giving the user a clear path to proceed.

The agent treats `inspect_intent()` as the routing contract for the current
turn. If the intent does not need clarification, execution reuses that inspected
intent directly instead of running selection again. This keeps the visible
`tool_intent` aligned with `tool_calls`, and avoids a second LLM fallback call
for the same user query.

`BusinessToolService.inspect_intent()` returns a structured intent shape:

```json
{
  "tool_name": "get_profit_chain_detail",
  "selection_source": "rules",
  "order_id": null,
  "confidence": 0.68,
  "reason": "识别到订单级问题信号，当前场景为 profit，命中关键词: 毛利/抽成/司机/收入/结算/链路。",
  "missing_fields": ["order_id"],
  "needs_clarification": true
}
```

If an order-level tool intent is detected but no order id is found, the agent
asks the user to provide an order id instead of calling the business system.
General policy questions such as `帮我解释一下毛利抽成规则` do not trigger tool
intent or clarification.

Operators can inspect the same routing contract without executing order-level
business APIs:

```text
POST /api/v1/business-tools/intent
{
  "scene_type": "profit",
  "query": "查询订单 ORD88888 的抽成和司机收入"
}
```

This endpoint uses read scope, returns `ToolIntent`, and never calls risk/profit
HTTP clients. Use it before `probe` when debugging why a natural-language query
would or would not select a Function Calling tool.

## HTTP Endpoints

When API base URLs are configured, clients call:

```text
GET {RISK_API_BASE_URL}/risk/events/{order_id}
GET {PROFIT_API_BASE_URL}/profit/orders/{order_id}/chain
```

Responses must be JSON objects. Non-object JSON is treated as an integration
error and reported as an `error` tool call.

The `{order_id}` path parameter uses the same safe identifier contract as probe:
letters, digits, `_`, and `-`, up to 128 characters, starting with an
alphanumeric character. If an LLM intent fallback emits an unsafe order id, the
service ignores it and only uses a safe order id extracted from the original
user query; otherwise it asks for clarification instead of calling HTTP.

HTTP responses are validated at the business client boundary before they are
passed to prompts or the frontend. Missing required fields, invalid primitive
types, invalid `hit_rules` entries, or invalid profit `chain` steps raise a
contract error and reuse the normal tool failure path. Real systems may return
unknown extra fields, but `BusinessToolService` only exposes allowlisted fields
to `tool_calls.result` and prompt injection. Extra fields are not rendered to the
frontend and are not included in `系统接口数据`.

HTTP transport failures are classified before they reach the tool layer:

- HTTP status failures such as 401/403/500 become `ConnectionError` with only the
  safe status code.
- DNS/connect/read failures become `ConnectionError` with a generic connection
  message.
- Timeout failures become `TimeoutError` with a generic timeout message.

These transport errors must not expose raw URLs, tokens, API keys, order ids, or
response bodies. Contract diagnostics may expose only stable diagnostic codes and
field names.

## Risk Response Contract

Minimum fields:

```json
{
  "order_id": "ORD12345",
  "decision": "block",
  "risk_score": 87,
  "hit_rules": [
    {
      "rule_id": "RISK-velocity-001",
      "rule_name": "短时间多次高额交易",
      "evidence": "10 分钟内同卡 4 次交易，累计金额 1820 元"
    }
  ],
  "recommended_action": "建议保持拦截，并引导用户完成二次验证后重试。"
}
```

Optional fields currently displayed or useful for prompt grounding:

```json
{
  "risk_level": "high",
  "customer_context": {
    "user_level": "standard",
    "recent_chargebacks": 1,
    "account_age_days": 42
  },
  "transaction_context": {
    "amount": 680.0,
    "city": "上海",
    "channel": "app",
    "payment_method": "credit_card"
  }
}
```

## Profit Response Contract

Minimum fields:

```json
{
  "order_id": "ORD88888",
  "gross_amount": 128.6,
  "platform_commission": 19.29,
  "driver_income": 92.35,
  "subsidy": 8.0,
  "coupon": 6.0,
  "platform_net_profit": 2.33
}
```

Recommended fields for chain visualization:

```json
{
  "settlement_status": "settled",
  "commission_rate": "15.0%",
  "channel_fee": 2.96,
  "driver_income_detail": {
    "base_fare": 78.0,
    "distance_fee": 16.35,
    "service_fee_deduction": -2.0
  },
  "chain": [
    { "node": "乘客支付", "amount": 128.6 },
    { "node": "平台抽成", "amount": 19.29 },
    { "node": "司机收入", "amount": 92.35 },
    { "node": "平台补贴", "amount": -8.0 },
    { "node": "用户优惠", "amount": -6.0 },
    { "node": "渠道成本", "amount": -2.96 },
    { "node": "平台净毛利", "amount": 2.33 }
  ]
}
```

The frontend renders `result.chain` as a money-flow strip when present. Missing
`chain` no longer blocks visualization when the minimum amount fields are
present: the backend derives a standard display chain before prompt/frontend
allowlisting and adds the display metadata field `chain_source=derived`. Derived
steps are:

1. `gross_amount` -> `乘客支付`
2. `platform_commission` -> `平台抽成`
3. `driver_income` -> `司机收入`
4. `subsidy` -> `平台补贴` as a negative amount
5. `coupon` -> `用户优惠` as a negative amount
6. `channel_fee` -> `渠道成本` as a negative amount, when available
7. `platform_net_profit` -> `平台净毛利`

If the real system returns an explicit `chain`, that chain is preserved after
allowlisting and the backend adds `chain_source=api`. `chain_source` is
therefore backend-added explainability metadata, not an upstream required or
optional HTTP field. If required amount fields are missing, the frontend falls
back to key field chips and the prompt is instructed to call out missing nodes.

The frontend also renders a `公式核对` strip above the money-flow timeline when
the required amount fields are available. It computes:

```text
platform_commission - subsidy - coupon - channel_fee = calculated_net_profit
```

`channel_fee` is treated as `0` when absent because it is optional in the
minimum contract. The strip displays whether the calculated value matches
`platform_net_profit`; a mismatch is shown as a review signal instead of being
silently hidden. `driver_income` stays visible in the flow as fulfillment
settlement evidence, but it is not counted again in the platform net-profit
formula.

## Display and Prompt Allowlist

Only the following fields may be exposed to the frontend or prompt context:

- Risk: `order_id`, `decision`, `risk_score`, `risk_level`, `hit_rules.rule_id`,
  `hit_rules.rule_name`, `hit_rules.evidence`, `transaction_context.amount`,
  `transaction_context.city`, `transaction_context.channel`,
  `transaction_context.payment_method`, `customer_context.user_level`,
  `customer_context.recent_chargebacks`, `customer_context.account_age_days`,
  `recommended_action`.
- Profit: `order_id`, `settlement_status`, `gross_amount`,
  `platform_commission`, `commission_rate`, `driver_income`,
  `driver_income_detail.base_fare`, `driver_income_detail.distance_fee`,
  `driver_income_detail.service_fee_deduction`, `subsidy`, `coupon`,
  `channel_fee`, `platform_net_profit`, `chain.node`,
  `chain.amount`, `chain.source_field`, `chain.role`, `chain.tone`,
  `chain.note`.
  Backend-added profit display metadata currently includes
  `display_metadata_fields = ["chain_source"]`; this metadata is exposed to the
  frontend/prompt after validation, but it is not part of the upstream HTTP
  response contract or `response_json_schema`.
For profit tools, the recommended `chain` should end with `平台净毛利` so the
frontend money-flow strip has an explicit conclusion.

Tool audit logs record allowlisted top-level result keys for troubleshooting,
but never log full result payload values or raw-system-only field names.

## API Response Shape

Business tool calls are returned in `QueryResponse.tool_calls` and in the SSE
`sources` event payload. When callers pass an explicit answer perspective,
`QueryResponse.answer_perspective` and the SSE `sources.answer_perspective`
echo the selected value so clients can display the applied perspective:

Streaming query endpoints may also emit `progress` events before `sources` and
`chunk` events. The progress payload includes `stage` and `message`; current
stages are `intent`, `retrieve`, `tool`, and `generate`.
Business scenes must only return `sources` whose `scene_type` matches the
requested scene, so profit explanations do not cite model-card or unrelated
risk-rule documents.

```json
{
  "tool_intent": {
    "tool_name": "get_profit_chain_detail",
    "label": "订单毛利链路",
    "scene_type": "profit",
    "selection_source": "rules",
    "order_id": "ORD88888",
    "confidence": 0.92,
    "reason": "识别到订单号 ORD88888，当前场景为 profit，命中关键词: 毛利/抽成/司机/收入/结算/链路。",
    "missing_fields": [],
    "needs_clarification": false,
    "clarification_options": []
  },
  "tool_calls": [
    {
      "name": "get_profit_chain_detail",
      "label": "订单毛利链路",
      "scene_type": "profit",
      "description": "按订单查询平台抽成、司机收入、补贴、优惠和结算链路",
      "endpoint_path": "/profit/orders/ORD88888/chain",
      "endpoint_template": "/profit/orders/{order_id}/chain",
      "contract_version": "v1",
      "data_source": "http",
      "selection_source": "rules",
      "arguments": { "order_id": "ORD88888" },
      "status": "success",
      "duration_ms": 12,
      "selection_reason": "识别到订单号 ORD88888，当前场景为 profit，命中关键词: 毛利/抽成/司机/收入/结算/链路。",
      "confidence": 0.92,
      "summary": "订单 ORD88888 总金额 128.6 元，平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 2.33 元。",
      "result": {}
    }
  ]
}
```

When an order-level intent is detected but the order id is missing,
`tool_calls` remains empty and `tool_intent` explains the missing field. In
SSE mode this is sent as a `clarification` event before any tool call or RAG
generation:

```json
{
  "needs_clarification": true,
  "clarification_options": [
    "请补充订单号后再查询，例如：订单 ORD88888 的订单毛利链路。"
  ],
  "tool_intent": {
    "tool_name": "get_profit_chain_detail",
    "selection_source": "rules",
    "order_id": null,
    "confidence": 0.68,
    "missing_fields": ["order_id"],
    "needs_clarification": true
  },
  "tool_calls": []
}
```

When a client call fails, the main RAG answer still continues. The failed call is
returned as:

```json
{
  "status": "error",
  "duration_ms": 12,
  "result": {},
  "summary": "订单毛利链路调用失败，请稍后重试或联系系统管理员。",
  "error_type": "RuntimeError"
}
```

Raw exception details are not returned to the frontend or injected into the
prompt. The frontend degradation panel shows the audit ID, safe exception class
name from `error_type`, safe contract diagnostics when available, and a
retry/probe suggestion. Non-streaming route failures return a generic message
with a request id, while backend logs keep the full exception for
troubleshooting.

The same rule applies to `POST /api/v1/business-tools/probe`: HTTP transport
failures from the real clients are returned as `status=error` with safe
`ConnectionError` or `TimeoutError` classes, empty `result`, and the generic
probe summary. Raw host names, URLs, tokens, authorization messages, and
transport exception text stay out of the API response. Only contract validation
failures may include structured diagnostic codes and field names.

For SSE route-level failures, the stream emits an `error` event with a generic
message, `error_type`, and `request_id`. The original exception message stays
only in backend logs.

The prompt contract also treats `status=error` as a degradation path: the
assistant must say that the realtime business interface did not successfully
return order data, must not invent an order-level conclusion, should answer only
from retrievable documents when useful, and should mention retrying or using the
visible audit ID for troubleshooting. When a tool call includes
`diagnostic_code`, `missing_fields`, or `invalid_fields`, the prompt context may
use those safe field names to point integrators toward the response contract
mismatch without exposing raw payload values.

Tool-call and probe responses may include safe contract diagnostics for response
contract failures:

```json
{
  "status": "error",
  "error_type": "BusinessContractError",
  "diagnostic": "Profit API response contract violation: missing required fields: platform_net_profit",
  "diagnostic_code": "missing_required_fields",
  "missing_fields": ["platform_net_profit"],
  "invalid_fields": []
}
```

These fields are only returned for response-contract failures. Operational
failures still return the generic probe summary plus `error_type` only.
Safe audit events may also retain `diagnostic_code`, `missing_fields`, and
`invalid_fields`; they do not retain raw response payloads or exception text.

When the business tool succeeds but the LLM generation fails or times out, the
assistant does not discard the verified system data. It returns a fallback
answer that starts with `业务系统接口数据已返回` and includes the formatted
`系统接口数据` summary. This keeps order-level risk/profit answers auditable even
when the language model provider is temporarily unavailable. Retrieved document
explanations and richer natural-language analysis can be regenerated after the
LLM recovers.

## Answer Shaping

The answer-shaping source of truth lives in
`api/services/prompt_templates.py`. `RAGService._build_prompt()` delegates to
`build_scene_prompt(...)`, and business tool summaries are passed through its
`tool_context` argument.

Business tool data is injected into the RAG prompt as `系统接口数据`. When present,
the assistant must use that verified system data for the business conclusion
first, then use retrieved documents to explain policies, rules, formulas, and
caveats. Unknown fields filtered out by the display/prompt allowlist must not be
reintroduced in prompt wording. If validation or diagnostic context includes
`ignored_result_keys` / 未展示字段, the prompt may only say that these top-level
fields were filtered by the display allowlist; it must not infer, quote, or use
their values as business evidence.

Scene-specific prompt contracts:

- `risk_rule`: answer with 风控结论, 命中规则/依据, key evidence fields, 处置建议,
  an operator/user-facing explanation, and a 风控策略视角 that covers rule
  thresholds, evidence strength, and whether strategy configuration should be
  reviewed. Missing evidence must be stated explicitly instead of inferred.
- `profit`: answer with 订单毛利结论 and 钱流链路. Cover 平台抽成, 司机收入, 补贴,
  优惠, 渠道成本, and 平台净毛利 when fields are available. Include a 财务口径
  that separates revenue, costs, subsidies, discounts, and net profit, and an
  运营口径 that highlights actionable anomalies such as high subsidy, discount
  erosion, or abnormal driver income. Missing chain nodes must be called out.
- `model_card`: focus on model purpose, version, status, metrics, features, and
  usage boundaries.
- `simulation`: focus on simulation conclusion, metric changes, abnormal
  signals, assumptions, and next analysis steps.

Each scene profile also defines a stable `建议输出段落` skeleton. This is a
prompt-level contract for readability and auditability; it does not change the
API response schema. Current business skeletons are:

- `risk_rule`: `结论`, `命中依据`, `处置建议`, `口径说明`, `信息来源`.
- `profit`: `订单结论`, `钱流链路`, `财务口径`, `运营关注点`, `信息来源`.

The skeleton tells the LLM how to organize the final answer after it has already
prioritized verified `系统接口数据`. `信息来源` should include system interface
data, audit ID when available, and retrieved document IDs so the frontend-visible
tool call, backend audit event, and answer text can be reconciled.

Within business scenes, the prompt also infers a primary answer perspective from
the user's wording and writes it into a `回答口径` block:

- Profit finance questions use `财务口径`: emphasize revenue, cost, subsidy,
  discount, channel fee, and platform net profit.
- Profit operations questions use `运营口径`: emphasize actionable margin
  anomalies such as subsidy, discount, driver income, or channel fee issues.
- Risk strategy questions use `风控策略口径`: emphasize rule thresholds,
  evidence strength, false-positive risk, and strategy review suggestions.
- Debugging questions use `技术排查口径`: emphasize interface status, audit ID,
  missing fields, invalid field types, and next troubleshooting steps.
- If no perspective keyword is detected, the prompt uses a balanced scene
  perspective and still follows the scene contract above.

Callers can override keyword inference by passing `answer_perspective` on
`POST /api/v1/{scene_type}/query` or `POST /api/v1/{scene_type}/query-stream`.
Supported business-scene values are:

- `profit`: `finance`, `operations`, `technical`, `balanced`.
- `risk_rule`: `strategy`, `operations`, `technical`, `balanced`.

Invalid or unsupported values are ignored and fall back to the deterministic
keyword inference described below. The frontend `API` business QA views expose
the same choice as a compact `回答口径` control with `自动` as the default, and
explicit selections are shown on the answer card.

Perspective keyword precedence is intentionally deterministic. For both risk
and profit scenes, technical/debug words such as interface failure, audit ID,
field problems, or troubleshooting are checked first so degradation answers do
not drift into business conclusions. In `risk_rule`, strategy keywords are then
checked before operations keywords, so explicit rule/threshold/review wording
uses the strategy perspective. In `profit`, operations keywords are checked
before finance keywords, so subsidy, discount, driver-income, channel, or
anomaly wording uses the operations perspective even when a query also mentions
margin concepts. Ordinary order or money-flow queries without those keywords
fall back to the balanced scene perspective.

## Audit Logging

Each executed business tool writes one safe audit log record:

```text
Business tool audit - tool=get_profit_chain_detail scene=profit status=success duration_ms=12 arguments={'order_id': 'ORD***888'} result_keys=['chain', 'driver_income', ...] error_type=None
```

The audit record includes:

- Audit ID, shared with `tool_calls[*].audit_id` and probe responses.
- Tool name and scene.
- Success/error status.
- Duration in milliseconds.
- Sanitized arguments.
- Sanitized tool selection reason and confidence, so operators can reconstruct
  why the tool was called without exposing raw order identifiers.
- Allowlisted top-level result keys only, not full business payload values or
  raw-system-only field names.
- Error type only, not raw exception messages.

Sensitive argument keys are masked before logging, including `order_id`,
`user_id`, `driver_id`, `phone`, `mobile`, `id_card`, `card_no`, and
`payment_account`.

Recent safe audit events are also available from a read-only endpoint:

```text
GET /api/v1/business-tools/audit-events?limit=20
```

The endpoint returns newest events first and uses the same sanitized arguments
as the log record. Events include audit ID, timestamp, tool name, scene, data
source, endpoint template, status, duration, sanitized arguments, top-level
result keys, contract version, sanitized selection reason, confidence, and
error type. They never include full result payload values or raw
exception messages. The current implementation keeps a small in-memory rolling
window for local debugging and integration checks. When file audit is enabled,
the endpoint also reads recent safe events back from the JSONL audit file and
deduplicates them by `audit_id`, so integration checks can still inspect recent
tool calls after a backend process rebuild.

For integration or production-like runs, set
`ENABLE_BUSINESS_TOOL_AUDIT_FILE=true` to append the same sanitized event shape
to `BUSINESS_TOOL_AUDIT_FILE` as JSONL. File audit persistence is best-effort:
write failures are logged with the error type only and do not fail the business
tool call. The JSONL record still excludes full result payload values and raw
exception messages, so it is suitable as an integration handoff format before a
real audit store is connected.

## Frontend Display

`frontend/src/components/QAView.vue` reads `tool_calls` from the SSE `sources`
event and displays:

- Tool-intent precheck status before or alongside execution: target tool,
  order id when available, matching reason, confidence, missing fields, and the
  next clarification step when the backend intentionally does not execute yet.
- A compact decision timeline that makes the route visible as
  `意图识别 -> 信息补齐 -> 接口执行 -> 结果返回`, including whether the flow is
  still waiting for order id / confirmation, already executed, or degraded.
- Tool name and success/error status.
- Audit ID for matching visible answer evidence to backend logs or JSONL audit
  records.
- Tool duration when available.
- Data source (`mock` or `http`) and endpoint path.
- Tool selection reason and confidence when available.
- Short summary generated by `BusinessToolService`.
- Key risk/profit fields.
- Risk `result.hit_rules` as a rule/evidence list when present.
- Profit `result.chain` as a role-tagged money-flow visualization when present:
  each node shows the business role, such as order revenue, platform revenue,
  driver settlement, platform/marketing/channel cost, or final operating result.
  When `gross_amount` is available, each node also shows its signed share of GMV
  and a short business note such as "income enters the margin formula",
  "discount erodes commission", or "final retained margin".
  Chain items may additionally carry `source_field / role / tone / note`
  metadata so frontend rendering stays deterministic even when real systems
  provide different field ordering or omit a prebuilt chain array. The chain
  header also displays the backend-added `result.chain_source` metadata as
  `接口原生链路` or `自动派生链路`.
- Profit calls also render a `毛利拆解` panel when amount fields are present:
  KPI blocks for GMV, platform commission, driver income, and net profit;
  an explicit formula row for
  `platform_commission - subsidy - coupon - channel_fee = platform_net_profit`;
  a revenue/cost/net-profit ledger for commission, subsidy, coupon, channel
  fee, and net profit; and anomaly signal chips for negative or low net margin,
  high subsidy, discount erosion, or high channel fee.
- The `订单钱流链路` panel includes a `公式核对` strip. It recomputes net profit
  from the exposed amount fields, labels matches as `与接口净毛利一致`, and labels
  differences as `与接口净毛利不一致` so finance or operations users can spot data
  contract drift quickly.
- Failed tool calls render an `接口降级提示` panel with the audit ID, safe
  `error_type`, safe contract diagnostics when available, and a suggestion to
  retry or use API Settings probe/response validation. Raw exception messages,
  stack traces, endpoint credentials, and order payload details are not
  rendered.

`frontend/src/views/ApiSettings.vue` also shows recent business tool audit
events so integrators can verify which tool ran, which endpoint template was
used, which audit ID links it back to answer cards and logs, whether the call
used mock or HTTP data, how long it took, which sanitized arguments were passed,
which sanitized selection reason and confidence led to the call, which result
keys were returned, and whether an error type was recorded. The audit list can
be filtered locally by tool, call status, and `selection_source`, so operators
can quickly isolate failed profit calls, manual probes, or LLM fallback events
without changing the backend query or requesting a wider audit payload.
For response-contract failures, the audit list and per-tool workbench summary
also show safe diagnostic codes plus missing/invalid field names, which keeps
field-shape debugging visible without exposing raw order payload values.

The same page includes an integration workbench for risk and profit tools. Each
tool card summarizes the contract version, runtime integration mode, contract
availability, latest probe result, latest offline response validation result,
latest sanitized audit event, exposed-field count, and a traceability footnote
when an audit event exists. Probe and validation summaries are tracked per tool,
so testing the profit interface does not overwrite the last visible risk
diagnostic, and vice versa. This gives operators a compact first stop before
opening the longer runtime, readiness, audit, and contract sections.

The same settings page shows the profit contract's auto-derived chain steps
from `GET /api/v1/business-tools/contracts`, so integrators can see which
top-level fields are enough to power the money-flow visualization even when the
real system does not return a dedicated `chain` array.

The settings page also renders a `业务工具接入安全检查` summary from
`runtime-status`, `readiness`, and `audit-events`. It highlights whether access
control is enabled and scope-ready, whether audit records are memory-only or
file-backed, whether configured tools are still in mock mode or pointed at HTTP
systems, the recent sanitized-call success ratio, and the backend-provided
readiness gates. This summary uses only safe booleans, counts, data-source
labels, safe audit IDs, and failure-rate metadata; it does not display raw base
URLs, tokens, API keys, order payloads, selection-reason text, or raw exception
details.

### Frontend Runtime Smoke Check

Run this after backend or frontend changes that affect `tool_calls`:

```bash
venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
cd frontend && npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/profit` and submit
`查询订单 ORD88888 的抽成和司机收入`.

Success-state checks:

- The status bar shows the backend is connected.
- `系统接口调用` is visible with status `成功`.
- Data source shows `Mock 数据` unless a real `PROFIT_API_BASE_URL` is configured.
- The endpoint path is `/profit/orders/ORD88888/chain`.
- The visible fields include audit ID, order id, gross amount, platform
  commission, driver income, and net profit.
- `毛利拆解`, `毛利公式`, and `订单钱流链路` are visible.
- The chain contains passenger payment, platform commission, driver income,
  subsidy, coupon, channel cost, and platform net profit nodes.
- Chain nodes show signed GMV share labels and business notes for income,
  settlement, costs, and final retained margin.

Degradation-state checks can be run with a temporary backend process that points
profit traffic at an unreachable local port:

```bash
PROFIT_API_BASE_URL=http://127.0.0.1:9 \
PROFIT_API_KEY=secret \
BUSINESS_TOOL_TIMEOUT=1 \
venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Then submit the same query. The page should render `系统接口调用` with status
`失败`, data source `真实接口`, the same endpoint path, `接口降级提示`, audit ID,
and safe `ConnectionError` or `TimeoutError`. It must not render raw host names,
URLs, tokens, authorization messages, stack traces, or raw transport exception
text.

## Integration Notes

- Keep sensitive fields out of `result` unless they are safe to show.
- Prefer numeric money fields in yuan as numbers.
- Real systems may return unknown optional fields, but frontend display and
  prompt context only receive fields allowed by `BusinessToolService`.
- Add contract tests before changing endpoint paths or field names.

## Integration Smoke Check

Before pointing the assistant at real risk/profit systems, run the local smoke
check in mock mode:

```bash
make business-smoke
```

For CI or a production integration gate, require a fully clean readiness report:

```bash
make business-smoke-strict
```

If you already have captured JSON samples from real systems, pass them to the
same command for offline contract validation:

```bash
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json
```

For CI logs or integration handoff notes, keep stdout compact while preserving
the full machine-readable report as an artifact:

```bash
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  BUSINESS_SMOKE_OUTPUT_FILE=/tmp/business_smoke_report.json \
  BUSINESS_SMOKE_SUMMARY_ONLY=1
```

For handoff to the real risk/profit system owners, generate an acceptance pack
that combines the contract snapshot, readiness gates, safe smoke evidence, and
recommended next actions:

```bash
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack.json

# Local HTTP-contract rehearsal without depending on external systems
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_FAKE_HTTP=1 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack_fake_http.json
```

The pack is produced by `scripts/business_tool_acceptance_pack.py`. It reuses
`api/services/business_contracts.py` and `scripts/business_tool_smoke.py`, so it
does not introduce a second contract source. Its top-level `status` is
`accepted`, `needs_attention`, or `blocked`, derived from
`readiness_summary.overall_status`. The `integration_handoff` section lists
`must_fix_before_real_order_traffic`, `should_fix_before_production`, and
`recommended_next_actions` so the recipient can see exactly which gate remains.
The pack includes safe evidence only and does not echo captured response
payloads. It also includes `sample_handoff`, which points to the editable risk
and profit response templates, the default `make business-validate-samples`
command, a custom command for captured files, and the report-safety guarantee.
The same pack includes `prompt_contract`, a machine-readable snapshot of the
risk/profit answer profiles, answer perspectives, expected section structure,
and safety rules from `api/services/prompt_templates.py`. This lets business
owners review not only the HTTP field contract, but also how verified system
data, diagnostics, and filtered fields will be explained to users.
If smoke execution fails before a readiness report can be built, the pack still
returns `status=blocked` with `smoke_execution` evidence. For known safe failure
shapes such as a profit tool call returning `ConnectionError`, the evidence
includes a diagnostic code, the affected tool, a safe failure type, and a
suggested next action instead of the raw assertion or transport details.

For a local end-to-end rehearsal that uses the real HTTP client path without
depending on external risk/profit systems, enable the built-in fake HTTP mode:

```bash
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  BUSINESS_SMOKE_FAKE_HTTP=1
```

The Makefile target automatically uses `./.venv/bin/python`, `./venv/bin/python`,
or `python3`, in that order. The direct script form is equivalent when you want
to call a specific interpreter:

```bash
venv/bin/python scripts/business_tool_smoke.py \
  --order-id ORD88888 \
  --audit-file /tmp/business_tool_audit.jsonl \
  --fail-on-blocked

venv/bin/python scripts/business_tool_smoke.py \
  --order-id ORD88888 \
  --audit-file /tmp/business_tool_audit.jsonl \
  --require-ready

venv/bin/python scripts/business_tool_smoke.py \
  --order-id ORD88888 \
  --audit-file /tmp/business_tool_audit.jsonl \
  --require-ready \
  --summary-only \
  --output-file /tmp/business_smoke_report.json

venv/bin/python scripts/business_tool_smoke.py \
  --order-id ORD88888 \
  --audit-file /tmp/business_tool_audit.jsonl \
  --require-ready \
  --fake-http
```

The command first runs a natural-language profit query such as `查询订单 ORD88888
的抽成和司机收入` through `BusinessToolService.inspect_intent()`,
`execute_intent()`, and `format_tool_context()`. It verifies that the inspected
intent chooses `get_profit_chain_detail`, execution reuses that intent without
rerouting, the tool call returns required money fields and a display chain, and
the prompt-ready `系统接口数据` context includes the endpoint path plus key profit
fields. The smoke report records this as `query_smoke.execution_path:
"inspected_intent"` so CI can catch accidental drift back to duplicate routing.

The report includes a safe `runtime_status` summary before probe results. Use it
to confirm whether business tools are enabled, access-control scopes are ready,
LLM intent fallback is enabled, each tool is running against `mock` or `http`,
and the configured timeout value. It only exposes booleans such as
`base_url_configured` and `api_key_configured`, not raw URLs, tokens, or API
keys.

The report also includes a machine-readable `readiness_check` section. Treat
the top-level smoke `status: "ok"` as "the smoke command ran to completion";
use `readiness_check.overall_status` to decide whether the integration is ready
for real order traffic:

- `ready`: all required checks passed and no warning remains.
- `ready_with_warnings`: required checks passed, but integration hygiene still
  needs attention, such as mock mode, access control not enabled, no JSONL audit
  file, or no captured real-system response samples.
- `blocked`: at least one required gate failed, such as business tools disabled,
  missing contracts, failed probes, missing audit traceability, unsafe
  degradation, leaked diagnostics, or captured response samples that do not
  satisfy the contract.

`readiness_check.items` contains one object per gate with safe `evidence` only:
booleans, tool names, data-source labels, diagnostic codes, missing/invalid
field names, counts, and safe audit IDs. The `intent_precheck` gate verifies
that standard risk/profit order questions select the expected tool through
`inspect_intent()` without executing business HTTP clients, and reports only
scene/tool/source/confidence metadata. The `audit_traceability` gate verifies
that the natural-language tool call has a matching audit event with sanitized
selection reason and numeric confidence, but it does not print the reason text.
It must not contain raw order IDs, response payload values, URLs, tokens, host
names, authorization messages, or raw exception text.
This makes the section suitable for CI output and integration handoff notes.
When `--fail-on-blocked` is passed, the script prints the full JSON report first
and then exits with code `2` if `overall_status` is `blocked`. `ready` and
`ready_with_warnings` still exit `0`, so warnings stay visible without blocking
local mock-mode checks.
When `--require-ready` is passed, `blocked` exits `2` and
`ready_with_warnings` exits `3`; only `ready` exits `0`. Use this stricter mode
for CI or the final gate before enabling real order traffic.
When using the Makefile target, treat `make business-smoke-strict` as a
non-zero/zero gate. GNU Make may return its own non-zero error code rather than
preserving the script's exact `2` or `3`; call the Python script directly when a
CI job needs to branch on the exact readiness exit code.
When `--summary-only` is passed, stdout contains only the top-level command
status, readiness status/counts, warning/blocker IDs, and audit event count.
When `--output-file PATH` is passed, the script writes the full safe JSON report
to that path regardless of whether stdout is full or summary-only.

It then probes both business tools through the same service boundary as
`POST /api/v1/business-tools/probe`, validates required response fields,
confirms `audit_id` propagation across query and probe calls, checks that audit
events do not contain the raw order id, and optionally validates JSONL audit
output.

When `--fake-http` is enabled, the smoke command patches the risk/profit HTTP
transport in process and serves deterministic payloads for the same endpoint
paths used by the real clients. This allows `runtime_status.tools[*].data_source`
and the `real_http_configured` readiness gate to move to `http` / `passed`
without leaking base URLs, tokens, depending on external systems, or binding a
local port.
In this mode, `runtime_status.tools[*].integration_mode` is `fake_http` rather
than `external_http`, so operators can distinguish local acceptance from a true
external system rollout.
The `real_http_configured` gate passes in fake mode because the HTTP client path
is exercised. The separate `external_http_configured` gate remains a warning
until both tools run with `integration_mode=external_http`.
Before treating real order traffic as ready, re-run the strict gate with the
actual external risk/profit base URLs and confirm `integration_mode` is
`external_http`.

The smoke also injects a temporary `RuntimeError` into the profit tool executor
to verify runtime degradation before real HTTP traffic is exposed to users. The
expected report section is `runtime_failure_smoke`: `status` must be `error`,
`error_type` must be the safe exception class name, `result` must stay empty,
the prompt-ready context must include only `错误类型: RuntimeError`, and neither
memory audit events nor optional JSONL audit output may contain the raw
exception message.

Contract-shape failures use a narrower degradation contract. Natural-language
tool calls, manual probe responses, prompt-ready context, and safe audit events
may include `diagnostic_code`, `missing_fields`, and `invalid_fields` when the
error is a `BusinessContractError`; runtime, network, and authentication errors
must not include these fields.

The report also includes `http_transport_failure_smoke`. This section patches
the HTTP transport boundary in-process, does not perform network I/O, and
verifies 401, 500, URL/connect errors, and timeout errors. Expected outputs use
only safe `ConnectionError` or `TimeoutError` classes plus generic messages; raw
URLs, tokens, host names, authorization messages, and order ids must not appear.

Finally, the smoke command submits an intentionally incomplete profit response
sample to the same offline response validator used by
`POST /api/v1/business-tools/validate-response`. This verifies that missing
required fields produce a structured `missing_required_fields` diagnostic while
the submitted order id and money values stay out of the diagnostic payload. This
is the fastest local check for real HTTP integrations that are reachable but do
not yet match the field contract. When captured valid samples contain extra
top-level fields that are accepted by the upstream response but filtered by the
display/prompt allowlist, `captured_sample_validation.evidence.ignored_result_keys`
records those field names so integrators can see which fields will not be shown
to users; the field values are still not echoed.

When `--risk-response-file` or `--profit-response-file` is provided, the report
adds `sample_validations`. Each entry returns only validation status, diagnostic
code, missing/invalid field names, and exposed result keys. It never echoes the
captured response payload values, so the same command can be shared in
integration notes without leaking order data.

After setting `RISK_API_BASE_URL` and `PROFIT_API_BASE_URL`, run the same command
against a non-production order id to catch response contract, authentication, or
timeout issues before exposing the integration in the UI.

For a real-environment go-live gate, treat `ready` as the only acceptable
`readiness_check.overall_status`. In practice, this means:

- `access_control_enabled` must be `passed`.
- `real_http_configured` must be `passed`.
- `external_http_configured` must be `passed` before real order traffic; it
  remains a warning for fake HTTP rehearsals.
- `persistent_audit_enabled` must be `passed`.
- `audit_traceability` must be `passed`.
- `llm_intent_fallback` must be `passed` only when production is expected to
  rely on ambiguous natural-language order questions. Treat this as satisfied
  only after at least one live fallback attempt has produced a successful
  structured intent result; model configuration alone is not enough. If you
  intentionally do not enable LLM fallback in production, keep
  `ENABLE_BUSINESS_TOOL_LLM_INTENT=false` and document that operating mode
  explicitly in the deployment handoff.
