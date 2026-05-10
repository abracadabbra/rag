#!/bin/bash

# Python 工程验证脚本
# 用途：验证项目结构和依赖是否正确

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

echo "=========================================="
echo "  Python 工程结构验证"
echo "=========================================="
echo ""

# 检查目录结构
print_info "检查目录结构..."

dirs=(
    "api"
    "api/routers"
    "api/services"
    "api/models"
    "ingestion"
    "infrastructure"
    "data/risk_rules"
    "data/test_cases"
    "tests"
    "logs"
)

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "$dir/"
    else
        print_error "$dir/ 不存在"
        exit 1
    fi
done

echo ""

# 检查关键文件
print_info "检查关键文件..."

files=(
    "api/__init__.py"
    "api/main.py"
    "api/config.py"
    "api/routers/__init__.py"
    "api/routers/health.py"
    "infrastructure/docker-compose.yml"
    "infrastructure/milvus_schema.py"
    "requirements.txt"
    "pyproject.toml"
    ".env.example"
    ".gitignore"
    "README.md"
    "Makefile"
    "setup.sh"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file"
    else
        print_error "$file 不存在"
        exit 1
    fi
done

echo ""

# 检查 Python 版本
print_info "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $python_version"

major_version=$(echo "$python_version" | cut -d. -f1)
minor_version=$(echo "$python_version" | cut -d. -f2)

if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 10 ]); then
    print_error "需要 Python 3.10+，当前版本: $python_version"
    exit 1
fi

echo ""

# 检查虚拟环境
print_info "检查虚拟环境..."
if [ -d "venv" ]; then
    print_success "虚拟环境已创建"
else
    print_info "虚拟环境未创建，运行: python3 -m venv venv"
fi

echo ""

# 尝试导入关键模块（如果虚拟环境存在）
if [ -d "venv" ]; then
    print_info "检查 Python 依赖..."

    source venv/bin/activate

    # 检查关键包
    packages=("fastapi" "uvicorn" "pydantic" "pymilvus" "redis")

    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            print_success "$pkg 已安装"
        else
            print_error "$pkg 未安装，运行: pip install -r requirements.txt"
        fi
    done

    deactivate
fi

echo ""

# 检查配置文件
print_info "检查配置文件..."
if [ -f ".env" ]; then
    print_success ".env 文件已创建"
else
    print_info ".env 文件未创建，运行: cp .env.example .env"
fi

echo ""

# 总结
echo "=========================================="
echo "  验证完成"
echo "=========================================="
echo ""
echo "📋 下一步："
echo "   1. 创建虚拟环境: python3 -m venv venv"
echo "   2. 安装依赖: source venv/bin/activate && pip install -r requirements.txt"
echo "   3. 创建配置: cp .env.example .env"
echo "   4. 启动基础设施: ./setup.sh"
echo "   5. 启动 API: make dev"
echo ""
