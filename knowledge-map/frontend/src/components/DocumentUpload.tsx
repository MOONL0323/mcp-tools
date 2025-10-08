import React, { useState, useCallback } from 'react';
import { Upload, message, Card, Typography, Tag, Divider, Space, Button, Progress, List } from 'antd';
import { FileTextOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;
const { Title, Text, Paragraph } = Typography;

interface DocumentUploadProps {
  onUploadSuccess?: (result: any) => void;
  onUploadError?: (error: string) => void;
}

interface UploadResult {
  fileName: string;
  status: 'success' | 'error';
  message: string;
  details?: {
    pages?: number;
    documents?: number;
    fileSize?: string;
  };
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [progress, setProgress] = useState(0);

  // 支持的文档文件类型
  const supportedDocTypes = [
    { ext: '.pdf', desc: 'PDF文档', icon: '📕' },
    { ext: '.docx', desc: 'Word文档', icon: '📄' },
    { ext: '.doc', desc: 'Word文档（旧版）', icon: '📄' },
    { ext: '.txt', desc: '纯文本文档', icon: '📝' },
    { ext: '.md', desc: 'Markdown文档', icon: '📋' },
    { ext: '.rtf', desc: 'RTF文档', icon: '📃' }
  ];

  const beforeUpload = (file: File) => {
    const fileName = file.name.toLowerCase();
    const isSupported = supportedDocTypes.some(type => fileName.endsWith(type.ext));
    
    if (!isSupported) {
      const supportedExts = supportedDocTypes.map(t => t.ext).join(', ');
      message.error(`不支持的文档类型！支持的格式: ${supportedExts}`);
      return false;
    }

    const isLt50M = file.size / 1024 / 1024 < 50;
    if (!isLt50M) {
      message.error('文档大小不能超过 50MB!');
      return false;
    }

    return true;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleUpload = useCallback(async (options: any) => {
    const { file, onSuccess, onError } = options;
    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'document'); // 标记为文档文件

    try {
      setProgress(30);
      
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      setProgress(60);

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`);
      }

      const result = await response.json();
      setProgress(100);

      // 添加成功结果
      const uploadResult: UploadResult = {
        fileName: file.name,
        status: 'success',
        message: `文档解析完成`,
        details: {
          pages: result.stats?.page_count || 0,
          documents: result.document_count || 0,
          fileSize: formatFileSize(file.size)
        }
      };

      setUploadResults(prev => [uploadResult, ...prev]);
      
      message.success(`${file.name} 文档处理完成！`);
      onSuccess?.(result);
      onUploadSuccess?.(result);

    } catch (error: any) {
      console.error('文档上传失败:', error);
      
      // 添加失败结果
      const uploadResult: UploadResult = {
        fileName: file.name,
        status: 'error',
        message: error.message || '文档处理失败'
      };

      setUploadResults(prev => [uploadResult, ...prev]);
      
      message.error(`${file.name} 文档处理失败: ${error.message}`);
      onError?.(error);
      onUploadError?.(error.message);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [onUploadSuccess, onUploadError]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    customRequest: handleUpload,
    beforeUpload: beforeUpload,
    onDrop: (e) => {
      console.log('拖拽的文档文件:', e.dataTransfer.files);
    },
    showUploadList: false,
  };

  const clearResults = () => {
    setUploadResults([]);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题和说明 */}
          <div>
            <Title level={3}>
              <FileTextOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              文档上传与管理
            </Title>
            <Paragraph type="secondary">
              专门用于处理文档文件，包括PDF、Word、文本等格式。系统会自动提取文档内容，
              建立语义索引，为AI Agent提供丰富的文档知识库。
            </Paragraph>
          </div>

          {/* 上传区域 */}
          <Card style={{ backgroundColor: '#f6ffed' }}>
            <Dragger {...uploadProps} style={{ padding: '40px 20px' }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
              </p>
              <p className="ant-upload-text">
                点击或拖拽文档文件到此区域进行上传
              </p>
              <p className="ant-upload-hint">
                支持单个或批量上传。文档将被自动解析并建立语义索引。
              </p>
            </Dragger>

            {/* 进度条 */}
            {uploading && (
              <div style={{ marginTop: 16 }}>
                <Progress 
                  percent={progress} 
                  status={progress === 100 ? 'success' : 'active'}
                  strokeColor={{
                    '0%': '#b7eb8f',
                    '100%': '#52c41a',
                  }}
                />
                <Text type="secondary">正在处理文档内容...</Text>
              </div>
            )}
          </Card>

          {/* 支持的文件类型 */}
          <Card title="支持的文档类型" size="small">
            <Space wrap>
              {supportedDocTypes.map((type, index) => (
                <Tag key={index} color="green" style={{ margin: '2px' }}>
                  <span style={{ marginRight: 4 }}>{type.icon}</span>
                  {type.ext} - {type.desc}
                </Tag>
              ))}
            </Space>
          </Card>

          <Divider />

          {/* 上传结果 */}
          {uploadResults.length > 0 && (
            <Card 
              title="文档处理结果" 
              size="small"
              extra={
                <Button size="small" onClick={clearResults}>
                  清空记录
                </Button>
              }
            >
              <List
                size="small"
                dataSource={uploadResults}
                renderItem={(result, index) => (
                  <List.Item key={index}>
                    <List.Item.Meta
                      avatar={
                        result.status === 'success' ? (
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
                        ) : (
                          <ExclamationCircleOutlined style={{ color: '#f5222d', fontSize: 16 }} />
                        )
                      }
                      title={
                        <Space>
                          <Text strong>{result.fileName}</Text>
                          <Tag color={result.status === 'success' ? 'success' : 'error'}>
                            {result.status === 'success' ? '处理成功' : '处理失败'}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Text type="secondary">{result.message}</Text>
                          {result.details && (
                            <div style={{ marginTop: 4 }}>
                              <Space size="middle">
                                {result.details.fileSize && (
                                  <Text type="secondary">大小: {result.details.fileSize}</Text>
                                )}
                                {result.details.pages !== undefined && (
                                  <Text type="secondary">页数: {result.details.pages}</Text>
                                )}
                                {result.details.documents !== undefined && (
                                  <Text type="secondary">文档块: {result.details.documents}</Text>
                                )}
                              </Space>
                            </div>
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {/* 使用提示 */}
          <Card title="📚 文档管理说明" size="small">
            <Space direction="vertical">
              <Text>• <strong>语义索引</strong>: 文档内容会被自动分析并建立语义关系</Text>
              <Text>• <strong>智能分块</strong>: 长文档会被智能分割为合适的文档块</Text>
              <Text>• <strong>知识图谱</strong>: 自动提取实体和关系，构建知识网络</Text>
              <Text>• <strong>AI搜索</strong>: AI Agent可根据语义相似度搜索相关文档</Text>
              <Text>• <strong>上下文服务</strong>: 为AI对话提供准确的文档背景知识</Text>
            </Space>
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default DocumentUpload;