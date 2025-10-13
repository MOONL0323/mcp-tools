#!/bin/bash

echo "================================="
echo "AI Context System Backend 启动"
echo "================================="

echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: Python3 未安装或不在PATH中"
    exit 1
fi

echo ""
echo "安装依赖包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo ""
echo "启动后端服务..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""

python3 -m app.main