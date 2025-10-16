#!/bin/bash

# 一键更新 krn-harmony-adapter 到 PyPI 上的最新正式版本
# 作者: AI Assistant

set -e

echo "🚀 正在从 PyPI 更新 krn-harmony-adapter 到最新正式版本..."
echo "--------------------------------------------------------"

# 检查pip是否安装
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到 pip 或 pip3 命令。请确保 Python 和 pip 已安装。"
    exit 1
fi

# 决定使用 pip 还是 pip3
PIP_CMD="pip"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
fi

# 获取当前安装的版本
CURRENT_VERSION=$($PIP_CMD show krn-harmony-adapter 2>/dev/null | grep Version | awk '{print $2}')
if [ -z "$CURRENT_VERSION" ]; then
    CURRENT_VERSION="未安装"
fi
echo "ℹ️  当前安装版本: $CURRENT_VERSION"

# 获取PyPI上的最新版本
echo "🔎 正在查询最新版本..."
LATEST_VERSION=$($PIP_CMD --index-url https://pypi.org/simple index versions krn-harmony-adapter 2>/dev/null | grep "LATEST:" | awk '{print $2}')

if [ -z "$LATEST_VERSION" ]; then
    echo "⚠️  无法自动查询到最新版本（可能是pip版本较旧），将继续尝试更新。"
else
    echo "✅ 最新可用版本: $LATEST_VERSION"
fi

# 如果版本相同，则无需更新
if [ "$CURRENT_VERSION" == "$LATEST_VERSION" ] && [ "$CURRENT_VERSION" != "未安装" ]; then
    echo "🎉 当前已是最新版本，无需更新。"
    echo "--------------------------------------------------------"
    exit 0
fi

echo ""
echo "▶️  执行命令: $PIP_CMD install --upgrade --no-cache-dir --index-url https://pypi.org/simple krn-harmony-adapter"

$PIP_CMD install --upgrade --no-cache-dir --index-url https://pypi.org/simple krn-harmony-adapter

echo ""
echo "--------------------------------------------------------"
NEW_VERSION=$($PIP_CMD show krn-harmony-adapter 2>/dev/null | grep Version | awk '{print $2}')
echo "✅ 更新完成！当前版本为: $NEW_VERSION"
echo "您现在可以使用 'kha' 命令了。"