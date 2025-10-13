/**
 * 文档管理相关接口定义
 */

// 文档状态枚举
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';

// 文档实体（兼容后端API）
export interface Document {
  id: string;
  type: 'business_doc' | 'demo_code';
  team: string;
  project: string;
  module: string;
  dev_type: string;
  title: string;
  description: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  upload_time: string;
  uploaded_by: string;
  uploader_name: string;
  uploader_avatar?: string;
  status: DocumentStatus;
  chunk_count?: number;
  entity_count?: number;
  tags: string[];
  version: string;
  access_level: 'private' | 'team' | 'public';
  download_count: number;
  last_modified: string;
  file_path?: string;
  processing_status: DocumentStatus;
}

// 文档分块
export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  embedding?: number[];
  metadata?: Record<string, any>;
  created_at: string;
}

export interface IDocumentMetadata {
  id: string;
  type: 'business_doc' | 'demo_code';
  team: string;
  project: string;
  module: string;
  dev_type: string;
  title: string;
  description: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  upload_time: string;
  uploaded_by: string;
  uploader_name: string;
  uploader_avatar?: string;
  status: 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  entity_count?: number;
  tags: string[];
  version: string;
  access_level: 'private' | 'team' | 'public';
  download_count: number;
  last_modified: string;
  file_path?: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface DocumentFilters {
  type?: 'business_doc' | 'demo_code';
  team?: string;
  project?: string;
  module?: string;
  dev_type?: string;
  status?: 'processing' | 'completed' | 'failed';
  access_level?: 'private' | 'team' | 'public';
  uploaded_by?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  tags?: string[];
}

export interface DocumentUploadRequest {
  type: 'business_doc' | 'demo_code';
  team: string;
  project: string;
  module: string;
  dev_type: string;
  title: string;
  description: string;
  access_level: 'private' | 'team' | 'public';
  tags: string[];
  version?: string;
}

export interface IDocumentService {
  uploadDocument(file: File, metadata: DocumentUploadRequest): Promise<string>;
  getDocuments(filters?: DocumentFilters): Promise<IDocumentMetadata[]>;
  getDocument(id: string): Promise<IDocumentMetadata>;
  deleteDocument(id: string): Promise<void>;
  updateDocument(id: string, updates: Partial<IDocumentMetadata>): Promise<void>;
  getDocumentContent(id: string): Promise<string>;
  downloadDocument(id: string): Promise<Blob>;
  searchDocuments(query: string, filters?: DocumentFilters): Promise<IDocumentMetadata[]>;
  batchDeleteDocuments(ids: string[]): Promise<void>;
}

export interface DocumentProcessingStatus {
  document_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  chunk_count?: number;
  entity_count?: number;
  created_at: string;
  updated_at: string;
}