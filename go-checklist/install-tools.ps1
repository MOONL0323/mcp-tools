# Go 代码检查工具安装脚本 (Windows PowerShell)

Write-Host "安装 Go 代码检查工具..." -ForegroundColor Green

# 检查 Go 是否已安装
if (-not (Get-Command "go" -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 请先安装 Go 语言环境" -ForegroundColor Red
    exit 1
}

# 安装 goimports
Write-Host "安装 goimports..." -ForegroundColor Yellow
go install golang.org/x/tools/cmd/goimports@latest

# 安装 golangci-lint (Windows)
Write-Host "安装 golangci-lint..." -ForegroundColor Yellow
if (-not (Get-Command "golangci-lint" -ErrorAction SilentlyContinue)) {
    # 下载 golangci-lint for Windows
    $url = "https://github.com/golangci/golangci-lint/releases/download/v1.55.2/golangci-lint-1.55.2-windows-amd64.zip"
    $output = "$env:TEMP\golangci-lint.zip"
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $output
        Expand-Archive -Path $output -DestinationPath "$env:TEMP\golangci-lint" -Force
        
        $gopath = go env GOPATH
        $binPath = "$gopath\bin"
        
        if (-not (Test-Path $binPath)) {
            New-Item -ItemType Directory -Force -Path $binPath
        }
        
        Copy-Item "$env:TEMP\golangci-lint\golangci-lint-1.55.2-windows-amd64\golangci-lint.exe" "$binPath\"
        Write-Host "golangci-lint 安装成功" -ForegroundColor Green
    }
    catch {
        Write-Host "golangci-lint 安装失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 安装 ineffassign
Write-Host "安装 ineffassign..." -ForegroundColor Yellow
go install github.com/gordonklaus/ineffassign@latest

# 安装 misspell
Write-Host "安装 misspell..." -ForegroundColor Yellow
go install github.com/client9/misspell/cmd/misspell@latest

# 安装 staticcheck
Write-Host "安装 staticcheck..." -ForegroundColor Yellow
go install honnef.co/go/tools/cmd/staticcheck@latest

# 安装 gosec（安全检查）
Write-Host "安装 gosec..." -ForegroundColor Yellow
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest

# 验证工具安装
Write-Host "验证工具安装..." -ForegroundColor Green

$tools = @{
    "gofmt" = "gofmt"
    "go vet" = "go"
    "goimports" = "goimports"
    "golangci-lint" = "golangci-lint"
    "ineffassign" = "ineffassign"
    "misspell" = "misspell"
    "staticcheck" = "staticcheck"
    "gosec" = "gosec"
}

foreach ($tool in $tools.GetEnumerator()) {
    $cmd = Get-Command $tool.Value -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "$($tool.Key): $($cmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "$($tool.Key): 未找到" -ForegroundColor Red
    }
}

Write-Host "Go 检查工具安装完成！" -ForegroundColor Green