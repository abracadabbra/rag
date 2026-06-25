.PHONY: help setup start stop restart logs clean test format lint install business-contracts business-acceptance-pack business-validate-samples business-smoke business-smoke-strict business-llm-acceptance

VENV_DIR ?= .venv
PYTHON_BIN ?= $(shell if [ -x ./$(VENV_DIR)/bin/python ]; then echo ./$(VENV_DIR)/bin/python; elif [ -x ./.venv/bin/python ]; then echo ./.venv/bin/python; elif [ -x ./venv/bin/python ]; then echo ./venv/bin/python; else echo python3; fi)
ORDER_ID ?= ORD88888
BUSINESS_SMOKE_AUDIT_FILE ?= /tmp/business_tool_audit.jsonl
BUSINESS_SMOKE_FAKE_HTTP ?=
RISK_RESPONSE_FILE ?=
PROFIT_RESPONSE_FILE ?=
BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE ?=
BUSINESS_SMOKE_OUTPUT_FILE ?=
BUSINESS_SMOKE_SUMMARY_ONLY ?=
BUSINESS_SMOKE_OPTIONAL_ARGS = $(if $(BUSINESS_SMOKE_OUTPUT_FILE),--output-file "$(BUSINESS_SMOKE_OUTPUT_FILE)",) $(if $(BUSINESS_SMOKE_SUMMARY_ONLY),--summary-only,) $(if $(BUSINESS_SMOKE_FAKE_HTTP),--fake-http,) $(if $(RISK_RESPONSE_FILE),--risk-response-file "$(RISK_RESPONSE_FILE)",) $(if $(PROFIT_RESPONSE_FILE),--profit-response-file "$(PROFIT_RESPONSE_FILE)",)
BUSINESS_CONTRACT_OUTPUT_FILE ?= /tmp/business_tool_contracts.json
BUSINESS_CONTRACT_COMPACT ?=
BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE ?= /tmp/business_tool_acceptance_pack.json
BUSINESS_ACCEPTANCE_PACK_OPTIONAL_ARGS = $(if $(BUSINESS_SMOKE_FAKE_HTTP),--fake-http,) $(if $(RISK_RESPONSE_FILE),--risk-response-file "$(RISK_RESPONSE_FILE)",) $(if $(PROFIT_RESPONSE_FILE),--profit-response-file "$(PROFIT_RESPONSE_FILE)",)
BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE ?=
BUSINESS_LLM_LOW_CONFIDENCE_THRESHOLD ?= 0.99

help:
	@echo "RAG 系统 - 常用命令"
	@echo ""
	@echo "setup          - 一键启动基础设施"
	@echo "install        - 安装 Python 依赖"
	@echo "start          - 启动 API 服务"
	@echo "dev            - 启动开发服务器（热重载）"
	@echo ""
	@echo "infra-up       - 启动基础设施（Milvus + Redis）"
	@echo "infra-down     - 停止基础设施"
	@echo "infra-restart  - 重启基础设施"
	@echo "infra-logs     - 查看基础设施日志"
	@echo ""
	@echo "test           - 运行测试"
	@echo "business-contracts - 导出风控/毛利业务工具合同 JSON"
	@echo "business-acceptance-pack - 导出合同 + readiness + 下一步动作验收包"
	@echo "business-validate-samples - 离线校验风控/毛利响应样例 JSON"
	@echo "business-smoke - 业务工具接入前 smoke/readiness 检查"
	@echo "business-smoke-strict - 业务工具严格 readiness 门禁"
	@echo "business-llm-acceptance - 真实 LLM 工具意图兜底验收"
	@echo "format         - 格式化代码"
	@echo "lint           - 代码检查"
	@echo "clean          - 清理临时文件"

setup:
	@echo "🚀 一键启动基础设施..."
	./setup.sh

install:
	@echo "📦 安装 Python 依赖..."
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt

start:
	@echo "🚀 启动 API 服务..."
	$(PYTHON_BIN) api/main.py

dev:
	@echo "🔧 启动开发服务器（热重载）..."
	$(PYTHON_BIN) -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

infra-up:
	@echo "🐳 启动基础设施..."
	cd infrastructure && docker-compose up -d

infra-down:
	@echo "🛑 停止基础设施..."
	cd infrastructure && docker-compose down

infra-restart:
	@echo "🔄 重启基础设施..."
	cd infrastructure && docker-compose restart

infra-logs:
	@echo "📋 查看基础设施日志..."
	cd infrastructure && docker-compose logs -f

test:
	@echo "🧪 运行测试..."
	$(PYTHON_BIN) -m pytest tests/ -v

business-contracts:
	@echo "📄 导出风控/毛利业务工具合同..."
	$(PYTHON_BIN) -B scripts/export_business_contracts.py \
		--output "$(BUSINESS_CONTRACT_OUTPUT_FILE)" \
		$(if $(BUSINESS_CONTRACT_COMPACT),--compact,)

business-acceptance-pack:
	@echo "📦 导出业务工具接入验收包..."
	$(PYTHON_BIN) -B scripts/business_tool_acceptance_pack.py \
		--order-id "$(ORDER_ID)" \
		--audit-file "$(BUSINESS_SMOKE_AUDIT_FILE)" \
		--output "$(BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE)" \
		$(BUSINESS_ACCEPTANCE_PACK_OPTIONAL_ARGS)

business-validate-samples:
	@echo "🧾 离线校验业务工具响应样例..."
	$(PYTHON_BIN) -B scripts/validate_business_response_samples.py \
		--risk-response-file "$(or $(RISK_RESPONSE_FILE),examples/business_tool_samples/risk_response.sample.json)" \
		--profit-response-file "$(or $(PROFIT_RESPONSE_FILE),examples/business_tool_samples/profit_response.sample.json)" \
		$(if $(BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE),--output "$(BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE)",)

business-smoke:
	@echo "🧪 业务工具接入前 smoke/readiness 检查..."
	$(PYTHON_BIN) -B scripts/business_tool_smoke.py \
		--order-id "$(ORDER_ID)" \
		--audit-file "$(BUSINESS_SMOKE_AUDIT_FILE)" \
		--fail-on-blocked \
		$(BUSINESS_SMOKE_OPTIONAL_ARGS)

business-smoke-strict:
	@echo "🧪 业务工具严格 readiness 门禁..."
	$(PYTHON_BIN) -B scripts/business_tool_smoke.py \
		--order-id "$(ORDER_ID)" \
		--audit-file "$(BUSINESS_SMOKE_AUDIT_FILE)" \
		--require-ready \
		$(BUSINESS_SMOKE_OPTIONAL_ARGS)

business-llm-acceptance:
	@echo "🧪 真实 LLM 工具意图兜底验收..."
	$(PYTHON_BIN) -B scripts/business_tool_llm_acceptance.py \
		--order-id "$(ORDER_ID)" \
		--low-confidence-threshold "$(BUSINESS_LLM_LOW_CONFIDENCE_THRESHOLD)" \
		$(if $(BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE),--output-file "$(BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE)",)

format:
	@echo "✨ 格式化代码..."
	$(PYTHON_BIN) -m black api/ ingestion/ tests/
	$(PYTHON_BIN) -m isort api/ ingestion/ tests/

lint:
	@echo "🔍 代码检查..."
	$(PYTHON_BIN) -m flake8 api/ ingestion/ tests/ --max-line-length=100
	$(PYTHON_BIN) -m mypy api/ ingestion/

clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
	@echo "✅ 清理完成"
