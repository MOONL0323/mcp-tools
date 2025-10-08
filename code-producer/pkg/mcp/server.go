package mcp

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// MCPRequest 表示MCP请求结构
type MCPRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params,omitempty"`
}

// MCPResponse 表示MCP响应结构
type MCPResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id"`
	Result  interface{} `json:"result,omitempty"`
	Error   *MCPError   `json:"error,omitempty"`
}

// MCPError 表示MCP错误结构
type MCPError struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// Tool 表示MCP工具
type Tool struct {
	Name        string      `json:"name"`
	Description string      `json:"description"`
	InputSchema interface{} `json:"inputSchema"`
}

// ToolResult 表示工具执行结果
type ToolResult struct {
	Content []Content `json:"content"`
	IsError bool      `json:"isError,omitempty"`
}

// Content 表示内容结构
type Content struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// Server MCP服务器
type Server struct {
	tools map[string]ToolHandler
}

// ToolHandler 工具处理函数类型
type ToolHandler func(params interface{}) (*ToolResult, error)

// NewServer 创建新的MCP服务器
func NewServer() *Server {
	return &Server{
		tools: make(map[string]ToolHandler),
	}
}

// RegisterTool 注册工具
func (s *Server) RegisterTool(name string, handler ToolHandler) {
	s.tools[name] = handler
}

// HandleRequest 处理MCP请求
func (s *Server) HandleRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		s.sendError(w, nil, -32700, "Parse error", nil)
		return
	}

	var req MCPRequest
	if err := json.Unmarshal(body, &req); err != nil {
		s.sendError(w, nil, -32700, "Parse error", nil)
		return
	}

	switch req.Method {
	case "tools/list":
		s.handleToolsList(w, &req)
	case "tools/call":
		s.handleToolsCall(w, &req)
	default:
		s.sendError(w, req.ID, -32601, "Method not found", nil)
	}
}

// handleToolsList 处理工具列表请求
func (s *Server) handleToolsList(w http.ResponseWriter, req *MCPRequest) {
	tools := make([]Tool, 0, len(s.tools))

	// 这里需要根据实际的工具定义来填充
	// 暂时返回空列表，后续会在handlers中具体实现
	for name := range s.tools {
		tool := Tool{
			Name:        name,
			Description: fmt.Sprintf("Tool: %s", name),
			InputSchema: map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			},
		}
		tools = append(tools, tool)
	}

	result := map[string]interface{}{
		"tools": tools,
	}

	s.sendResponse(w, req.ID, result)
}

// handleToolsCall 处理工具调用请求
func (s *Server) handleToolsCall(w http.ResponseWriter, req *MCPRequest) {
	params, ok := req.Params.(map[string]interface{})
	if !ok {
		s.sendError(w, req.ID, -32602, "Invalid params", nil)
		return
	}

	name, ok := params["name"].(string)
	if !ok {
		s.sendError(w, req.ID, -32602, "Missing tool name", nil)
		return
	}

	handler, exists := s.tools[name]
	if !exists {
		s.sendError(w, req.ID, -32601, "Tool not found", nil)
		return
	}

	args := params["arguments"]
	result, err := handler(args)
	if err != nil {
		s.sendError(w, req.ID, -32603, "Internal error", err.Error())
		return
	}

	s.sendResponse(w, req.ID, result)
}

// sendResponse 发送响应
func (s *Server) sendResponse(w http.ResponseWriter, id interface{}, result interface{}) {
	response := MCPResponse{
		JSONRPC: "2.0",
		ID:      id,
		Result:  result,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// sendError 发送错误响应
func (s *Server) sendError(w http.ResponseWriter, id interface{}, code int, message string, data interface{}) {
	response := MCPResponse{
		JSONRPC: "2.0",
		ID:      id,
		Error: &MCPError{
			Code:    code,
			Message: message,
			Data:    data,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
