# 业务工具真实接入 Quickstart

这份文档只回答一件事：把风控/毛利工具从本地 mock 切到真实业务系统时，最短路径怎么走。

完整合同、审计、安全门禁和前端展示细节仍以 [docs/BUSINESS_TOOLS.md](./BUSINESS_TOOLS.md) 为准；这份文档更像接入清单。

## 1. 先准备最小返回字段

如果要先把当前合同发给真实系统联调方，可以离线导出机器可读快照：

```bash
make business-contracts

# 自定义输出路径
make business-contracts BUSINESS_CONTRACT_OUTPUT_FILE=/tmp/business_tool_contracts.json
```

这个命令只读取 `api/services/business_contracts.py` 的本地合同定义，不启动 API，
也不会调用风控或毛利真实系统。导出的 JSON 默认写入
`/tmp/business_tool_contracts.json`，并与
`GET /api/v1/business-tools/contracts` 使用同一个后端来源。
导出的 JSON 还包含顶层 `integration_handoff`：联调顺序、可复制命令、
`go_live_gates`、mock/fake/external 三种模式语义和安全说明。
如果你需要把回答口径也一起交给联调方，`GET /api/v1/business-tools/contracts`
和 `make business-contracts` 还会带上 `prompt_contract`，里面包含风控/毛利两类场景的
回答口径、建议输出段落和安全说明，前端 `/settings` 的“业务接口合同”也会同步展示。

如果要把合同、readiness 结果、阻塞项和下一步动作一起交给联调方，可以生成验收包：

```bash
make business-acceptance-pack
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack.json
```

验收包会复用同一份合同定义和 smoke/readiness 检查，默认写入
`/tmp/business_tool_acceptance_pack.json`。它包含 `contracts`、
`readiness_summary`、逐项 `readiness_items`、安全 smoke 证据和
`integration_handoff.recommended_next_actions`；不回显真实响应 payload。

### 风控接口最小合同

至少返回这些字段：

```json
{
  "order_id": "ORD88888",
  "decision": "block",
  "risk_score": 92,
  "risk_level": "high",
  "recommended_action": "人工复核后拦截",
  "hit_rules": [
    {
      "rule_id": "R001",
      "rule_name": "高风险设备",
      "evidence": "设备指纹命中历史黑名单"
    }
  ]
}
```

### 毛利接口最小合同

至少返回这些字段：

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

建议同时返回 `chain`，这样前端可以直接展示完整钱流链路；如果真实接口暂时不返回，后端会按顶层金额字段自动派生基础链路，并把 `chain_source` 标记为自动派生，方便联调排障。

这里要特别注意：`chain_source` 不是上游接口必填字段，也不应该由真实业务系统返回。它是后端在合同校验通过之后补充的展示元信息，只用于前端和 Prompt 解释“这条链路是接口原生返回还是后端自动派生”。

## 2. 配好 `.env`

```env
ENABLE_BUSINESS_TOOLS=true
ENABLE_BUSINESS_TOOL_LLM_INTENT=false
ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false
ENABLE_BUSINESS_TOOL_AUDIT_FILE=false

RISK_API_BASE_URL=https://risk.example.com/api
RISK_API_KEY=your-risk-token

PROFIT_API_BASE_URL=https://profit.example.com/api
PROFIT_API_KEY=your-profit-token
```

说明：

- `RISK_API_BASE_URL` / `PROFIT_API_BASE_URL` 留空时走 mock。
- 配成真实地址后会切到 HTTP 模式。
- 要先联调安全门禁，再打开 `ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=true`。
- 要先确认脱敏策略，再打开 `ENABLE_BUSINESS_TOOL_AUDIT_FILE=true`。

## 3. 建议按这条顺序联调

1. `mock`
   验证问答链路、前端展示、Prompt 口径。
2. `fake_http`
   验证 HTTP 路径、合同校验、错误降级和审计，不依赖真实系统。
3. `external_http`
   接真实风控/毛利系统，做小流量探测。

如果只是想看“当前到底在走哪种模式”，直接打开前端 `API 设置` 页面，或者调用：

```bash
curl http://127.0.0.1:8000/api/v1/business-tools/runtime-status
curl "http://127.0.0.1:8000/api/v1/business-tools/readiness?limit=20"
```

这些管理接口已经在 `/openapi.json` 发布稳定响应模型：
`BusinessToolRuntimeStatusResponse`、`BusinessToolReadinessResponse`、
`BusinessToolProbeResponse`、`BusinessToolValidationResponse`、
`BusinessToolBatchValidationResponse` 和 `BusinessToolAuditEventsResponse`。
联调脚本或外部系统可以优先按这些 schema 做字段校验，再进入真实订单探测。

## 4. 用预检、探测和样例校验先卡住合同

### 4.1 先预检自然语言会不会调工具

```bash
curl -X POST http://127.0.0.1:8000/api/v1/business-tools/intent \
  -H 'Content-Type: application/json' \
  -d '{"scene_type":"profit","query":"查询订单 ORD88888 的抽成和司机收入"}'
```

这个接口只返回 `tool_intent`，不会调用真实风控/毛利系统。先看
`tool_name`、`selection_source`、`confidence`、`missing_fields` 和
`needs_clarification`，确认路由判断正确后再做探测。

### 4.2 探测真实接口

