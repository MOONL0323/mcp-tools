package checker

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"mcp-checklist-checker/internal/checklist"
)

// CodeChecker 代码检查器
type CodeChecker struct {
	checklist *checklist.Checklist
}

// NewCodeChecker 创建新的代码检查器
func NewCodeChecker(cl *checklist.Checklist) *CodeChecker {
	return &CodeChecker{
		checklist: cl,
	}
}

// CheckFile 检查单个文件
func (cc *CodeChecker) CheckFile(filePath string) (*checklist.CheckReport, error) {
	// 获取文件信息
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}

	if fileInfo.IsDir() {
		return nil, fmt.Errorf("路径 '%s' 是目录，请使用 CheckDirectory 方法", filePath)
	}

	// 获取文件扩展名和语言
	ext := filepath.Ext(filePath)
	language := getLanguageByExtension(ext)

	// 筛选适用的检查项
	applicableItems := cc.getApplicableItems(ext, language)

	report := &checklist.CheckReport{
		ChecklistName: cc.checklist.Name,
		Target:        filePath,
		TotalItems:    len(applicableItems),
		Results:       []checklist.CheckResult{},
		Summary:       checklist.Summary{},
	}

	// 执行检查
	for _, item := range applicableItems {
		results, err := cc.checkItem(item, filePath)
		if err != nil {
			// 记录错误但继续检查其他项
			fmt.Printf("检查项 '%s' 执行失败: %v\n", item.ID, err)
			continue
		}
		report.Results = append(report.Results, results...)
	}

	// 计算摘要
	cc.calculateSummary(report)

	return report, nil
}

// CheckDirectory 检查整个目录
func (cc *CodeChecker) CheckDirectory(dirPath string) (*checklist.CheckReport, error) {
	report := &checklist.CheckReport{
		ChecklistName: cc.checklist.Name,
		Target:        dirPath,
		TotalItems:    len(cc.checklist.Items),
		Results:       []checklist.CheckResult{},
		Summary:       checklist.Summary{},
	}

	// 遍历目录中的所有文件
	err := filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// 跳过目录和隐藏文件
		if info.IsDir() || strings.HasPrefix(info.Name(), ".") {
			return nil
		}

		// 跳过不相关的文件类型
		if !cc.isRelevantFile(path) {
			return nil
		}

		// 检查文件
		fileReport, err := cc.CheckFile(path)
		if err != nil {
			fmt.Printf("检查文件 '%s' 失败: %v\n", path, err)
			return nil // 继续处理其他文件
		}

		// 合并结果
		report.Results = append(report.Results, fileReport.Results...)

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("遍历目录失败: %w", err)
	}

	// 计算摘要
	cc.calculateSummary(report)

	return report, nil
}

// getApplicableItems 获取适用于特定文件的检查项
func (cc *CodeChecker) getApplicableItems(fileExt, language string) []checklist.ChecklistItem {
	var items []checklist.ChecklistItem

	for _, item := range cc.checklist.Items {
		// 检查文件类型
		if len(item.FileTypes) > 0 && !contains(item.FileTypes, fileExt) {
			continue
		}

		// 检查编程语言
		if len(item.Languages) > 0 && !contains(item.Languages, language) {
			continue
		}

		items = append(items, item)
	}

	return items
}

// checkItem 执行单个检查项
func (cc *CodeChecker) checkItem(item checklist.ChecklistItem, filePath string) ([]checklist.CheckResult, error) {
	var results []checklist.CheckResult

	// 如果有外部命令，执行命令检查
	if item.Command != "" {
		cmdResults, err := cc.executeCommand(item, filePath)
		if err != nil {
			return nil, err
		}
		results = append(results, cmdResults...)
	}

	// 如果有正则表达式模式，执行模式匹配
	if item.Pattern != "" {
		patternResults, err := cc.executePattern(item, filePath)
		if err != nil {
			return nil, err
		}
		results = append(results, patternResults...)
	}

	return results, nil
}

