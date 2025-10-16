#!/bin/bash
# Harmony Adapter 构建脚本

set -e

# Token 配置
TEST_PYPI_TOKEN="pypi-AgENdGVzdC5weXBpLm9yZwIkMjNmZWE3YjctYjRhOS00MjNjLTg1NDUtZWEzNTJjODA0NWQ3AAIqWzMsImNhNzJjNmI3LTI4ZTYtNDFlNi1hYzY0LTRjYzg4MWNiNmE0ZiJdAAAGIH1RJzdjuvBusipJUpxYSYXh-MLt9Ls7BfwDIT1F_7wo"
RELEASE_PYPI_TOKEN="pypi-AgEIcHlwaS5vcmcCJDVlY2RiZjQ1LTJhOTUtNDI4Zi04YTkyLWVkNWE0NDRlNTI2MQACG1sxLFsia3JuLWhhcm1vbnktYWRhcHRlciJdXQACLFsyLFsiYjUwNDc5ZjktMDZkZC00MGE4LThkNGEtNWM1NzQwNTFiZmU0Il1dAAAGIJHqwYbiHG_US-MxQLiGbeAMTQT0LiC8wO0MY8e1qclE"

# 解析命令行参数
RELEASE_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            RELEASE_MODE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [-r|--release]"
            echo "  -r, --release    发布到正式 PyPI（默认发布到 Test PyPI）"
            exit 1
            ;;
    esac
done

if [ "$RELEASE_MODE" = true ]; then
    echo "🔨 开始构建 KRN Harmony Adapter (正式版本)..."
else
    echo "🔨 开始构建 KRN Harmony Adapter (测试版本)..."
fi

# 清理之前的构建
echo "🧹 清理之前的构建文件..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# 检查依赖
echo "📦 检查构建依赖..."
pip install --upgrade pip setuptools wheel build twine

# 检查 expect 是否安装（用于自动输入 token）
if ! command -v expect >/dev/null 2>&1; then
    echo "⚠️  expect 未安装，将使用环境变量方式自动输入 token"
    echo "💡 如需更好的体验，可安装 expect："
    echo "   macOS: brew install expect"
    echo "   Ubuntu/Debian: sudo apt-get install expect"
    echo "   CentOS/RHEL: sudo yum install expect"
else
    echo "✅ expect 已安装，将自动输入 token"
fi

# 自动递增版本号
echo "🔢 自动递增版本号..."

if [ "$RELEASE_MODE" = true ]; then
    # 正式版本模式：使用 release-version
    echo "📦 正式版本模式"
    current_version=$(grep '^release-version = ' pyproject.toml | sed 's/release-version = "\(.*\)"/\1/')
    echo "当前正式版本: $current_version"
    
    # 分割版本号并递增最后一位
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    last_index=$((${#VERSION_PARTS[@]} - 1))
    last_part=${VERSION_PARTS[$last_index]}
    new_last_part=$((last_part + 1))
    VERSION_PARTS[$last_index]=$new_last_part
    
    # 重新组合版本号
    new_version=$(IFS='.'; echo "${VERSION_PARTS[*]}")
    echo "新正式版本: $new_version"
    
    # 更新 pyproject.toml 中的版本号
    sed -i.bak "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
    sed -i.bak "s/release-version = \"$current_version\"/release-version = \"$new_version\"/" pyproject.toml
    
    # 更新 src/__init__.py 中的版本号
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$new_version\"/" src/__init__.py
    
    echo "✅ 正式版本号已更新为: $new_version"
else
    # 测试版本模式：使用 test-version (alpha格式: 1.0.0a1)
    echo "🧪 测试版本模式"
    current_version=$(grep '^test-version = ' pyproject.toml | sed 's/test-version = "\(.*\)"/\1/')
    echo "当前测试版本: $current_version"
    
    # 检查是否包含a数字格式（Python PEP 440标准）
    if [[ $current_version =~ ^(.+a)([0-9]+)$ ]]; then
        # 提取基础版本和alpha数字
        base_version="${BASH_REMATCH[1]}"
        alpha_num="${BASH_REMATCH[2]}"
        new_alpha_num=$((alpha_num + 1))
        new_version="${base_version}${new_alpha_num}"
    else
        # 如果不包含a格式，添加a1
        new_version="${current_version}a1"
    fi
    
    echo "新测试版本: $new_version"
    
    # 更新 pyproject.toml 中的版本号
    sed -i.bak "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
    sed -i.bak "s/test-version = \"$current_version\"/test-version = \"$new_version\"/" pyproject.toml
    
    # 更新 src/__init__.py 中的版本号
    sed -i.bak "s/__version__ = \".*\"/__version__ = \"$new_version\"/" src/__init__.py
    
    echo "✅ 测试版本号已更新为: $new_version"
fi

# 构建包
echo "🏗️  构建Python包..."
python -m build

# 检查构建结果
echo "✅ 构建完成！"
echo "📁 构建文件："
ls -la dist/

# 自动输入 token 的函数
auto_upload_with_token() {
    local repository=$1
    local token=$2
    local upload_cmd=$3
    
    echo "🔐 准备自动输入 token..."
    echo "Repository: $repository"
    echo "Token: $token"
    echo "⏱️  3秒后自动执行上传..."
    sleep 1
    echo "⏱️  2秒后开始上传..."
    sleep 1
    echo "⏱️  1秒后开始上传..."
    sleep 1
    echo "✅ 开始上传..."
    
    # 检查是否安装了 expect
    if command -v expect >/dev/null 2>&1; then
        # 使用 expect 自动输入 token
        expect << EOF
spawn $upload_cmd
expect "Enter your API token:"
send "$token\r"
expect eof
EOF
    else
        # 如果没有 expect，使用环境变量方式
        echo "📝 expect 未安装，使用环境变量方式..."
        TWINE_USERNAME="__token__" TWINE_PASSWORD="$token" $upload_cmd
    fi
}

if [ "$RELEASE_MODE" = true ]; then
    echo "📤 发布到正式 PyPI："
    auto_upload_with_token "pypi" "$RELEASE_PYPI_TOKEN" "python3 -m twine upload dist/*"
    
    echo ""
    echo "🚀 正式版安装方法："
    echo "pip install --upgrade --no-cache-dir --index-url https://pypi.org/simple krn-harmony-adapter"
else
    echo "📤 发布到Test PyPI："
    auto_upload_with_token "testpypi" "$TEST_PYPI_TOKEN" "python3 -m twine upload --repository testpypi dist/*"
    
    echo ""
    echo "🚀 测试版安装方法："
    echo "pip install --no-cache-dir --force-reinstall --index-url https://test.pypi.org/simple/ --no-deps krn-harmony-adapter"
fi

echo ""


# 查看版本：pip index versions krn-harmony-adapter
