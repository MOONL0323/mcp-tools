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
  Typography
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined, 
  FileTextOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, UploadResponse } from '../services/api_v2';

const { Dragger } = Upload;
const { Text } = Typography;

interface EnhancedDocumentUploadProps {
  onUploadSuccess?: () => void;
}

interface UploadStatus {
  file: File;
  status: 'uploading' | 'success' | 'error';
  progress: number;
  response?: UploadResponse;
  error?: string;
}

const EnhancedDocumentUpload: React.FC<EnhancedDocumentUploadProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadList, setUploadList] = useState<UploadStatus[]>([]);
  const [processImmediately, setProcessImmediately] = useState(true);

  const supportedFormats = ['.pdf', '.docx', '.txt', '.md'];

  const handleFileUpload = async (file: File) => {
    // 检查文件类型
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!supportedFormats.includes(fileExtension)) {
      message.error(`不支持的文件格式: ${fileExtension}`);
      return false;
    }

    // 检查文件大小 (50MB)
    if (file.size > 50 * 1024 * 1024) {
      message.error('文件大小不能超过 50MB');
      return false;
    }

    const uploadStatus: UploadStatus = {
      file,
      status: 'uploading',
      progress: 0
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
      }, 200);

      const response = await KnowledgeGraphApi.uploadDocument(file, processImmediately);

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
        message.success(`文档上传成功: ${response.message}`);
        onUploadSuccess?.();
      } else {
        message.error(`文档上传失败: ${response.message}`);
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

  const renderUploadItem = (item: UploadStatus) => {
    const { file, status, progress, response, error } = item;
    
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
                <FileTextOutlined />
                <Text strong>{file.name}</Text>
                <Text type="secondary">({(file.size / 1024 / 1024).toFixed(2)} MB)</Text>
              </Space>
              <Tag color={statusColor} icon={statusIcon}>
                {status === 'uploading' ? '上传中' : status === 'success' ? '成功' : '失败'}
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
                      处理信息: {JSON.stringify(response.processing_info, null, 2)}
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
      <Card title="文档上传" style={{ marginBottom: 20 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="支持的文档格式"
            description={`${supportedFormats.join(', ')} - 单个文件最大 50MB`}
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
                {processImmediately ? '立即向量化并存储' : '提交到后台队列处理'}
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
              <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单个或批量上传。严格禁止上传公司数据或其他受限制的文件。
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

export default EnhancedDocumentUpload;