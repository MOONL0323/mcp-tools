package services

import (
	"bytes"
	"code-producer/internal/models"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// KnowledgeMapService 提供与knowledge-map系统交互的服务
type KnowledgeMapService struct {
	baseURL string
	apiKey  string
	client  *http.Client
}

// NewKnowledgeMapService 创建新的KnowledgeMapService实例
func NewKnowledgeMapService(baseURL, apiKey string) *KnowledgeMapService {
	return &KnowledgeMapService{
		baseURL: baseURL,
		apiKey:  apiKey,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// SearchDocuments 搜索knowledge-map中的文档
func (k *KnowledgeMapService) SearchDocuments(req *models.SearchRequest) (*models.SearchResponse, error) {
	if req.Limit == 0 {
		req.Limit = 10
	}

	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", k.baseURL+"/api/search", bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if k.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+k.apiKey)
	}

	resp, err := k.client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var searchResp models.SearchResponse
	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &searchResp, nil
}

// GetDocument 根据ID获取具体文档
func (k *KnowledgeMapService) GetDocument(documentID string) (*models.KnowledgeMapDocument, error) {
	url := fmt.Sprintf("%s/api/documents/%s", k.baseURL, documentID)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if k.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+k.apiKey)
	}

	resp, err := k.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var doc models.KnowledgeMapDocument
	if err := json.NewDecoder(resp.Body).Decode(&doc); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &doc, nil
}

// SearchCodeExamples 搜索代码示例
func (k *KnowledgeMapService) SearchCodeExamples(language, query string) (*models.SearchResponse, error) {
	req := &models.SearchRequest{
		Query:    query,
		Language: language,
		Type:     "code",
		Filters: map[string]string{
			"type": "code_example",
		},
		Limit: 5,
	}

	return k.SearchDocuments(req)
}

// SearchTemplates 搜索代码模板
func (k *KnowledgeMapService) SearchTemplates(language, framework string) ([]models.Template, error) {
	req := &models.SearchRequest{
		Query:    fmt.Sprintf("template %s %s", language, framework),
		Language: language,
		Type:     "template",
		Filters: map[string]string{
			"type":      "template",
			"language":  language,
			"framework": framework,
		},
		Limit: 10,
	}

	searchResp, err := k.SearchDocuments(req)
	if err != nil {
		return nil, err
	}

	templates := make([]models.Template, 0, len(searchResp.Results))
	for _, result := range searchResp.Results {
		template := models.Template{
			ID:          result.ID,
			Name:        result.Title,
			Description: extractDescription(result.Content),
			Language:    result.Language,
			Framework:   result.Metadata["framework"],
			Content:     result.Content,
			Tags:        result.Tags,
			Metadata:    result.Metadata,
		}
		templates = append(templates, template)
	}

	return templates, nil
}

// SearchRelatedDocuments 搜索相关文档
func (k *KnowledgeMapService) SearchRelatedDocuments(keywords []string, limit int) (*models.SearchResponse, error) {
	if limit == 0 {
		limit = 5
	}

	query := ""
	for i, keyword := range keywords {
		if i > 0 {
			query += " "
		}
		query += keyword
	}

	req := &models.SearchRequest{
		Query: query,
		Limit: limit,
	}

	return k.SearchDocuments(req)
}

// extractDescription 从内容中提取描述
func extractDescription(content string) string {
	if len(content) > 200 {
		return content[:200] + "..."
	}
	return content
}

// IsHealthy 检查knowledge-map服务是否健康
func (k *KnowledgeMapService) IsHealthy() bool {
	if k.baseURL == "" {
		return false
	}

	req, err := http.NewRequest("GET", k.baseURL+"/health", nil)
	if err != nil {
		return false
	}

	resp, err := k.client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}
