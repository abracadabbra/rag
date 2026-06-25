# Business Tool Acceptance Checklist

This document records the verified acceptance state for the risk/profit business
tool integration and the remaining go-live blockers.

## Scope

Acceptance covers five areas:

1. HTTP client acceptance chain through in-process fake HTTP transport
2. Persistent audit file loop
3. Frontend business acceptance
4. Real LLM intent-fallback acceptance
5. Final go-live checklist and handoff notes

## Current Status

As of June 23, 2026, the current live acceptance status is:

- `real_http_configured`: passed
- `external_http_configured`: not accepted yet
- `persistent_audit_enabled`: passed
- `audit_traceability`: passed
- `intent_precheck`: passed
- `frontend profit/risk evidence display`: passed
- `LLM intent fallback`: not accepted yet

Current readiness snapshot:

- `overall_status=ready_with_warnings`
- warnings:
  - `access_control_enabled`
  - `external_http_configured`
  - `llm_intent_fallback`
- blockers: none

Readiness semantics for `llm_intent_fallback` are now stricter:

- `passed` only after LLM fallback is enabled, the model is configured, and at
  least one real live attempt has produced a successful structured intent result
- `warning` when fallback is disabled, not fully configured, has never
  succeeded, or the latest live attempt failed

## Accepted Items

### 1. HTTP Client Acceptance Chain

Verified through the in-process fake HTTP path:

- both business tools run with `data_source=http`
- both business tools expose `integration_mode=fake_http`
- `GET /api/v1/business-tools/readiness` returns `real_http_configured=passed`
- smoke `readiness_check` includes `intent_precheck=passed` for risk/profit
  standard prompts without executing business HTTP clients
- tool probes succeed through the real HTTP client path
- transport/runtime degradation handling remains safe

This proves the HTTP client, contract validation, audit, and readiness paths. It
does not by itself prove an external production risk/profit system is reachable;
that final rollout gate requires `integration_mode=external_http`.

Evidence:

- `GET /api/v1/business-tools/runtime-status`
- `GET /api/v1/business-tools/readiness?limit=5`
- `POST /api/v1/business-tools/probe`
- `make business-smoke-strict BUSINESS_SMOKE_FAKE_HTTP=1`

### 2. Persistent Audit Loop

Verified end to end:

- JSONL audit is enabled
- natural-language order queries create audit events
- `audit_id`, `selection_reason`, and `confidence` are persisted
- `/settings` audit summary matches the file-backed event count
- `/api/v1/business-tools/audit-events` matches the latest JSONL entries

Evidence gathered on June 18, 2026:

- `logs/business_tool_audit.jsonl` line count increased during live queries
- latest audit ids from UI were found in the JSONL file
- latest audit ids from UI were found in `/api/v1/business-tools/audit-events`

### 3. Frontend Business Acceptance

Verified in the live UI:

- `/settings`
  - shows `fake-http 验证`
  - shows readiness counts and warning items
  - shows audit file readability and persisted event count
- `/profit`
  - shows `tool_calls`
  - shows `audit_id`
  - shows `selection_reason`
  - shows `模式: 进程内 fake-http 验证`
  - shows profit breakdown and money-flow chain
- `/risk-rules`
  - shows `tool_calls`
  - shows `audit_id`
  - shows `selection_reason`
  - shows `模式: 进程内 fake-http 验证`
  - shows hit-rule evidence clearly

## Not Yet Accepted

### 4. Real LLM Intent Fallback

This item is not complete yet.

Required acceptance behavior:

- ambiguous questions produce structured tool intent
- low-confidence intent asks for clarification
- invalid or low-confidence output does not call business APIs

Current blocker as of June 18, 2026:

- live LLM calls return `401 Invalid token`
- current runtime setting is `ENABLE_BUSINESS_TOOL_LLM_INTENT=false`
- runtime/readiness intentionally keep `llm_intent_fallback=warning` until a
  successful live structured fallback attempt is observed

Observed evidence:

- backend log contains repeated authentication failures from the configured LLM
  path
- live business queries fall back to the safe non-LLM response path

Before re-running this acceptance:

1. provide a valid LLM credential
2. enable `ENABLE_BUSINESS_TOOL_LLM_INTENT=true`
3. keep `BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE=0.75` or another reviewed value
4. verify one high-confidence case and one low-confidence clarification case

What is already covered before live re-run:

- unit tests verify that LLM fallback can select the correct tool when rules are
  ambiguous
- unit tests verify that low-confidence fallback does not execute the business
  tool and instead asks for confirmation
- unit tests verify that missing order id asks for clarification
- unit tests verify that malformed JSON, unknown tools, cross-scene tools, and
  invalid order ids are rejected safely
- unit tests verify that untrusted LLM `reason` text does not leak into
  execution context
- runtime status now records safe fallback telemetry:
  `attempt_count`, `success_count`, `error_count`, `last_status`,
  `last_resolution`, `last_error_type`, and safe timestamps

Relevant tests:

