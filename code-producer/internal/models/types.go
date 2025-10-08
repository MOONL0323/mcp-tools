package models

import "time"

// SearchRequest 表示搜索请求
type SearchRequest struct {
	Query    string            `json:"query"`
	Filters  map[string]string `json:"filters,omitempty"`
	Limit    int               `json:"limit,omitempty"`
	Language string            `json:"language,omitempty"`
	Type     string            `json:"type,omitempty"`
}

// SearchResult 表示搜索结果
type SearchResult struct {
	ID        string            `json:"id"`
	Title     string            `json:"title"`
	Content   string            `json:"content"`
	Type      string            `json:"type"`
	Language  string            `json:"language,omitempty"`
	Tags      []string          `json:"tags"`
	Metadata  map[string]string `json:"metadata"`
	Relevance float64           `json:"relevance"`
	CreatedAt time.Time         `json:"created_at"`
	UpdatedAt time.Time         `json:"updated_at"`
}

// SearchResponse 表示搜索响应
type SearchResponse struct {
	Results []SearchResult `json:"results"`
	Total   int            `json:"total"`
	Query   string         `json:"query"`
}

// CodeGenerationRequest 表示代码生成请求
type CodeGenerationRequest struct {
	Requirements string            `json:"requirements"`
	Language     string            `json:"language"`
	Framework    string            `json:"framework,omitempty"`
	Style        string            `json:"style,omitempty"`
	Context      map[string]string `json:"context,omitempty"`
	Templates    []string          `json:"templates,omitempty"`
}

// CodeGenerationResponse 表示代码生成响应
type CodeGenerationResponse struct {
	Code        string            `json:"code"`
	Language    string            `json:"language"`
	Explanation string            `json:"explanation"`
	Suggestions []string          `json:"suggestions,omitempty"`
	References  []SearchResult    `json:"references,omitempty"`
	Metadata    map[string]string `json:"metadata,omitempty"`
}

// RequirementsAnalysis 表示需求分析结果
type RequirementsAnalysis struct {
	Summary      string         `json:"summary"`
	KeyFeatures  []string       `json:"key_features"`
	Technologies []string       `json:"technologies"`
	Complexity   string         `json:"complexity"`
	Suggestions  []string       `json:"suggestions"`
	References   []SearchResult `json:"references,omitempty"`
}

// Template 表示代码模板
type Template struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Language    string            `json:"language"`
	Framework   string            `json:"framework,omitempty"`
	Content     string            `json:"content"`
	Variables   []TemplateVar     `json:"variables,omitempty"`
	Tags        []string          `json:"tags"`
	Metadata    map[string]string `json:"metadata,omitempty"`
}

// TemplateVar 表示模板变量
type TemplateVar struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Type        string `json:"type"`
	Default     string `json:"default,omitempty"`
	Required    bool   `json:"required"`
}

// KnowledgeMapDocument 表示知识图谱文档
type KnowledgeMapDocument struct {
	ID        string            `json:"id"`
	Title     string            `json:"title"`
	Content   string            `json:"content"`
	Type      string            `json:"type"`
	Language  string            `json:"language,omitempty"`
	Tags      []string          `json:"tags"`
	Category  string            `json:"category,omitempty"`
	Author    string            `json:"author,omitempty"`
	Version   string            `json:"version,omitempty"`
	Metadata  map[string]string `json:"metadata"`
	CreatedAt time.Time         `json:"created_at"`
	UpdatedAt time.Time         `json:"updated_at"`
}
