/**
 * 智能推荐工具
 * 
 * 提供基于 AI 的智能推荐功能：
 * 1. 相似代码推荐
 * 2. 最佳实践建议
 * 3. 相关文档推荐
 * 4. 架构模式建议
 */

import { RagService } from '../services/rag-service.js';
import { logger } from '../utils/logger.js';

export interface RecommendationParams {
  context: string;
  context_type: 'code' | 'requirement' | 'architecture' | 'debug';
  language?: string;
  limit?: number;
}

export interface BestPracticeParams {
  scenario: string;
  language?: string;
  category?: string;
}

export interface Recommendation {
  type: 'code' | 'document' | 'pattern' | 'practice';
  title: string;
  content: string;
  relevance_score: number;
  reason: string;
  source?: string;
  metadata?: any;
}

export class SmartRecommendationsService {
  private ragService: RagService;

  constructor() {
    this.ragService = new RagService();
  }

  /**
   * 推荐相似代码
   */
  async recommendSimilarCode(params: RecommendationParams): Promise<Recommendation[]> {
    logger.info('推荐相似代码:', { context_type: params.context_type });

    try {
      // 根据上下文类型构建查询
      const query = this.buildQueryFromContext(params.context, params.context_type);
      
      // 搜索相关代码
      const codeResults = await this.ragService.searchCodeExamples({
        query,
        language: params.language as any,
        limit: params.limit || 5
      });

      // 转换为推荐格式
      const recommendations: Recommendation[] = codeResults.map((result: any, index: number) => ({
        type: 'code' as const,
        title: result.title || `代码示例 ${index + 1}`,
        content: result.code || result.content || '',
        relevance_score: result.score || (1 - index * 0.1),
        reason: this.generateRecommendationReason(result, params.context_type),
        source: result.file_path || result.source,
        metadata: {
          language: result.language,
          framework: result.framework,
          best_practices: result.best_practices
        }
      }));

      return recommendations;
    } catch (error) {
      logger.error('推荐相似代码失败:', error);
      return [];
    }
  }

  /**
   * 建议最佳实践
   */
  async suggestBestPractices(params: BestPracticeParams): Promise<Recommendation[]> {
    logger.info('建议最佳实践:', { scenario: params.scenario });

    try {
      // 构建最佳实践查询
      const query = `${params.scenario} best practices ${params.language || ''} ${params.category || ''}`.trim();
      
      // 搜索编码规范
      const standards = await this.ragService.getCodingStandards({
        language: params.language as any || 'python',
        category: params.category as any
      });

      // 搜索相关文档
      const docs = await this.ragService.getDesignDocs({
        query,
        doc_type: 'business_logic'
      });

      const recommendations: Recommendation[] = [];

      // 从编码规范生成推荐
      if (standards.best_practices) {
        standards.best_practices.forEach((practice: string, index: number) => {
          recommendations.push({
            type: 'practice',
            title: `最佳实践 ${index + 1}`,
            content: practice,
            relevance_score: 0.9 - index * 0.05,
            reason: `${params.language || ''} 编码规范推荐`,
            source: 'coding_standards',
            metadata: {
              category: params.category,
              language: params.language
            }
          });
        });
      }

      // 从文档生成推荐
      docs.slice(0, 3).forEach((doc: any, index: number) => {
        recommendations.push({
          type: 'document',
          title: doc.title || `相关文档 ${index + 1}`,
          content: doc.content?.substring(0, 300) || '',
          relevance_score: 0.8 - index * 0.1,
          reason: '相关设计文档建议',
          source: doc.source,
          metadata: doc
        });
      });

      return recommendations.sort((a, b) => b.relevance_score - a.relevance_score);
    } catch (error) {
      logger.error('建议最佳实践失败:', error);
      return [];
    }
  }

  /**
   * 推荐相关文档
   */
  async recommendRelatedDocs(params: {
    entity_name: string;
    doc_types?: string[];
    limit?: number;
  }): Promise<Recommendation[]> {
    logger.info('推荐相关文档:', { entity: params.entity_name });

    try {
      // 查询实体的知识图谱信息
      const entity = await this.ragService.queryEntity(params.entity_name);
      const relatedEntities = await this.ragService.findRelatedEntities(
        params.entity_name,
        2
      );

      // 构建查询词
      const queryTerms = [
        params.entity_name,
        ...relatedEntities.map((e: any) => e.name)
      ].join(' ');

      // 搜索相关文档
      const docs = await this.ragService.getDesignDocs({
        query: queryTerms
      });

      // 转换为推荐格式
      const recommendations: Recommendation[] = docs
        .slice(0, params.limit || 5)
        .map((doc: any, index: number) => ({
          type: 'document' as const,
          title: doc.title || `文档 ${index + 1}`,
          content: doc.content?.substring(0, 500) || '',
          relevance_score: 0.85 - index * 0.08,
          reason: `与 ${params.entity_name} 相关的设计文档`,
          source: doc.source,
          metadata: {
            doc_type: doc.doc_type,
            team: doc.team,
            project: doc.project
          }
        }));

      return recommendations;
    } catch (error) {
      logger.error('推荐相关文档失败:', error);
      return [];
    }
  }

