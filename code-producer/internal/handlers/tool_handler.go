package handlers

import (
	"code-producer/internal/models"
	"code-producer/internal/services"
	"code-producer/pkg/mcp"
	"encoding/json"
	"fmt"
)

// ToolHandler 处理MCP工具调用
type ToolHandler struct {
	codeProducerService *services.CodeProducerService
	knowledgeMapService *services.KnowledgeMapService
}

// NewToolHandler 创建新的ToolHandler实例
func NewToolHandler(codeProducerService *services.CodeProducerService, knowledgeMapService *services.KnowledgeMapService) *ToolHandler {
	return &ToolHandler{
		codeProducerService: codeProducerService,
		knowledgeMapService: knowledgeMapService,
	}
}

// GenerateCode 处理代码生成工具调用
func (h *ToolHandler) GenerateCode(params interface{}) (*mcp.ToolResult, error) {
	// 解析参数
	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Invalid parameters"}},
			IsError: true,
		}, nil
	}

	// 构建代码生成请求
	req := &models.CodeGenerationRequest{}

	if requirements, ok := paramsMap["requirements"].(string); ok {
		req.Requirements = requirements
	} else {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Missing required parameter: requirements"}},
			IsError: true,
		}, nil
	}

	if language, ok := paramsMap["language"].(string); ok {
		req.Language = language
	} else {
		req.Language = "go" // 默认语言
	}

	if framework, ok := paramsMap["framework"].(string); ok {
		req.Framework = framework
	}

	if style, ok := paramsMap["style"].(string); ok {
		req.Style = style
	}

	if context, ok := paramsMap["context"].(map[string]interface{}); ok {
		req.Context = make(map[string]string)
		for k, v := range context {
			if strVal, ok := v.(string); ok {
				req.Context[k] = strVal
			}
		}
	}

	if templates, ok := paramsMap["templates"].([]interface{}); ok {
		req.Templates = make([]string, len(templates))
		for i, t := range templates {
			if strVal, ok := t.(string); ok {
				req.Templates[i] = strVal
			}
		}
	}

	// 调用代码生成服务
	response, err := h.codeProducerService.GenerateCode(req)
	if err != nil {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: fmt.Sprintf("Failed to generate code: %v", err)}},
			IsError: true,
		}, nil
	}

	// 格式化响应
	responseText := fmt.Sprintf("## Generated %s Code\n\n", response.Language)
	responseText += "```" + response.Language + "\n"
	responseText += response.Code + "\n"
	responseText += "```\n\n"
	responseText += "## Explanation\n"
	responseText += response.Explanation + "\n\n"

	if len(response.Suggestions) > 0 {
		responseText += "## Suggestions\n"
		for _, suggestion := range response.Suggestions {
			responseText += "- " + suggestion + "\n"
		}
		responseText += "\n"
	}

	if len(response.References) > 0 {
		responseText += "## References\n"
		for _, ref := range response.References {
			responseText += fmt.Sprintf("- %s (Relevance: %.2f)\n", ref.Title, ref.Relevance)
		}
	}

	return &mcp.ToolResult{
		Content: []mcp.Content{{Type: "text", Text: responseText}},
		IsError: false,
	}, nil
}

// SearchKnowledge 处理知识搜索工具调用
func (h *ToolHandler) SearchKnowledge(params interface{}) (*mcp.ToolResult, error) {
	// 解析参数
	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Invalid parameters"}},
			IsError: true,
		}, nil
	}

	// 构建搜索请求
	req := &models.SearchRequest{}

	if query, ok := paramsMap["query"].(string); ok {
		req.Query = query
	} else {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Missing required parameter: query"}},
			IsError: true,
		}, nil
	}

	if language, ok := paramsMap["language"].(string); ok {
		req.Language = language
	}

	if docType, ok := paramsMap["type"].(string); ok {
		req.Type = docType
	}

	if limit, ok := paramsMap["limit"].(float64); ok {
		req.Limit = int(limit)
	} else {
		req.Limit = 10
	}

	if filters, ok := paramsMap["filters"].(map[string]interface{}); ok {
		req.Filters = make(map[string]string)
		for k, v := range filters {
			if strVal, ok := v.(string); ok {
				req.Filters[k] = strVal
			}
		}
	}

	// 调用搜索服务
	response, err := h.knowledgeMapService.SearchDocuments(req)
	if err != nil {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: fmt.Sprintf("Failed to search knowledge: %v", err)}},
			IsError: true,
		}, nil
	}

	// 格式化响应
	responseText := fmt.Sprintf("## Search Results for: %s\n\n", req.Query)
	responseText += fmt.Sprintf("Found %d results:\n\n", response.Total)

	for i, result := range response.Results {
		responseText += fmt.Sprintf("### %d. %s\n", i+1, result.Title)
		responseText += fmt.Sprintf("**Type:** %s | **Relevance:** %.2f\n\n", result.Type, result.Relevance)

		// 截取内容预览
		content := result.Content
		if len(content) > 200 {
			content = content[:200] + "..."
		}
		responseText += content + "\n\n"

		if len(result.Tags) > 0 {
			responseText += "**Tags:** " + fmt.Sprintf("%v", result.Tags) + "\n\n"
		}

		responseText += "---\n\n"
	}

	return &mcp.ToolResult{
		Content: []mcp.Content{{Type: "text", Text: responseText}},
		IsError: false,
	}, nil
}

