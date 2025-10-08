package services

import (
	"code-producer/internal/models"
	"fmt"
	"regexp"
	"strings"
)

// CodeProducerService 提供代码生成服务
type CodeProducerService struct {
	knowledgeMapService *KnowledgeMapService
}

// NewCodeProducerService 创建新的CodeProducerService实例
func NewCodeProducerService(knowledgeMapService *KnowledgeMapService) *CodeProducerService {
	return &CodeProducerService{
		knowledgeMapService: knowledgeMapService,
	}
}

// GenerateCode 根据需求生成代码
func (c *CodeProducerService) GenerateCode(req *models.CodeGenerationRequest) (*models.CodeGenerationResponse, error) {
	// 1. 分析需求，提取关键词
	keywords := c.extractKeywords(req.Requirements)

	// 2. 搜索相关的代码示例和文档
	relatedDocs, err := c.knowledgeMapService.SearchRelatedDocuments(keywords, 5)
	if err != nil {
		return nil, fmt.Errorf("failed to search related documents: %w", err)
	}

	// 3. 搜索代码示例
	var codeExamples *models.SearchResponse
	if req.Language != "" {
		codeExamples, err = c.knowledgeMapService.SearchCodeExamples(req.Language, req.Requirements)
		if err != nil {
			return nil, fmt.Errorf("failed to search code examples: %w", err)
		}
	}

	// 4. 搜索模板
	var templates []models.Template
	if req.Language != "" {
		templates, err = c.knowledgeMapService.SearchTemplates(req.Language, req.Framework)
		if err != nil {
			return nil, fmt.Errorf("failed to search templates: %w", err)
		}
	}

	// 5. 基于上下文生成代码
	code := c.generateCodeFromContext(req, relatedDocs, codeExamples, templates)

	// 6. 生成解释和建议
	explanation := c.generateExplanation(req, code)
	suggestions := c.generateSuggestions(req, relatedDocs)

	// 7. 合并参考资料
	references := append(relatedDocs.Results, codeExamples.Results...)

	return &models.CodeGenerationResponse{
		Code:        code,
		Language:    req.Language,
		Explanation: explanation,
		Suggestions: suggestions,
		References:  references,
		Metadata: map[string]string{
			"framework":       req.Framework,
			"style":           req.Style,
			"templates_used":  fmt.Sprintf("%d", len(templates)),
			"references_used": fmt.Sprintf("%d", len(references)),
		},
	}, nil
}

// AnalyzeRequirements 分析需求
func (c *CodeProducerService) AnalyzeRequirements(requirements string) (*models.RequirementsAnalysis, error) {
	// 1. 提取关键词
	keywords := c.extractKeywords(requirements)

	// 2. 搜索相关文档
	relatedDocs, err := c.knowledgeMapService.SearchRelatedDocuments(keywords, 10)
	if err != nil {
		return nil, fmt.Errorf("failed to search related documents: %w", err)
	}

	// 3. 分析技术栈
	technologies := c.extractTechnologies(requirements, relatedDocs)

	// 4. 分析复杂度
	complexity := c.assessComplexity(requirements)

	// 5. 生成建议
	suggestions := c.generateImplementationSuggestions(requirements, technologies)

	return &models.RequirementsAnalysis{
		Summary:      c.generateSummary(requirements),
		KeyFeatures:  c.extractKeyFeatures(requirements),
		Technologies: technologies,
		Complexity:   complexity,
		Suggestions:  suggestions,
		References:   relatedDocs.Results,
	}, nil
}

// GetCodeTemplate 获取代码模板
func (c *CodeProducerService) GetCodeTemplate(language, framework, templateType string) (*models.Template, error) {
	templates, err := c.knowledgeMapService.SearchTemplates(language, framework)
	if err != nil {
		return nil, fmt.Errorf("failed to search templates: %w", err)
	}

	// 根据类型筛选最合适的模板
	for _, template := range templates {
		if strings.Contains(strings.ToLower(template.Name), strings.ToLower(templateType)) ||
			contains(template.Tags, templateType) {
			return &template, nil
		}
	}

	// 如果没有找到特定类型，返回第一个
	if len(templates) > 0 {
		return &templates[0], nil
	}

	return nil, fmt.Errorf("no templates found for %s %s", language, framework)
}

