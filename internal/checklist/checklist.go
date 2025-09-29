package checklist

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"gopkg.in/yaml.v3"
)

// ChecklistItem 表示单个检查项
type ChecklistItem struct {
	ID          string   `json:"id" yaml:"id"`
	Name        string   `json:"name" yaml:"name"`
	Description string   `json:"description" yaml:"description"`
	Category    string   `json:"category" yaml:"category"`
	Severity    string   `json:"severity" yaml:"severity"` // error, warning, info
	Pattern     string   `json:"pattern,omitempty" yaml:"pattern,omitempty"` // 正则表达式或特定模式
	FileTypes   []string `json:"file_types,omitempty" yaml:"file_types,omitempty"` // 适用的文件类型
	Languages   []string `json:"languages,omitempty" yaml:"languages,omitempty"` // 适用的编程语言
	Command     string   `json:"command,omitempty" yaml:"command,omitempty"` // 外部命令
}

// Checklist 表示完整的检查清单
type Checklist struct {
	Name        string          `json:"name" yaml:"name"`
	Version     string          `json:"version" yaml:"version"`
	Description string          `json:"description" yaml:"description"`
	Author      string          `json:"author,omitempty" yaml:"author,omitempty"`
	Items       []ChecklistItem `json:"items" yaml:"items"`
}

// CheckResult 表示检查结果
type CheckResult struct {
	ItemID      string `json:"item_id"`
	ItemName    string `json:"item_name"`
	FilePath    string `json:"file_path"`
	LineNumber  int    `json:"line_number,omitempty"`
	Message     string `json:"message"`
	Severity    string `json:"severity"`
	Suggestion  string `json:"suggestion,omitempty"`
}

// CheckReport 表示检查报告
type CheckReport struct {
	ChecklistName string        `json:"checklist_name"`
	Target        string        `json:"target"` // 被检查的文件或目录
	TotalItems    int           `json:"total_items"`
	Results       []CheckResult `json:"results"`
	Summary       Summary       `json:"summary"`
}

// Summary 表示检查摘要
type Summary struct {
	TotalIssues int `json:"total_issues"`
	Errors      int `json:"errors"`
	Warnings    int `json:"warnings"`
	Info        int `json:"info"`
}

// LoadChecklist 从文件加载检查清单
func LoadChecklist(filePath string) (*Checklist, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("读取检查清单文件失败: %w", err)
	}
	
	var checklist Checklist
	
	// 根据文件扩展名判断格式
	ext := filepath.Ext(filePath)
	switch ext {
	case ".json":
		if err := json.Unmarshal(data, &checklist); err != nil {
			return nil, fmt.Errorf("解析 JSON 检查清单失败: %w", err)
		}
	case ".yaml", ".yml":
		if err := yaml.Unmarshal(data, &checklist); err != nil {
			return nil, fmt.Errorf("解析 YAML 检查清单失败: %w", err)
		}
	default:
		return nil, fmt.Errorf("不支持的文件格式: %s", ext)
	}
	
	return &checklist, nil
}

// SaveChecklist 保存检查清单到文件
func (c *Checklist) SaveChecklist(filePath string) error {
	// 确保目录存在
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("创建目录失败: %w", err)
	}
	
	var data []byte
	var err error
	
	// 根据文件扩展名选择格式
	ext := filepath.Ext(filePath)
	switch ext {
	case ".json":
		data, err = json.MarshalIndent(c, "", "  ")
	case ".yaml", ".yml":
		data, err = yaml.Marshal(c)
	default:
		return fmt.Errorf("不支持的文件格式: %s", ext)
	}
	
	if err != nil {
		return fmt.Errorf("序列化检查清单失败: %w", err)
	}
	
	return os.WriteFile(filePath, data, 0644)
}

// ValidateChecklist 验证检查清单格式
func (c *Checklist) ValidateChecklist() error {
	if c.Name == "" {
		return fmt.Errorf("检查清单名称不能为空")
	}
	
	if len(c.Items) == 0 {
		return fmt.Errorf("检查清单必须包含至少一个检查项")
	}
	
	// 检查 ID 唯一性
	idMap := make(map[string]bool)
	for i, item := range c.Items {
		if item.ID == "" {
			return fmt.Errorf("第 %d 个检查项的 ID 不能为空", i+1)
		}
		
		if idMap[item.ID] {
			return fmt.Errorf("检查项 ID '%s' 重复", item.ID)
		}
		idMap[item.ID] = true
		
		if item.Name == "" {
			return fmt.Errorf("检查项 '%s' 的名称不能为空", item.ID)
		}
		
		// 验证严重级别
		switch item.Severity {
		case "error", "warning", "info":
			// 有效的严重级别
		case "":
			c.Items[i].Severity = "warning" // 默认警告级别
		default:
			return fmt.Errorf("检查项 '%s' 的严重级别 '%s' 无效，必须是 error、warning 或 info", item.ID, item.Severity)
		}
	}
	
	return nil
}

// GetItemsByLanguage 根据编程语言筛选检查项
func (c *Checklist) GetItemsByLanguage(language string) []ChecklistItem {
	var items []ChecklistItem
	for _, item := range c.Items {
		if len(item.Languages) == 0 || contains(item.Languages, language) {
			items = append(items, item)
		}
	}
	return items
}

// GetItemsByFileType 根据文件类型筛选检查项
func (c *Checklist) GetItemsByFileType(fileExt string) []ChecklistItem {
	var items []ChecklistItem
	for _, item := range c.Items {
		if len(item.FileTypes) == 0 || contains(item.FileTypes, fileExt) {
			items = append(items, item)
		}
	}
	return items
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