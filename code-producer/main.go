package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"code-producer/internal/handlers"
	"code-producer/internal/services"
	"code-producer/pkg/mcp"

	"github.com/gorilla/mux"
	"github.com/joho/godotenv"
)

func main() {
	// 加载环境变量
	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: .env file not found: %v", err)
	}

	// 初始化服务
	knowledgeMapService := services.NewKnowledgeMapService(
		os.Getenv("KNOWLEDGE_MAP_URL"),
		os.Getenv("KNOWLEDGE_MAP_API_KEY"),
	)

	codeProducerService := services.NewCodeProducerService(knowledgeMapService)

	// 创建MCP服务器
	mcpServer := mcp.NewServer()

	// 创建处理器
	toolHandler := handlers.NewToolHandler(codeProducerService, knowledgeMapService)

	// 注册工具
	mcpServer.RegisterTool("generate_code", toolHandler.GenerateCode)
	mcpServer.RegisterTool("search_knowledge", toolHandler.SearchKnowledge)
	mcpServer.RegisterTool("get_code_template", toolHandler.GetCodeTemplate)
	mcpServer.RegisterTool("analyze_requirements", toolHandler.AnalyzeRequirements)

	// 设置HTTP路由
	router := mux.NewRouter()
	router.HandleFunc("/mcp", mcpServer.HandleRequest).Methods("POST")
	router.HandleFunc("/health", healthCheck).Methods("GET")

	// 配置服务器
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// 启动服务器
	go func() {
		fmt.Printf("Starting code-producer MCP server on port %s\n", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// 优雅关闭
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	fmt.Println("Server stopped")
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"healthy","service":"code-producer"}`))
}
