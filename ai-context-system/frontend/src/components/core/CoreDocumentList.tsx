/**
 * AI代码生成系统 - 核心文档列表组件
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Space,
  Tag,
  Button,
  Input,
  Select,
  message,
  Typography,
  Modal,
  Descriptions,
  Alert
} from 'antd';
import {
  FileTextOutlined,
  CodeOutlined,
  EyeOutlined,
  DeleteOutlined,
  SearchOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface DocumentItem {
  id: number;
  title: string;
  doc_type: 'business_doc' | 'demo_code';
  team: string;
  project: string;
  module?: string;
  tags: string[];
  file_size: number;
  created_at: string;
}

const CoreDocumentList: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedTeam, setSelectedTeam] = useState<string>();
  const [selectedProject, setSelectedProject] = useState<string>();
  const [selectedDocType, setSelectedDocType] = useState<string>();
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);

  const teamOptions = [
    { value: 'frontend-team', label: '前端团队' },
    { value: 'backend-team', label: '后端团队' },
    { value: 'ai-team', label: 'AI算法团队' },
    { value: 'product-team', label: '产品团队' },
    { value: 'architecture-team', label: '架构团队' }
  ];

  const loadDocuments = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (selectedTeam) params.append('team', selectedTeam);
      if (selectedProject) params.append('project', selectedProject);
      if (selectedDocType) params.append('doc_type', selectedDocType);
      
      // 修复: API现在直接返回文档数组
      const docs = await api.documents.list(Object.fromEntries(params));
      setDocuments(Array.isArray(docs) ? docs : []);
      
    } catch (error: any) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档列表失败');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const searchDocuments = async () => {
    if (!searchText.trim()) {
      loadDocuments();
      return;
    }

    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      params.append('query', searchText);
      if (selectedTeam) params.append('team', selectedTeam);
      if (selectedProject) params.append('project', selectedProject);
      if (selectedDocType) params.append('doc_type', selectedDocType);
      
      const response = await api.documents.search(Object.fromEntries(params));
      
      // 修复: API现在直接返回文档数组
      setDocuments(Array.isArray(response) ? response : []);
      
    } catch (error: any) {
      console.error('搜索失败:', error);
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const viewDocument = async (id: number) => {
    try {
      // 修复: API现在直接返回文档对象
      const doc = await api.documents.get(id.toString());
      setSelectedDocument(doc);
      setDetailModalVisible(true);
      
    } catch (error: any) {
      console.error('获取文档详情失败:', error);
      message.error('获取文档详情失败');
    }
  };

  const deleteDocument = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文档吗？删除后AI Agent将无法访问该上下文信息。',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await api.documents.delete(id.toString());
          
          if (response.data.success) {
            message.success('文档删除成功');
            loadDocuments();
          } else {
            throw new Error(response.data.error || '删除失败');
          }
        } catch (error: any) {
          console.error('删除失败:', error);
          message.error('删除失败');
        }
      }
    });
  };

  useEffect(() => {
    loadDocuments();
  }, [selectedTeam, selectedProject, selectedDocType]);

  const columns = [
    {
      title: '文档名称',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: DocumentItem) => (
        <Space>
          {record.doc_type === 'business_doc' ? 
            <FileTextOutlined style={{ color: '#1890ff' }} /> : 
            <CodeOutlined style={{ color: '#52c41a' }} />
          }
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      render: (type: string) => (
        <Tag color={type === 'business_doc' ? 'blue' : 'green'}>
          {type === 'business_doc' ? '业务文档' : 'Demo代码'}
        </Tag>
      ),
    },
    {
      title: '团队',
      dataIndex: 'team',
      key: 'team',
      render: (team: string) => (
        <Space>
          <TeamOutlined />
          <Text>{teamOptions.find(t => t.value === team)?.label || team}</Text>
        </Space>
      ),
    },
    {
      title: '项目',
      dataIndex: 'project',
      key: 'project',
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      render: (module: string) => module || '-',
    },
    {
      title: '技术标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space wrap>
          {tags?.slice(0, 3).map((tag, index) => (
            <Tag key={index}>{tag}</Tag>
          ))}
          {tags?.length > 3 && <Text type="secondary">+{tags.length - 3}</Text>}
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => {
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / 1024 / 1024).toFixed(1)} MB`;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: DocumentItem) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => viewDocument(record.id)}
          >
            查看
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteDocument(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={2}>
              <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              团队知识库
            </Title>
            <Alert
              message="这些文档和代码为AI Agent提供团队上下文，确保生成的代码符合团队规范"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          </div>

          {/* 筛选和搜索 */}
          <Space wrap>
            <Input
              placeholder="搜索文档内容..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={searchDocuments}
              style={{ width: 250 }}
              suffix={<SearchOutlined onClick={searchDocuments} style={{ cursor: 'pointer' }} />}
            />
            <Select
              placeholder="选择团队"
              value={selectedTeam}
              onChange={setSelectedTeam}
              allowClear
              style={{ width: 150 }}
            >
              {teamOptions.map(team => (
                <Option key={team.value} value={team.value}>{team.label}</Option>
              ))}
            </Select>
            <Input
              placeholder="项目名称"
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              style={{ width: 120 }}
            />
            <Select
              placeholder="文档类型"
              value={selectedDocType}
              onChange={setSelectedDocType}
              allowClear
              style={{ width: 120 }}
            >
              <Option value="business_doc">业务文档</Option>
              <Option value="demo_code">Demo代码</Option>
            </Select>
            <Button onClick={() => {
              setSearchText('');
              setSelectedTeam(undefined);
              setSelectedProject(undefined);
              setSelectedDocType(undefined);
              loadDocuments();
            }}>
              重置
            </Button>
          </Space>

          {/* 文档表格 */}
          <Table
            columns={columns}
            dataSource={documents}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 个文档`,
            }}
          />
        </Space>
      </Card>

      {/* 文档详情Modal */}
      <Modal
        title="文档详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedDocument && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="文档名称">{selectedDocument.title}</Descriptions.Item>
              <Descriptions.Item label="文档类型">
                <Tag color={selectedDocument.doc_type === 'business_doc' ? 'blue' : 'green'}>
                  {selectedDocument.doc_type === 'business_doc' ? '业务文档' : 'Demo代码'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="团队">{selectedDocument.team}</Descriptions.Item>
              <Descriptions.Item label="项目">{selectedDocument.project}</Descriptions.Item>
              <Descriptions.Item label="模块">{selectedDocument.module || '-'}</Descriptions.Item>
              <Descriptions.Item label="文件路径">{selectedDocument.file_path}</Descriptions.Item>
              <Descriptions.Item label="技术标签" span={2}>
                <Space wrap>
                  {selectedDocument.tags?.map((tag: string, index: number) => (
                    <Tag key={index}>{tag}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
            </Descriptions>
            
            <div>
              <Text strong>文档内容：</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                backgroundColor: '#f6f6f6', 
                borderRadius: 4,
                maxHeight: 300,
                overflow: 'auto'
              }}>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontSize: 12 }}>
                  {selectedDocument.content}
                </pre>
              </div>
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default CoreDocumentList;