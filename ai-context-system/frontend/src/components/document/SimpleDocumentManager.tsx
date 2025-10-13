/**
 * 简化的文档管理器组件
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Upload,
  message,
  Tooltip,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CloudUploadOutlined,
  NodeIndexOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';
import { DIContainer } from '../../core/DIContainer';
import { IDocumentService } from '../../interfaces/IDocumentService';
import { IClassificationService } from '../../interfaces/IClassificationService';
import type { IDocumentMetadata, DocumentUploadRequest } from '../../interfaces/IDocumentService';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export const SimpleDocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<IDocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<IDocumentMetadata | null>(null);
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([]);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  const documentService = DIContainer.getInstance().resolve<IDocumentService>('DocumentService');
  const classificationService = DIContainer.getInstance().resolve<IClassificationService>('ClassificationService');

  // 加载文档列表
  const loadDocuments = async () => {
    setLoading(true);
    try {
      const docs = await documentService.getDocuments();
      setDocuments(docs);
    } catch (error) {
      message.error('加载文档列表失败');
      console.error('加载文档失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // 上传文档
  const handleUpload = async (values: any) => {
    if (uploadFileList.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    try {
      const file = uploadFileList[0].originFileObj as File;
      const metadata: DocumentUploadRequest = {
        type: values.type || 'business_doc',
        team: values.team,
        project: values.project,
        module: values.module,
        dev_type: values.dev_type,
        title: values.title,
        description: values.description || '',
        access_level: values.access_level || 'team',
        tags: values.tags || [],
        version: values.version || '1.0'
      };

      await documentService.uploadDocument(file, metadata);
      message.success('文档上传成功');
      setUploadModalVisible(false);
      form.resetFields();
      setUploadFileList([]);
      loadDocuments();
    } catch (error) {
      message.error('文档上传失败');
      console.error('上传失败:', error);
    }
  };

  // 编辑文档
  const handleEdit = async (values: any) => {
    if (!selectedDocument) return;

    try {
      await documentService.updateDocument(selectedDocument.id, values);
      message.success('文档更新成功');
      setEditModalVisible(false);
      setSelectedDocument(null);
      editForm.resetFields();
      loadDocuments();
    } catch (error) {
      message.error('文档更新失败');
      console.error('更新失败:', error);
    }
  };

  // 删除文档
  const handleDelete = async (id: string) => {
    try {
      await documentService.deleteDocument(id);
      message.success('文档删除成功');
      loadDocuments();
    } catch (error) {
      message.error('文档删除失败');
      console.error('删除失败:', error);
    }
  };

  // 获取状态标签
  const getStatusTag = (status: 'processing' | 'completed' | 'failed') => {
    const statusConfig = {
      processing: { color: 'blue', text: '处理中' },
      completed: { color: 'green', text: '已完成' },
      failed: { color: 'red', text: '失败' }
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<IDocumentMetadata> = [
    {
      title: '文档标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text, record) => (
        <Space>
          <FileTextOutlined />
          <Tooltip title={text}>
            <Text strong style={{ cursor: 'pointer' }}>
              {text}
            </Text>
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '分类信息',
      key: 'classification',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Text type="secondary">团队: {record.team}</Text>
          <Text type="secondary">项目: {record.project}</Text>
          <Text type="secondary">模块: {record.module}</Text>
          <Text type="secondary">类型: {record.dev_type}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      align: 'center',
      render: (status: 'processing' | 'completed' | 'failed') => getStatusTag(status),
    },
    {
      title: '文档块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      align: 'center',
      render: (count) => (
        <Statistic
          value={count || 0}
          valueStyle={{ fontSize: '14px' }}
          prefix={<NodeIndexOutlined />}
        />
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      align: 'center',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                message.info('文档详情功能开发中');
              }}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedDocument(record);
                editForm.setFieldsValue(record);
                setEditModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个文档吗？"
              description="删除后将无法恢复，请谨慎操作。"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 统计信息
  const stats = {
    total: documents.length,
    processing: documents.filter(d => d.status === 'processing').length,
    completed: documents.filter(d => d.status === 'completed').length,
    failed: documents.filter(d => d.status === 'failed').length,
  };

  return (
    <div className="document-manager">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>文档管理</Title>
        
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic title="总文档数" value={stats.total} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="处理中" value={stats.processing} valueStyle={{ color: '#1890ff' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="已完成" value={stats.completed} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="失败" value={stats.failed} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
        </Row>

        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
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
      </div>

      {/* 文档表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 上传文档模态框 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false);
          form.resetFields();
          setUploadFileList([]);
        }}
        onOk={() => form.submit()}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpload}
        >
          <Form.Item
            label="文档标题"
            name="title"
            rules={[{ required: true, message: '请输入文档标题' }]}
          >
            <Input placeholder="请输入文档标题" />
          </Form.Item>
          
          <Form.Item
            label="文档描述"
            name="description"
          >
            <TextArea rows={3} placeholder="请输入文档描述（可选）" />
          </Form.Item>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                label="团队名称"
                name="team"
                rules={[{ required: true, message: '请输入团队名称' }]}
              >
                <Input placeholder="例如：frontend-team" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="项目名称"
                name="project"
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input placeholder="例如：ai-context-system" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                label="模块名称"
                name="module"
                rules={[{ required: true, message: '请输入模块名称' }]}
              >
                <Input placeholder="例如：frontend" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="文档类型"
                name="dev_type"
                rules={[{ required: true, message: '请输入文档类型' }]}
              >
                <Input placeholder="例如：requirement" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="选择文件"
            required
          >
            <Upload
              fileList={uploadFileList}
              onChange={({ fileList }) => setUploadFileList(fileList)}
              beforeUpload={() => false}
              accept=".pdf,.doc,.docx,.txt,.md"
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑文档模态框 */}
      <Modal
        title="编辑文档"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedDocument(null);
          editForm.resetFields();
        }}
        onOk={() => editForm.submit()}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEdit}
        >
          <Form.Item
            label="文档标题"
            name="title"
            rules={[{ required: true, message: '请输入文档标题' }]}
          >
            <Input placeholder="请输入文档标题" />
          </Form.Item>
          
          <Form.Item
            label="文档描述"
            name="description"
          >
            <TextArea rows={3} placeholder="请输入文档描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};