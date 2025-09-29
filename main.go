package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"mcp-checklist-checker/internal/checklist"
	"mcp-checklist-checker/internal/checker"
	"mcp-checklist-checker/internal/config"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// MCPChecklistServer MCP 检查清单服务器
type MCPChecklistServer struct {
	config *config.Config
}

// NewMCPChecklistServer 创建新的 MCP 服务器实例
func NewMCPChecklistServer() *MCPChecklistServer {
	// 初始化 Viper 配置
	if err := config.InitViper(); err != nil {
		log.Printf("初始化 Viper 失败: %v", err)
	}
	
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Printf("加载配置失败，使用默认配置: %v", err)
		cfg = &config.Config{
			DefaultChecklist: "go-basic",
			Checklists: map[string]string{
				"go-basic": "checklists/go-basic.json",
			},
		}
	}

	return &MCPChecklistServer{
		config: cfg,
	}
}

func main() {
	serverInstance := NewMCPChecklistServer()

	// 创建 MCP 服务器
	server := mcp.NewServer(
		&mcp.Implementation{Name: "checklist-checker", Version: "1.0.0"}, 
		nil,
	)

	// 注册工具
	mcp.AddTool(server, &mcp.Tool{
		Name:        "upload_checklist",
		Description: "上传自定义检查清单",
	}, serverInstance.uploadChecklistTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "list_checklists",
		Description: "列出所有检查清单",
	}, serverInstance.listChecklistsTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "set_default_checklist",
		Description: "设置默认检查清单",
	}, serverInstance.setDefaultChecklistTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_default_checklist",
		Description: "获取默认检查清单",
	}, serverInstance.getDefaultChecklistTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "check_code",
		Description: "检查代码文件或目录",
	}, serverInstance.checkCodeTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "check_current_file",
		Description: "检查当前打开的文件",
	}, serverInstance.checkCurrentFileTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "check_directory",
		Description: "检查目录中的所有代码文件",
	}, serverInstance.checkDirectoryTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "get_checklist_details",
		Description: "获取检查清单详细信息",
	}, serverInstance.getChecklistDetailsTool)

	// 启动服务器，通过 stdin/stdout 通信
	log.Println("MCP Checklist Checker 服务器启动中...")
	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatal(err)
	}
}

// 输入和输出结构体定义
type UploadChecklistInput struct {
	Name    string `json:"name" jsonschema:"检查清单名称"`
	Content string `json:"content" jsonschema:"检查清单内容（JSON或YAML格式）"`
	Format  string `json:"format,omitempty" jsonschema:"文件格式（json或yaml），默认为json"`
}

type UploadChecklistOutput struct {
	Message    string `json:"message"`
	Name       string `json:"name"`
	Path       string `json:"path"`
	TotalItems int    `json:"total_items"`
	IsDefault  bool   `json:"is_default"`
}

type ListChecklistsOutput struct {
	Checklists       []ChecklistInfo `json:"checklists"`
	Total            int             `json:"total"`
	DefaultChecklist string          `json:"default_checklist"`
}

type ChecklistInfo struct {
	Name        string `json:"name"`
	Path        string `json:"path"`
	Description string `json:"description"`
	Version     string `json:"version"`
	Author      string `json:"author"`
	TotalItems  int    `json:"total_items"`
	IsDefault   bool   `json:"is_default"`
}

type SetDefaultChecklistInput struct {
	Name string `json:"name" jsonschema:"要设置为默认的检查清单名称"`
}

type SetDefaultChecklistOutput struct {
	Message          string `json:"message"`
	DefaultChecklist string `json:"default_checklist"`
}

type GetDefaultChecklistOutput struct {
	DefaultChecklist string `json:"default_checklist"`
}

type CheckCodeInput struct {
	Target    string `json:"target" jsonschema:"要检查的文件或目录路径"`
	Checklist string `json:"checklist,omitempty" jsonschema:"指定使用的检查清单名称（可选）"`
}

type CheckCurrentFileInput struct {
	Checklist string `json:"checklist,omitempty" jsonschema:"指定使用的检查清单名称（可选）"`
}

type CheckDirectoryInput struct {
	Directory string `json:"directory,omitempty" jsonschema:"要检查的目录路径（可选，默认为当前工作目录）"`
	Checklist string `json:"checklist,omitempty" jsonschema:"指定使用的检查清单名称（可选）"`
}

type GetChecklistDetailsInput struct {
	Name string `json:"name" jsonschema:"要获取详细信息的检查清单名称"`
}

