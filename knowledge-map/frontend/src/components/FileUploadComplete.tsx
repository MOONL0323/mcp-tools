import React, { useState, useCallback } from 'react';
import { Upload, message, Card, Progress, Input, Button, Spin, Typography, Tabs } from 'antd';
import { CloudUploadOutlined, FileTextOutlined, InboxOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { KnowledgeGraphApi } from '../services/api';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Dragger } = Upload;

interface UploadedItem {
  uid: string;
  name: string;
  status: 'uploading' | 'done' | 'error';
  percent: number;
  response?: any;
  error?: string;
  type: 'file' | 'text';
}

export const FileUploadComplete: React.FC = () => {
  const [uploadList, setUploadList] = useState<UploadedItem[]>([]);
  const [textContent, setTextContent] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('text');

  // 文件上传处理
  const handleFileUpload = useCallback(async (file: File) => {
    const uploadedItem: UploadedItem = {
      uid: Date.now().toString(),
      name: file.name,
      status: 'uploading',
      percent: 0,
      type: 'file'
    };

    setUploadList(prev => [...prev, uploadedItem]);

    try {
      const response = await KnowledgeGraphApi.uploadFile(file, true);
      const taskId = response.task_id;
      
      message.success('文件上传成功，正在处理...');
      
      // 轮询任务状态
      const pollStatus = async () => {
        try {
          const status = await KnowledgeGraphApi.getTaskStatus(taskId);
          
          // 更新进度
          setUploadList(prev => prev.map(item => 
            item.uid === uploadedItem.uid 
              ? { ...item, percent: status.progress || 50 }
              : item
          ));
          
          if (status.status === 'completed') {
            setUploadList(prev => prev.map(item => 
              item.uid === uploadedItem.uid 
                ? { ...item, status: 'done', percent: 100, response: status.result }
                : item
            ));
            message.success(status.message || '文件处理完成');
          } else if (status.status === 'failed') {
            setUploadList(prev => prev.map(item => 
              item.uid === uploadedItem.uid 
                ? { ...item, status: 'error', error: status.error }
                : item
            ));
            message.error(status.error || '文件处理失败');
          } else {
            // 继续轮询
            setTimeout(pollStatus, 1000);
          }
        } catch (error) {
          console.error('轮询任务状态失败:', error);
          setUploadList(prev => prev.map(item => 
            item.uid === uploadedItem.uid 
              ? { ...item, status: 'error', error: '状态查询失败' }
              : item
          ));
        }
      };
      
      setTimeout(pollStatus, 1000);
    } catch (error) {
      console.error('文件上传失败:', error);
      setUploadList(prev => prev.map(item => 
        item.uid === uploadedItem.uid 
          ? { ...item, status: 'error', error: '网络错误' }
          : item
      ));
      message.error('文件上传失败');
    }
  }, []);

  // 文本添加处理
  const handleTextUpload = async () => {
    if (!textContent.trim()) {
      message.error('请输入文本内容');
      return;
    }

    setIsProcessing(true);
    
    const textItem: UploadedItem = {
      uid: Date.now().toString(),
      name: textTitle || '用户文本',
      status: 'uploading',
      percent: 0,
      type: 'text'
    };

    setUploadList(prev => [...prev, textItem]);
    
    try {
      const response = await KnowledgeGraphApi.addText({
        content: textContent,
        title: textTitle || '用户文本',
        save_graph: true
      });

      const taskId = response.task_id;
      message.success('文本添加成功，正在处理...');
      
      // 轮询任务状态
      const pollStatus = async () => {
        try {
          const status = await KnowledgeGraphApi.getTaskStatus(taskId);
          
          // 更新进度
          setUploadList(prev => prev.map(item => 
            item.uid === textItem.uid 
              ? { ...item, percent: status.progress || 50 }
              : item
          ));
          
          if (status.status === 'completed') {
            setUploadList(prev => prev.map(item => 
              item.uid === textItem.uid 
                ? { ...item, status: 'done', percent: 100, response: status.result }
                : item
            ));
            message.success(status.message || '文本处理完成');
            setTextContent('');
            setTextTitle('');
            setIsProcessing(false);
          } else if (status.status === 'failed') {
            setUploadList(prev => prev.map(item => 
              item.uid === textItem.uid 
                ? { ...item, status: 'error', error: status.error }
                : item
            ));
            message.error(status.error || '文本处理失败');
            setIsProcessing(false);
          } else {
            // 继续轮询
            setTimeout(pollStatus, 1000);
          }
        } catch (error) {
          console.error('轮询任务状态失败:', error);
          message.error('获取任务状态失败');
          setIsProcessing(false);
        }
      };
      
      setTimeout(pollStatus, 1000);
    } catch (error) {
      console.error('文本添加失败:', error);
      message.error('文本添加失败');
      setIsProcessing(false);
    }
  };

  const uploadProps = {
    name: 'file',
    multiple: true,
    showUploadList: false,
    beforeUpload: (file: File) => {
      handleFileUpload(file);
      return false; // 阻止自动上传
    },
    accept: '.txt,.md,.pdf,.docx',
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={4}>
          <CloudUploadOutlined style={{ marginRight: '8px' }} />
          添加文档到知识库
        </Title>
        
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="文本输入" key="text" icon={<FileTextOutlined />}>
            <div>
              <div style={{ marginBottom: '16px' }}>
                <Text strong>文档标题 (可选):</Text>
                <Input
                  placeholder="请输入文档标题..."
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                  style={{ marginTop: '8px' }}
                  disabled={isProcessing}
                />
              </div>
              
              <div style={{ marginBottom: '16px' }}>
                <Text strong>文本内容:</Text>
                <TextArea
                  placeholder="请输入要添加到知识库的文本内容..."
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  rows={10}
                  style={{ marginTop: '8px' }}
                  disabled={isProcessing}
                />
              </div>
              
              <Button
                type="primary"
                icon={<CloudUploadOutlined />}
                onClick={handleTextUpload}
                loading={isProcessing}
                disabled={!textContent.trim()}
                size="large"
              >
                {isProcessing ? '处理中...' : '添加到知识库'}
              </Button>
            </div>
          </TabPane>
          
          <TabPane tab="文件上传" key="file" icon={<InboxOutlined />}>
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个或批量上传。支持格式: .txt, .md, .pdf, .docx
              </p>
            </Dragger>
          </TabPane>
        </Tabs>
      </Card>

      {/* 上传历史 */}
      {uploadList.length > 0 && (
        <Card title="处理历史" style={{ marginTop: '24px' }}>
          {uploadList.map(item => (
            <div key={item.uid} style={{ 
              display: 'flex', 
              alignItems: 'center', 
              padding: '12px 0',
              borderBottom: '1px solid #f0f0f0' 
            }}>
              {item.status === 'done' ? (
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '12px', fontSize: '16px' }} />
              ) : item.status === 'error' ? (
                <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: '12px', fontSize: '16px' }} />
              ) : (
                <Spin size="small" style={{ marginRight: '12px' }} />
              )}
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                  {item.type === 'file' ? (
                    <InboxOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                  ) : (
                    <FileTextOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
                  )}
                  <Text strong>{item.name}</Text>
                  {item.response && (
                    <Text type="secondary" style={{ marginLeft: '8px', fontSize: '12px' }}>
                      ({item.response.document_count} 个文档块)
                    </Text>
                  )}
                </div>
                
                {item.status === 'uploading' && (
                  <Progress percent={item.percent} size="small" style={{ marginTop: '4px' }} />
                )}
                
                {item.status === 'error' && (
                  <Text type="danger" style={{ fontSize: '12px' }}>
                    {item.error}
                  </Text>
                )}
                
                {item.status === 'done' && (
                  <Text type="success" style={{ fontSize: '12px' }}>
                    处理完成
                  </Text>
                )}
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
};