- `tests/test_tool_service.py::test_llm_intent_fallback_executes_when_rules_are_ambiguous`
- `tests/test_tool_service.py::test_llm_intent_fallback_does_not_execute_below_threshold`
- `tests/test_tool_service.py::test_llm_intent_fallback_clarifies_missing_order_id`
- `tests/test_tool_service.py::test_llm_intent_fallback_rejects_malformed_or_contract_breaking_output`
- `tests/test_tool_service.py::test_llm_intent_fallback_does_not_echo_untrusted_reason`

Suggested live re-acceptance flow after credentials recover:

1. Run the live acceptance command:
   `make business-llm-acceptance ORDER_ID=ORD88888 BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE=/tmp/business_llm_acceptance.json`
2. Confirm the report has `status=ok`.
3. Confirm `checks.high_confidence_tool_intent=true`.
4. Confirm `checks.low_confidence_clarification=true`.
5. Confirm `checks.invalid_order_id_not_executed=true`.
6. Confirm `llm_intent_runtime.last_status=success`.
7. Optionally repeat through the UI/API and inspect audit events to confirm no
   unintended business call was executed during clarification cases.

Manual equivalent:

1. `PATCH /api/v1/settings/` to enable `enable_business_tool_llm_intent=true`
2. ask one ambiguous but tool-relevant profit question, for example:
   `看看订单 ORD88888 的费用是怎么分的`
3. confirm the response returns a structured `tool_intent` with
   `selection_source=llm`
4. raise `BUSINESS_TOOL_LLM_INTENT_MIN_CONFIDENCE` temporarily, ask a similar
   question, and confirm `needs_clarification=true`,
   `missing_fields=["tool_intent_confirmation"]`, and `tool_calls=[]`
5. ask with an invalid order id and confirm `tool_calls=[]`

## Go-Live Checklist

Treat `ready` as the only acceptable final state for real production rollout.

Required before real order traffic:

- `real_http_configured=passed`
- `external_http_configured=passed`
- `persistent_audit_enabled=passed`
- `audit_traceability=passed`
- `access_control_enabled=passed`
- captured response samples validated against contract

Conditional requirement:

- if production depends on ambiguous natural-language order questions,
  `llm_intent_fallback=passed` is required, which now means there is at least
  one successful live fallback record rather than only a configured model name
- if production does not use LLM fallback, keep
  `ENABLE_BUSINESS_TOOL_LLM_INTENT=false` and document that operating mode in
  deployment notes

## Recommended Commands

Read-only checks:

```bash
curl http://127.0.0.1:8000/api/v1/business-tools/runtime-status
curl "http://127.0.0.1:8000/api/v1/business-tools/readiness?limit=20"
curl "http://127.0.0.1:8000/api/v1/business-tools/audit-events?limit=20"
```

Acceptance smoke:

```bash
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack.json
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_FAKE_HTTP=1 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack_fake_http.json
make business-smoke
make business-smoke-strict
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  BUSINESS_SMOKE_FAKE_HTTP=1
make business-llm-acceptance ORDER_ID=ORD88888 \
  BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE=/tmp/business_llm_acceptance.json
```

The smoke report's `intent_precheck` gate is safe for CI logs: it records only
scene/tool/source/confidence and clarification flags, not raw order IDs or
business payload values.

Use `/tmp/business_tool_acceptance_pack.json` as the integration handoff artifact
when coordinating with real-system owners. It bundles the current machine-
readable contracts, readiness item evidence, safe smoke summaries, and
`integration_handoff.recommended_next_actions` without echoing captured response
payloads. The pack also includes `sample_handoff` with the editable sample
templates, `make business-validate-samples`, a custom captured-file command, and
the report-safety guarantee for offline response validation. If smoke execution
fails before readiness can be assembled, the pack remains machine-readable with
`status=blocked`, `smoke_execution.diagnostic_code`, safe failure type, and a
suggested action rather than raw transport details.
It also includes `prompt_contract`, which snapshots the risk/profit answer
profiles, supported perspectives, expected answer structure, and prompt safety
rules from `api/services/prompt_templates.py`.
Offline validation reports may list `ignored_result_keys`, which are top-level
field names accepted from valid samples but intentionally not exposed to prompts
or frontend views; field values are still never echoed.

Offline response validation:

```bash
make business-validate-samples
make business-validate-samples \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json \
  BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation.json

curl -X POST http://127.0.0.1:8000/api/v1/business-tools/validate-response \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"get_profit_chain_detail","payload":{"order_id":"ORD88888","gross_amount":128.6,"platform_commission":19.29,"driver_income":92.35,"subsidy":8.0,"coupon":6.0,"platform_net_profit":2.33}}'
```

## Handoff Notes

- `MINIMAX_API_BASE` default is `https://topapi.link/v1`
- fake HTTP acceptance proves the real HTTP client path is stable, but it is not
  the same as external production-system rollout
- current live warnings are expected until access control and optional LLM
  fallback are finalized
