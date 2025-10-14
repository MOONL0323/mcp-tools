/**
 * 文档详情组件
 * 显示文档的完整信息、内容预览、chunks列表等
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Spin,
  message,
  Tabs,
  Typography,
  Divider,
  Alert,
  Collapse,
} from 'antd';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CodeOutlined,
  BlockOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

interface DocumentDetailData {
  id: string;
  title: string;
  description?: string;
  doc_type: string;
  content: string;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  team?: {
    id: string;
    name: string;
    display_name: string;
  };
  project?: {
    id: string;
    name: string;
    display_name: string;
  };
  module?: {
    id: string;
    name: string;
  };
  dev_type?: {
    id: string;
    name: string;
    display_name: string;
    category: string;
  };
  team_role?: string;
  code_function?: string;
  tags: string[];
  uploaded_by: string;
  processing_status: string;
  chunk_count?: number;
  entity_count?: number;
  access_level: string;
  version: string;
  created_at: string;
  updated_at: string;
}

interface Chunk {
  id: string;
  chunk_index: number;
  content: string;
  content_summary?: string;
  token_count?: number;
  metadata: Record<string, any>;
  embedding_status?: string;
  created_at: string;
}

const DocumentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [docData, setDocData] = useState<DocumentDetailData | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [chunkingInProgress, setChunkingInProgress] = useState(false);
  const [embeddingInProgress, setEmbeddingInProgress] = useState(false);

  const loadDocumentDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}/detail`);
      
      if (response.ok) {
        const data = await response.json();
        setDocData(data);
      } else {
        message.error('加载文档详情失败');
      }
    } catch (error) {
      console.error('加载文档详情失败:', error);
      message.error('加载文档详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadDocumentDetail();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadChunks = async () => {
    setLoadingChunks(true);
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}/chunks`);
      
      if (response.ok) {
        const data = await response.json();
        setChunks(data.chunks || []);
      } else {
        message.error('加载chunks失败');
      }
    } catch (error) {
      console.error('加载chunks失败:', error);
      message.error('加载chunks失败');
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}/download`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = docData?.file_name || 'download';
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
        message.success('下载成功');
      } else {
        message.error('下载失败');
      }
    } catch (error) {
      console.error('下载失败:', error);
      message.error('下载失败');
    }
  };

  const handleBack = () => {
    navigate('/documents');
  };

  const handleStartChunking = async () => {
    if (!id) return;
    
    setChunkingInProgress(true);
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}/chunk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          max_chunk_size: 2000
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        message.success(`分块成功！共生成 ${result.total_chunks} 个文档块`);
        
        // 重新加载文档详情和chunks
        await loadDocumentDetail();
        await loadChunks();
      } else {
        const error = await response.json();
        message.error(`分块失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('分块失败:', error);
      message.error('分块失败，请稍后重试');
    } finally {
      setChunkingInProgress(false);
    }
  };

  const handleStartEmbedding = async () => {
    if (!id) return;
    
    if (chunks.length === 0) {
      message.warning('请先进行文档分块');
      return;
    }
    
    setEmbeddingInProgress(true);
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}/embed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        const stats = result.embedding_stats;
        message.success(
          `向量化成功！成功: ${stats.success}, 失败: ${stats.failed}, 跳过: ${stats.skipped}`
        );
        
        // 重新加载chunks以显示embedding状态
        await loadChunks();
      } else {
        const error = await response.json();
        message.error(`向量化失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('向量化失败:', error);
      message.error('向量化失败，请稍后重试');
    } finally {
      setEmbeddingInProgress(false);
    }
  };

  const getDocTypeTag = (docType: string) => {
    const typeMap: Record<string, { color: string; text: string }> = {
      business_doc: { color: 'blue', text: '业务文档' },
      demo_code: { color: 'green', text: '示例代码' },
      checklist: { color: 'orange', text: '规范文档' },
    };
    const typeInfo = typeMap[docType] || { color: 'default', text: docType };
    return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>;
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    };
    const statusInfo = statusMap[status] || { color: 'default', text: status };
    return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const renderContent = () => {
    if (!docData) return null;

    const isCode = docData.mime_type?.includes('python') ||
                   docData.mime_type?.includes('javascript') ||
                   docData.mime_type?.includes('typescript') ||
                   docData.file_name.match(/\.(py|js|ts|tsx|jsx|java|go|cpp|c|h|rs|rb|php)$/);

    const isMarkdown = docData.mime_type?.includes('markdown') ||
                       docData.file_name.endsWith('.md');

    if (isMarkdown) {
      return (
        <ReactMarkdown
          components={{
            code({ className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const inline = !match;
              return !inline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus as any}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {docData.content}
        </ReactMarkdown>
      );
    }

    if (isCode) {
      const language = docData.file_name.split('.').pop() || 'text';
      return (
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus as any}
          showLineNumbers
        >
          {docData.content}
        </SyntaxHighlighter>
      );
    }

    // 普通文本
    return (
      <Paragraph style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
        {docData.content}
      </Paragraph>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!docData) {
    return (
      <Alert
        message="文档不存在"
        description="未找到指定的文档，请检查链接是否正确"
        type="error"
        showIcon
      />
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* 头部操作栏 */}
      <Card bordered={false} style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
              返回列表
            </Button>
            <Title level={3} style={{ margin: 0 }}>
              {docData.title}
            </Title>
            {getDocTypeTag(docData.doc_type)}
            {getStatusTag(docData.processing_status)}
          </Space>
          <Space>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
            >
              下载文档
            </Button>
            <Button
              type="default"
              icon={<BlockOutlined />}
              onClick={handleStartChunking}
              loading={chunkingInProgress}
              disabled={docData.processing_status === 'processing'}
            >
              {chunks.length > 0 ? '重新分块' : '开始分块'}
            </Button>
            <Button
              type="default"
              icon={<CodeOutlined />}
              onClick={handleStartEmbedding}
              loading={embeddingInProgress}
              disabled={chunks.length === 0 || embeddingInProgress}
            >
              生成向量
            </Button>
          </Space>
        </Space>
      </Card>

      {/* 主要内容 */}
      <Tabs 
        defaultActiveKey="content"
        onChange={(key) => {
          if (key === 'chunks' && chunks.length === 0 && !loadingChunks) {
            loadChunks();
          }
        }}
      >
        {/* 内容标签页 */}
        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              文档内容
            </span>
          }
          key="content"
        >
          <Card bordered={false}>
            {renderContent()}
          </Card>
        </TabPane>

        {/* 元数据标签页 */}
        <TabPane
          tab={
            <span>
              <InfoCircleOutlined />
              元数据
            </span>
          }
          key="metadata"
        >
          <Card bordered={false}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="文件名">
                {docData.file_name}
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {formatFileSize(docData.file_size)}
              </Descriptions.Item>
              <Descriptions.Item label="MIME类型">
                {docData.mime_type}
              </Descriptions.Item>
              <Descriptions.Item label="文档类型">
                {getDocTypeTag(docData.doc_type)}
              </Descriptions.Item>
              
              {docData.team && (
                <Descriptions.Item label="所属团队">
                  <Tag color="blue">{docData.team.display_name}</Tag>
                </Descriptions.Item>
              )}
              
              {docData.project && (
                <Descriptions.Item label="所属项目">
                  <Tag color="cyan">{docData.project.display_name}</Tag>
                </Descriptions.Item>
              )}
              
              {docData.module && (
                <Descriptions.Item label="所属模块">
                  {docData.module.name}
                </Descriptions.Item>
              )}
              
              {docData.dev_type && (
                <Descriptions.Item label="开发类型">
                  <Tag>{docData.dev_type.display_name}</Tag>
                </Descriptions.Item>
              )}
              
              {docData.team_role && (
                <Descriptions.Item label="团队角色">
                  <Tag color="purple">{docData.team_role}</Tag>
                </Descriptions.Item>
              )}
              
              {docData.code_function && (
                <Descriptions.Item label="代码功能">
                  <Tag color="orange">{docData.code_function}</Tag>
                </Descriptions.Item>
              )}
              
              {docData.description && (
                <Descriptions.Item label="描述" span={2}>
                  {docData.description}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="标签" span={2}>
                {docData.tags.length > 0 ? (
                  docData.tags.map((tag: string) => (
                    <Tag key={tag} color="default">{tag}</Tag>
                  ))
                ) : (
                  <Text type="secondary">无标签</Text>
                )}
              </Descriptions.Item>

              <Descriptions.Item label="上传者">
                {docData.uploaded_by}
              </Descriptions.Item>
              <Descriptions.Item label="访问级别">
                <Tag>{docData.access_level}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="版本">
                {docData.version}
              </Descriptions.Item>
              <Descriptions.Item label="处理状态">
                {getStatusTag(docData.processing_status)}
              </Descriptions.Item>

              {docData.chunk_count !== undefined && (
                <Descriptions.Item label="Chunk数量">
                  {docData.chunk_count}
                </Descriptions.Item>
              )}

              {docData.entity_count !== undefined && (
                <Descriptions.Item label="实体数量">
                  {docData.entity_count}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="创建时间">
                {formatDate(docData.created_at)}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {formatDate(docData.updated_at)}
              </Descriptions.Item>

              <Descriptions.Item label="文件路径" span={2}>
                <Text code copyable>{docData.file_path}</Text>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </TabPane>

        {/* Chunks标签页 */}
        <TabPane
          tab={
            <span>
              <BlockOutlined />
              Chunks {docData.chunk_count ? `(${docData.chunk_count})` : ''}
            </span>
          }
          key="chunks"
        >
          <Card bordered={false}>
            {chunks.length === 0 && !loadingChunks ? (
              <Alert
                message="暂无Chunks"
                description={
                  <Space direction="vertical">
                    <Text>此文档尚未进行智能分块处理</Text>
                    <Button type="primary" onClick={loadChunks}>
                      加载Chunks
                    </Button>
                  </Space>
                }
                type="info"
                showIcon
              />
            ) : (
              <>
                <Button
                  type="primary"
                  onClick={loadChunks}
                  loading={loadingChunks}
                  style={{ marginBottom: 16 }}
                >
                  刷新Chunks
                </Button>

                <Collapse>
                  {chunks.map((chunk) => (
                    <Panel
                      header={
                        <Space>
                          <Text strong>Chunk #{chunk.chunk_index}</Text>
                          {chunk.content_summary && (
                            <Text type="secondary">{chunk.content_summary}</Text>
                          )}
                          {chunk.token_count && (
                            <Tag color="cyan">{chunk.token_count} tokens</Tag>
                          )}
                          {chunk.embedding_status && (
                            <Tag color={chunk.embedding_status === 'completed' ? 'success' : 'processing'}>
                              {chunk.embedding_status}
                            </Tag>
                          )}
                        </Space>
                      }
                      key={chunk.id}
                    >
                      <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                        {chunk.content}
                      </Paragraph>

                      {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                        <>
                          <Divider />
                          <Text type="secondary">元数据</Text>
                          <pre>{JSON.stringify(chunk.metadata, null, 2)}</pre>
                        </>
                      )}
                    </Panel>
                  ))}
                </Collapse>
              </>
            )}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default DocumentDetail;
