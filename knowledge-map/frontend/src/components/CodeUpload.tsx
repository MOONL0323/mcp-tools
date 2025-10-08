import React, { useState, useCallback } from 'react';
import { Upload, message, Card, Typography, Tag, Divider, Space, Button, Progress, List } from 'antd';
import { CodeOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;
const { Title, Text, Paragraph } = Typography;

interface CodeUploadProps {
  onUploadSuccess?: (result: any) => void;
  onUploadError?: (error: string) => void;
}

interface UploadResult {
  fileName: string;
  status: 'success' | 'error';
  message: string;
  details?: {
    structs?: number;
    functions?: number;
    interfaces?: number;
    documents?: number;
  };
}

const CodeUpload: React.FC<CodeUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const [progress, setProgress] = useState(0);

  // 支持的代码文件类型
  const supportedCodeTypes = [
    { ext: '.go', desc: 'Go源码文件', icon: '🔧' },
    { ext: '.mod', desc: 'Go模块配置', icon: '📦' },
    { ext: '.sum', desc: 'Go依赖校验', icon: '🔒' },
    { ext: '.py', desc: 'Python源码', icon: '🐍' },
    { ext: '.js', desc: 'JavaScript源码', icon: '📜' },
    { ext: '.ts', desc: 'TypeScript源码', icon: '📘' },
    { ext: '.json', desc: 'JSON配置文件', icon: '⚙️' },
    { ext: '.yaml', desc: 'YAML配置文件', icon: '📄' },
    { ext: '.yml', desc: 'YAML配置文件', icon: '📄' }
  ];

  const beforeUpload = (file: File) => {
    const fileName = file.name.toLowerCase();
    const isSupported = supportedCodeTypes.some(type => fileName.endsWith(type.ext));
    
    if (!isSupported) {
      const supportedExts = supportedCodeTypes.map(t => t.ext).join(', ');
      message.error(`不支持的代码文件类型！支持的格式: ${supportedExts}`);
      return false;
    }

    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('代码文件大小不能超过 10MB!');
      return false;
    }

    return true;
  };

  const handleUpload = useCallback(async (options: any) => {
    const { file, onSuccess, onError } = options;
    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'code'); // 标记为代码文件

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
        message: `成功解析代码文件`,
        details: {
          structs: result.stats?.struct_count || 0,
          functions: result.stats?.function_count || 0,
          interfaces: result.stats?.interface_count || 0,
          documents: result.document_count || 0
        }
      };

      setUploadResults(prev => [uploadResult, ...prev]);
      
      message.success(`${file.name} 代码解析完成！`);
      onSuccess?.(result);
      onUploadSuccess?.(result);

    } catch (error: any) {
      console.error('代码上传失败:', error);
      
      // 添加失败结果
      const uploadResult: UploadResult = {
        fileName: file.name,
        status: 'error',
        message: error.message || '代码解析失败'
      };

      setUploadResults(prev => [uploadResult, ...prev]);
      
      message.error(`${file.name} 代码解析失败: ${error.message}`);
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
      console.log('拖拽的代码文件:', e.dataTransfer.files);
    },
    showUploadList: false, // 使用自定义的结果显示
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
              <CodeOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              代码上传与解析
            </Title>
            <Paragraph type="secondary">
              专门用于解析和分析代码文件，提取函数、结构体、接口等代码结构，为AI Agent提供精准的代码上下文。
              与文档管理分离，便于AI Agent根据需要获取不同类型的知识。
            </Paragraph>
          </div>

          {/* 上传区域 */}
          <Card style={{ backgroundColor: '#fafafa' }}>
            <Dragger {...uploadProps} style={{ padding: '40px 20px' }}>
              <p className="ant-upload-drag-icon">
                <CodeOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                点击或拖拽代码文件到此区域进行上传
              </p>
              <p className="ant-upload-hint">
                支持单个或批量上传。代码将被结构化解析，提取函数、类、接口等信息。
              </p>
            </Dragger>

            {/* 进度条 */}
            {uploading && (
              <div style={{ marginTop: 16 }}>
                <Progress 
                  percent={progress} 
                  status={progress === 100 ? 'success' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <Text type="secondary">正在解析代码结构...</Text>
              </div>
            )}
          </Card>

          {/* 支持的文件类型 */}
          <Card title="支持的代码文件类型" size="small">
            <Space wrap>
              {supportedCodeTypes.map((type, index) => (
                <Tag key={index} color="blue" style={{ margin: '2px' }}>
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
              title="代码解析结果" 
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
                            {result.status === 'success' ? '解析成功' : '解析失败'}
                          </Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Text type="secondary">{result.message}</Text>
                          {result.details && (
                            <div style={{ marginTop: 4 }}>
                              <Space size="middle">
                                {result.details.structs !== undefined && (
                                  <Text type="secondary">结构体: {result.details.structs}</Text>
                                )}
                                {result.details.functions !== undefined && (
                                  <Text type="secondary">函数: {result.details.functions}</Text>
                                )}
                                {result.details.interfaces !== undefined && (
                                  <Text type="secondary">接口: {result.details.interfaces}</Text>
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
          <Card title="💡 使用建议" size="small">
            <Space direction="vertical">
              <Text>• <strong>Go项目</strong>: 上传 .go, .mod, .sum 文件获得完整的项目结构分析</Text>
              <Text>• <strong>函数分析</strong>: 系统会自动提取函数签名、参数、返回值和注释</Text>
              <Text>• <strong>结构体解析</strong>: 包括字段、标签、嵌入类型等详细信息</Text>
              <Text>• <strong>AI集成</strong>: 代码将作为独立的知识库，AI Agent可精准搜索相关代码</Text>
              <Text>• <strong>最佳实践</strong>: 确保代码有完整的注释，这样AI Agent能获得更准确的上下文</Text>
            </Space>
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default CodeUpload;