// 工具处理函数
func (s *MCPChecklistServer) uploadChecklistTool(ctx context.Context, req *mcp.CallToolRequest, input UploadChecklistInput) (*mcp.CallToolResult, UploadChecklistOutput, error) {
	name := input.Name
	if name == "" {
		return nil, UploadChecklistOutput{}, fmt.Errorf("缺少检查清单名称")
	}

	content := input.Content
	if content == "" {
		return nil, UploadChecklistOutput{}, fmt.Errorf("缺少检查清单内容")
	}

	format := input.Format
	if format == "" {
		format = "json" // 默认格式
	}

	// 确定文件扩展名
	var ext string
	switch format {
	case "json":
		ext = ".json"
	case "yaml", "yml":
		ext = ".yaml"
	default:
		return nil, UploadChecklistOutput{}, fmt.Errorf("不支持的格式: %s", format)
	}

	// 创建文件路径
	fileName := fmt.Sprintf("%s%s", name, ext)
	filePath := filepath.Join("checklists", fileName)

	// 确保目录存在
	if err := os.MkdirAll("checklists", 0755); err != nil {
		return nil, UploadChecklistOutput{}, fmt.Errorf("创建目录失败: %w", err)
	}

	// 保存文件
	if err := os.WriteFile(filePath, []byte(content), 0644); err != nil {
		return nil, UploadChecklistOutput{}, fmt.Errorf("保存文件失败: %w", err)
	}

	// 验证检查清单格式
	cl, err := checklist.LoadChecklist(filePath)
	if err != nil {
		// 删除无效文件
		os.Remove(filePath)
		return nil, UploadChecklistOutput{}, fmt.Errorf("检查清单格式无效: %w", err)
	}

	if err := cl.ValidateChecklist(); err != nil {
		// 删除无效文件
		os.Remove(filePath)
		return nil, UploadChecklistOutput{}, fmt.Errorf("检查清单验证失败: %w", err)
	}

	// 更新配置
	s.config.AddChecklist(name, filePath)
	
	// 如果这是第一个检查清单，设为默认
	if s.config.DefaultChecklist == "" {
		s.config.SetDefaultChecklist(name)
	}
	
	if err := s.config.SaveConfig(); err != nil {
		return nil, UploadChecklistOutput{}, fmt.Errorf("保存配置失败: %w", err)
	}

	output := UploadChecklistOutput{
		Message:    "检查清单上传成功",
		Name:       name,
		Path:       filePath,
		TotalItems: len(cl.Items),
		IsDefault:  s.config.DefaultChecklist == name,
	}

	return nil, output, nil
}

func (s *MCPChecklistServer) listChecklistsTool(ctx context.Context, req *mcp.CallToolRequest, input struct{}) (*mcp.CallToolResult, ListChecklistsOutput, error) {
	checklists := make([]ChecklistInfo, 0)

	for name, path := range s.config.ListChecklists() {
		cl, err := checklist.LoadChecklist(path)
		if err != nil {
			continue // 跳过无法加载的文件
		}

		info := ChecklistInfo{
			Name:        name,
			Path:        path,
			Description: cl.Description,
			Version:     cl.Version,
			Author:      cl.Author,
			TotalItems:  len(cl.Items),
			IsDefault:   s.config.DefaultChecklist == name,
		}
		checklists = append(checklists, info)
	}

	output := ListChecklistsOutput{
		Checklists:       checklists,
		Total:            len(checklists),
		DefaultChecklist: s.config.DefaultChecklist,
	}

	return nil, output, nil
}

func (s *MCPChecklistServer) setDefaultChecklistTool(ctx context.Context, req *mcp.CallToolRequest, input SetDefaultChecklistInput) (*mcp.CallToolResult, SetDefaultChecklistOutput, error) {
	name := input.Name
	if name == "" {
		return nil, SetDefaultChecklistOutput{}, fmt.Errorf("缺少检查清单名称")
	}

	if err := s.config.SetDefaultChecklist(name); err != nil {
		return nil, SetDefaultChecklistOutput{}, err
	}

	if err := s.config.SaveConfig(); err != nil {
		return nil, SetDefaultChecklistOutput{}, fmt.Errorf("保存配置失败: %w", err)
	}

	output := SetDefaultChecklistOutput{
		Message:          "默认检查清单设置成功",
		DefaultChecklist: name,
	}

	return nil, output, nil
}

func (s *MCPChecklistServer) getDefaultChecklistTool(ctx context.Context, req *mcp.CallToolRequest, input struct{}) (*mcp.CallToolResult, GetDefaultChecklistOutput, error) {
	output := GetDefaultChecklistOutput{
		DefaultChecklist: s.config.DefaultChecklist,
	}
	
	return nil, output, nil
}

