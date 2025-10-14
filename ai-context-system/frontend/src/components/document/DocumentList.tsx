/**
 * 文档列表组件 - 生产版本
 * 完全使用真实API，无mock数据
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Input,
  Card,
  Typography,
  Tooltip,
} from 'antd';
import {
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CodeOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;
const { Search } = Input;

interface Document {
  id: string;
  title: string;
  file_name?: string;
  doc_type: string;
  dev_type?: string;
  team?: string;
  project?: string;
  module?: string;
  tags?: string[];
  file_size: number;
  processing_status: string;
  uploaded_by?: string;
  created_at: string;
  chunk_count?: number;
  team_role?: string;
  code_function?: string;
  description?: string;
}

interface DocumentListProps {
  refresh?: number;
}

const DocumentList: React.FC<DocumentListProps> = ({ refresh }) => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 加载文档列表
  const loadDocuments = async (search?: string) => {
    setLoading(true);
    try {
      let url = 'http://localhost:8080/api/v1/documents/list';
      if (search) {
        url += `?search=${encodeURIComponent(search)}`;
      }

      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        // 后端直接返回数组
        if (Array.isArray(data)) {
          setDocuments(data);
        } else {
          message.error('数据格式错误');
        }
      } else {
        message.error('加载文档列表失败');
      }
    } catch (error) {
      console.error('加载文档失败:', error);
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除文档
  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8080/api/v1/documents/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('删除成功');
        loadDocuments();
      } else {
        const data = await response.json();
        message.error(data.message || '删除失败');
      }
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  // 查看详情
  const handleView = (record: Document) => {
    navigate(`/documents/${record.id}`);
  };

  // 搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
    loadDocuments(value);
  };

  useEffect(() => {
    loadDocuments();
  }, [refresh]);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 表格列定义
  const columns: ColumnsType<Document> = [
    {
      title: '文件名',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text strong>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 120,
      filters: [
        { text: '项目文档', value: 'business_doc' },
        { text: 'Demo代码', value: 'demo_code' },
      ],
      onFilter: (value, record) => record.doc_type === value,
      render: (type: string) => (
        <Tag
          color={type === 'business_doc' ? 'blue' : 'green'}
          icon={type === 'business_doc' ? <FileTextOutlined /> : <CodeOutlined />}
        >
          {type === 'business_doc' ? '项目文档' : 'Demo代码'}
        </Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'dev_type',
      key: 'dev_type',
      width: 120,
      render: (name: string) => (name ? <Tag color="purple">{name}</Tag> : '-'),
    },
    {
      title: '团队',
      dataIndex: 'team',
      key: 'team',
      width: 150,
      render: (name: string) => (
        <Space>
          <TeamOutlined style={{ color: '#1890ff' }} />
          <Text>{name}</Text>
        </Space>
      ),
    },
    {
      title: '团队角色',
      dataIndex: 'team_role',
      key: 'team_role',
      width: 100,
      render: (role: string) => {
        if (!role) return '-';
        const roleColors: Record<string, string> = {
          frontend: 'blue',
          backend: 'green',
          test: 'orange',
          planning: 'purple',
          other: 'default'
        };
        const roleLabels: Record<string, string> = {
          frontend: '前端',
          backend: '后端',
          test: '测试',
          planning: '规划',
          other: '其它'
        };
        return <Tag color={roleColors[role] || 'default'}>{roleLabels[role] || role}</Tag>;
      },
    },
    {
      title: '代码功能',
      dataIndex: 'code_function',
      key: 'code_function',
      width: 100,
      render: (func: string) => {
        if (!func) return '-';
        const funcColors: Record<string, string> = {
          api: 'blue',
          pkg: 'cyan',
          cmd: 'geekblue',
          unittest: 'orange',
          other: 'default'
        };
        const funcLabels: Record<string, string> = {
          api: 'API',
          pkg: 'PKG',
          cmd: 'CMD',
          unittest: '单测',
          other: '其它'
        };
        return <Tag color={funcColors[func] || 'default'}>{funcLabels[func] || func}</Tag>;
      },
    },
    {
      title: '项目',
      dataIndex: 'project',
      key: 'project',
      width: 150,
      ellipsis: true,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 180,
      render: (tags: string[]) => (
        <>
          {tags && tags.length > 0 ? (
            tags.slice(0, 2).map((tag, index) => (
              <Tag key={index} color="orange" style={{ marginBottom: 4 }}>
                {tag}
              </Tag>
            ))
          ) : (
            '-'
          )}
          {tags && tags.length > 2 && (
            <Tooltip title={tags.slice(2).join(', ')}>
              <Tag color="orange">+{tags.length - 2}</Tag>
            </Tooltip>
          )}
        </>
      ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      sorter: (a, b) => a.file_size - b.file_size,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'processing_status',
      key: 'processing_status',
      width: 100,
      filters: [
        { text: '已完成', value: 'completed' },
        { text: '处理中', value: 'processing' },
        { text: '失败', value: 'failed' },
        { text: '等待中', value: 'pending' },
      ],
      onFilter: (value, record) => record.processing_status === value,
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          completed: { color: 'success', text: '已完成' },
          processing: { color: 'processing', text: '处理中' },
          failed: { color: 'error', text: '失败' },
          pending: { color: 'default', text: '等待中' },
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '上传者',
      dataIndex: 'uploaded_by',
      key: 'uploaded_by',
      width: 120,
      render: (user: string) => user || '-',
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (time: string) => formatDate(time),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: Document) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个文档吗？此操作不可恢复。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除文档">
              <Button
                type="link"
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <Text strong>文档列表</Text>
          <Tag color="blue">{documents.length} 个文档</Tag>
        </Space>
      }
      extra={
        <Space>
          <Search
            placeholder="搜索文档..."
            allowClear
            onSearch={handleSearch}
            style={{ width: 250 }}
            prefix={<SearchOutlined />}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => loadDocuments(searchText)}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
      bordered={false}
    >
      <Table
        columns={columns}
        dataSource={documents}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1800 }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </Card>
  );
};

export default DocumentList;
