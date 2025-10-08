import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Tabs, 
  Table, 
  Button, 
  Space, 
  message, 
  Popconfirm,
  Tag,
  Typography,
  Spin,
  Alert
} from 'antd';
import { 
  DeleteOutlined, 
  ReloadOutlined,
  FileTextOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, DocumentInfo, CodeFileInfo } from '../services/api_v2';

const { Text } = Typography;

interface ContentManagerProps {
  onUpdate?: () => void;
}

const ContentManager: React.FC<ContentManagerProps> = ({ onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [codeFiles, setCodeFiles] = useState<CodeFileInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = async () => {
    try {
      const docs = await KnowledgeGraphApi.listDocuments();
      setDocuments(docs);
    } catch (err: any) {
      message.error(`加载文档失败: ${err.message}`);
    }
  };

  const loadCodeFiles = async () => {
    try {
      const files = await KnowledgeGraphApi.listCodeFiles();
      setCodeFiles(files);
    } catch (err: any) {
      message.error(`加载代码文件失败: ${err.message}`);
    }
  };

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([loadDocuments(), loadCodeFiles()]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string, filename: string) => {
    try {
      await KnowledgeGraphApi.deleteDocument(docId);
      message.success(`文档 "${filename}" 已删除`);
      await loadDocuments();
      onUpdate?.();
    } catch (err: any) {
      message.error(`删除文档失败: ${err.message}`);
    }
  };

  const handleDeleteCodeFile = async (fileId: string, filename: string) => {
    try {
      await KnowledgeGraphApi.deleteCodeFile(fileId);
      message.success(`代码文件 "${filename}" 已删除`);
      await loadCodeFiles();
      onUpdate?.();
    } catch (err: any) {
      message.error(`删除代码文件失败: ${err.message}`);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const documentColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename: string) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{filename}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (fileType: string) => <Tag color="blue">{fileType}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '片段数',
      dataIndex: 'total_chunks',
      key: 'total_chunks',
      render: (chunks: number) => <Tag color="green">{chunks}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'processed',
      key: 'processed',
      render: (processed: boolean, record: DocumentInfo) => (
        <Space>
          {processed ? (
            <Tag color="success" icon={<CheckCircleOutlined />}>已处理</Tag>
          ) : (
            <Tag color="error" icon={<ExclamationCircleOutlined />}>处理失败</Tag>
          )}
          {record.error_message && (
            <Text type="danger" style={{ fontSize: '12px' }}>
              {record.error_message}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: DocumentInfo) => (
        <Popconfirm
          title="确定要删除这个文档吗？"
          description="删除后将无法恢复，所有相关的向量数据也会被删除。"
          onConfirm={() => handleDeleteDocument(record.doc_id, record.filename)}
          okText="确定"
          cancelText="取消"
        >
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />}
            size="small"
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const codeFileColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename: string) => (
        <Space>
          <CodeOutlined />
          <Text strong>{filename}</Text>
        </Space>
      ),
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
      render: (language: string) => <Tag color="purple">{language}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => `${(size / 1024).toFixed(1)} KB`,
    },
    {
      title: '代码块数',
      dataIndex: 'total_blocks',
      key: 'total_blocks',
      render: (blocks: number) => <Tag color="orange">{blocks}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'processed',
      key: 'processed',
      render: (processed: boolean, record: CodeFileInfo) => (
        <Space>
          {processed ? (
            <Tag color="success" icon={<CheckCircleOutlined />}>已处理</Tag>
          ) : (
            <Tag color="error" icon={<ExclamationCircleOutlined />}>处理失败</Tag>
          )}
          {record.error_message && (
            <Text type="danger" style={{ fontSize: '12px' }}>
              {record.error_message}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: CodeFileInfo) => (
        <Popconfirm
          title="确定要删除这个代码文件吗？"
          description="删除后将无法恢复，所有相关的代码块和向量数据也会被删除。"
          onConfirm={() => handleDeleteCodeFile(record.file_id, record.filename)}
          okText="确定"
          cancelText="取消"
        >
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />}
            size="small"
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card 
        title="内容管理"
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadAll}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        {error && (
          <Alert
            type="error"
            message="加载失败"
            description={error}
            style={{ marginBottom: 20 }}
            closable
          />
        )}

        <Spin spinning={loading}>
          <Tabs
            items={[
              {
                key: 'documents',
                label: (
                  <Space>
                    <FileTextOutlined />
                    文档 ({documents.length})
                  </Space>
                ),
                children: (
                  <Table
                    columns={documentColumns}
                    dataSource={documents}
                    rowKey="doc_id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => 
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 个文档`
                    }}
                    scroll={{ x: 'max-content' }}
                  />
                )
              },
              {
                key: 'code',
                label: (
                  <Space>
                    <CodeOutlined />
                    代码 ({codeFiles.length})
                  </Space>
                ),
                children: (
                  <Table
                    columns={codeFileColumns}
                    dataSource={codeFiles}
                    rowKey="file_id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => 
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 个代码文件`
                    }}
                    scroll={{ x: 'max-content' }}
                  />
                )
              }
            ]}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default ContentManager;