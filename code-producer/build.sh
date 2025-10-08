#!/bin/bash

# 构建脚本

echo "Building code-producer MCP service..."

# 检查Go版本
if ! command -v go &> /dev/null; then
    echo "Go is not installed. Please install Go 1.21 or later."
    exit 1
fi

GO_VERSION=$(go version | cut -d' ' -f3 | sed 's/go//')
REQUIRED_VERSION="1.21"

if ! printf '%s\n%s\n' "$REQUIRED_VERSION" "$GO_VERSION" | sort -V -C; then
    echo "Go version $GO_VERSION is too old. Please upgrade to Go $REQUIRED_VERSION or later."
    exit 1
fi

# 清理之前的构建
echo "Cleaning previous builds..."
go clean

# 下载依赖
echo "Downloading dependencies..."
go mod tidy

# 运行测试（如果存在）
if [ -f "*_test.go" ]; then
    echo "Running tests..."
    go test ./...
fi

# 构建应用
echo "Building application..."
go build -o bin/code-producer main.go

if [ $? -eq 0 ]; then
    echo "Build successful! Binary available at: bin/code-producer"
    echo "To run the service: ./bin/code-producer"
else
    echo "Build failed!"
    exit 1
fi

# 生成版本信息
echo "Generating version info..."
VERSION=$(date +%Y%m%d-%H%M%S)
echo "Build version: $VERSION"
echo "$VERSION" > VERSION

echo "Build completed successfully!"