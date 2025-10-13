/**
 * 文档服务实现
 */

import axios from 'axios';
import { IDocumentService } from '../interfaces/IDocumentService';
import type { 
  IDocumentMetadata, 
  DocumentFilters, 
  DocumentUploadRequest 
} from '../interfaces/IDocumentService';

export class DocumentService implements IDocumentService {
  private readonly baseURL = 'http://localhost:8000/api/v1';
  private axiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 文档上传可能需要更长时间
    });

    // 请求拦截器 - 添加认证头
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  async uploadDocument(file: File, metadata: DocumentUploadRequest): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify(metadata));
      
      const response = await this.axiosInstance.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.id;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('文档上传失败');
    }
  }

  async getDocuments(filters?: DocumentFilters): Promise<IDocumentMetadata[]> {
    try {
      const response = await this.axiosInstance.get('/documents/', {
        params: filters,
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取文档列表失败');
    }
  }

  async getDocument(id: string): Promise<IDocumentMetadata> {
    try {
      const response = await this.axiosInstance.get(`/documents/${id}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取文档详情失败');
    }
  }

  async updateDocument(id: string, updates: Partial<IDocumentMetadata>): Promise<void> {
    try {
      await this.axiosInstance.put(`/documents/${id}`, updates);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('更新文档失败');
    }
  }

  async deleteDocument(id: string): Promise<void> {
    try {
      await this.axiosInstance.delete(`/documents/${id}`);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('删除文档失败');
    }
  }

  async getDocumentContent(id: string): Promise<string> {
    try {
      const response = await this.axiosInstance.get(`/documents/${id}/content`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取文档内容失败');
    }
  }

  async downloadDocument(id: string): Promise<Blob> {
    try {
      const response = await this.axiosInstance.get(`/documents/${id}/download`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('下载文档失败');
    }
  }

  async searchDocuments(query: string, filters?: DocumentFilters): Promise<IDocumentMetadata[]> {
    try {
      const response = await this.axiosInstance.post('/documents/search', {
        query,
        ...filters,
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('搜索文档失败');
    }
  }

  async batchDeleteDocuments(ids: string[]): Promise<void> {
    try {
      await this.axiosInstance.post('/documents/batch-delete', { ids });
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('批量删除失败');
    }
  }
}
