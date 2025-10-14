/**
 * 批量操作工具
 * 
 * 提供高级批量处理功能：
 * 1. 批量文档分析和实体提取
 * 2. 批量搜索和聚合
 * 3. 批量知识图谱更新
 */

import { RagService } from '../services/rag-service.js';
import { logger } from '../utils/logger.js';

export interface BatchAnalyzeParams {
  document_ids: number[];
  operations: ('extract_entities' | 'update_graph' | 'generate_summary')[];
  options?: {
    parallel?: boolean;
    max_concurrent?: number;
  };
}

export interface BatchSearchParams {
  queries: string[];
  search_type?: 'code' | 'docs' | 'all';
  aggregate_results?: boolean;
  min_score?: number;
}

export interface BatchResult {
  total: number;
  successful: number;
  failed: number;
  results: any[];
  errors: Array<{ id: any; error: string }>;
}

export class BatchOperationsService {
  private ragService: RagService;

  constructor() {
    this.ragService = new RagService();
  }

  /**
   * 批量分析文档
   */
  async batchAnalyzeDocuments(params: BatchAnalyzeParams): Promise<BatchResult> {
    logger.info('批量分析文档:', {
      count: params.document_ids.length,
      operations: params.operations
    });

    const results: any[] = [];
    const errors: Array<{ id: any; error: string }> = [];
    let successful = 0;
    let failed = 0;

    const maxConcurrent = params.options?.max_concurrent || 5;
    const useParallel = params.options?.parallel !== false;

    if (useParallel) {
      // 并行处理（分批）
      for (let i = 0; i < params.document_ids.length; i += maxConcurrent) {
        const batch = params.document_ids.slice(i, i + maxConcurrent);
        const batchPromises = batch.map(docId => 
          this.analyzeDocument(docId, params.operations)
            .then(result => {
              successful++;
              results.push(result);
              return result;
            })
            .catch(error => {
              failed++;
              const errorMsg = error instanceof Error ? error.message : String(error);
              errors.push({ id: docId, error: errorMsg });
              logger.error(`文档 ${docId} 分析失败:`, error);
              return null;
            })
        );

        await Promise.all(batchPromises);
        
        // 进度日志
        logger.info(`批量分析进度: ${i + batch.length}/${params.document_ids.length}`);
      }
    } else {
      // 串行处理
      for (const docId of params.document_ids) {
        try {
          const result = await this.analyzeDocument(docId, params.operations);
          successful++;
          results.push(result);
        } catch (error) {
          failed++;
          const errorMsg = error instanceof Error ? error.message : String(error);
          errors.push({ id: docId, error: errorMsg });
          logger.error(`文档 ${docId} 分析失败:`, error);
        }
      }
    }

    return {
      total: params.document_ids.length,
      successful,
      failed,
      results: results.filter(r => r !== null),
      errors
    };
  }

  /**
   * 分析单个文档
   */
  private async analyzeDocument(
    documentId: number,
    operations: string[]
  ): Promise<any> {
    const result: any = {
      document_id: documentId,
      operations: {}
    };

    for (const operation of operations) {
      switch (operation) {
        case 'extract_entities':
          result.operations.entities = await this.extractDocumentEntities(documentId);
          break;
        
        case 'update_graph':
          result.operations.graph = await this.updateDocumentGraph(documentId);
          break;
        
        case 'generate_summary':
          result.operations.summary = await this.generateDocumentSummary(documentId);
          break;
        
        default:
          logger.warn(`未知操作: ${operation}`);
      }
    }

    return result;
  }

