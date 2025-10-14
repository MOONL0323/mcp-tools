/**
 * API 客户端实例
 * 为前端组件提供统一的API调用接口
 */

import { ApiClient } from './ApiClient';

// 创建全局API客户端实例
// 注意: baseURL在ApiClient内部从环境变量读取，这里不再重复设置
export const apiClient = new ApiClient({
  timeout: 30000,
});

// 导出方便使用的方法
export const api = {
  // 文档管理API
  documents: {
    upload: (formData: FormData) => 
      apiClient.post('/v1/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }),
    
    list: async (params?: any) => {
      const response = await apiClient.get('/v1/documents/list', { params });
      // 后端直接返回数组，所以data就是数组
      return response.data || [];
    },
    
    search: async (params?: any) => {
      const response = await apiClient.get('/v1/documents/search', { params });
      // 后端直接返回数组
      return response.data || [];
    },
    
    get: async (id: string) => {
      const response = await apiClient.get(`/v1/documents/${id}`);
      // 后端直接返回对象
      return response.data;
    },
    
    delete: (id: string) => 
      apiClient.delete(`/v1/documents/${id}`)
  },

  // MCP相关API
  mcp: {
    searchCodeExamples: (data: any) => 
      apiClient.post('/v1/mcp/search-code-examples', data),
    
    getDesignDocs: (params: any) => 
      apiClient.post('/v1/mcp/get-design-docs', params),
    
    getCodingStandards: (language: string) => 
      apiClient.get(`/v1/mcp/coding-standards/${language}`),
    
    getTeamContext: (team: string, project?: string) => 
      apiClient.get(`/v1/mcp/team-context/${team}`, { 
        params: project ? { project } : undefined 
      })
  }
};

export default apiClient;