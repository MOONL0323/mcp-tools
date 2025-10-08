import React, { useState } from 'react';
import { 
  Upload, 
  Button, 
  Card, 
  message, 
  Progress, 
  List, 
  Tag, 
  Space,
  Switch,
  Alert,
  Typography,
  Select
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined, 
  CodeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, UploadResponse } from '../services/api_v2';

const { Dragger } = Upload;
const { Text } = Typography;
const { Option } = Select;

interface EnhancedCodeUploadProps {
  onUploadSuccess?: () => void;
}

interface UploadStatus {
  file: File;
  status: 'uploading' | 'success' | 'error';
  progress: number;
  response?: UploadResponse;
  error?: string;
  detectedLanguage?: string;
}

const EnhancedCodeUpload: React.FC<EnhancedCodeUploadProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadList, setUploadList] = useState<UploadStatus[]>([]);
  const [processImmediately, setProcessImmediately] = useState(true);

  const supportedLanguages = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JSX',
    '.tsx': 'TSX',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.vue': 'Vue',
    '.sh': 'Shell',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.md': 'Markdown'
  };

  const supportedExtensions = Object.keys(supportedLanguages);

  const detectLanguage = (filename: string): string => {
    const extension = '.' + filename.split('.').pop()?.toLowerCase();
    return supportedLanguages[extension as keyof typeof supportedLanguages] || 'Unknown';
  };

  const handleFileUpload = async (file: File) => {
    // 检查文件类型
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!supportedExtensions.includes(fileExtension)) {
      message.error(`不支持的代码文件格式: ${fileExtension}`);
      return false;
    }

    // 检查文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      message.error('代码文件大小不能超过 10MB');
      return false;
    }

    const detectedLanguage = detectLanguage(file.name);
    
    const uploadStatus: UploadStatus = {
      file,
      status: 'uploading',
      progress: 0,
      detectedLanguage
    };

    setUploadList(prev => [...prev, uploadStatus]);
    setUploading(true);

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setUploadList(prev => prev.map(item => 
          item.file === file && item.status === 'uploading'
            ? { ...item, progress: Math.min(item.progress + 10, 90) }
            : item
        ));
      }, 150);

      const response = await KnowledgeGraphApi.uploadCodeFile(file, processImmediately);

      clearInterval(progressInterval);

      setUploadList(prev => prev.map(item => 
        item.file === file
          ? { 
              ...item, 
              status: response.success ? 'success' : 'error',
              progress: 100,
              response: response,
              error: response.success ? undefined : response.message
            }
          : item
      ));

      if (response.success) {
        message.success(`代码文件上传成功: ${response.message}`);
        onUploadSuccess?.();
      } else {
        message.error(`代码文件上传失败: ${response.message}`);
      }

    } catch (error: any) {
      setUploadList(prev => prev.map(item => 
        item.file === file
          ? { 
              ...item, 
              status: 'error',
              progress: 100,
              error: error.message
            }
          : item
      ));
      message.error(`上传失败: ${error.message}`);
    } finally {
      setUploading(false);
    }

    return false; // 阻止默认上传行为
  };

  const clearUploadList = () => {
    setUploadList([]);
  };

  const getLanguageColor = (language: string): string => {
    const colorMap: Record<string, string> = {
      'Python': '#3776ab',
      'JavaScript': '#f7df1e',
      'TypeScript': '#007acc',
      'Java': '#ed8b00',
      'C++': '#00599c',
      'C': '#a8b9cc',
      'Go': '#00add8',
      'Rust': '#dea584',
      'PHP': '#777bb4',
      'Ruby': '#cc342d',
      'Swift': '#fa7343',
      'HTML': '#e34f26',
      'CSS': '#1572b6'
    };
    return colorMap[language] || '#666666';
  };

  const renderUploadItem = (item: UploadStatus) => {
    const { file, status, progress, response, error, detectedLanguage } = item;
    
    let statusIcon;
    let statusColor;
    
    switch (status) {
      case 'uploading':
        statusIcon = <UploadOutlined spin />;
        statusColor = '#1890ff';
        break;
      case 'success':
        statusIcon = <CheckCircleOutlined />;
        statusColor = '#52c41a';
        break;
      case 'error':
        statusIcon = <ExclamationCircleOutlined />;
        statusColor = '#ff4d4f';
        break;
    }

    return (
      <List.Item key={file.name}>
        <Card size="small" style={{ width: '100%' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <CodeOutlined />
                <Text strong>{file.name}</Text>
                <Text type="secondary">({(file.size / 1024).toFixed(1)} KB)</Text>
                {detectedLanguage && (
                  <Tag color={getLanguageColor(detectedLanguage)}>
                    {detectedLanguage}
                  </Tag>
                )}
              </Space>
              <Tag color={statusColor} icon={statusIcon}>
                {status === 'uploading' ? '处理中' : status === 'success' ? '成功' : '失败'}
              </Tag>
            </div>
            
            {status === 'uploading' && (
              <Progress percent={progress} size="small" />
            )}
            
            {status === 'success' && response && (
              <div>
                <Text type="success">{response.message}</Text>
                {response.processing_info && (
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      文件大小: {response.processing_info.file_size} 字节
                    </Text>
                  </div>
                )}
              </div>
            )}
            
            {status === 'error' && error && (
              <Text type="danger">{error}</Text>
            )}
          </Space>
        </Card>
      </List.Item>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card title="代码文件上传" style={{ marginBottom: 20 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="支持的编程语言"
            description={
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>主流语言:</Text> Python, JavaScript, TypeScript, Java, C++, Go, Rust
                </div>
                <div style={{ marginBottom: 8 }}>
                  <Text strong>其他语言:</Text> C#, PHP, Ruby, Swift, Kotlin, Scala
                </div>
                <div>
                  <Text strong>标记语言:</Text> HTML, CSS, SQL, JSON, YAML, Markdown
                </div>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">单个文件最大 10MB，系统将自动解析为函数、类、方法等代码块</Text>
                </div>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <div style={{ marginBottom: 16 }}>
            <Space>
              <Text>处理方式:</Text>
              <Switch
                checkedChildren="立即处理"
                unCheckedChildren="后台处理"
                checked={processImmediately}
                onChange={setProcessImmediately}
              />
              <Text type="secondary">
                {processImmediately ? '立即解析代码块并向量化' : '提交到后台队列处理'}
              </Text>
            </Space>
          </div>

          <Dragger
            multiple
            beforeUpload={handleFileUpload}
            showUploadList={false}
            disabled={uploading}
            style={{ padding: '20px' }}
          >
            <p className="ant-upload-drag-icon">
              <CodeOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽代码文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单个或批量上传多种编程语言的源代码文件。系统将智能解析代码结构。
            </p>
          </Dragger>
        </Space>
      </Card>

      {uploadList.length > 0 && (
        <Card 
          title="上传历史" 
          extra={
            <Button onClick={clearUploadList} size="small">
              清空列表
            </Button>
          }
        >
          <List
            dataSource={uploadList}
            renderItem={renderUploadItem}
            style={{ maxHeight: '400px', overflow: 'auto' }}
          />
        </Card>
      )}
    </div>
  );
};

export default EnhancedCodeUpload;