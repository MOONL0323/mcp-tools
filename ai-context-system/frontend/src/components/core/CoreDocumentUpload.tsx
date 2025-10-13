/**
 * AI代码生成系统 - 核心文档上传组件
 * 符合原始方案：为AI Agent提供团队上下文
 */

import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Upload,
  Button,
  message,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Divider,
  Alert
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CodeOutlined,
  TeamOutlined,
  ProjectOutlined
} from '@ant-design/icons';
import { apiClient } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface UploadFormData {
  doc_type: 'business_doc' | 'demo_code';
  team: string;
  project: string;
  module?: string;
  tags: string[];
}

const CoreDocumentUpload: React.FC = () => {
  const [form] = Form.useForm();
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState<any[]>([]);

  // 预定义的团队和项目选项
  const teamOptions = [
    { value: 'frontend-team', label: '前端团队' },
    { value: 'backend-team', label: '后端团队' },
    { value: 'ai-team', label: 'AI算法团队' },
    { value: 'product-team', label: '产品团队' },
    { value: 'architecture-team', label: '架构团队' }
  ];

  const projectOptions = [
    { value: 'ai-context-system', label: 'AI上下文系统' },
    { value: 'user-platform', label: '用户平台' },
    { value: 'data-pipeline', label: '数据管道' },
    { value: 'mobile-app', label: '移动应用' },
    { value: 'api-gateway', label: 'API网关' }
  ];

  // 常用技术标签
  const commonTags = [
    'React', 'Vue', 'Angular', 'TypeScript', 'JavaScript',
    'Python', 'Java', 'Go', 'Node.js', 'Express',
    'FastAPI', 'Django', 'Spring Boot', 'MySQL', 'PostgreSQL',
    'Redis', 'MongoDB', 'Docker', 'Kubernetes', 'API设计',
    '系统架构', '数据库设计', '性能优化', '安全设计'
  ];

  const handleUpload = async () => {
    try {
      const values = await form.validateFields();
      
      if (fileList.length === 0) {
        message.error('请选择要上传的文件');
        return;
      }

      setUploading(true);

      const file = fileList[0];
      const formData = new FormData();
      
      formData.append('file', file);
      formData.append('doc_type', values.doc_type);
      formData.append('team', values.team);
      formData.append('project', values.project);
      if (values.module) {
        formData.append('module', values.module);
      }
      formData.append('tags', JSON.stringify(values.tags || []));

      const response = await apiClient.post('/api/v1/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        message.success('文档上传成功！AI Agent现在可以访问这个上下文信息。');
        form.resetFields();
        setFileList([]);
      } else {
        throw new Error(response.data.error || '上传失败');
      }

    } catch (error: any) {
      console.error('上传失败:', error);
      message.error(`上传失败: ${error.message || '请检查网络连接'}`);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    onRemove: (file: any) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file: any) => {
      setFileList([file]);
      return false; // 阻止自动上传
    },
    fileList,
    maxCount: 1,
  };

  return (
    <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={2}>
              <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              AI代码生成系统 - 文档上传
            </Title>
            <Paragraph type="secondary">
              上传团队的业务文档和Demo代码，为AI Agent提供上下文信息
            </Paragraph>
          </div>

          <Alert
            message="系统核心目标"
            description="通过MCP协议为AI Agent提供团队业务上下文，使生成的代码符合团队规范和业务场景。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              doc_type: 'business_doc',
              tags: []
            }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="文档类型"
                  name="doc_type"
                  rules={[{ required: true, message: '请选择文档类型' }]}
                >
                  <Select size="large">
                    <Option value="business_doc">
                      <Space>
                        <FileTextOutlined style={{ color: '#1890ff' }} />
                        业务文档
                      </Space>
                    </Option>
                    <Option value="demo_code">
                      <Space>
                        <CodeOutlined style={{ color: '#52c41a' }} />
                        Demo代码
                      </Space>
                    </Option>
                  </Select>
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item
                  label="所属团队"
                  name="team"
                  rules={[{ required: true, message: '请选择团队' }]}
                >
                  <Select size="large" placeholder="选择团队">
                    {teamOptions.map(team => (
                      <Option key={team.value} value={team.value}>
                        <Space>
                          <TeamOutlined />
                          {team.label}
                        </Space>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="所属项目"
                  name="project"
                  rules={[{ required: true, message: '请选择项目' }]}
                >
                  <Select size="large" placeholder="选择项目">
                    {projectOptions.map(project => (
                      <Option key={project.value} value={project.value}>
                        <Space>
                          <ProjectOutlined />
                          {project.label}
                        </Space>
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item
                  label="模块名称"
                  name="module"
                >
                  <Input size="large" placeholder="可选：具体模块名称" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item
              label="技术标签"
              name="tags"
            >
              <Select
                mode="multiple"
                size="large"
                placeholder="选择相关技术标签（可多选）"
                optionLabelProp="label"
              >
                {commonTags.map(tag => (
                  <Option key={tag} value={tag} label={tag}>
                    <Tag color="blue">{tag}</Tag>
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="文件上传"
              required
            >
              <Upload.Dragger {...uploadProps}>
                <p className="ant-upload-drag-icon">
                  <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到这里上传</p>
                <p className="ant-upload-hint">
                  支持 .md, .txt, .doc, .docx, .pdf, .py, .js, .ts, .java, .go 等格式
                </p>
              </Upload.Dragger>
            </Form.Item>

            <Divider />

            <Form.Item>
              <Space size="large">
                <Button
                  type="primary"
                  size="large"
                  loading={uploading}
                  onClick={handleUpload}
                  icon={<UploadOutlined />}
                >
                  {uploading ? '上传中...' : '上传文档'}
                </Button>
                <Button size="large" onClick={() => form.resetFields()}>
                  重置表单
                </Button>
              </Space>
            </Form.Item>
          </Form>

          <Alert
            message="上传后的效果"
            description={
              <ul style={{ marginBottom: 0 }}>
                <li>AI Agent可以通过MCP协议访问这些上下文信息</li>
                <li>生成的代码将符合团队的技术栈和业务场景</li>
                <li>可以引用相关的设计文档和Demo代码</li>
                <li>支持按团队、项目、技术标签进行智能检索</li>
              </ul>
            }
            type="success"
            showIcon
          />
        </Space>
      </Card>
    </div>
  );
};

export default CoreDocumentUpload;