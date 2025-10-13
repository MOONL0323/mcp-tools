/**
 * 真实文档管理器组件
 * 连接真实后端API
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  message,
  Tag,
  Popconfirm,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  SearchOutlined,
  FileTextOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

// 完全内联的API客户端和服务
class ApiClient {
  private baseURL: string;
  
  constructor(config: { baseURL: string; timeout: number }) {
    this.baseURL = config.baseURL;
  }
  
  async get<T>(url: string): Promise<{ success: boolean; data?: T; error?: string }> {
    try {
      const response = await fetch(`${this.baseURL}${url}`);
      const data = await response.json();
      return { success: response.ok, data };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
  
  async post<T>(url: string, body?: any, options?: any): Promise<{ success: boolean; data?: T; error?: string }> {
    try {
      const config: RequestInit = {
        method: 'POST',
        headers: options?.headers || {},
      };
      
      if (body instanceof FormData) {
        config.body = body;
      } else {
        config.headers = { ...config.headers, 'Content-Type': 'application/json' };
        config.body = JSON.stringify(body);
      }
      
      const response = await fetch(`${this.baseURL}${url}`, config);
      const data = await response.json();
      return { success: response.ok, data };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
  
  async delete(url: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseURL}${url}`, { method: 'DELETE' });
      return { success: response.ok };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
}

// 临时内联服务定义
interface DocumentMetadata {
  id: string;
  title: string;
  doc_type: string;
  file_name: string;
  file_size: number;
  status: string;
  upload_time: string;
  chunk_count?: number;
  entity_count?: number;
}

class RealDocumentServiceClass {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient({
      baseURL: 'http://127.0.0.1:8000/api',
      timeout: 30000,
    });
  }

  async uploadDocument(file: File, metadata: any): Promise<DocumentMetadata> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', metadata.title);
    formData.append('doc_type', metadata.doc_type);
    if (metadata.description) {
      formData.append('description', metadata.description);
    }

    const response = await this.apiClient.post<DocumentMetadata>('/v1/docs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    if (!response.success || !response.data) {
      throw new Error(response.error || '文档上传失败');
    }
    return response.data;
  }

  async getDocuments(): Promise<DocumentMetadata[]> {
    const response = await this.apiClient.get<DocumentMetadata[]>('/v1/docs');
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档列表失败');
    }
    return response.data;
  }

  async getDocument(id: string): Promise<DocumentMetadata> {
    const response = await this.apiClient.get<DocumentMetadata>(`/v1/docs/${id}`);
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档详情失败');
    }
    return response.data;
  }

  async deleteDocument(id: string): Promise<void> {
    const response = await this.apiClient.delete(`/v1/docs/${id}`);
    if (!response.success) {
      throw new Error(response.error || '删除文档失败');
    }
  }

  async searchDocuments(request: any): Promise<any[]> {
    const response = await this.apiClient.post<any[]>('/v1/docs/search', request);
    if (!response.success || !response.data) {
      throw new Error(response.error || '搜索失败');
    }
    return response.data;
  }

  async getDocumentChunks(id: string): Promise<any[]> {
    const response = await this.apiClient.get<any[]>(`/v1/docs/${id}/chunks`);
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档分块失败');
    }
    return response.data;
  }

  async getDocumentEntities(id: string): Promise<any[]> {
    const response = await this.apiClient.get<any[]>(`/v1/docs/${id}/entities`);
    if (!response.success || !response.data) {
      throw new Error(response.error || '获取文档实体失败');
    }
    return response.data;
  }
}

const realDocumentService = new RealDocumentServiceClass();

const { Option } = Select;

const RealDocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentMetadata | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [documentChunks, setDocumentChunks] = useState<any[]>([]);
  const [documentEntities, setDocumentEntities] = useState<any[]>([]);
  
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();

  // 加载文档列表
  const loadDocuments = async () => {
    setLoading(true);
    try {
      const docs = await realDocumentService.getDocuments();
      setDocuments(docs);
      message.success(`加载了 ${docs.length} 个文档`);
    } catch (error: any) {
      message.error(`加载失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // 上传文档
  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择文件');
      return;
    }

    const file = fileList[0].originFileObj as File;
    
    setLoading(true);
    try {
      const doc = await realDocumentService.uploadDocument(file, {
        title: values.title,
        doc_type: values.doc_type,
        description: values.description,
      });
      
      message.success('文档上传成功！正在后台处理...');
      setUploadModalVisible(false);
      form.resetFields();
      setFileList([]);
      
      // 刷新列表
      await loadDocuments();
    } catch (error: any) {
      message.error(`上传失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 删除文档
  const handleDelete = async (id: string) => {
    setLoading(true);
    try {
      await realDocumentService.deleteDocument(id);
      message.success('删除成功');
      await loadDocuments();
    } catch (error: any) {
      message.error(`删除失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 查看详情
  const handleViewDetail = async (record: DocumentMetadata) => {
    setLoading(true);
    try {
      const [chunks, entities] = await Promise.all([
        realDocumentService.getDocumentChunks(record.id),
        realDocumentService.getDocumentEntities(record.id),
      ]);
      
      setSelectedDocument(record);
      setDocumentChunks(chunks);
      setDocumentEntities(entities);
      setDetailModalVisible(true);
    } catch (error: any) {
      message.error(`获取详情失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 向量搜索
  const handleSearch = async (values: any) => {
    setLoading(true);
    try {
      const results = await realDocumentService.searchDocuments({
        query: values.query,
        top_k: values.top_k || 5,
      });
      
      setSearchResults(results);
      message.success(`找到 ${results.length} 个相关结果`);
    } catch (error: any) {
      message.error(`搜索失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 150,
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'code' ? 'blue' : 'green'}>{type}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colors: Record<string, string> = {
          completed: 'success',
          processing: 'processing',
          failed: 'error',
          pending: 'default',
        };
        return <Tag color={colors[status] || 'default'}>{status}</Tag>;
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 80,
    },
    {
      title: '实体数',
      dataIndex: 'entity_count',
      key: 'entity_count',
      width: 80,
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: DocumentMetadata) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除这个文档吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const searchColumns = [
    {
      title: '文档',
      dataIndex: 'document_title',
      key: 'document_title',
      width: 200,
    },
    {
      title: '相似度',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      render: (score: number) => `${(score * 100).toFixed(2)}%`,
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="文档总数"
              value={documents.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="处理中"
              value={documents.filter(d => d.status === 'processing').length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={documents.filter(d => d.status === 'completed').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总分块数"
              value={documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0)}
            />
          </Card>
        </Col>
      </Row>

      {/* 主表格 */}
      <Card
        title="文档列表"
        extra={
          <Space>
            <Button
              icon={<SearchOutlined />}
              onClick={() => setSearchModalVisible(true)}
            >
              向量搜索
            </Button>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传文档
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadDocuments}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1500 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 上传对话框 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        onOk={() => form.submit()}
        confirmLoading={loading}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleUpload}>
          <Form.Item
            label="选择文件"
            required
          >
            <Upload
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item
            label="文档标题"
            name="title"
            rules={[{ required: true, message: '请输入文档标题' }]}
          >
            <Input placeholder="输入文档标题" />
          </Form.Item>

          <Form.Item
            label="文档类型"
            name="doc_type"
            initialValue="document"
            rules={[{ required: true, message: '请选择文档类型' }]}
          >
            <Select>
              <Option value="document">普通文档</Option>
              <Option value="code">代码文档</Option>
              <Option value="api">API文档</Option>
              <Option value="guide">使用指南</Option>
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="输入文档描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 搜索对话框 */}
      <Modal
        title="向量搜索"
        open={searchModalVisible}
        onCancel={() => {
          setSearchModalVisible(false);
          searchForm.resetFields();
          setSearchResults([]);
        }}
        footer={null}
        width={800}
      >
        <Form form={searchForm} layout="inline" onFinish={handleSearch} style={{ marginBottom: 16 }}>
          <Form.Item
            name="query"
            rules={[{ required: true, message: '请输入搜索内容' }]}
            style={{ width: 400 }}
          >
            <Input placeholder="输入搜索内容" />
          </Form.Item>
          <Form.Item name="top_k" initialValue={5}>
            <Select style={{ width: 100 }}>
              <Option value={5}>前5条</Option>
              <Option value={10}>前10条</Option>
              <Option value={20}>前20条</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              搜索
            </Button>
          </Form.Item>
        </Form>

        <Table
          columns={searchColumns}
          dataSource={searchResults}
          rowKey="chunk_id"
          loading={loading}
          pagination={{ pageSize: 5 }}
        />
      </Modal>

      {/* 详情对话框 */}
      <Modal
        title="文档详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {selectedDocument && (
          <div>
            <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
              <p><strong>ID:</strong> {selectedDocument.id}</p>
              <p><strong>标题:</strong> {selectedDocument.title}</p>
              <p><strong>类型:</strong> {selectedDocument.doc_type}</p>
              <p><strong>状态:</strong> <Tag color={selectedDocument.status === 'completed' ? 'success' : 'processing'}>{selectedDocument.status}</Tag></p>
              <p><strong>大小:</strong> {(selectedDocument.file_size / 1024).toFixed(2)} KB</p>
            </Card>

            <Card size="small" title={`文档分块 (${documentChunks.length})`} style={{ marginBottom: 16 }}>
              <Table
                size="small"
                columns={[
                  { title: '序号', dataIndex: 'chunk_index', key: 'chunk_index', width: 80 },
                  { title: '内容预览', dataIndex: 'content', key: 'content', ellipsis: true },
                ]}
                dataSource={documentChunks}
                rowKey="chunk_id"
                pagination={{ pageSize: 5 }}
              />
            </Card>

            <Card size="small" title={`提取实体 (${documentEntities.length})`}>
              <Table
                size="small"
                columns={[
                  { title: '实体名称', dataIndex: 'name', key: 'name' },
                  { title: '类型', dataIndex: 'entity_type', key: 'entity_type', render: (type: string) => <Tag>{type}</Tag> },
                ]}
                dataSource={documentEntities}
                rowKey="entity_id"
                pagination={{ pageSize: 5 }}
              />
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RealDocumentManager;
