/**
 * 分类服务实现
 */

import axios from 'axios';
import { IClassificationService } from '../interfaces/IClassificationService';
import type { HierarchicalClassification, ProjectInfo, ModuleInfo, TeamInfo, DevTypeInfo, DocumentClassification } from '../interfaces/IClassificationService';

export class ClassificationService implements IClassificationService {
  private readonly baseURL = 'http://localhost:8000/api/v1';
  private axiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
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
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  async getClassifications(): Promise<HierarchicalClassification> {
    try {
      const response = await this.axiosInstance.get('/classifications/');
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取分类列表失败');
    }
  }

  async createClassification(data: Omit<HierarchicalClassification, 'id' | 'created_at' | 'updated_at'>): Promise<HierarchicalClassification> {
    try {
      const response = await this.axiosInstance.post('/classifications/', data);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('创建分类失败');
    }
  }

  async updateClassification(id: string, data: Partial<HierarchicalClassification>): Promise<HierarchicalClassification> {
    try {
      const response = await this.axiosInstance.put(`/classifications/${id}`, data);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('更新分类失败');
    }
  }

  async deleteClassification(id: string): Promise<void> {
    try {
      await this.axiosInstance.delete(`/classifications/${id}`);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('删除分类失败');
    }
  }

  async getTeams(): Promise<string[]> {
    try {
      const response = await this.axiosInstance.get('/classifications/teams');
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取团队列表失败');
    }
  }

  async getProjectsByTeam(teamId: string): Promise<ProjectInfo[]> {
    try {
      const response = await this.axiosInstance.get(`/classifications/teams/${teamId}/projects`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取项目列表失败');
    }
  }

  async getModulesByProject(projectId: string): Promise<ModuleInfo[]> {
    try {
      const response = await this.axiosInstance.get(`/classifications/projects/${projectId}/modules`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取模块列表失败');
    }
  }

  async getDocumentTypes(): Promise<string[]> {
    try {
      const response = await this.axiosInstance.get('/classifications/document-types');
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取文档类型列表失败');
    }
  }

  async getClassificationStats(): Promise<{
    total_teams: number;
    total_projects: number;
    total_modules: number;
    total_document_types: number;
    hierarchy_depth: number;
  }> {
    try {
      const response = await this.axiosInstance.get('/classifications/stats');
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取分类统计失败');
    }
  }

  // 实现接口要求的方法
  async getTeamsByUser(userId: string): Promise<TeamInfo[]> {
    try {
      const response = await this.axiosInstance.get(`/classifications/users/${userId}/teams`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取用户团队失败');
    }
  }

  async getDevTypesByCategory(category: 'business_doc' | 'demo_code'): Promise<DevTypeInfo[]> {
    try {
      const response = await this.axiosInstance.get(`/classifications/dev-types?category=${category}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取开发类型失败');
    }
  }

  async validateClassification(classification: DocumentClassification): Promise<boolean> {
    try {
      const response = await this.axiosInstance.post('/classifications/validate', classification);
      return response.data.valid;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('验证分类失败');
    }
  }

  async getAllTeams(): Promise<TeamInfo[]> {
    try {
      const response = await this.axiosInstance.get('/classifications/teams');
      return response.data;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('获取所有团队失败');
    }
  }

  async createTeam(team: Omit<TeamInfo, 'id' | 'created_at' | 'member_count'>): Promise<string> {
    try {
      const response = await this.axiosInstance.post('/classifications/teams', team);
      return response.data.id;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('创建团队失败');
    }
  }

  async createProject(project: Omit<ProjectInfo, 'id' | 'created_at' | 'module_count'>): Promise<string> {
    try {
      const response = await this.axiosInstance.post('/classifications/projects', project);
      return response.data.id;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('创建项目失败');
    }
  }

  async createModule(module: Omit<ModuleInfo, 'id' | 'created_at' | 'document_count'>): Promise<string> {
    try {
      const response = await this.axiosInstance.post('/classifications/modules', module);
      return response.data.id;
    } catch (error: any) {
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      }
      throw new Error('创建模块失败');
    }
  }
}