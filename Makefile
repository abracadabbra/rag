.PHONY: help setup start stop restart logs clean test format lint install

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
	@echo "format         - 格式化代码"
	@echo "lint           - 代码检查"
	@echo "clean          - 清理临时文件"

setup:
	@echo "🚀 一键启动基础设施..."
	./setup.sh

install:
	@echo "📦 安装 Python 依赖..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

start:
	@echo "🚀 启动 API 服务..."
	. venv/bin/activate && python api/main.py

dev:
	@echo "🔧 启动开发服务器（热重载）..."
	. venv/bin/activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

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
	. venv/bin/activate && pytest tests/ -v

format:
	@echo "✨ 格式化代码..."
	. venv/bin/activate && black api/ ingestion/ tests/
	. venv/bin/activate && isort api/ ingestion/ tests/

lint:
	@echo "🔍 代码检查..."
	. venv/bin/activate && flake8 api/ ingestion/ tests/ --max-line-length=100
	. venv/bin/activate && mypy api/ ingestion/

clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
	@echo "✅ 清理完成"
