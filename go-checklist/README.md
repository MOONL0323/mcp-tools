# MCP Checklist Checker

基于 **官方 MCP Go SDK** 构建的 Go 代码质量检查工具，通过 Model Context Protocol 提供代码检查服务。

## 🎯 项目特性

- ✅ **官方 MCP SDK** - 使用 `github.com/modelcontextprotocol/go-sdk` 
- ✅ **Go 工具集成** - 支持 gofmt、go vet、goimports、golangci-lint
- ✅ **Viper 配置管理** - 使用 `github.com/spf13/viper` 提供强大的配置能力
- ✅ **多格式支持** - 支持 JSON、YAML、TOML 等多种配置格式
- ✅ **环境变量集成** - 无缝支持环境变量和配置文件的混合使用
- ✅ **实时配置重载** - 支持配置文件监听和热重载
- ✅ **模块化架构** - 清晰的内部包结构和职责分离
- ✅ **Convey 测试** - 完整的 BDD 风格单元测试覆盖

## 🚀 快速开始

### 1. 安装 Go 工具依赖

```powershell
# Windows PowerShell
.\install-tools.ps1

# Linux/Mac Bash
chmod +x install-tools.sh && ./install-tools.sh
```

### 2. 构建 MCP 服务器

```bash
go build -o mcp-checker.exe main.go
```

### 3. 启动 MCP 服务器

```bash
.\mcp-checker.exe
```

服务器将通过 stdin/stdout 使用 MCP 协议进行通信。

## 🔧 MCP 工作流程

### MCP 协议流程

```
客户端 (Claude, VS Code等)  ←→  MCP 服务器 (mcp-checker.exe)
     │                              │
     │ 1. 发现可用工具                 │
     │ ←─────────────────────────────  │
     │                              │
     │ 2. 调用具体工具                 │
     │ ─────────────────────────────→ │
     │                              │
     │ 3. 返回检查结果                 │
     │ ←─────────────────────────────  │
```

### 可用的 MCP 工具

| 工具名称 | 功能描述 | 输入参数 | 输出结果 |
|---------|---------|---------|---------|
| `upload_checklist` | 上传自定义检查清单 | `name`, `content` | 上传状态 |
| `list_checklists` | 列出所有可用检查清单 | 无 | 检查清单列表 |
| `check_file` | 检查单个 Go 文件 | `filepath`, `checklist` | 检查报告 |
| `check_directory` | 检查整个目录 | `directory`, `checklist` | 目录检查报告 |
| `get_report` | 获取详细的检查报告 | `target` | 格式化报告 |
| `set_default_checklist` | 设置默认检查清单 | `checklist_name` | 设置状态 |

### 典型使用场景

1. **日常代码检查**
   ```
   客户端: "检查这个Go文件的代码质量"
   MCP服务器: 调用 check_file → 运行 gofmt, go vet, golangci-lint → 返回问题列表
   ```

2. **项目质量检查**
   ```
   客户端: "检查整个项目的代码规范"
   MCP服务器: 调用 check_directory → 递归检查所有.go文件 → 生成综合报告
   ```

3. **自定义规则**
   ```
   客户端: "上传团队代码规范检查清单"
   MCP服务器: 调用 upload_checklist → 保存自定义规则 → 后续检查使用新规则
   ```

## 📁 项目结构

```
d:\mcp_project/
├── mcp-checker.exe           # 可执行的 MCP 服务器 (8.5MB)
├── main.go                   # MCP 服务器入口点
├── main_test.go              # Convey 框架单元测试
├── go.mod/go.sum            # Go 模块依赖管理
│
├── configs/
│   └── default.json         # 默认配置 (检查清单映射)
│
├── checklists/
│   └── go-basic.json        # Go 基础检查清单 (12项检查规则)
│
├── internal/                # 内部模块 (不对外暴露)
│   ├── config/
│   │   └── config.go        # 配置文件加载和管理
│   ├── checklist/
│   │   └── checklist.go     # 检查清单解析和验证
│   └── checker/
│       └── checker.go       # 代码检查引擎和报告生成
│
└── install-tools.ps1/.sh    # 依赖工具自动安装脚本
```

## ⚙️ 配置系统（基于 Viper）

### 配置优先级（从高到低）

1. **显式设置** - 代码中直接调用 `viper.Set()`
2. **命令行参数** - 通过 flag 传入的参数  
3. **环境变量** - 以 `MCP_` 为前缀的环境变量
4. **配置文件** - `configs/default.json`
5. **默认值** - 程序内置的默认配置

### 环境变量支持

```bash
# 设置默认检查清单
export MCP_DEFAULT_CHECKLIST=my-custom-rules

# 启用调试模式
export MCP_DEBUG=true

# 设置最大并发检查数
export MCP_MAX_CONCURRENT_CHECKS=8
```

### 默认配置 (`configs/default.json`)

```json
{
  "default_checklist": "go-basic",
  "checklists": {
    "go-basic": "checklists/go-basic.json"
  },
  "max_concurrent_checks": 4,
  "timeout_seconds": 30,
  "enable_cache": true
}
```

