/**
 * 文档上传组件 - 生产版本
 * 完全使用真实API，无mock数据
 */

import React, { useState, useEffect } from 'react';
import {
  Form,
  Upload,
  Input,
  Select,
  Button,
  message,
  Space,
  Tag,
  Alert,
  Card,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  CodeOutlined,
  TeamOutlined,
  ProjectOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';

const { TextArea } = Input;
const { Option } = Select;

interface ClassificationOptions {
  business_doc_types: Array<{ id: number; name: string; category: string }>;
  demo_code_types: Array<{ id: number; name: string; category: string }>;
  checklist_types: Array<{ id: number; name: string; category: string }>;  // 新增规范文档类型
  teams: Array<{ id: number; name: string }>;
}

// 团队角色选项
const TEAM_ROLES = [
  { value: 'frontend', label: '前端' },
  { value: 'backend', label: '后端' },
  { value: 'test', label: '测试' },
  { value: 'planning', label: '规划' },
  { value: 'other', label: '其它' },
];

// 代码功能选项
const CODE_FUNCTIONS = [
  { value: 'api', label: 'API' },
  { value: 'pkg', label: 'PKG' },
  { value: 'cmd', label: 'CMD' },
  { value: 'unittest', label: '单测' },
  { value: 'other', label: '其它' },
];

interface DocumentUploadProps {
  onSuccess?: () => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onSuccess }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [documentType, setDocumentType] = useState<string>('');
  const [classifications, setClassifications] = useState<ClassificationOptions>({
    business_doc_types: [],
    demo_code_types: [],
    checklist_types: [],  // 新增规范文档类型初始化
    teams: [{ id: 1, name: 'xaas开发组' }], // 默认团队
  });
  const [loadingClassifications, setLoadingClassifications] = useState(false);

  // 获取当前用户信息
  const getCurrentUser = () => {
    const userStr = localStorage.getItem('current_user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }
    return null;
  };

  // 加载分类选项
  useEffect(() => {
    loadClassifications();
  }, []);

  const loadClassifications = async () => {
    setLoadingClassifications(true);
    try {
      const response = await fetch('http://localhost:8080/api/v1/classifications/options');
      
      if (response.ok) {
        const data = await response.json();
        setClassifications(data);
      } else {
        message.error('加载分类选项失败');
      }
    } catch (error) {
      console.error('加载分类选项失败:', error);
      message.error('加载分类选项失败');
    } finally {
      setLoadingClassifications(false);
    }
  };

  const handleUpload = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    // 获取当前用户
    const currentUser = getCurrentUser();
    if (!currentUser) {
      message.error('未找到用户信息，请重新登录');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    
    // 添加文件
    formData.append('file', fileList[0] as any);
    
    // 添加表单数据
    formData.append('doc_type', values.doc_type);
    // dev_type_id：如果有值才添加，避免发送空字符串导致422错误
    if (values.dev_type_id) {
      formData.append('dev_type_id', values.dev_type_id.toString());
    }
    formData.append('team_name', values.team_name || '');
    formData.append('project_name', values.project_name || '');
    // module_name：可选字段，有值才添加
    if (values.module_name) {
      formData.append('module_name', values.module_name);
    }
    // description：可选字段，有值才添加
    if (values.description) {
      formData.append('description', values.description);
    }
    formData.append('uploaded_by', currentUser.username || ''); // 添加上传用户
    
    // Demo代码特有字段
    if (values.doc_type === 'demo_code' && values.code_function) {
      // code_function可能是数组（mode="tags"），取第一个值
      const codeFunc = Array.isArray(values.code_function) 
        ? values.code_function[0] 
        : values.code_function;
      formData.append('code_function', codeFunc);
    }
    
    // 团队角色可能是数组（mode="tags"），取第一个值
    if (values.team_role) {
      const teamRole = Array.isArray(values.team_role)
        ? values.team_role[0]
        : values.team_role;
      formData.append('team_role', teamRole);
    }
    
    if (values.tags && values.tags.length > 0) {
      formData.append('tags', JSON.stringify(values.tags));
    }

    try {
      const response = await fetch('http://localhost:8080/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        message.success('文档上传成功！');
        form.resetFields();
        setFileList([]);
        setDocumentType('');
        onSuccess?.();
      } else {
        message.error(data.message || '上传失败');
      }
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败，请稍后重试');
    } finally {
      setUploading(false);
    }
  };

  const uploadProps: UploadProps = {
    onRemove: () => {
      setFileList([]);
    },
    beforeUpload: (file) => {
      setFileList([file]);
      return false; // 阻止自动上传
    },
    fileList,
    maxCount: 1,
  };

  const handleDocTypeChange = (value: string) => {
    setDocumentType(value);
    form.setFieldValue('dev_type_id', undefined);
  };

  // 获取当前文档类型的分类选项
  const getDevTypeOptions = () => {
    if (documentType === 'business_doc') {
      return classifications.business_doc_types;
    } else if (documentType === 'demo_code') {
      return classifications.demo_code_types;
    } else if (documentType === 'checklist') {
      return classifications.checklist_types;
    }
    return [];
  };

  return (
    <Card title="上传文档" bordered={false}>
      <Alert
        message="支持的文件类型"
        description="文档: .md, .txt, .doc, .docx, .pdf | 表格: .xlsx, .xls, .csv | 代码: .py, .js, .ts, .java, .go, .cpp 等"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleUpload}
        initialValues={{
          tags: [],
        }}
      >
        {/* 文件选择 */}
        <Form.Item
          label="选择文件"
          required
          tooltip="请选择要上传的文档文件"
        >
          <Upload 
            {...uploadProps}
            accept=".md,.txt,.doc,.docx,.pdf,.xlsx,.xls,.csv,.py,.js,.ts,.tsx,.jsx,.java,.go,.cpp,.c,.h,.hpp,.rs,.rb,.php,.swift,.kt,.json,.yaml,.yml,.xml,.toml,.ini,.sql,.sh,.bash,.ps1,.bat"
          >
            <Button icon={<UploadOutlined />} disabled={fileList.length > 0}>
              选择文件
            </Button>
          </Upload>
        </Form.Item>

        {/* 文档类型 */}
        <Form.Item
          name="doc_type"
          label="文档类型"
          rules={[{ required: true, message: '请选择文档类型' }]}
          tooltip="选择文档的类型"
        >
          <Select
            placeholder="请选择文档类型"
            onChange={handleDocTypeChange}
            size="large"
          >
            <Option value="business_doc">
              <Space>
                <FileTextOutlined style={{ color: '#1890ff' }} />
                项目文档
                <Tag color="blue">需求、设计、API文档等</Tag>
              </Space>
            </Option>
            <Option value="demo_code">
              <Space>
                <CodeOutlined style={{ color: '#52c41a' }} />
                Demo代码
                <Tag color="green">示例代码、工具包、单测等</Tag>
              </Space>
            </Option>
            <Option value="checklist">
              <Space>
                <CheckCircleOutlined style={{ color: '#faad14' }} />
                规范文档
                <Tag color="gold">代码规范、流程规范、检查清单等</Tag>
              </Space>
            </Option>
          </Select>
        </Form.Item>

        {/* 文档分类 */}
        {documentType && (
          <Form.Item
            name="dev_type_id"
            label={`${
              documentType === 'business_doc' 
                ? '文档' 
                : documentType === 'demo_code' 
                  ? '代码' 
                  : '规范'
            }分类`}
            rules={[{ required: true, message: '请选择分类' }]}
            tooltip="选择具体的文档分类"
          >
            <Select
              placeholder={`请选择${
                documentType === 'business_doc' 
                  ? '文档' 
                  : documentType === 'demo_code' 
                    ? '代码' 
                    : '规范'
              }分类`}
              loading={loadingClassifications}
              size="large"
            >
              {getDevTypeOptions().map((type) => (
                <Option key={type.id} value={type.id}>
                  <Tag>{type.category}</Tag> {type.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        )}

        {/* Demo代码的代码功能 */}
        {documentType === 'demo_code' && (
          <Form.Item
            name="code_function"
            label="代码功能"
            rules={[{ required: true, message: '请选择代码功能' }]}
            tooltip="选择代码的主要功能类型"
          >
            <Select
              mode="tags"
              placeholder="选择代码功能或自定义输入"
              maxTagCount={1}
              size="large"
            >
              {CODE_FUNCTIONS.map((func) => (
                <Option key={func.value} value={func.value}>
                  {func.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
        )}

        {/* 团队名称 */}
        <Form.Item
          name="team_name"
          label="所属团队"
          rules={[{ required: true, message: '请选择或输入团队名称' }]}
          tooltip="选择预设团队或输入新团队名称"
          initialValue="xaas开发组"
        >
          <Select
            mode="tags"
            placeholder="选择团队或输入新团队名称"
            maxTagCount={1}
            loading={loadingClassifications}
            size="large"
            suffixIcon={<TeamOutlined />}
          >
            <Option key="xaas" value="xaas开发组">
              xaas开发组
            </Option>
            {classifications.teams.filter(t => t.name !== 'xaas开发组').map((team) => (
              <Option key={team.id} value={team.name}>
                {team.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* 团队角色 */}
        <Form.Item
          name="team_role"
          label="团队角色"
          rules={[{ required: true, message: '请选择团队角色' }]}
          tooltip="选择您的团队角色"
        >
          <Select
            placeholder="选择团队角色"
            size="large"
            mode="tags"
            maxTagCount={1}
          >
            {TEAM_ROLES.map((role) => (
              <Option key={role.value} value={role.value}>
                {role.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* 项目名称 */}
        <Form.Item
          name="project_name"
          label="项目名称"
          rules={[{ required: true, message: '请输入项目名称' }]}
          tooltip="输入该文档所属的项目名称"
        >
          <Input
            placeholder="例如：用户管理系统、支付服务"
            prefix={<ProjectOutlined />}
            size="large"
          />
        </Form.Item>

        {/* 模块名称 */}
        <Form.Item
          name="module_name"
          label="模块名称"
          tooltip="（可选）输入具体的模块名称"
        >
          <Input
            placeholder="例如：用户认证、订单处理"
            size="large"
          />
        </Form.Item>

        {/* 标签 */}
        <Form.Item
          name="tags"
          label="标签"
          tooltip="（可选）添加标签便于搜索"
        >
          <Select
            mode="tags"
            placeholder="输入标签并按回车添加"
            size="large"
          >
            <Option value="重要">重要</Option>
            <Option value="常用">常用</Option>
            <Option value="参考">参考</Option>
          </Select>
        </Form.Item>

        {/* 描述 */}
        <Form.Item
          name="description"
          label="文档描述"
          tooltip="（可选）简要描述文档内容"
        >
          <TextArea
            rows={4}
            placeholder="请输入文档的简要描述..."
            maxLength={500}
            showCount
          />
        </Form.Item>

        {/* 提交按钮 */}
        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={uploading}
              icon={<UploadOutlined />}
              size="large"
            >
              {uploading ? '上传中...' : '开始上传'}
            </Button>
            <Button
              onClick={() => {
                form.resetFields();
                setFileList([]);
                setDocumentType('');
              }}
              disabled={uploading}
              size="large"
            >
              重置表单
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default DocumentUpload;
