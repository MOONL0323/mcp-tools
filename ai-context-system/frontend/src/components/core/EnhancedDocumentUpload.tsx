/**
 * 改进的文档上传组件 - 支持动态分类
 * 从API获取团队、文档类型等分类信息
 */

import React, { useState, useEffect } from 'react';
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
  Alert,
  Spin
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CodeOutlined,
  TeamOutlined,
  ProjectOutlined,
  PlusOutlined
} from '@ant-design/icons';
import { apiClient } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface ClassificationOptions {
  business_doc_types: Array<{
    id: string;
    name: string;
    display_name: string;
    description: string;
    icon: string;
  }>;
  demo_code_types: Array<{
    id: string;
    name: string;
    display_name: string;
    description: string;
    icon: string;
  }>;
  teams: Array<{
    id: string;
    name: string;
    display_name: string;
    description: string;
  }>;
}

const EnhancedDocumentUpload: React.FC = () => {
  const [form] = Form.useForm();
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [fileList, setFileList] = useState<any[]>([]);
  const [docType, setDocType] = useState<'business_doc' | 'demo_code'>('business_doc');
  const [classifications, setClassifications] = useState<ClassificationOptions | null>(null);
  const [customTeam, setCustomTeam] = useState('');
  const [showCustomTeam, setShowCustomTeam] = useState(false);

  // 加载分类选项
  useEffect(() => {
    loadClassifications();
  }, []);

  const loadClassifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/v1/classifications/options');
      
      if (response.success && response.data) {
        setClassifications(response.data);
      } else {
        message.error('加载分类选项失败');
      }
    } catch (error) {
      console.error('加载分类失败:', error);
      message.error('加载分类选项失败，请刷新页面重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDocTypeChange = (value: 'business_doc' | 'demo_code') => {
    setDocType(value);
    // 清空文档子类型
    form.setFieldsValue({ dev_type_id: undefined });
  };

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
      formData.append('dev_type_id', values.dev_type_id);
      
      // 使用自定义团队名或选择的团队
      const teamName = showCustomTeam ? customTeam : values.team;
      formData.append('team_name', teamName);
      formData.append('project_name', values.project);
      
      if (values.module) {
        formData.append('module_name', values.module);
      }
      formData.append('tags', JSON.stringify(values.tags || []));
      
      // 从localStorage获取用户信息
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      formData.append('uploaded_by', user.id || 'anonymous');

      const response = await apiClient.post('/v1/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.success) {
        message.success('文档上传成功！AI Agent现在可以访问这个上下文信息。');
        form.resetFields();
        setFileList([]);
        setShowCustomTeam(false);
        setCustomTeam('');
      } else {
        throw new Error(response.error || '上传失败');
      }

    } catch (error: any) {
      console.error('上传失败:', error);
      message.error(`上传失败: ${error.message || '请检查网络连接'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = ({ fileList }: any) => {
    setFileList(fileList.slice(-1)); // 只保留最后一个文件
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>加载分类选项...</div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={3}>
            <UploadOutlined /> 上传团队文档
          </Title>
          <Paragraph type="secondary">
            为AI Agent提供团队的项目文档和示例代码，增强代码生成的上下文理解
          </Paragraph>
        </div>

        <Alert
          message="上传提示"
          description="上传的文档将被处理并存储，供AI Agent在代码生成时参考。支持的文件格式：.md, .txt, .py, .go, .js, .java等。"
          type="info"
          showIcon
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
                name="doc_type"
                label="文档类型"
                rules={[{ required: true, message: '请选择文档类型' }]}
              >
                <Select
                  size="large"
                  onChange={handleDocTypeChange}
                  placeholder="选择文档类型"
                >
                  <Option value="business_doc">
                    <Space>
                      <FileTextOutlined />
                      项目文档
                    </Space>
                  </Option>
                  <Option value="demo_code">
                    <Space>
                      <CodeOutlined />
                      Demo代码
                    </Space>
                  </Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="dev_type_id"
                label={docType === 'business_doc' ? '文档分类' : '代码分类'}
                rules={[{ required: true, message: '请选择分类' }]}
              >
                <Select size="large" placeholder="选择具体分类">
                  {docType === 'business_doc' 
                    ? classifications?.business_doc_types.map(type => (
                        <Option key={type.id} value={type.id}>
                          {type.display_name}
                          {type.description && (
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                              - {type.description}
                            </Text>
                          )}
                        </Option>
                      ))
                    : classifications?.demo_code_types.map(type => (
                        <Option key={type.id} value={type.id}>
                          {type.display_name}
                          {type.description && (
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                              - {type.description}
                            </Text>
                          )}
                        </Option>
                      ))
                  }
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label={
                  <Space>
                    <TeamOutlined />
                    所属团队
                    <Button 
                      type="link" 
                      size="small"
                      icon={<PlusOutlined />}
                      onClick={() => setShowCustomTeam(!showCustomTeam)}
                    >
                      {showCustomTeam ? '选择现有' : '自定义'}
                    </Button>
                  </Space>
                }
              >
                {showCustomTeam ? (
                  <Input
                    size="large"
                    value={customTeam}
                    onChange={(e) => setCustomTeam(e.target.value)}
                    placeholder="输入团队名称（如：前端、后端、测试等）"
                  />
                ) : (
                  <Form.Item
                    name="team"
                    noStyle
                    rules={[{ required: !showCustomTeam, message: '请选择团队' }]}
                  >
                    <Select size="large" placeholder="选择团队" showSearch>
                      {classifications?.teams.map(team => (
                        <Option key={team.id} value={team.name}>
                          {team.display_name}
                          {team.description && (
                            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                              - {team.description}
                            </Text>
                          )}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                )}
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item
                name="project"
                label={
                  <Space>
                    <ProjectOutlined />
                    所属项目
                  </Space>
                }
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input size="large" placeholder="输入项目名称" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="module"
            label="模块名称（可选）"
          >
            <Input size="large" placeholder="如：user-service, api-gateway" />
          </Form.Item>

          <Form.Item
            name="tags"
            label="技术标签"
          >
            <Select
              mode="tags"
              size="large"
              placeholder="选择或输入技术标签"
              style={{ width: '100%' }}
            >
              {['React', 'Vue', 'Python', 'Go', 'TypeScript', 'FastAPI', 'API设计', '系统架构'].map(tag => (
                <Option key={tag} value={tag}>{tag}</Option>
              ))}
            </Select>
          </Form.Item>

          <Divider />

          <Form.Item
            label="选择文件"
            required
          >
            <Upload
              fileList={fileList}
              onChange={handleFileChange}
              beforeUpload={() => false}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />} size="large">
                点击选择文件
              </Button>
            </Upload>
            <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
              支持格式: .md, .txt, .py, .go, .js, .ts, .java, .cpp, .c, .h等
            </Text>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              size="large"
              onClick={handleUpload}
              loading={uploading}
              icon={<UploadOutlined />}
              block
            >
              {uploading ? '上传中...' : '开始上传'}
            </Button>
          </Form.Item>
        </Form>
      </Space>
    </Card>
  );
};

export default EnhancedDocumentUpload;
