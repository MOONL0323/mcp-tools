/**
 * AI上下文增强MCP服务器
 * 
 * 这是一个基于Model Context Protocol (MCP)的服务器实现，
 * 为AI Agent提供团队知识库的上下文增强能力。
 * 
 * 主要功能：
 * 1. 搜索团队代码示例
 * 2. 获取设计文档上下文
 * 3. 查询编码规范和最佳实践
 * 4. 提供知识图谱检索能力
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { config } from './config/config.js';
import { logger } from './utils/logger.js';
import { RagService } from './services/rag-service.js';
import { CacheService } from './services/cache-service.js';
import { ValidatorService } from './services/validator-service.js';
import { 
  SearchCodeExamplesParams, 
  GetDesignDocsParams, 
  GetCodingStandardsParams,
  QueryKnowledgeGraphParams 
} from './types/tool-params.js';

class TeamContextMCPServer {
  private server: Server;
  private ragService: RagService;
  private cacheService: CacheService;
  private validatorService: ValidatorService;

  constructor() {
    this.server = new Server(
      {
        name: config.serverName,
        version: config.serverVersion,
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    this.ragService = new RagService();
    this.cacheService = new CacheService();
    this.validatorService = new ValidatorService();

    this.setupToolHandlers();
    this.setupResourceHandlers();
    this.setupErrorHandlers();
  }

  /**
   * 设置工具处理器
   */
  private setupToolHandlers(): void {
    // 列出可用工具
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_code_examples',
            description: '搜索团队代码示例和最佳实践',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: '搜索查询，描述需要的功能或代码模式'
                },
                language: {
                  type: 'string',
                  enum: ['python', 'typescript', 'javascript', 'java', 'go', 'cpp'],
                  description: '编程语言'
                },
                framework: {
                  type: 'string',
                  description: '框架名称，如fastapi、react、express等'
                },
                limit: {
                  type: 'number',
                  default: 5,
                  minimum: 1,
                  maximum: 20,
                  description: '返回结果数量限制'
                }
              },
              required: ['query']
            }
          },
          {
            name: 'get_design_docs',
            description: '获取相关的设计文档和架构说明',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: '查询描述，如功能模块、架构组件等'
                },
                doc_type: {
                  type: 'string',
                  enum: ['api_design', 'architecture', 'database_design', 'business_logic'],
                  description: '文档类型'
                },
                team: {
                  type: 'string',
                  description: '团队名称'
                },
                project: {
                  type: 'string',
                  description: '项目名称'
                }
              },
              required: ['query']
            }
          },
          {
            name: 'get_coding_standards',
            description: '获取团队编码规范和代码风格指南',
            inputSchema: {
              type: 'object',
              properties: {
                language: {
                  type: 'string',
                  enum: ['python', 'typescript', 'javascript', 'java', 'go', 'cpp'],
                  description: '编程语言'
                },
                category: {
                  type: 'string',
                  enum: ['naming', 'structure', 'testing', 'documentation', 'security'],
                  description: '规范类别'
                }
              },
              required: ['language']
            }
          },
          {
            name: 'query_knowledge_graph',
            description: '查询知识图谱中的实体关系和语义信息',
            inputSchema: {
              type: 'object',
              properties: {
                entity: {
                  type: 'string',
                  description: '要查询的实体名称'
                },
                relation_type: {
                  type: 'string',
                  enum: ['CALLS', 'INHERITS', 'USES', 'DEPENDS_ON', 'IMPLEMENTS'],
                  description: '关系类型'
                },
                depth: {
                  type: 'number',
                  default: 2,
                  minimum: 1,
                  maximum: 5,
                  description: '查询深度'
                }
              },
              required: ['entity']
            }
          }
        ]
      };
    });

    // 处理工具调用
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        logger.info(`执行工具: ${name}`, { args });

        switch (name) {
          case 'search_code_examples':
            return await this.handleSearchCodeExamples(args as unknown as SearchCodeExamplesParams);
          
          case 'get_design_docs':
            return await this.handleGetDesignDocs(args as unknown as GetDesignDocsParams);
          
          case 'get_coding_standards':
            return await this.handleGetCodingStandards(args as unknown as GetCodingStandardsParams);
          
          case 'query_knowledge_graph':
            return await this.handleQueryKnowledgeGraph(args as unknown as QueryKnowledgeGraphParams);
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `未知工具: ${name}`
            );
        }
      } catch (error) {
        logger.error('工具执行失败:', error);
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `工具执行失败: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    });
  }

  /**
   * 设置资源处理器
   */
  private setupResourceHandlers(): void {
    // 列出可用资源
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: 'context://team-knowledge-base',
            name: '团队知识库',
            description: '包含团队所有文档、代码示例和最佳实践的知识库',
            mimeType: 'application/json'
          },
          {
            uri: 'context://coding-standards',
            name: '编码规范',
            description: '团队编码规范和代码风格指南',
            mimeType: 'text/markdown'
          },
          {
            uri: 'context://design-patterns',
            name: '设计模式',
            description: '团队常用的设计模式和架构实践',
            mimeType: 'application/json'
          }
        ]
      };
    });

    // 读取资源内容
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      
      try {
        logger.info(`读取资源: ${uri}`);

        switch (uri) {
          case 'context://team-knowledge-base':
            return await this.getTeamKnowledgeBase();
          
          case 'context://coding-standards':
            return await this.getCodingStandardsResource();
          
          case 'context://design-patterns':
            return await this.getDesignPatternsResource();
          
          default:
            throw new McpError(
              ErrorCode.InvalidRequest,
              `未知资源: ${uri}`
            );
        }
      } catch (error) {
        logger.error('资源读取失败:', error);
        throw new McpError(
          ErrorCode.InternalError,
          `资源读取失败: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    });
  }

  /**
   * 设置错误处理器
   */
  private setupErrorHandlers(): void {
    this.server.onerror = (error) => {
      logger.error('MCP服务器错误:', error);
    };

    process.on('SIGINT', async () => {
      logger.info('接收到SIGINT信号，正在关闭服务器...');
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * 处理代码示例搜索
   */
  private async handleSearchCodeExamples(params: SearchCodeExamplesParams) {
    const cacheKey = `code_examples:${JSON.stringify(params)}`;
    const cached = this.cacheService.get(cacheKey);
    
    if (cached) {
      logger.info('返回缓存的代码示例');
      return cached;
    }

    // 验证参数
    this.validatorService.validateSearchParams(params);

    const results = await this.ragService.searchCodeExamples(params);
    
    const response = {
      content: [
        {
          type: 'text' as const,
          text: this.formatCodeExamplesResponse(results, params)
        }
      ]
    };

    this.cacheService.set(cacheKey, response);
    return response;
  }

  /**
   * 处理设计文档获取
   */
  private async handleGetDesignDocs(params: GetDesignDocsParams) {
    const cacheKey = `design_docs:${JSON.stringify(params)}`;
    const cached = this.cacheService.get(cacheKey);
    
    if (cached) {
      logger.info('返回缓存的设计文档');
      return cached;
    }

    const results = await this.ragService.getDesignDocs(params);
    
    const response = {
      content: [
        {
          type: 'text' as const,
          text: this.formatDesignDocsResponse(results, params)
        }
      ]
    };

    this.cacheService.set(cacheKey, response);
    return response;
  }

  /**
   * 处理编码规范获取
   */
  private async handleGetCodingStandards(params: GetCodingStandardsParams) {
    const cacheKey = `coding_standards:${JSON.stringify(params)}`;
    const cached = this.cacheService.get(cacheKey);
    
    if (cached) {
      logger.info('返回缓存的编码规范');
      return cached;
    }

    const results = await this.ragService.getCodingStandards(params);
    
    const response = {
      content: [
        {
          type: 'text' as const,
          text: this.formatCodingStandardsResponse(results, params)
        }
      ]
    };

    this.cacheService.set(cacheKey, response);
    return response;
  }

  /**
   * 处理知识图谱查询
   */
  private async handleQueryKnowledgeGraph(params: QueryKnowledgeGraphParams) {
    const cacheKey = `knowledge_graph:${JSON.stringify(params)}`;
    const cached = this.cacheService.get(cacheKey);
    
    if (cached) {
      logger.info('返回缓存的知识图谱查询结果');
      return cached;
    }

    const results = await this.ragService.queryKnowledgeGraph(params);
    
    const response = {
      content: [
        {
          type: 'text' as const,
          text: this.formatKnowledgeGraphResponse(results, params)
        }
      ]
    };

    this.cacheService.set(cacheKey, response);
    return response;
  }

  /**
   * 格式化代码示例响应
   */
  private formatCodeExamplesResponse(results: any[], params: SearchCodeExamplesParams): string {
    if (!results.length) {
      return `没有找到与 "${params.query}" 相关的${params.language || ''}代码示例。`;
    }

    let response = `## 🔍 代码示例搜索结果\n\n`;
    response += `**查询**: ${params.query}\n`;
    if (params.language) response += `**语言**: ${params.language}\n`;
    if (params.framework) response += `**框架**: ${params.framework}\n`;
    response += `**找到**: ${results.length} 个相关示例\n\n`;

    results.forEach((result, index) => {
      response += `### ${index + 1}. ${result.title || '代码示例'}\n\n`;
      response += `**文件**: \`${result.file_path || '未知'}\`\n`;
      response += `**描述**: ${result.description || '无描述'}\n\n`;
      
      if (result.code) {
        response += '```' + (params.language || '') + '\n';
        response += result.code;
        response += '\n```\n\n';
      }
      
      if (result.usage_context) {
        response += `**使用场景**: ${result.usage_context}\n\n`;
      }
      
      if (result.best_practices?.length) {
        response += `**最佳实践**:\n`;
        result.best_practices.forEach((practice: string) => {
          response += `- ${practice}\n`;
        });
        response += '\n';
      }
      
      if (result.related_docs?.length) {
        response += `**相关文档**: ${result.related_docs.join(', ')}\n\n`;
      }
      
      response += '---\n\n';
    });

    return response;
  }

  /**
   * 格式化设计文档响应
   */
  private formatDesignDocsResponse(results: any[], params: GetDesignDocsParams): string {
    if (!results.length) {
      return `没有找到与 "${params.query}" 相关的设计文档。`;
    }

    let response = `## 📋 设计文档查询结果\n\n`;
    response += `**查询**: ${params.query}\n`;
    if (params.doc_type) response += `**类型**: ${params.doc_type}\n`;
    if (params.team) response += `**团队**: ${params.team}\n`;
    if (params.project) response += `**项目**: ${params.project}\n`;
    response += `**找到**: ${results.length} 个相关文档\n\n`;

    results.forEach((result, index) => {
      response += `### ${index + 1}. ${result.title}\n\n`;
      response += `**文档类型**: ${result.doc_type || '未分类'}\n`;
      response += `**团队**: ${result.team || '未知'}\n`;
      response += `**项目**: ${result.project || '未知'}\n`;
      response += `**模块**: ${result.module || '未知'}\n\n`;
      
      if (result.content) {
        // 截取前500字符作为预览
        const preview = result.content.length > 500 
          ? result.content.substring(0, 500) + '...'
          : result.content;
        response += `**内容预览**:\n${preview}\n\n`;
      }
      
      if (result.entities?.length) {
        response += `**相关实体**: ${result.entities.join(', ')}\n\n`;
      }
      
      response += '---\n\n';
    });

    return response;
  }

  /**
   * 格式化编码规范响应
   */
  private formatCodingStandardsResponse(results: any, params: GetCodingStandardsParams): string {
    let response = `## 📏 编码规范 - ${params.language.toUpperCase()}\n\n`;
    
    if (params.category) {
      response += `**类别**: ${params.category}\n\n`;
    }

    if (results.naming_conventions) {
      response += `### 命名规范\n\n`;
      Object.entries(results.naming_conventions).forEach(([key, value]) => {
        response += `- **${key}**: ${value}\n`;
      });
      response += '\n';
    }

    if (results.code_structure) {
      response += `### 代码结构\n\n`;
      Object.entries(results.code_structure).forEach(([key, value]) => {
        response += `- **${key}**: ${value}\n`;
      });
      response += '\n';
    }

    if (results.best_practices?.length) {
      response += `### 最佳实践\n\n`;
      results.best_practices.forEach((practice: string) => {
        response += `- ${practice}\n`;
      });
      response += '\n';
    }

    if (results.code_templates) {
      response += `### 代码模板\n\n`;
      Object.entries(results.code_templates).forEach(([name, template]) => {
        response += `#### ${name}\n\n`;
        response += '```' + params.language + '\n';
        response += template;
        response += '\n```\n\n';
      });
    }

    if (results.tools) {
      response += `### 推荐工具\n\n`;
      if (results.tools.formatters?.length) {
        response += `**格式化工具**: ${results.tools.formatters.join(', ')}\n`;
      }
      if (results.tools.linters?.length) {
        response += `**代码检查**: ${results.tools.linters.join(', ')}\n`;
      }
      if (results.tools.test_frameworks?.length) {
        response += `**测试框架**: ${results.tools.test_frameworks.join(', ')}\n`;
      }
    }

    return response;
  }

  /**
   * 格式化知识图谱响应
   */
  private formatKnowledgeGraphResponse(results: any, params: QueryKnowledgeGraphParams): string {
    let response = `## 🕸️ 知识图谱查询结果\n\n`;
    response += `**查询实体**: ${params.entity}\n`;
    if (params.relation_type) response += `**关系类型**: ${params.relation_type}\n`;
    response += `**查询深度**: ${params.depth || 2}\n\n`;

    if (results.entity_info) {
      response += `### 实体信息\n\n`;
      response += `- **名称**: ${results.entity_info.name}\n`;
      response += `- **类型**: ${results.entity_info.type}\n`;
      if (results.entity_info.description) {
        response += `- **描述**: ${results.entity_info.description}\n`;
      }
      response += '\n';
    }

    if (results.relationships?.length) {
      response += `### 关系网络\n\n`;
      results.relationships.forEach((rel: any, index: number) => {
        response += `${index + 1}. ${rel.source} **${rel.type}** ${rel.target}\n`;
        if (rel.description) {
          response += `   *${rel.description}*\n`;
        }
      });
      response += '\n';
    }

    if (results.related_entities?.length) {
      response += `### 相关实体\n\n`;
      results.related_entities.forEach((entity: any) => {
        response += `- **${entity.name}** (${entity.type})`;
        if (entity.distance) {
          response += ` - 距离: ${entity.distance}`;
        }
        response += '\n';
      });
      response += '\n';
    }

    if (results.usage_examples?.length) {
      response += `### 使用示例\n\n`;
      results.usage_examples.forEach((example: any, index: number) => {
        response += `#### 示例 ${index + 1}\n\n`;
        response += `**场景**: ${example.context}\n\n`;
        if (example.code) {
          response += '```' + (example.language || '') + '\n';
          response += example.code;
          response += '\n```\n\n';
        }
      });
    }

    return response;
  }

  /**
   * 获取团队知识库资源
   */
  private async getTeamKnowledgeBase() {
    const stats = await this.ragService.getKnowledgeBaseStats();
    
    return {
      contents: [
        {
          uri: 'context://team-knowledge-base',
          mimeType: 'application/json',
          text: JSON.stringify({
            summary: '团队知识库概览',
            statistics: stats,
            last_updated: new Date().toISOString(),
            capabilities: [
              '代码示例搜索',
              '设计文档查询',
              '编码规范获取',
              '知识图谱遍历'
            ]
          }, null, 2)
        }
      ]
    };
  }

  /**
   * 获取编码规范资源
   */
  private async getCodingStandardsResource() {
    const standards = await this.ragService.getAllCodingStandards();
    
    let content = '# 团队编码规范\n\n';
    content += '本文档包含团队的编码规范和最佳实践。\n\n';
    
    Object.entries(standards).forEach(([language, rules]) => {
      content += `## ${language.toUpperCase()}\n\n`;
      content += JSON.stringify(rules, null, 2);
      content += '\n\n';
    });

    return {
      contents: [
        {
          uri: 'context://coding-standards',
          mimeType: 'text/markdown',
          text: content
        }
      ]
    };
  }

  /**
   * 获取设计模式资源
   */
  private async getDesignPatternsResource() {
    const patterns = await this.ragService.getDesignPatterns();
    
    return {
      contents: [
        {
          uri: 'context://design-patterns',
          mimeType: 'application/json',
          text: JSON.stringify({
            patterns: patterns,
            categories: ['创建型模式', '结构型模式', '行为型模式'],
            usage_guidelines: '根据具体场景选择合适的设计模式'
          }, null, 2)
        }
      ]
    };
  }

  /**
   * 启动MCP服务器
   */
  async start(): Promise<void> {
    const transport = new StdioServerTransport();
    
    logger.info(`启动 ${config.serverName} v${config.serverVersion}`);
    logger.info('连接RAG引擎:', config.ragEngineUrl);
    
    await this.server.connect(transport);
    logger.info('MCP服务器已启动，等待连接...');
  }

  /**
   * 关闭服务器
   */
  async stop(): Promise<void> {
    await this.server.close();
    logger.info('MCP服务器已关闭');
  }
}

export { TeamContextMCPServer };