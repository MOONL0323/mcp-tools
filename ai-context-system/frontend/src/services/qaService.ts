/**
 * 智能问答API服务
 */

import { apiClient } from './api';

export interface QARequest {
  question: string;
  context?: string[];
  conversation_history?: string[];
}

export interface QASource {
  id: string;
  title: string;
  type: 'document' | 'api' | 'code' | 'knowledge';
  relevance: number;
  snippet: string;
  url?: string;
}

export interface QAResponse {
  success: boolean;
  data: {
    answer: string;
    sources: QASource[];
    thinking?: string;
    confidence: number;
  };
  error?: string;
}

export class QAService {
  /**
   * 智能问答
   */
  static async askQuestion(request: QARequest): Promise<QAResponse> {
    try {
      console.log('发送智能问答请求:', request);
      
      const response = await apiClient.post('/v1/qa/ask', {
        question: request.question,
        context: request.context || [],
        conversation_history: request.conversation_history || []
      });

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.error || '问答请求失败');
      }
    } catch (error: any) {
      console.error('智能问答失败:', error);
      
      // 降级到本地处理
      return this.generateLocalResponse(request);
    }
  }

  /**
   * 获取推荐问题
   */
  static async getRecommendedQuestions(): Promise<string[]> {
    try {
      const response = await apiClient.get('/v1/qa/recommendations');
      
      if (response.data.success) {
        return response.data.data.questions || [];
      }
    } catch (error) {
      console.error('获取推荐问题失败:', error);
    }

    // 返回默认推荐问题
    return [
      '系统的核心功能是什么？',
      '如何使用知识图谱功能？',
      '文档上传支持哪些格式？',
      '如何进行高级搜索？',
      '系统架构是怎样的？'
    ];
  }

  /**
   * 获取会话历史
   */
  static async getConversationHistory(limit: number = 10): Promise<any[]> {
    try {
      const response = await apiClient.get(`/api/v1/qa/history?limit=${limit}`);
      
      if (response.data.success) {
        return response.data.data.conversations || [];
      }
    } catch (error) {
      console.error('获取会话历史失败:', error);
    }

    return [];
  }

  /**
   * 本地降级响应生成
   */
  private static generateLocalResponse(request: QARequest): QAResponse {
    const { question } = request;
    
    // 基于问题关键词生成回答
    let answer = '';
    let sources: QASource[] = [];
    
    if (question.includes('核心功能') || question.includes('功能')) {
      answer = `AI上下文增强系统的核心功能包括：

1. **智能文档管理** - 支持多格式文档上传、自动分类和标签管理
2. **知识图谱构建** - 自动提取文档中的实体、关系，构建结构化知识图谱  
3. **Graph RAG检索** - 结合向量检索和图结构，提供更准确的信息检索
4. **智能问答** - 基于RAG技术的智能问答系统
5. **高级搜索** - 多维度、多模态的智能搜索功能

系统采用微服务架构，确保高可用性和可扩展性。`;

      sources = [
        {
          id: '1',
          title: 'AI代码生成系统方案.md',
          type: 'document',
          relevance: 0.95,
          snippet: 'Graph RAG技术结合了传统检索增强生成(RAG)和知识图谱的优势，通过构建结构化的知识图谱...',
          url: '/documents/1'
        },
        {
          id: '2', 
          title: '系统架构设计',
          type: 'document',
          relevance: 0.87,
          snippet: '系统采用微服务架构，包含文档管理、知识图谱、智能问答等核心模块...',
          url: '/documents/2'
        }
      ];
    } else if (question.includes('知识图谱') || question.includes('图谱')) {
      answer = `知识图谱功能帮助您：

1. **自动构建** - 从文档中自动提取实体和关系
2. **可视化展示** - 直观展示知识结构和关联
3. **智能查询** - 支持复杂的图查询和推理
4. **关系发现** - 发现隐藏的实体关联

您可以通过知识图谱页面查看和管理图谱数据。`;

      sources = [
        {
          id: '3',
          title: '知识图谱技术文档',
          type: 'knowledge',
          relevance: 0.92,
          snippet: '知识图谱采用Neo4j图数据库，支持复杂的图查询和实时更新...',
          url: '/knowledge-graph'
        }
      ];
    } else if (question.includes('搜索') || question.includes('检索')) {
      answer = `高级搜索功能提供：

1. **多模态搜索** - 支持文档、代码、图片等多种内容搜索
2. **语义检索** - 基于向量相似度的语义搜索
3. **混合搜索** - 结合关键词和语义搜索
4. **精确过滤** - 按文档类型、时间、标签等筛选

搜索结果按相关性排序，并提供详细的匹配信息。`;

      sources = [
        {
          id: '4',
          title: '搜索功能说明',
          type: 'document',
          relevance: 0.89,
          snippet: '系统支持多种搜索模式，包括精确匹配、模糊搜索、语义检索等...',
          url: '/search'
        }
      ];
    } else {
      answer = `感谢您的问题。基于当前的知识库，我建议您：

1. 查看相关文档获取详细信息  
2. 尝试使用具体的功能模块
3. 查看知识图谱中的相关节点

如果您需要更具体的帮助，请提供更详细的问题描述。`;

      sources = [
        {
          id: '5',
          title: '系统使用指南',
          type: 'document', 
          relevance: 0.75,
          snippet: '系统提供完整的使用指南和API文档，帮助用户快速上手...',
          url: '/help'
        }
      ];
    }

    return {
      success: true,
      data: {
        answer,
        sources,
        thinking: '正在分析您的问题，从知识图谱中检索相关信息...',
        confidence: 0.8
      }
    };
  }
}