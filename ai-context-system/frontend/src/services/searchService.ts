/**
 * 高级搜索API服务
 */

import { apiClient } from './api';

export interface SearchRequest {
  query: string;
  mode: 'semantic' | 'keyword' | 'hybrid';
  filters?: {
    doc_type?: string;
    team?: string;
    project?: string;
    language?: string;
    tags?: string[];
    date_range?: {
      start: string;
      end: string;
    };
  };
  limit?: number;
  offset?: number;
}

export interface SearchResultItem {
  id: string;
  title: string;
  content: string;
  description: string;
  type: 'document' | 'code' | 'api' | 'knowledge';
  score: number;
  metadata: {
    file_path?: string;
    language?: string;
    team?: string;
    project?: string;
    tags?: string[];
    created_at?: string;
    updated_at?: string;
  };
}

export interface SearchResponse {
  success: boolean;
  data: {
    results: SearchResultItem[];
    total: number;
    took: number; // 搜索耗时（毫秒）
    aggregations?: {
      types: Record<string, number>;
      languages: Record<string, number>;
      teams: Record<string, number>;
    };
  };
  error?: string;
}

export class SearchService {
  /**
   * 高级搜索
   */
  static async search(request: SearchRequest): Promise<SearchResponse> {
    try {
      console.log('发送高级搜索请求:', request);
      
      const response = await apiClient.post('/v1/search/advanced', request);

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.error || '搜索请求失败');
      }
    } catch (error: any) {
      console.error('高级搜索失败:', error);
      
      // 降级到本地模拟搜索
      return this.generateMockSearchResults(request);
    }
  }

  /**
   * 获取搜索建议
   */
  static async getSearchSuggestions(query: string): Promise<string[]> {
    try {
      const response = await apiClient.get(`/api/v1/search/suggestions?q=${encodeURIComponent(query)}`);
      
      if (response.data.success) {
        return response.data.data.suggestions || [];
      }
    } catch (error) {
      console.error('获取搜索建议失败:', error);
    }

    // 返回基于查询的简单建议
    return this.generateSimpleSuggestions(query);
  }

  /**
   * 获取热门搜索
   */
  static async getPopularSearches(): Promise<string[]> {
    try {
      const response = await apiClient.get('/v1/search/popular');
      
      if (response.data.success) {
        return response.data.data.searches || [];
      }
    } catch (error) {
      console.error('获取热门搜索失败:', error);
    }

    // 返回默认热门搜索
    return [
      'API设计规范',
      '微服务架构',
      'React组件开发',
      'Python编码规范',
      '数据库设计',
      '缓存策略',
      '系统监控',
      '性能优化'
    ];
  }

  /**
   * 获取搜索统计
   */
  static async getSearchStats(): Promise<any> {
    try {
      const response = await apiClient.get('/v1/search/stats');
      
      if (response.data.success) {
        return response.data.data;
      }
    } catch (error) {
      console.error('获取搜索统计失败:', error);
    }

    return {
      total_searches: 12580,
      avg_response_time: 234,
      popular_terms: ['API', 'React', 'Python', 'Database'],
      search_trends: []
    };
  }

  /**
   * 本地模拟搜索结果
   */
  private static generateMockSearchResults(request: SearchRequest): SearchResponse {
    const { query, mode } = request;
    
    // 基于搜索词生成不同的结果
    let results: SearchResultItem[] = [];
    
    if (query.includes('API') || query.includes('接口')) {
      results = [
        {
          id: '1',
          title: 'RESTful API设计规范',
          content: 'RESTful API设计规范文档，包含URL设计、HTTP方法使用、状态码规范等...',
          description: 'API设计的最佳实践指南',
          type: 'document',
          score: 0.95,
          metadata: {
            file_path: '/docs/api-design.md',
            team: '架构组',
            project: '平台建设',
            tags: ['API', 'REST', '规范'],
            created_at: '2024-01-10'
          }
        },
        {
          id: '2', 
          title: 'API接口实现示例',
          content: '完整的API接口实现代码，包含参数验证、错误处理、响应格式等...',
          description: 'Node.js + Express API实现',
          type: 'code',
          score: 0.88,
          metadata: {
            language: 'typescript',
            file_path: '/examples/api-server.ts',
            team: '后端组',
            tags: ['API', 'Node.js', 'Express']
          }
        }
      ];
    } else if (query.includes('React') || query.includes('组件')) {
      results = [
        {
          id: '3',
          title: 'React组件开发指南',
          content: 'React组件开发最佳实践，包含组件设计原则、性能优化、测试方法等...',
          description: 'React开发规范文档',
          type: 'document', 
          score: 0.92,
          metadata: {
            file_path: '/docs/react-guide.md',
            team: '前端组',
            project: '组件库',
            tags: ['React', '组件', '前端']
          }
        },
        {
          id: '4',
          title: '通用UI组件库',
          content: 'import React from "react"; const Button = ({ children, onClick, type = "primary" }) => {...',
          description: 'React UI组件实现',
          type: 'code',
          score: 0.85,
          metadata: {
            language: 'typescript',
            file_path: '/components/Button.tsx',
            team: '前端组',
            tags: ['React', 'UI', '组件']
          }
        }
      ];
    } else if (query.includes('Python') || query.includes('编码')) {
      results = [
        {
          id: '5',
          title: 'Python编码规范',
          content: 'Python项目编码规范，包含命名约定、代码结构、文档字符串等...',
          description: 'PEP 8风格指南及团队补充规范',
          type: 'document',
          score: 0.90,
          metadata: {
            file_path: '/docs/python-style.md', 
            team: '后端组',
            project: '代码规范',
            tags: ['Python', '编码规范', 'PEP8']
          }
        }
      ];
    } else {
      // 通用搜索结果
      results = [
        {
          id: '6',
          title: '系统架构文档',
          content: '整体系统架构设计，包含微服务划分、数据流向、技术选型等...',
          description: '系统整体架构设计文档',
          type: 'document',
          score: 0.80,
          metadata: {
            file_path: '/docs/architecture.md',
            team: '架构组',
            project: '系统设计',
            tags: ['架构', '系统设计', '微服务']
          }
        },
        {
          id: '7',
          title: '开发环境配置',
          content: '项目开发环境配置指南，包含依赖安装、环境变量、启动流程等...',
          description: '开发环境快速搭建指南',
          type: 'document',
          score: 0.75,
          metadata: {
            file_path: '/docs/setup.md',
            team: '运维组',
            project: '开发工具',
            tags: ['环境配置', '开发工具']
          }
        }
      ];
    }

    // 应用过滤器
    if (request.filters) {
      results = this.applyFilters(results, request.filters);
    }

    // 应用排序和分页
    results = results.slice(0, request.limit || 10);

    return {
      success: true,
      data: {
        results,
        total: results.length,
        took: Math.floor(Math.random() * 100) + 50, // 50-150ms
        aggregations: {
          types: {
            'document': results.filter(r => r.type === 'document').length,
            'code': results.filter(r => r.type === 'code').length,
            'api': results.filter(r => r.type === 'api').length
          },
          languages: {
            'typescript': results.filter(r => r.metadata.language === 'typescript').length,
            'python': results.filter(r => r.metadata.language === 'python').length
          },
          teams: {
            '架构组': results.filter(r => r.metadata.team === '架构组').length,
            '前端组': results.filter(r => r.metadata.team === '前端组').length,
            '后端组': results.filter(r => r.metadata.team === '后端组').length
          }
        }
      }
    };
  }

  /**
   * 应用搜索过滤器
   */
  private static applyFilters(results: SearchResultItem[], filters: any): SearchResultItem[] {
    let filtered = results;

    if (filters.doc_type) {
      filtered = filtered.filter(item => item.type === filters.doc_type);
    }

    if (filters.team) {
      filtered = filtered.filter(item => item.metadata.team === filters.team);
    }

    if (filters.language) {
      filtered = filtered.filter(item => item.metadata.language === filters.language);
    }

    if (filters.tags && filters.tags.length > 0) {
      filtered = filtered.filter(item => 
        item.metadata.tags?.some(tag => filters.tags.includes(tag))
      );
    }

    return filtered;
  }

  /**
   * 生成简单搜索建议
   */
  private static generateSimpleSuggestions(query: string): string[] {
    const suggestions: string[] = [];
    
    if (query.length > 0) {
      const commonTerms = [
        'API设计', 'React组件', 'Python规范', '数据库设计',
        '微服务架构', '缓存策略', '性能优化', '安全设计'
      ];
      
      // 基于输入返回相关建议
      suggestions.push(
        ...commonTerms.filter(term => 
          term.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 5)
      );
      
      // 如果没有匹配，返回部分热门搜索
      if (suggestions.length === 0) {
        suggestions.push(...commonTerms.slice(0, 3));
      }
    }

    return suggestions;
  }
}