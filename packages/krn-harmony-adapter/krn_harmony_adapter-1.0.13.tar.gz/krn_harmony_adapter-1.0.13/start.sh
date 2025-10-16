#!/bin/bash

# 鸿蒙适配自动化脚本启动器
# 作者: AI Assistant
# 功能: 启动Python版本的鸿蒙适配工具

echo "🚀 使用鸿蒙适配器"
PYTHON_SCRIPT="src/Main.py"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3"
    exit 1
fi

# 检查Python脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ 错误: 未找到Python脚本 $PYTHON_SCRIPT"
    exit 1
fi

# 给Python脚本添加执行权限
chmod +x "$PYTHON_SCRIPT"

echo "📍 工作目录: $(pwd)"
echo "📄 脚本位置: $PYTHON_SCRIPT"
echo ""

# 传递所有参数给Python脚本
python3 -B "$PYTHON_SCRIPT" "$@"