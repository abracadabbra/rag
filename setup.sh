#!/bin/bash

# RAG 系统快速启动脚本
# 用途：一键启动基础设施并初始化环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 检查前置条件
check_prerequisites() {
    print_info "检查前置条件..."

    check_command docker
    check_command docker-compose
    check_command python3

    print_success "前置条件检查通过"
}

# 创建 .env 文件
setup_env() {
    if [ ! -f .env ]; then
        print_info "创建 .env 文件..."
        cp .env.example .env
        print_warning "请编辑 .env 文件，填入必要的配置（如 OPENAI_API_KEY）"
        print_warning "按 Enter 继续..."
        read
    else
        print_info ".env 文件已存在，跳过创建"
    fi
}

# 启动基础设施
start_infrastructure() {
    print_info "启动基础设施（Milvus + Redis）..."

    cd infrastructure
    docker-compose up -d
    cd ..

    print_info "等待服务启动（30秒）..."
    sleep 30
}

# 检查服务健康
check_health() {
    print_info "检查服务健康状态..."

    # 检查 Milvus
    if curl -s http://localhost:9091/healthz | grep -q "OK"; then
        print_success "Milvus 运行正常"
    else
        print_error "Milvus 启动失败，请检查日志: docker-compose logs milvus"
        exit 1
    fi

    # 检查 Redis
    if docker exec rag-redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis 运行正常"
    else
        print_error "Redis 启动失败，请检查日志: docker-compose logs redis"
        exit 1
    fi
}

# 安装 Python 依赖
install_dependencies() {
    print_info "安装 Python 依赖..."

    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi

    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_warning "requirements.txt 不存在，跳过依赖安装"
    fi
}

# 初始化 Milvus Collection
init_milvus() {
    print_info "初始化 Milvus Collection..."

    source venv/bin/activate
    python3 infrastructure/milvus_schema.py --action create

    print_success "Milvus Collection 创建成功"
}

# 显示访问信息
show_info() {
    echo ""
    print_success "🎉 RAG 系统基础设施启动成功！"
    echo ""
    echo "📊 服务访问地址："
    echo "   - Milvus:          localhost:19530"
    echo "   - Redis:           localhost:6379"
    echo "   - MinIO Console:   http://localhost:9001 (minioadmin/minioadmin)"
    echo "   - Redis Commander: http://localhost:8081"
    echo ""
    echo "📝 下一步："
    echo "   1. 编辑 .env 文件，配置 OPENAI_API_KEY"
    echo "   2. 准备数据：参考 数据准备指南.md"
    echo "   3. 运行数据摄入：python ingestion/ingest.py --source data/risk_rules"
    echo "   4. 启动 API 服务：python api/main.py"
    echo ""
    echo "🔧 常用命令："
    echo "   - 查看日志：cd infrastructure && docker-compose logs -f"
    echo "   - 停止服务：cd infrastructure && docker-compose stop"
    echo "   - 重启服务：cd infrastructure && docker-compose restart"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  RAG 系统基础设施快速启动"
    echo "=========================================="
    echo ""

    check_prerequisites
    setup_env
    start_infrastructure
    check_health
    install_dependencies
    init_milvus
    show_info
}

# 执行主函数
main
