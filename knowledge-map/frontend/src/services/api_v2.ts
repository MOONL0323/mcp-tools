/**
 * AI Agent知识管理系统 API客户端
 * 支持文档和代码的上传、管理、搜索功能
 */

export interface SearchRequest {
  query: string;
  top_k?: number;
  content_type?: 'document' | 'code' | 'all';
  language?: string;
  block_type?: string;
  file_type?: string;
}

export interface SearchResult {
  content_id: string;
  content: string;
  content_type: 'document' | 'code';
  source_file: string;
  source_path: string;
  similarity: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time: number;
}

export interface SystemStatus {
  // 文档统计
  total_documents: number;
  processed_documents: number;
  total_document_chunks: number;
  
  // 代码统计
  total_code_files: number;
  processed_code_files: number;
  total_code_blocks: number;
  
  // 系统信息
  embedding_model: string;
  embedding_dimension: number;
  supported_file_types: string[];
  supported_languages: string[];
  
  // 详细统计
  document_file_types: Record<string, number>;
  code_languages: Record<string, number>;
  code_block_types: Record<string, number>;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  content_id?: string;
  content_type: 'document' | 'code';
  processing_info?: Record<string, any>;
}

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  total_chunks: number;
  upload_time: string;
  processed: boolean;
  error_message?: string;
}

export interface CodeFileInfo {
  file_id: string;
  filename: string;
  language: string;
  file_size: number;
  total_blocks: number;
  upload_time: string;
  processed: boolean;
  error_message?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  components_status: Record<string, string>;
}

const BASE_URL = 'http://localhost:8000';

class KnowledgeGraphApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // ===== 健康检查和状态 =====

  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getSystemStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/status');
  }

  // ===== 文档管理 =====

  async uploadDocument(
    file: File,
    processImmediately: boolean = true
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('process_immediately', processImmediately.toString());

    const response = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  async listDocuments(): Promise<DocumentInfo[]> {
    return this.request<DocumentInfo[]>('/documents');
  }

  async deleteDocument(docId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/documents/${docId}`, {
      method: 'DELETE',
    });
  }

  // ===== 代码管理 =====

  async uploadCodeFile(
    file: File,
    processImmediately: boolean = true
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('process_immediately', processImmediately.toString());

    const response = await fetch(`${this.baseUrl}/code/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Upload Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  async listCodeFiles(): Promise<CodeFileInfo[]> {
    return this.request<CodeFileInfo[]>('/code/files');
  }

  async deleteCodeFile(fileId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/code/files/${fileId}`, {
      method: 'DELETE',
    });
  }

  // ===== 智能搜索 =====

  async search(request: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async searchSimple(
    query: string,
    options: {
      top_k?: number;
      content_type?: 'document' | 'code' | 'all';
      language?: string;
      block_type?: string;
    } = {}
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query,
      top_k: (options.top_k || 10).toString(),
      content_type: options.content_type || 'all',
      ...(options.language && { language: options.language }),
      ...(options.block_type && { block_type: options.block_type }),
    });

    return this.request<SearchResponse>(`/search?${params}`);
  }

  // ===== 旧版本兼容性方法 =====

  async uploadFile(file: File): Promise<UploadResponse> {
    // 根据文件扩展名判断是文档还是代码
    const extension = file.name.split('.').pop()?.toLowerCase();
    const codeExtensions = ['py', 'js', 'ts', 'java', 'cpp', 'c', 'cs', 'go', 'rs', 'php', 'rb'];
    
    if (codeExtensions.includes(extension || '')) {
      return this.uploadCodeFile(file);
    } else {
      return this.uploadDocument(file);
    }
  }

  async searchDocuments(
    query: string,
    topK: number = 10,
    fileType?: string
  ): Promise<SearchResponse> {
    return this.search({
      query,
      top_k: topK,
      content_type: 'document',
      file_type: fileType,
    });
  }

  async searchCode(
    query: string,
    topK: number = 10,
    language?: string
  ): Promise<SearchResponse> {
    return this.search({
      query,
      top_k: topK,
      content_type: 'code',
      language,
    });
  }
}

export const KnowledgeGraphApi = new KnowledgeGraphApiClient();

// 导出类型
export type {
  SystemStatus as SystemStatusType,
  DocumentInfo as DocumentInfoType,
  CodeFileInfo as CodeFileInfoType,
  SearchResult as SearchResultType,
  SearchResponse as SearchResponseType,
};

export default KnowledgeGraphApi;