// GetCodeTemplate 处理获取代码模板工具调用
func (h *ToolHandler) GetCodeTemplate(params interface{}) (*mcp.ToolResult, error) {
	// 解析参数
	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Invalid parameters"}},
			IsError: true,
		}, nil
	}

	language, ok := paramsMap["language"].(string)
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Missing required parameter: language"}},
			IsError: true,
		}, nil
	}

	framework := ""
	if fw, ok := paramsMap["framework"].(string); ok {
		framework = fw
	}

	templateType := ""
	if tt, ok := paramsMap["template_type"].(string); ok {
		templateType = tt
	}

	// 调用模板服务
	template, err := h.codeProducerService.GetCodeTemplate(language, framework, templateType)
	if err != nil {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: fmt.Sprintf("Failed to get template: %v", err)}},
			IsError: true,
		}, nil
	}

	// 格式化响应
	responseText := fmt.Sprintf("## Template: %s\n\n", template.Name)
	responseText += fmt.Sprintf("**Description:** %s\n\n", template.Description)
	responseText += fmt.Sprintf("**Language:** %s\n", template.Language)

	if template.Framework != "" {
		responseText += fmt.Sprintf("**Framework:** %s\n", template.Framework)
	}

	responseText += "\n### Template Content\n\n"
	responseText += "```" + template.Language + "\n"
	responseText += template.Content + "\n"
	responseText += "```\n\n"

	if len(template.Variables) > 0 {
		responseText += "### Template Variables\n\n"
		for _, variable := range template.Variables {
			responseText += fmt.Sprintf("- **%s** (%s): %s", variable.Name, variable.Type, variable.Description)
			if variable.Default != "" {
				responseText += fmt.Sprintf(" (default: %s)", variable.Default)
			}
			if variable.Required {
				responseText += " [Required]"
			}
			responseText += "\n"
		}
		responseText += "\n"
	}

	if len(template.Tags) > 0 {
		responseText += fmt.Sprintf("**Tags:** %v\n", template.Tags)
	}

	return &mcp.ToolResult{
		Content: []mcp.Content{{Type: "text", Text: responseText}},
		IsError: false,
	}, nil
}

// AnalyzeRequirements 处理需求分析工具调用
func (h *ToolHandler) AnalyzeRequirements(params interface{}) (*mcp.ToolResult, error) {
	// 解析参数
	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Invalid parameters"}},
			IsError: true,
		}, nil
	}

	requirements, ok := paramsMap["requirements"].(string)
	if !ok {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: "Missing required parameter: requirements"}},
			IsError: true,
		}, nil
	}

	// 调用需求分析服务
	analysis, err := h.codeProducerService.AnalyzeRequirements(requirements)
	if err != nil {
		return &mcp.ToolResult{
			Content: []mcp.Content{{Type: "text", Text: fmt.Sprintf("Failed to analyze requirements: %v", err)}},
			IsError: true,
		}, nil
	}

	// 格式化响应
	responseText := "## Requirements Analysis\n\n"
	responseText += fmt.Sprintf("**Summary:** %s\n\n", analysis.Summary)
	responseText += fmt.Sprintf("**Complexity:** %s\n\n", analysis.Complexity)

	if len(analysis.KeyFeatures) > 0 {
		responseText += "### Key Features\n"
		for _, feature := range analysis.KeyFeatures {
			responseText += "- " + feature + "\n"
		}
		responseText += "\n"
	}

	if len(analysis.Technologies) > 0 {
		responseText += "### Recommended Technologies\n"
		for _, tech := range analysis.Technologies {
			responseText += "- " + tech + "\n"
		}
		responseText += "\n"
	}

	if len(analysis.Suggestions) > 0 {
		responseText += "### Implementation Suggestions\n"
		for _, suggestion := range analysis.Suggestions {
			responseText += "- " + suggestion + "\n"
		}
		responseText += "\n"
	}

	if len(analysis.References) > 0 {
		responseText += "### Related References\n"
		for _, ref := range analysis.References {
			responseText += fmt.Sprintf("- %s (Relevance: %.2f)\n", ref.Title, ref.Relevance)
		}
	}

	return &mcp.ToolResult{
		Content: []mcp.Content{{Type: "text", Text: responseText}},
		IsError: false,
	}, nil
}

// convertToJSON 将结果转换为JSON格式（可选功能）
func (h *ToolHandler) convertToJSON(data interface{}) (string, error) {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "", err
	}
	return string(jsonData), nil
}