  /**
   * 提取文档实体
   */
  private async extractDocumentEntities(documentId: number): Promise<any> {
    try {
      const response = await this.ragService.extractEntitiesFromDocument(documentId);
      return {
        success: true,
        entities: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 更新文档知识图谱
   */
  private async updateDocumentGraph(documentId: number): Promise<any> {
    try {
      // 先提取实体
      const entities = await this.extractDocumentEntities(documentId);
      
      if (!entities.success) {
        return entities;
      }

      // 更新图谱
      const response = await this.ragService.storeEntitiesToGraph(
        documentId,
        entities.entities
      );
      
      return {
        success: true,
        graph_update: response
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 生成文档摘要
   */
  private async generateDocumentSummary(documentId: number): Promise<any> {
    try {
      // 获取文档内容
      const doc = await this.ragService.getDocument(documentId);
      
      // 简单摘要（前200字符）
      const summary = doc.content?.substring(0, 200) || '';
      
      return {
        success: true,
        summary,
        length: doc.content?.length || 0
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * 批量搜索
   */
  async batchSearch(params: BatchSearchParams): Promise<BatchResult> {
    logger.info('批量搜索:', {
      queries: params.queries.length,
      type: params.search_type
    });

    const results: any[] = [];
    const errors: Array<{ id: any; error: string }> = [];
    let successful = 0;
    let failed = 0;

    // 并行搜索所有查询
    const searchPromises = params.queries.map(async (query, index) => {
      try {
        const searchResults = await this.performSearch(
          query,
          params.search_type || 'all',
          params.min_score
        );
        
        successful++;
        return {
          query,
          results: searchResults
        };
      } catch (error) {
        failed++;
        const errorMsg = error instanceof Error ? error.message : String(error);
        errors.push({ id: query, error: errorMsg });
        logger.error(`搜索失败 "${query}":`, error);
        return null;
      }
    });

    const allResults = await Promise.all(searchPromises);
    results.push(...allResults.filter(r => r !== null));

    // 聚合结果（如果需要）
    let aggregatedResults = results;
    if (params.aggregate_results) {
      aggregatedResults = this.aggregateSearchResults(results);
    }

    return {
      total: params.queries.length,
      successful,
      failed,
      results: aggregatedResults,
      errors
    };
  }

  /**
   * 执行单次搜索
   */
  private async performSearch(
    query: string,
    searchType: string,
    minScore?: number
  ): Promise<any[]> {
    switch (searchType) {
      case 'code':
        return await this.ragService.searchCodeExamples({
          query,
          limit: 10
        });
      
      case 'docs':
        return await this.ragService.getDesignDocs({
          query
        });
      
      case 'all':
      default:
        // 搜索所有类型并合并
        const [codeResults, docResults] = await Promise.all([
          this.ragService.searchCodeExamples({ query, limit: 5 }),
          this.ragService.getDesignDocs({ query })
        ]);
        
        return [
          ...codeResults.map((r: any) => ({ ...r, type: 'code' })),
          ...docResults.map((r: any) => ({ ...r, type: 'doc' }))
        ];
    }
  }

  /**
   * 聚合搜索结果
   */
  private aggregateSearchResults(results: any[]): any[] {
    // 按文档ID去重并聚合
    const docMap = new Map<string, any>();

    for (const queryResult of results) {
      for (const item of queryResult.results) {
        const key = `${item.type}-${item.id || item.file_path}`;
        
        if (!docMap.has(key)) {
          docMap.set(key, {
            ...item,
            matched_queries: [queryResult.query]
          });
        } else {
          const existing = docMap.get(key);
          existing.matched_queries.push(queryResult.query);
        }
      }
    }

    // 按匹配查询数量排序
    return Array.from(docMap.values())
      .sort((a, b) => b.matched_queries.length - a.matched_queries.length);
  }

  /**
   * 批量导出数据
   */
  async batchExport(params: {
    entity_names: string[];
    include_relations?: boolean;
    depth?: number;
  }): Promise<BatchResult> {
    logger.info('批量导出实体:', {
      count: params.entity_names.length,
      depth: params.depth
    });

    const results: any[] = [];
    const errors: Array<{ id: any; error: string }> = [];
    let successful = 0;
    let failed = 0;

    for (const entityName of params.entity_names) {
      try {
        // 获取实体详情
        const entity = await this.ragService.queryEntity(entityName);
        
        // 获取关系（如果需要）
        let relations = [];
        if (params.include_relations) {
          relations = await this.ragService.findRelatedEntities(
            entityName,
            params.depth || 2
          );
        }

        successful++;
        results.push({
          entity,
          relations
        });
      } catch (error) {
        failed++;
        const errorMsg = error instanceof Error ? error.message : String(error);
        errors.push({ id: entityName, error: errorMsg });
        logger.error(`导出实体 "${entityName}" 失败:`, error);
      }
    }

    return {
      total: params.entity_names.length,
      successful,
      failed,
      results,
      errors
    };
  }
}

// 导出单例
export const batchOperations = new BatchOperationsService();
