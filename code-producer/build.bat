@echo off
REM Windows构建脚本

echo Building code-producer MCP service...

REM 检查Go是否安装
where go >nul 2>nul
if %errorlevel% neq 0 (
    echo Go is not installed. Please install Go 1.21 or later.
    exit /b 1
)

REM 清理之前的构建
echo Cleaning previous builds...
go clean

REM 下载依赖
echo Downloading dependencies...
go mod tidy

REM 构建应用
echo Building application...
if not exist bin mkdir bin
go build -o bin\code-producer.exe main.go

if %errorlevel% equ 0 (
    echo Build successful! Binary available at: bin\code-producer.exe
    echo To run the service: bin\code-producer.exe
) else (
    echo Build failed!
    exit /b 1
)

REM 生成版本信息
echo Generating version info...
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set mydate=%%c%%a%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set VERSION=%mydate%-%mytime%
echo Build version: %VERSION%
echo %VERSION% > VERSION

echo Build completed successfully!
pause