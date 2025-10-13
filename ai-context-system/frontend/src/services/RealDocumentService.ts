/**
 * 真实的文档服务实现（连接后端API）
 */

import { ApiClient, ApiResponse } from './ApiClient';

export interface DocumentUploadRequest {
  title: string;
  doc_type: string;
  description?: string;
}

export interface DocumentMetadata {
  id: string;
  title: string;
  doc_type: string;
  file_name: string;
  file_size: number;
  status: string;
  upload_time: string;
  chunk_count?: number;
  entity_count?: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
}

export interface SearchResult {
  document_id: string;
  document_title: string;
  chunk_id: string;
  content: string;
  score: number;
}

export class RealDocumentService {
  private apiClient: ApiClient;
  private baseUrl = '/v1/docs';

  constructor() {
    // 创建API客户端，连接到真实后端
    this.apiClient = new ApiClient({
      baseURL: 'http://127.0.0.1:8000/api',
      timeout: 30000, // 30秒超时
    });
  }

  async uploadDocument(file: File, metadata: DocumentUploadRequest): Promise<DocumentMetadata> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', metadata.title);
    formData.append('doc_type', metadata.doc_type);
    if (metadata.description) {
      formData.append('description', metadata.description);
    }

    const response: ApiResponse<DocumentMetadata> = await this.apiClient.post(
      `${this.baseUrl}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    if (!response.success || !response.data) {
      throw new Error(response.error || '文档上传失败');
    }

    return response.data;
  }

  async getDocuments(): Promise<DocumentMetadata[]> {
    const response: ApiResponse<DocumentMetadata[]> = await this.apiClient.get(this.baseUrl);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档列表失败');
    }

    return response.data;
  }

  async getDocument(id: string): Promise<DocumentMetadata> {
    const response: ApiResponse<DocumentMetadata> = await this.apiClient.get(`${this.baseUrl}/${id}`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档详情失败');
    }

    return response.data;
  }

  async deleteDocument(id: string): Promise<void> {
    const response: ApiResponse<void> = await this.apiClient.delete(`${this.baseUrl}/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || '删除文档失败');
    }
  }

  async searchDocuments(request: SearchRequest): Promise<SearchResult[]> {
    const response: ApiResponse<SearchResult[]> = await this.apiClient.post(
      `${this.baseUrl}/search`,
      request
    );
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '搜索失败');
    }

    return response.data;
  }

  async getDocumentChunks(id: string): Promise<any[]> {
    const response: ApiResponse<any[]> = await this.apiClient.get(`${this.baseUrl}/${id}/chunks`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档分块失败');
    }

    return response.data;
  }

  async getDocumentEntities(id: string): Promise<any[]> {
    const response: ApiResponse<any[]> = await this.apiClient.get(`${this.baseUrl}/${id}/entities`);
    
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档实体失败');
    }

    return response.data;
  }
}

// 导出单例
export const realDocumentService = new RealDocumentService();