  /**
   * 建议架构模式
   */
  async suggestArchitecturePatterns(params: {
    requirement: string;
    constraints?: string[];
    tech_stack?: string[];
  }): Promise<Recommendation[]> {
    logger.info('建议架构模式:', { requirement: params.requirement });

    try {
      // 搜索架构相关文档
      const query = `${params.requirement} architecture ${params.tech_stack?.join(' ') || ''}`.trim();
      
      const architectureDocs = await this.ragService.getDesignDocs({
        query,
        doc_type: 'architecture'
      });

      // 获取设计模式
      const patterns = await this.ragService.getDesignPatterns();

      const recommendations: Recommendation[] = [];

      // 从架构文档生成推荐
      architectureDocs.slice(0, 3).forEach((doc: any, index: number) => {
        recommendations.push({
          type: 'pattern',
          title: doc.title || `架构模式 ${index + 1}`,
          content: doc.content?.substring(0, 400) || '',
          relevance_score: 0.9 - index * 0.1,
          reason: this.matchPatternReason(doc, params.requirement),
          source: doc.source,
          metadata: {
            constraints_match: this.checkConstraintsMatch(doc, params.constraints),
            tech_stack_match: this.checkTechStackMatch(doc, params.tech_stack)
          }
        });
      });

      // 从设计模式生成推荐
      if (Array.isArray(patterns) && patterns.length > 0) {
        patterns.slice(0, 3).forEach((pattern: any, index: number) => {
          recommendations.push({
            type: 'pattern',
            title: pattern.name || `设计模式 ${index + 1}`,
            content: pattern.description || '',
            relevance_score: 0.75 - index * 0.05,
            reason: '常用设计模式',
            source: 'design_patterns',
            metadata: pattern
          });
        });
      }

      return recommendations.sort((a, b) => b.relevance_score - a.relevance_score);
    } catch (error) {
      logger.error('建议架构模式失败:', error);
      return [];
    }
  }

  /**
   * 智能代码补全建议
   */
  async suggestCodeCompletion(params: {
    code_context: string;
    cursor_position?: number;
    language: string;
  }): Promise<Recommendation[]> {
    logger.info('智能代码补全建议:', { language: params.language });

    try {
      // 分析代码上下文
      const contextAnalysis = this.analyzeCodeContext(
        params.code_context,
        params.language
      );

      // 搜索相似代码片段
      const similarCode = await this.ragService.searchCodeExamples({
        query: contextAnalysis.intent || params.code_context.substring(0, 100),
        language: params.language as any,
        limit: 5
      });

      // 生成补全建议
      const recommendations: Recommendation[] = similarCode.map((result: any, index: number) => ({
        type: 'code' as const,
        title: `补全建议 ${index + 1}`,
        content: this.extractRelevantSnippet(result.code, contextAnalysis),
        relevance_score: 0.8 - index * 0.1,
        reason: contextAnalysis.reason || '基于相似代码模式',
        source: result.file_path,
        metadata: {
          full_example: result.code,
          context_match: contextAnalysis
        }
      }));

      return recommendations;
    } catch (error) {
      logger.error('智能代码补全建议失败:', error);
      return [];
    }
  }

  /**
   * 从上下文构建查询
   */
  private buildQueryFromContext(context: string, contextType: string): string {
    switch (contextType) {
      case 'code':
        return `implement function like: ${context.substring(0, 100)}`;
      case 'requirement':
        return `code example for: ${context}`;
      case 'architecture':
        return `architecture pattern for: ${context}`;
      case 'debug':
        return `solution for: ${context}`;
      default:
        return context;
    }
  }

  /**
   * 生成推荐理由
   */
  private generateRecommendationReason(result: any, contextType: string): string {
    const reasons: Record<string, string> = {
      code: '基于代码模式匹配',
      requirement: '满足功能需求',
      architecture: '符合架构设计',
      debug: '可能的解决方案'
    };

    let reason = reasons[contextType] || '相关推荐';
    
    if (result.usage_context) {
      reason += ` - ${result.usage_context}`;
    }
    
    return reason;
  }

  /**
   * 匹配模式理由
   */
  private matchPatternReason(doc: any, requirement: string): string {
    // 简单的关键词匹配
    const keywords = requirement.toLowerCase().split(' ');
    const docContent = (doc.content || '').toLowerCase();
    
    const matchedKeywords = keywords.filter(kw => 
      kw.length > 3 && docContent.includes(kw)
    );

    if (matchedKeywords.length > 0) {
      return `匹配关键词: ${matchedKeywords.join(', ')}`;
    }
    
    return '架构模式推荐';
  }

  /**
   * 检查约束匹配
   */
  private checkConstraintsMatch(doc: any, constraints?: string[]): boolean {
    if (!constraints || constraints.length === 0) return true;
    
    const docContent = (doc.content || '').toLowerCase();
    return constraints.some(constraint => 
      docContent.includes(constraint.toLowerCase())
    );
  }

  /**
   * 检查技术栈匹配
   */
  private checkTechStackMatch(doc: any, techStack?: string[]): boolean {
    if (!techStack || techStack.length === 0) return true;
    
    const docContent = (doc.content || '').toLowerCase();
    return techStack.some(tech => 
      docContent.includes(tech.toLowerCase())
    );
  }

  /**
   * 分析代码上下文
   */
  private analyzeCodeContext(code: string, language: string): any {
    // 简单的上下文分析
    const lines = code.split('\n');
    const lastLine = lines[lines.length - 1] || '';
    
    // 检测常见模式
    if (lastLine.includes('def ') || lastLine.includes('function ')) {
      return {
        intent: 'function definition',
        reason: '函数定义模式'
      };
    }
    
    if (lastLine.includes('class ')) {
      return {
        intent: 'class definition',
        reason: '类定义模式'
      };
    }
    
    if (lastLine.includes('import ') || lastLine.includes('from ')) {
      return {
        intent: 'import statement',
        reason: '导入语句'
      };
    }
    
    return {
      intent: 'general code',
      reason: '通用代码补全'
    };
  }

  /**
   * 提取相关代码片段
   */
  private extractRelevantSnippet(code: string, context: any): string {
    // 简单提取：返回前10行
    const lines = code.split('\n').slice(0, 10);
    return lines.join('\n');
  }
}

// 导出单例
export const smartRecommendations = new SmartRecommendationsService();
