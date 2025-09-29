#!/bin/bash

# Go 代码检查工具安装脚本

echo "安装 Go 代码检查工具..."

# 安装 goimports
echo "安装 goimports..."
go install golang.org/x/tools/cmd/goimports@latest

# 安装 golangci-lint
echo "安装 golangci-lint..."
curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin v1.55.2

# 安装 ineffassign
echo "安装 ineffassign..."
go install github.com/gordonklaus/ineffassign@latest

# 安装 misspell
echo "安装 misspell..."
go install github.com/client9/misspell/cmd/misspell@latest

# 安装 staticcheck
echo "安装 staticcheck..."
go install honnef.co/go/tools/cmd/staticcheck@latest

# 安装 gosec（安全检查）
echo "安装 gosec..."
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest

# 验证工具安装
echo "验证工具安装..."
echo "gofmt: $(which gofmt)"
echo "go vet: go vet (built-in)"
echo "goimports: $(which goimports)"
echo "golangci-lint: $(which golangci-lint)"
echo "ineffassign: $(which ineffassign)"
echo "misspell: $(which misspell)"
echo "staticcheck: $(which staticcheck)"
echo "gosec: $(which gosec)"

echo "所有 Go 检查工具安装完成！"