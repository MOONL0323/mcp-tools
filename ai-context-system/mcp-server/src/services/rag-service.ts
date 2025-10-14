/**
 * RAG服务 - 与后端Graph RAG引擎通信
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { config } from '../config/config.js';
import { logger } from '../utils/logger.js';
import {
  SearchCodeExamplesParams,
  GetDesignDocsParams, 
  GetCodingStandardsParams,
  QueryKnowledgeGraphParams,
  RagSearchResult,
  GraphQueryResult,
  CodingStandardsResult,
  KnowledgeBaseStats,
  ApiResponse
} from '../types/tool-params.js';

export class RagService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.ragEngineUrl,
      timeout: config.ragEngineTimeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': `${config.serverName}/${config.serverVersion}`
      }
    });

    // 请求拦截器 - 添加日志
    this.client.interceptors.request.use(
      (config) => {
        logger.debug(`发送API请求: ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data
        });
        return config;
      },
      (error) => {
        logger.error('API请求失败:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器 - 处理响应和错误
    this.client.interceptors.response.use(
      (response) => {
        logger.debug(`收到API响应: ${response.status} ${response.config.url}`, {
          data: response.data
        });
        return response;
      },
      (error) => {
        logger.error('API响应错误:', {
          status: error.response?.status,
          message: error.message,
          data: error.response?.data
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * 搜索代码示例
   */
  async searchCodeExamples(params: SearchCodeExamplesParams): Promise<RagSearchResult[]> {
    try {
      logger.info('搜索代码示例:', params);

      const response = await this.client.post<ApiResponse<RagSearchResult[]>>('/api/v1/docs/search', {
        query: params.query,
        filters: {
          doc_type: 'demo_code',
          language: params.language,
          framework: params.framework
        },
        limit: params.limit || 5,
        search_type: 'hybrid' // 混合搜索：向量+关键词
      });

      if (!response.data.success) {
        throw new Error(response.data.message || '搜索失败');
      }

      return response.data.data || [];
    } catch (error) {
      logger.error('搜索代码示例失败:', error);
      throw new Error(`搜索代码示例失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 获取设计文档
   */
  async getDesignDocs(params: GetDesignDocsParams): Promise<RagSearchResult[]> {
    try {
      logger.info('获取设计文档:', params);

      // 首先尝试使用专门的设计文档API
      try {
        const designDocResponse = await this.client.post<ApiResponse<any>>('/api/v1/design/design-docs', {
          topic: params.query,
          component: params.component,
          team: params.team,
          doc_type: params.doc_type
        });

        if (designDocResponse.data.success && designDocResponse.data.data.length > 0) {
          // 转换设计文档格式为RAG搜索结果格式
          const designResults: RagSearchResult[] = designDocResponse.data.data.map((doc: any) => ({
            id: doc.id,
            title: doc.title,
            content: doc.content,
            description: doc.summary || `${doc.document_type}文档`,
            score: 0.95, // 设计文档API的结果给高分
            metadata: {
              doc_type: doc.document_type,
              team: doc.team,
              project: doc.project,
              tags: doc.tags
            }
          }));
          
          logger.info(`通过设计文档API获取到 ${designResults.length} 个结果`);
          return designResults;
        }
      } catch (designDocError) {
        logger.warn('设计文档API调用失败，降级到通用搜索:', designDocError);
      }

      // 降级到通用文档搜索
      const response = await this.client.post<ApiResponse<RagSearchResult[]>>('/api/v1/docs/search', {
        query: params.query,
        filters: {
          doc_type: 'business_doc',
          dev_type: params.doc_type,
          team: params.team,
          project: params.project
        },
        limit: 10,
        search_type: 'semantic' // 语义搜索
      });

      if (!response.data.success) {
        throw new Error(response.data.message || '获取设计文档失败');
      }

      return response.data.data || [];
    } catch (error) {
      logger.error('获取设计文档失败:', error);
      throw new Error(`获取设计文档失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 获取编码规范
   */
  async getCodingStandards(params: GetCodingStandardsParams): Promise<CodingStandardsResult> {
    try {
      logger.info('获取编码规范:', params);

      // 首先尝试使用专门的编码规范API
      try {
        const standardsResponse = await this.client.get<ApiResponse<any>>(`/api/v1/mcp/coding-standards/${params.language}`, {
          params: {
            category: params.category
          }
        });

        if (standardsResponse.data.success) {
          const standardsData = standardsResponse.data.data;
          logger.info(`通过编码规范API获取到 ${params.language} 规范`);
          
          return {
            language: standardsData.language,
            naming_conventions: standardsData.naming_conventions,
            code_structure: standardsData.code_structure,
            best_practices: standardsData.best_practices || [],
            code_templates: standardsData.code_templates || {},
            linting_rules: standardsData.linting_rules || {},
            testing_guidelines: standardsData.testing_guidelines || [],
            tools: standardsData.tools || {
              formatters: [],
              linters: [],
              test_frameworks: []
            }
          };
        }
      } catch (standardsError) {
        logger.warn('编码规范API调用失败，降级到文档搜索:', standardsError);
      }

      // 降级到文档搜索
      const response = await this.client.post<ApiResponse<RagSearchResult[]>>('/api/v1/docs/search', {
        query: `${params.language} coding standards ${params.category || ''}`,
        filters: {
          doc_type: 'business_doc',
          tags: ['coding-standards', 'best-practices', params.language]
        },
        limit: 5,
        search_type: 'hybrid'
      });

      if (!response.data.success) {
        throw new Error(response.data.message || '获取编码规范失败');
      }

      // 将搜索结果转换为编码规范格式
      const docs = response.data.data || [];
      return this.parseStandardsFromDocs(docs, params.language);
    } catch (error) {
      logger.error('获取编码规范失败:', error);
      throw new Error(`获取编码规范失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 查询知识图谱
   */
  async queryKnowledgeGraph(params: QueryKnowledgeGraphParams): Promise<GraphQueryResult> {
    try {
      logger.info('查询知识图谱:', params);

      // 首先尝试使用专门的知识图谱API
      try {
        const graphResponse = await this.client.post<ApiResponse<any>>('/api/v1/mcp/graph/query', {
          entity: params.entity,
          relation_type: params.relation_type,
          depth: params.depth || 2,
          include_examples: true
        });

        if (graphResponse.data.success) {
          const graphData = graphResponse.data.data;
          logger.info(`通过知识图谱API获取到实体 ${params.entity} 的信息`);
          
          return {
            entity_info: graphData.entity_info || {
              id: params.entity,
              name: params.entity,
              type: 'unknown',
              properties: {}
            },
            relationships: graphData.relationships || [],
            related_entities: graphData.related_entities || [],
            usage_examples: graphData.usage_examples || []
          };
        }
      } catch (graphError) {
        logger.warn('知识图谱API调用失败，降级到通用查询:', graphError);
      }

      // 降级到通用图谱查询
      const response = await this.client.post<ApiResponse<GraphQueryResult>>('/api/v1/graph/query', {
        entity: params.entity,
        relation_type: params.relation_type,
        depth: params.depth || 2,
        include_examples: true
      });

      if (!response.data.success) {
        throw new Error(response.data.message || '图谱查询失败');
      }

      return response.data.data || {
        entity_info: { id: '', name: params.entity, type: 'unknown', properties: {} },
        relationships: [],
        related_entities: [],
        usage_examples: []
      };
    } catch (error) {
      logger.error('查询知识图谱失败:', error);
      throw new Error(`查询知识图谱失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 获取知识库统计
   */
  async getKnowledgeBaseStats(): Promise<KnowledgeBaseStats> {
    try {
      logger.info('获取知识库统计');

      const response = await this.client.get<ApiResponse<KnowledgeBaseStats>>('/api/v1/stats/knowledge-base');

      if (!response.data.success) {
        throw new Error(response.data.message || '获取统计失败');
      }

      return response.data.data || {
        total_documents: 0,
        total_chunks: 0,
        total_entities: 0,
        total_relations: 0,
        languages: [],
        teams: [],
        projects: [],
        last_updated: new Date().toISOString()
      };
    } catch (error) {
      logger.error('获取知识库统计失败:', error);
      throw new Error(`获取知识库统计失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 获取所有编码规范
   */
  async getAllCodingStandards(): Promise<Record<string, CodingStandardsResult>> {
    try {
      logger.info('获取所有编码规范');

      const languages = ['python', 'typescript', 'javascript', 'java', 'go', 'cpp'];
      const results: Record<string, CodingStandardsResult> = {};

      // 并发获取各语言的编码规范
      const promises = languages.map(async (language) => {
        try {
          const standards = await this.getCodingStandards({ 
            language: language as any 
          });
          results[language] = standards;
        } catch (error) {
          logger.warn(`获取 ${language} 编码规范失败:`, error);
          // 返回默认规范
          results[language] = this.getDefaultStandards(language);
        }
      });

      await Promise.all(promises);
      return results;
    } catch (error) {
      logger.error('获取所有编码规范失败:', error);
      throw new Error(`获取所有编码规范失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 获取设计模式
   */
  async getDesignPatterns(): Promise<any[]> {
    try {
      logger.info('获取设计模式');

      const response = await this.client.post<ApiResponse<RagSearchResult[]>>('/api/v1/docs/search', {
        query: 'design patterns architecture',
        filters: {
          doc_type: 'business_doc',
          tags: ['design-patterns', 'architecture']
        },
        limit: 20,
        search_type: 'semantic'
      });

      if (!response.data.success) {
        throw new Error(response.data.message || '获取设计模式失败');
      }

      return this.parseDesignPatternsFromDocs(response.data.data || []);
    } catch (error) {
      logger.error('获取设计模式失败:', error);
      throw new Error(`获取设计模式失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 从文档中解析编码规范
   */
  private parseStandardsFromDocs(docs: RagSearchResult[], language: string): CodingStandardsResult {
    // 这里应该有更智能的解析逻辑，暂时返回基本结构
    const result: CodingStandardsResult = {
      language,
      naming_conventions: {},
      code_structure: {},
      best_practices: [],
      code_templates: {},
      linting_rules: {},
      testing_guidelines: [],
      tools: {
        formatters: [],
        linters: [],
        test_frameworks: []
      }
    };

    // 从文档内容中提取规范信息
    docs.forEach(doc => {
      // 简单的关键词提取 - 实际应用中可以使用更复杂的NLP
      if (doc.content.toLowerCase().includes('naming')) {
        result.naming_conventions[doc.title || 'general'] = doc.content.substring(0, 200);
      }
      
      if (doc.best_practices) {
        result.best_practices.push(...doc.best_practices);
      }
      
      if (doc.code) {
        result.code_templates[doc.title || 'template'] = doc.code;
      }
    });

    return result;
  }

  /**
   * 获取默认编码规范
   */
  private getDefaultStandards(language: string): CodingStandardsResult {
    const defaultStandards: Record<string, Partial<CodingStandardsResult>> = {
      python: {
        naming_conventions: {
          'variables': 'snake_case',
          'functions': 'snake_case', 
          'classes': 'PascalCase',
          'constants': 'UPPER_SNAKE_CASE'
        },
        best_practices: [
          '遵循PEP 8编码规范',
          '使用类型提示',
          '编写文档字符串',
          '保持函数简短和专一'
        ],
        tools: {
          formatters: ['black', 'autopep8'],
          linters: ['pylint', 'flake8', 'mypy'],
          test_frameworks: ['pytest', 'unittest']
        }
      },
      typescript: {
        naming_conventions: {
          'variables': 'camelCase',
          'functions': 'camelCase',
          'classes': 'PascalCase',
          'interfaces': 'PascalCase (I前缀)'
        },
        best_practices: [
          '启用严格类型检查',
          '使用明确的类型注解',
          '避免any类型',
          '使用枚举和联合类型'
        ],
        tools: {
          formatters: ['prettier'],
          linters: ['eslint', 'tslint'],
          test_frameworks: ['jest', 'mocha', 'vitest']
        }
      }
    };

    return {
      language,
      naming_conventions: {},
      code_structure: {},
      best_practices: [],
      code_templates: {},
      linting_rules: {},
      testing_guidelines: [],
      tools: { formatters: [], linters: [], test_frameworks: [] },
      ...defaultStandards[language]
    } as CodingStandardsResult;
  }

  /**
   * 从文档中解析设计模式
   */
  private parseDesignPatternsFromDocs(docs: RagSearchResult[]): any[] {
    return docs.map(doc => ({
      name: doc.title,
      description: doc.description || doc.content.substring(0, 200),
      category: this.categorizePattern(doc.title || ''),
      code_example: doc.code,
      usage_context: doc.usage_context,
      file_path: doc.file_path
    }));
  }

  /**
   * 分类设计模式
   */
  private categorizePattern(title: string): string {
    const creational = ['factory', 'builder', 'singleton', 'prototype'];
    const structural = ['adapter', 'bridge', 'composite', 'decorator', 'facade', 'proxy'];
    const behavioral = ['observer', 'strategy', 'command', 'iterator', 'mediator', 'state'];

    const lowerTitle = title.toLowerCase();
    
    if (creational.some(pattern => lowerTitle.includes(pattern))) {
      return '创建型模式';
    }
    if (structural.some(pattern => lowerTitle.includes(pattern))) {
      return '结构型模式';
    }
    if (behavioral.some(pattern => lowerTitle.includes(pattern))) {
      return '行为型模式';
    }
    
    return '其他模式';
  }

  /**
   * 查询知识图谱实体
   */
  async queryEntity(entityName: string): Promise<any> {
    try {
      logger.info('查询实体:', entityName);

      const response = await this.client.get<ApiResponse<any>>(
        `/api/v1/graph/entity/${encodeURIComponent(entityName)}`
      );

      if (!response.data.success && !response.data.data) {
        throw new Error(response.data.message || '查询实体失败');
      }

      return response.data.data || response.data || {};
    } catch (error) {
      logger.error('查询实体失败:', error);
      throw new Error(`查询实体失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 查找相关实体
   */
  async findRelatedEntities(entityName: string, depth: number = 2): Promise<any[]> {
    try {
      logger.info('查找相关实体:', { entity: entityName, depth });

      const response = await this.client.get<ApiResponse<any>>(
        `/api/v1/graph/related/${encodeURIComponent(entityName)}?max_depth=${depth}`
      );

      if (!response.data.success && !response.data.data) {
        throw new Error(response.data.message || '查找相关实体失败');
      }

      return response.data.data || [];
    } catch (error) {
      logger.error('查找相关实体失败:', error);
      return [];
    }
  }

  /**
   * 获取文档
   */
  async getDocument(documentId: number): Promise<any> {
    try {
      logger.info('获取文档:', documentId);

      const response = await this.client.get<ApiResponse<any>>(
        `/api/v1/documents/${documentId}`
      );

      if (!response.data.success) {
        throw new Error(response.data.message || '获取文档失败');
      }

      return response.data.data || response.data;
    } catch (error) {
      logger.error('获取文档失败:', error);
      throw new Error(`获取文档失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 从文档提取实体
   */
  async extractEntitiesFromDocument(documentId: number): Promise<any> {
    try {
      logger.info('从文档提取实体:', documentId);

      const response = await this.client.post<ApiResponse<any>>(
        `/api/v1/entities/extract-from-document/${documentId}`
      );

      if (!response.data.success) {
        throw new Error(response.data.message || '提取实体失败');
      }

      return response.data.data || response.data;
    } catch (error) {
      logger.error('从文档提取实体失败:', error);
      throw new Error(`提取实体失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }

  /**
   * 存储实体到知识图谱
   */
  async storeEntitiesToGraph(documentId: number, entities: any): Promise<any> {
    try {
      logger.info('存储实体到知识图谱:', documentId);

      const response = await this.client.post<ApiResponse<any>>(
        '/api/v1/graph/store-from-document/' + documentId
      );

      if (!response.data.success) {
        throw new Error(response.data.message || '存储实体失败');
      }

      return response.data.data || response.data;
    } catch (error) {
      logger.error('存储实体到知识图谱失败:', error);
      throw new Error(`存储实体失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  }
}