func (s *MCPChecklistServer) checkCodeTool(ctx context.Context, req *mcp.CallToolRequest, input CheckCodeInput) (*mcp.CallToolResult, interface{}, error) {
	target := input.Target
	if target == "" {
		return nil, nil, fmt.Errorf("缺少检查目标路径")
	}

	checklistName := input.Checklist

	// 获取检查清单路径
	checklistPath, err := s.config.GetChecklistPath(checklistName)
	if err != nil {
		return nil, nil, err
	}

	// 加载检查清单
	cl, err := checklist.LoadChecklist(checklistPath)
	if err != nil {
		return nil, nil, fmt.Errorf("加载检查清单失败: %w", err)
	}

	// 创建检查器
	codeChecker := checker.NewCodeChecker(cl)

	// 检查目标是文件还是目录
	fileInfo, err := os.Stat(target)
	if err != nil {
		return nil, nil, fmt.Errorf("获取目标信息失败: %w", err)
	}

	var report *checklist.CheckReport
	if fileInfo.IsDir() {
		report, err = codeChecker.CheckDirectory(target)
	} else {
		report, err = codeChecker.CheckFile(target)
	}

	if err != nil {
		return nil, nil, fmt.Errorf("执行代码检查失败: %w", err)
	}

	return nil, report, nil
}

func (s *MCPChecklistServer) checkCurrentFileTool(ctx context.Context, req *mcp.CallToolRequest, input CheckCurrentFileInput) (*mcp.CallToolResult, interface{}, error) {
	// 尝试从环境变量或工作目录获取当前文件
	currentFile := os.Getenv("CURRENT_FILE")
	if currentFile == "" {
		// 如果没有环境变量，尝试获取工作目录中的文件
		wd, err := os.Getwd()
		if err != nil {
			return nil, nil, fmt.Errorf("无法获取当前工作目录: %w", err)
		}
		
		// 查找第一个代码文件作为当前文件
		files, err := filepath.Glob(filepath.Join(wd, "*"))
		if err != nil {
			return nil, nil, fmt.Errorf("查找文件失败: %w", err)
		}
		
		for _, file := range files {
			if info, err := os.Stat(file); err == nil && !info.IsDir() {
				ext := filepath.Ext(file)
				if isCodeFile(ext) {
					currentFile = file
					break
				}
			}
		}
		
		if currentFile == "" {
			return nil, nil, fmt.Errorf("找不到当前文件，请指定目标文件")
		}
	}

	// 使用 checkCodeTool 方法检查当前文件
	checkInput := CheckCodeInput{
		Target:    currentFile,
		Checklist: input.Checklist,
	}
	return s.checkCodeTool(ctx, req, checkInput)
}

func (s *MCPChecklistServer) checkDirectoryTool(ctx context.Context, req *mcp.CallToolRequest, input CheckDirectoryInput) (*mcp.CallToolResult, interface{}, error) {
	dirPath := input.Directory
	if dirPath == "" {
		// 如果没有指定目录，使用当前工作目录
		wd, err := os.Getwd()
		if err != nil {
			return nil, nil, fmt.Errorf("获取当前工作目录失败: %w", err)
		}
		dirPath = wd
	}

	// 使用 checkCodeTool 方法检查目录
	checkInput := CheckCodeInput{
		Target:    dirPath,
		Checklist: input.Checklist,
	}
	return s.checkCodeTool(ctx, req, checkInput)
}

func (s *MCPChecklistServer) getChecklistDetailsTool(ctx context.Context, req *mcp.CallToolRequest, input GetChecklistDetailsInput) (*mcp.CallToolResult, interface{}, error) {
	name := input.Name
	if name == "" {
		return nil, nil, fmt.Errorf("缺少检查清单名称")
	}

	checklistPath, err := s.config.GetChecklistPath(name)
	if err != nil {
		return nil, nil, err
	}

	cl, err := checklist.LoadChecklist(checklistPath)
	if err != nil {
		return nil, nil, fmt.Errorf("加载检查清单失败: %w", err)
	}

	result := map[string]interface{}{
		"name":        cl.Name,
		"version":     cl.Version,
		"description": cl.Description,
		"author":      cl.Author,
		"items":       cl.Items,
		"total_items": len(cl.Items),
	}

	return nil, result, nil
}

// isCodeFile 检查是否为代码文件
func isCodeFile(ext string) bool {
	goExts := []string{
		".go",  // Go 源文件
		".mod", // go.mod 文件
		".sum", // go.sum 文件
	}
	
	for _, goExt := range goExts {
		if ext == goExt {
			return true
		}
	}
	return false
}