```bash
curl -X POST http://127.0.0.1:8000/api/v1/business-tools/probe \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"get_risk_event_detail","order_id":"ORD88888"}'

curl -X POST http://127.0.0.1:8000/api/v1/business-tools/probe \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"get_profit_chain_detail","order_id":"ORD88888"}'
```

看四件事：

- `status` 是否成功
- `integration_mode` 是否已经变成 `external_http`
- `diagnostic` / `missing_fields` / `invalid_fields` 是否为空
- `audit_id`、`duration_ms`、`endpoint_path` 是否可追踪

### 4.3 不打真实接口，只校验样例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/business-tools/validate-response \
  -H 'Content-Type: application/json' \
  -d '{
    "tool_name":"get_profit_chain_detail",
    "payload":{
      "order_id":"ORD88888",
      "gross_amount":128.6,
      "platform_commission":19.29,
      "driver_income":92.35,
      "subsidy":8.0,
      "coupon":6.0,
      "platform_net_profit":2.33
    }
  }'
```

这一步很适合在真实系统还没放开联调环境前先做合同对齐。
如果业务方一次给多条真实响应样例，可以走批量校验：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/business-tools/validate-responses \
  -H 'Content-Type: application/json' \
  -d '{"tool_name":"get_profit_chain_detail","payloads":[{"order_id":"ORD88888","gross_amount":128.6,"platform_commission":19.29,"driver_income":92.35,"subsidy":8.0,"coupon":6.0,"platform_net_profit":2.33}]}'
```

批量响应只返回通过/失败数量、诊断码计数、缺失/异常字段、未展示字段名和逐条
index，不回显原始订单号、金额、手机号或完整 payload。

仓库也提供了可直接复制给联调方填写的样例文件：

- `examples/business_tool_samples/risk_response.sample.json`
- `examples/business_tool_samples/profit_response.sample.json`

把真实系统返回粘进去后，可以完全离线校验，不会调用任何风控/毛利接口：

```bash
make business-validate-samples

make business-validate-samples \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json \
  BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation.json
```

输出只包含通过/失败、诊断码、缺失字段、异常字段、可展示字段和未展示字段名，
不回显完整响应 payload。

## 5. 前端该看哪里

### API 设置

`/settings` 页能看：

- 接入检查工作台
- 合同快照
- 回答口径合同 `prompt_contract`
- 当前 mock / fake_http / external_http 模式
- readiness 门禁
- 接口探测
- 响应样例校验
- 最近审计事件

建议先看 `接入检查工作台`：它会按风控/毛利两个工具汇总合同版本、接入模式、合同状态、最近探测、样例校验、字段暴露和最近审计。工作台会按工具分别保留最近一次探测和样例校验结果，所以可以连续测风控和毛利，不会因为后测一个工具就把另一个工具的联调状态抹掉。

排查调用记录时看 `业务工具审计`：可以按工具、成功/失败状态、选择来源筛选，快速定位“毛利真实接口失败”“风控手动探测”“LLM 兜底触发”等场景。筛选只发生在当前已加载的脱敏审计列表里，不会扩大后端返回范围。

### 风控 / 毛利问答页

回答卡下方会展示 `tool_calls`，重点看：

- 调了哪个工具
- 走的是 mock 还是真实接口
- 接口路径、审计 ID、耗时
- 工具选择依据和置信度
- 风控命中规则证据
- 毛利拆解与订单钱流链路
- 毛利链路里的 `公式核对` 是否显示 `与接口净毛利一致`
- 链路来源是接口原生返回还是后端自动派生
- 失败时的安全降级提示

## 6. 上线前最少过一遍这个清单

- [ ] `GET /api/v1/business-tools/contracts` 能拿到当前合同
- [ ] `scripts/export_business_contracts.py` 导出的离线合同已同步给真实系统联调方
- [ ] `POST /api/v1/business-tools/intent` 能解释会不会选择工具且不调用真实接口
- [ ] 风控 probe 成功，字段无缺失
- [ ] 毛利 probe 成功，字段无缺失
- [ ] `validate-response` 能拦住缺字段和错类型
- [ ] `validate-responses` 能批量汇总真实样例诊断且不回显 payload
- [ ] `make business-validate-samples` 能校验真实系统响应样例文件
- [ ] `runtime-status` 显示真实接口已配置
- [ ] `readiness` 的 `external_http_configured` 已通过；fake-http 演练不能替代真实外部系统门禁
- [ ] `readiness` 没有 access control / contract / audit 相关 blocked
- [ ] 前端问答页能看到 `tool_calls`
- [ ] 前端能看到风控证据或毛利链路
- [ ] 失败调用只暴露安全的 `error_type` / `diagnostic`
- [ ] 审计里不出现原始密钥、完整 payload、堆栈

## 7. 发现问题时先看什么

- 缺字段 / 类型不对：
  先跑 `validate-response`；多条样例一起看时跑 `validate-responses`
- 不确定一句话为什么会/不会调接口：
  先跑 `intent`
- HTTP 通了但页面没展示：
  先看 `tool_calls.result` 是否有 allowlist 字段
- 页面显示“接口降级提示”：
  先看 `probe` 返回的 `diagnostic_code`
- readiness 不通过：
  先看 `/settings` 页里的门禁项和 evidence

更完整的字段语义、Schema、审计和 Prompt 合同说明，见 [docs/BUSINESS_TOOLS.md](./BUSINESS_TOOLS.md)。
