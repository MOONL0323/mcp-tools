/**
 * API服务层 - 与后端API通信的封装
 * 实现前后端解耦，所有API调用都通过这个服务层
 */

import axios, { AxiosResponse } from 'axios';

// API响应接口定义
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message: string;
  error?: string;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  file_type?: 'code' | 'document' | 'all';
}

export interface SearchResult {
  content: string;
  metadata: Record<string, any>;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}

export interface AddTextRequest {
  content: string;
  title?: string;
  save_graph?: boolean;
}

export interface SystemStatus {
  document_count: number;
  vector_dimension: number;
  graph_nodes: number;
  graph_edges: number;
  supported_extensions: string[];
  available_components: Record<string, string[]>;
}

export interface UploadResponse {
  task_id: string;
}

export interface ProcessingStatus {
  status: 'processing' | 'completed' | 'failed';
  message: string;
  progress: number;
  result?: any;
  error?: string;
}

// 配置axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api',
  timeout: 60000, // 60秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config: any) => {
    console.log(`API请求: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error: any) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    if (!response.data.success) {
      console.warn('API业务错误:', response.data.message || response.data.error);
    }
    return response;
  },
  (error: any) => {
    console.error('API响应错误:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API服务类
export class KnowledgeGraphApi {
  /**
   * 健康检查
   */
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/health');
    return response.data;
  }

  /**
   * 获取系统状态
   */
  static async getSystemStatus(): Promise<SystemStatus> {
    const response = await api.get<ApiResponse<SystemStatus>>('/status');
    if (!response.data.success) {
      throw new Error(response.data.error || '获取系统状态失败');
    }
    return response.data.data!;
  }

  /**
   * 搜索知识库
   */
  static async searchKnowledge(request: SearchRequest): Promise<SearchResponse> {
    const response = await api.post<ApiResponse<SearchResponse>>('/search', request);
    if (!response.data.success) {
      throw new Error(response.data.error || '搜索失败');
    }
    return response.data.data!;
  }

  /**
   * 添加文本到知识库
   */
  static async addText(request: AddTextRequest): Promise<{ task_id: string }> {
    const formData = new FormData();
    formData.append('content', request.content);
    if (request.title) {
      formData.append('title', request.title);
    }
    formData.append('save_graph', request.save_graph?.toString() || 'true');

    const response = await api.post<ApiResponse<UploadResponse>>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    if (!response.data.success) {
      throw new Error(response.data.error || '文本添加失败');
    }
    return response.data.data!;
  }

  /**
   * 上传文件
   */
  static async uploadFile(file: File, saveGraph: boolean = true): Promise<{ task_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('save_graph', saveGraph.toString());

    const response = await api.post<ApiResponse<UploadResponse>>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    if (!response.data.success) {
      throw new Error(response.data.error || '文件上传失败');
    }
    return response.data.data!;
  }

  /**
   * 获取任务处理状态
   */
  static async getTaskStatus(taskId: string): Promise<ProcessingStatus> {
    const response = await api.get<ApiResponse<ProcessingStatus>>(`/upload/status/${taskId}`);
    if (!response.data.success) {
      throw new Error(response.data.error || '获取处理状态失败');
    }
    return response.data.data!;
  }

  /**
   * 获取可用组件
   */
  static async getAvailableComponents(): Promise<Record<string, string[]>> {
    const response = await api.get<ApiResponse<Record<string, string[]>>>('/components');
    if (!response.data.success) {
      throw new Error(response.data.error || '获取组件列表失败');
    }
    return response.data.data!;
  }

  /**
   * 清空知识库（开发用）
   */
  static async clearKnowledgeBase(): Promise<void> {
    const response = await api.delete<ApiResponse>('/clear');
    if (!response.data.success) {
      throw new Error(response.data.error || '清空知识库失败');
    }
  }
}

// 错误处理工具
export class ApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// 工具函数：格式化文件大小
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 工具函数：延迟执行
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default KnowledgeGraphApi;