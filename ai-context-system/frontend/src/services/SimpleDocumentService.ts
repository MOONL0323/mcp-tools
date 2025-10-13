/**
 * 简单的文档服务实现（用于测试）
 */

import { IDocumentService, IDocumentMetadata, DocumentFilters, DocumentUploadRequest } from '../interfaces/IDocumentService';

export class SimpleDocumentService implements IDocumentService {
  private documents: IDocumentMetadata[] = [];

  async uploadDocument(file: File, metadata: DocumentUploadRequest): Promise<string> {
    const id = Date.now().toString();
    const document: IDocumentMetadata = {
      id,
      type: metadata.type,
      team: metadata.team,
      project: metadata.project,
      module: metadata.module,
      dev_type: metadata.dev_type,
      title: metadata.title,
      description: metadata.description,
      file_name: file.name,
      file_size: file.size,
      mime_type: file.type,
      upload_time: new Date().toISOString(),
      uploaded_by: 'admin',
      uploader_name: '系统管理员',
      status: 'processing',
      chunk_count: 0,
      entity_count: 0,
      tags: metadata.tags,
      version: metadata.version || '1.0',
      access_level: metadata.access_level,
      download_count: 0,
      last_modified: new Date().toISOString(),
      processing_status: 'processing'
    };

    this.documents.push(document);

    // 模拟异步处理
    setTimeout(() => {
      const doc = this.documents.find(d => d.id === id);
      if (doc) {
        doc.status = 'completed';
        doc.processing_status = 'completed';
        doc.chunk_count = Math.floor(Math.random() * 50) + 10;
        doc.entity_count = Math.floor(Math.random() * 100) + 20;
      }
    }, 2000);

    return id;
  }

  async getDocuments(filters?: DocumentFilters): Promise<IDocumentMetadata[]> {
    let result = [...this.documents];

    if (filters) {
      if (filters.type) {
        result = result.filter(doc => doc.type === filters.type);
      }
      if (filters.team) {
        result = result.filter(doc => doc.team === filters.team);
      }
      if (filters.project) {
        result = result.filter(doc => doc.project === filters.project);
      }
      if (filters.module) {
        result = result.filter(doc => doc.module === filters.module);
      }
      if (filters.status) {
        result = result.filter(doc => doc.status === filters.status);
      }
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        result = result.filter(doc => 
          doc.title.toLowerCase().includes(searchLower) ||
          doc.description.toLowerCase().includes(searchLower)
        );
      }
    }

    return result;
  }

  async getDocument(id: string): Promise<IDocumentMetadata> {
    const document = this.documents.find(doc => doc.id === id);
    if (!document) {
      throw new Error('文档不存在');
    }
    return document;
  }

  async deleteDocument(id: string): Promise<void> {
    const index = this.documents.findIndex(doc => doc.id === id);
    if (index === -1) {
      throw new Error('文档不存在');
    }
    this.documents.splice(index, 1);
  }

  async updateDocument(id: string, updates: Partial<IDocumentMetadata>): Promise<void> {
    const document = this.documents.find(doc => doc.id === id);
    if (!document) {
      throw new Error('文档不存在');
    }
    Object.assign(document, updates, { last_modified: new Date().toISOString() });
  }

  async getDocumentContent(id: string): Promise<string> {
    const document = await this.getDocument(id);
    return `这是文档 "${document.title}" 的内容`;
  }

  async downloadDocument(id: string): Promise<Blob> {
    const document = await this.getDocument(id);
    const content = await this.getDocumentContent(id);
    return new Blob([content], { type: 'text/plain' });
  }

  async searchDocuments(query: string, filters?: DocumentFilters): Promise<IDocumentMetadata[]> {
    const searchFilters = { ...filters, search: query };
    return this.getDocuments(searchFilters);
  }

  async batchDeleteDocuments(ids: string[]): Promise<void> {
    for (const id of ids) {
      await this.deleteDocument(id);
    }
  }
}