// executeCommand 执行外部命令检查
func (cc *CodeChecker) executeCommand(item checklist.ChecklistItem, filePath string) ([]checklist.CheckResult, error) {
	// 替换命令中的占位符
	command := strings.ReplaceAll(item.Command, "{file}", filePath)
	
	// 分割命令和参数
	parts := strings.Fields(command)
	if len(parts) == 0 {
		return nil, fmt.Errorf("命令为空")
	}

	cmd := exec.Command(parts[0], parts[1:]...)
	output, err := cmd.CombinedOutput()
	
	var results []checklist.CheckResult
	
	// 即使命令失败也尝试解析输出
	if len(output) > 0 {
		// 解析命令输出
		results = cc.parseCommandOutput(item, filePath, string(output))
	} else if err != nil {
		// 如果命令执行失败且没有输出，记录错误
		results = append(results, checklist.CheckResult{
			ItemID:     item.ID,
			ItemName:   item.Name,
			FilePath:   filePath,
			Message:    fmt.Sprintf("执行命令失败: %v", err),
			Severity:   "error",
			Suggestion: "检查工具是否正确安装",
		})
	}

	return results, nil
}

// executePattern 执行正则表达式模式检查
func (cc *CodeChecker) executePattern(item checklist.ChecklistItem, filePath string) ([]checklist.CheckResult, error) {
	regex, err := regexp.Compile(item.Pattern)
	if err != nil {
		return nil, fmt.Errorf("编译正则表达式失败: %w", err)
	}

	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("打开文件失败: %w", err)
	}
	defer file.Close()

	var results []checklist.CheckResult
	scanner := bufio.NewScanner(file)
	lineNumber := 0

	for scanner.Scan() {
		lineNumber++
		line := scanner.Text()

		if regex.MatchString(line) {
			results = append(results, checklist.CheckResult{
				ItemID:     item.ID,
				ItemName:   item.Name,
				FilePath:   filePath,
				LineNumber: lineNumber,
				Message:    fmt.Sprintf("第 %d 行匹配模式: %s", lineNumber, item.Pattern),
				Severity:   item.Severity,
				Suggestion: item.Description,
			})
		}
	}

	return results, scanner.Err()
}

// parseCommandOutput 解析命令输出
func (cc *CodeChecker) parseCommandOutput(item checklist.ChecklistItem, filePath, output string) []checklist.CheckResult {
	var results []checklist.CheckResult
	
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// 创建基本结果
		result := checklist.CheckResult{
			ItemID:     item.ID,
			ItemName:   item.Name,
			FilePath:   filePath,
			Message:    line,
			Severity:   item.Severity,
			Suggestion: item.Description,
		}

		// 尝试解析行号（常见格式：filename:line:column: message）
		if parts := strings.SplitN(line, ":", 4); len(parts) >= 2 {
			if lineNum := parseInt(parts[1]); lineNum > 0 {
				result.LineNumber = lineNum
				if len(parts) >= 4 {
					result.Message = strings.TrimSpace(parts[3])
				}
			}
		}

		results = append(results, result)
	}

	return results
}

// calculateSummary 计算检查摘要
func (cc *CodeChecker) calculateSummary(report *checklist.CheckReport) {
	summary := &report.Summary
	summary.TotalIssues = len(report.Results)

	for _, result := range report.Results {
		switch result.Severity {
		case "error":
			summary.Errors++
		case "warning":
			summary.Warnings++
		case "info":
			summary.Info++
		}
	}
}

// isRelevantFile 检查文件是否与检查清单相关
func (cc *CodeChecker) isRelevantFile(filePath string) bool {
	ext := filepath.Ext(filePath)
	language := getLanguageByExtension(ext)

	for _, item := range cc.checklist.Items {
		// 如果检查项没有指定文件类型和语言限制，则认为所有文件都相关
		if len(item.FileTypes) == 0 && len(item.Languages) == 0 {
			return true
		}

		// 检查文件类型
		if len(item.FileTypes) > 0 && contains(item.FileTypes, ext) {
			return true
		}

		// 检查编程语言
		if len(item.Languages) > 0 && contains(item.Languages, language) {
			return true
		}
	}

	return false
}

// getLanguageByExtension 根据文件扩展名获取编程语言
func getLanguageByExtension(ext string) string {
	switch ext {
	case ".go":
		return "go"
	case ".mod":
		return "go" // go.mod 文件也属于 Go 语言
	case ".sum":
		return "go" // go.sum 文件也属于 Go 语言
	default:
		return "unknown"
	}
}

// parseInt 安全地解析整数
func parseInt(s string) int {
	var result int
	fmt.Sscanf(s, "%d", &result)
	return result
}

// contains 检查字符串切片是否包含指定字符串
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}