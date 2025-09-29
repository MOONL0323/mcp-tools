# MCP Checklist Checker 项目说明

这是一个基于 Model Context Protocol (MCP) 的代码规范检查工具项目。

## 项目概述

### 功能特性
- 集成官方代码检查工具（如 golangci-lint、flake8 等）
- 支持自定义团队 checklist 文件上传和管理
- 提供详细的检查报告和修复建议
- 支持 AI 驱动的自动化代码修复
- 多语言支持（Go、Python、JavaScript 等）

### 架构设计
- **MCP 服务器**: 基于 Go 语言和官方 MCP Go SDK
- **存储层**: SQLite 数据库存储 checklist 和检查历史
- **检查引擎**: 集成多种官方检查工具
- **AI 集成**: 通过 MCP 协议调用大模型进行修复

### 开发规范
- 使用 Go modules 进行依赖管理
- 遵循 MCP 协议规范
- 实现完整的错误处理和日志记录
- 提供全面的单元测试覆盖