// extractKeywords 从需求中提取关键词
func (c *CodeProducerService) extractKeywords(requirements string) []string {
	// 简单的关键词提取逻辑
	words := strings.Fields(strings.ToLower(requirements))
	var keywords []string

	// 过滤常见词汇，保留技术相关词汇
	stopWords := map[string]bool{
		"the": true, "a": true, "an": true, "and": true, "or": true, "but": true,
		"in": true, "on": true, "at": true, "to": true, "for": true, "of": true,
		"with": true, "by": true, "is": true, "are": true, "was": true, "were": true,
		"be": true, "been": true, "have": true, "has": true, "had": true, "do": true,
		"does": true, "did": true, "will": true, "would": true, "could": true, "should": true,
	}

	for _, word := range words {
		// 清理标点符号
		word = regexp.MustCompile(`[^\w]`).ReplaceAllString(word, "")
		if len(word) > 2 && !stopWords[word] {
			keywords = append(keywords, word)
		}
	}

	return keywords
}

// generateCodeFromContext 基于上下文生成代码
func (c *CodeProducerService) generateCodeFromContext(req *models.CodeGenerationRequest, relatedDocs *models.SearchResponse, codeExamples *models.SearchResponse, templates []models.Template) string {
	var codeBuilder strings.Builder

	// 如果有模板，使用模板作为基础
	if len(templates) > 0 {
		template := templates[0]
		codeBuilder.WriteString("// Generated from template: " + template.Name + "\n")
		codeBuilder.WriteString(template.Content)
		codeBuilder.WriteString("\n\n")
	}

	// 添加代码示例的注释
	if codeExamples != nil && len(codeExamples.Results) > 0 {
		codeBuilder.WriteString("// Based on examples:\n")
		for _, example := range codeExamples.Results {
			codeBuilder.WriteString("// - " + example.Title + "\n")
		}
		codeBuilder.WriteString("\n")
	}

	// 生成基础代码结构
	switch req.Language {
	case "go", "golang":
		codeBuilder.WriteString(c.generateGoCode(req))
	case "javascript", "js":
		codeBuilder.WriteString(c.generateJavaScriptCode(req))
	case "python":
		codeBuilder.WriteString(c.generatePythonCode(req))
	case "java":
		codeBuilder.WriteString(c.generateJavaCode(req))
	default:
		codeBuilder.WriteString(c.generateGenericCode(req))
	}

	return codeBuilder.String()
}

// generateGoCode 生成Go代码
func (c *CodeProducerService) generateGoCode(req *models.CodeGenerationRequest) string {
	var code strings.Builder

	code.WriteString("package main\n\n")
	code.WriteString("import (\n")
	code.WriteString("    \"fmt\"\n")
	code.WriteString(")\n\n")

	code.WriteString("// " + req.Requirements + "\n")
	code.WriteString("func main() {\n")
	code.WriteString("    fmt.Println(\"Generated code based on requirements\")\n")
	code.WriteString("    // TODO: Implement the required functionality\n")
	code.WriteString("}\n")

	return code.String()
}

// generateJavaScriptCode 生成JavaScript代码
func (c *CodeProducerService) generateJavaScriptCode(req *models.CodeGenerationRequest) string {
	var code strings.Builder

	code.WriteString("// " + req.Requirements + "\n")
	code.WriteString("function main() {\n")
	code.WriteString("    console.log('Generated code based on requirements');\n")
	code.WriteString("    // TODO: Implement the required functionality\n")
	code.WriteString("}\n\n")
	code.WriteString("main();\n")

	return code.String()
}

// generatePythonCode 生成Python代码
func (c *CodeProducerService) generatePythonCode(req *models.CodeGenerationRequest) string {
	var code strings.Builder

	code.WriteString("# " + req.Requirements + "\n\n")
	code.WriteString("def main():\n")
	code.WriteString("    print('Generated code based on requirements')\n")
	code.WriteString("    # TODO: Implement the required functionality\n")
	code.WriteString("    pass\n\n")
	code.WriteString("if __name__ == '__main__':\n")
	code.WriteString("    main()\n")

	return code.String()
}

// generateJavaCode 生成Java代码
func (c *CodeProducerService) generateJavaCode(req *models.CodeGenerationRequest) string {
	var code strings.Builder

	code.WriteString("// " + req.Requirements + "\n")
	code.WriteString("public class Main {\n")
	code.WriteString("    public static void main(String[] args) {\n")
	code.WriteString("        System.out.println(\"Generated code based on requirements\");\n")
	code.WriteString("        // TODO: Implement the required functionality\n")
	code.WriteString("    }\n")
	code.WriteString("}\n")

	return code.String()
}

// generateGenericCode 生成通用代码
func (c *CodeProducerService) generateGenericCode(req *models.CodeGenerationRequest) string {
	return fmt.Sprintf("// %s\n// TODO: Implement the required functionality\n", req.Requirements)
}