### 多格式支持

Viper 支持多种配置文件格式：
- **JSON** (默认) - `configs/default.json`
- **YAML** - `configs/default.yaml`
- **TOML** - `configs/default.toml`
- **HCL** - `configs/default.hcl`
- **INI** - `configs/default.ini`

### 实时配置重载

配置文件修改后会自动重新加载，无需重启服务：

```go
// 启用配置文件监听
viper.WatchConfig()
viper.OnConfigChange(func(e fsnotify.Event) {
    fmt.Println("配置文件已更新:", e.Name)
})
```

### 检查清单格式 (`checklists/go-basic.json`)

```json
{
  "name": "Go 基础检查清单",
  "description": "Go 语言代码质量基础检查",
  "version": "1.0.0",
  "language": "go",
  "items": [
    {
      "id": "gofmt-check",
      "name": "代码格式检查",
      "command": "gofmt -d {file}",
      "pattern": ".*",
      "file_types": [".go"],
      "severity": "error"
    }
    // ... 更多检查项
  ]
}
```

## 🧪 测试与验证

### 运行单元测试

```bash
go test .  # 运行所有 Convey 测试
go test -v  # 详细输出
```

### 测试覆盖

- ✅ 配置管理模块测试
- ✅ 检查清单解析测试  
- ✅ 代码检查引擎测试
- ✅ MCP 工具集成测试
- ✅ 边界条件和错误处理测试

## 🔌 MCP 客户端集成

### Claude Desktop 集成

在 Claude Desktop 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "checklist-checker": {
      "command": "d:\\mcp_project\\mcp-checker.exe",
      "args": []
    }
  }
}
```

### VS Code MCP 扩展集成

通过支持 MCP 协议的 VS Code 扩展，可以直接在编辑器中调用检查工具。

## 📝 检查工具说明

| 工具 | 作用 | 检查内容 |
|-----|------|---------|
| **gofmt** | 代码格式化检查 | 缩进、括号、空格等格式规范 |
| **go vet** | 静态分析检查 | 潜在错误、可疑代码结构 |
| **goimports** | 导入包检查 | import 语句格式和顺序 |
| **golangci-lint** | 综合代码检查 | 代码质量、性能、安全等多维度检查 |

## 🎯 使用示例

### 通过 MCP 客户端使用

1. **检查单个文件**
   - 工具: `check_file`
   - 输入: `{"filepath": "main.go", "checklist": "go-basic"}`
   - 输出: 检查报告包含发现的问题和建议修复方案

2. **检查整个项目**
   - 工具: `check_directory` 
   - 输入: `{"directory": "./", "checklist": "go-basic"}`
   - 输出: 项目级别的代码质量报告

3. **管理检查清单**
   - 工具: `list_checklists` → 查看可用清单
   - 工具: `upload_checklist` → 上传自定义规则
   - 工具: `set_default_checklist` → 设置默认规则

## 🔄 MCP 详细工作流

### 1. 服务器启动流程

```
1. 加载配置文件 (configs/default.json)
2. 初始化检查清单 (checklists/*.json)
3. 注册 MCP 工具到服务器
4. 启动 stdin/stdout 传输层
5. 等待客户端连接和工具调用
```

### 2. 工具调用流程

```
客户端请求 → MCP协议解析 → 工具路由 → 参数验证 → 执行检查 → 格式化结果 → 返回响应
```

### 3. 代码检查执行流程

```
1. 接收目标文件/目录
2. 加载指定检查清单
3. 过滤适用的检查项
4. 并行执行多个检查工具
5. 收集和聚合检查结果
6. 生成格式化的检查报告
7. 返回 JSON 格式的结果
```

### 4. 配置管理流程

```
默认配置加载 → 检查清单映射 → 动态上传新清单 → 更新配置文件 → 重新加载规则
```

## 🚀 配置管理最佳实践

### 1. 生产环境配置

```bash
# 使用环境变量覆盖配置
export MCP_DEFAULT_CHECKLIST=production-rules
export MCP_MAX_CONCURRENT_CHECKS=16
export MCP_TIMEOUT_SECONDS=60
export MCP_ENABLE_CACHE=true

# 启动服务
./mcp-checker.exe
```

### 2. 开发环境配置

```yaml
# configs/development.yaml
default_checklist: dev-rules
max_concurrent_checks: 2
timeout_seconds: 10
enable_cache: false
debug: true
```

### 3. 配置验证

```go
// 自动验证配置有效性
func validateConfig() error {
    if viper.GetInt("max_concurrent_checks") <= 0 {
        return errors.New("max_concurrent_checks 必须大于 0")
    }
    return nil
}
```

## 📊 性能特点

- **并行检查**: 多个检查工具同时执行，提高检查效率
- **增量检查**: 支持只检查修改过的文件
- **缓存机制**: 避免重复检查相同内容
- **资源控制**: 限制同时运行的检查进程数量

## 🚀 未来扩展

- [ ] 支持更多编程语言
- [ ] Web UI 界面
- [ ] 检查结果持久化
- [ ] 团队协作和规则共享
- [ ] CI/CD 流水线集成