// generateExplanation 生成代码解释
func (c *CodeProducerService) generateExplanation(req *models.CodeGenerationRequest, code string) string {
	explanation := fmt.Sprintf("Generated %s code based on the requirements: %s\n\n", req.Language, req.Requirements)
	explanation += "The code includes:\n"
	explanation += "- Basic structure for " + req.Language + "\n"
	explanation += "- Comments indicating the requirements\n"
	explanation += "- TODO markers for further implementation\n"

	if req.Framework != "" {
		explanation += "- Framework considerations for " + req.Framework + "\n"
	}

	return explanation
}

// generateSuggestions 生成建议
func (c *CodeProducerService) generateSuggestions(req *models.CodeGenerationRequest, relatedDocs *models.SearchResponse) []string {
	suggestions := []string{
		"Consider adding error handling",
		"Add unit tests for the functionality",
		"Consider performance optimization",
		"Add proper documentation",
	}

	if req.Language == "go" {
		suggestions = append(suggestions, "Follow Go best practices and idioms")
		suggestions = append(suggestions, "Consider using interfaces for better testability")
	}

	if len(relatedDocs.Results) > 0 {
		suggestions = append(suggestions, "Review the related documents for additional insights")
	}

	return suggestions
}

// extractTechnologies 提取技术栈
func (c *CodeProducerService) extractTechnologies(requirements string, relatedDocs *models.SearchResponse) []string {
	technologies := []string{}
	reqLower := strings.ToLower(requirements)

	// 常见技术关键词
	techKeywords := map[string]string{
		"react":      "React",
		"vue":        "Vue.js",
		"angular":    "Angular",
		"node":       "Node.js",
		"express":    "Express.js",
		"mongodb":    "MongoDB",
		"mysql":      "MySQL",
		"postgresql": "PostgreSQL",
		"redis":      "Redis",
		"docker":     "Docker",
		"kubernetes": "Kubernetes",
		"aws":        "AWS",
		"azure":      "Azure",
		"gcp":        "Google Cloud",
	}

	for keyword, tech := range techKeywords {
		if strings.Contains(reqLower, keyword) {
			technologies = append(technologies, tech)
		}
	}

	// 从相关文档中提取技术
	if relatedDocs != nil {
		for _, doc := range relatedDocs.Results {
			for _, tag := range doc.Tags {
				if !contains(technologies, tag) {
					technologies = append(technologies, tag)
				}
			}
		}
	}

	return technologies
}

// assessComplexity 评估复杂度
func (c *CodeProducerService) assessComplexity(requirements string) string {
	reqLower := strings.ToLower(requirements)
	complexityIndicators := map[string]int{
		"simple":       1,
		"basic":        1,
		"complex":      3,
		"advanced":     3,
		"enterprise":   4,
		"scalable":     3,
		"distributed":  4,
		"microservice": 4,
	}

	score := 2 // default medium
	for indicator, value := range complexityIndicators {
		if strings.Contains(reqLower, indicator) {
			score = value
			break
		}
	}

	switch score {
	case 1:
		return "Low"
	case 2:
		return "Medium"
	case 3:
		return "High"
	case 4:
		return "Very High"
	default:
		return "Medium"
	}
}

// generateSummary 生成需求摘要
func (c *CodeProducerService) generateSummary(requirements string) string {
	if len(requirements) <= 100 {
		return requirements
	}
	return requirements[:100] + "..."
}

// extractKeyFeatures 提取关键特性
func (c *CodeProducerService) extractKeyFeatures(requirements string) []string {
	features := []string{}
	reqLower := strings.ToLower(requirements)

	featureKeywords := []string{
		"authentication", "authorization", "user management", "database",
		"api", "rest", "graphql", "real-time", "chat", "notification",
		"payment", "integration", "dashboard", "analytics", "reporting",
	}

	for _, keyword := range featureKeywords {
		if strings.Contains(reqLower, keyword) {
			features = append(features, keyword)
		}
	}

	return features
}

// generateImplementationSuggestions 生成实现建议
func (c *CodeProducerService) generateImplementationSuggestions(requirements string, technologies []string) []string {
	suggestions := []string{
		"Start with a minimal viable product (MVP)",
		"Use version control (Git) from the beginning",
		"Set up continuous integration/deployment (CI/CD)",
		"Write tests alongside development",
		"Document API endpoints and data models",
	}

	reqLower := strings.ToLower(requirements)

	if strings.Contains(reqLower, "web") {
		suggestions = append(suggestions, "Consider responsive design for mobile compatibility")
	}

	if strings.Contains(reqLower, "database") {
		suggestions = append(suggestions, "Design database schema carefully")
		suggestions = append(suggestions, "Consider data migration strategies")
	}

	if contains(technologies, "Docker") {
		suggestions = append(suggestions, "Use Docker for consistent development environment")
	}

	return suggestions
}

// contains 检查切片是否包含某个字符串
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
