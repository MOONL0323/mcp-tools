/**
 * 系统设置页面
 */

import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Button, 
  Space, 
  Typography, 
  Divider, 
  message,
  Modal,
  Row,
  Col,
  InputNumber,
  Alert
} from 'antd';
import { 
  SettingOutlined, 
  DatabaseOutlined, 
  ApiOutlined, 
  SafetyOutlined,
  ThunderboltOutlined 
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const SystemSettings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 系统配置数据
  const [settings, setSettings] = useState({
    // 基本设置
    systemName: 'AI上下文增强系统',
    systemDescription: '基于Graph RAG技术的智能上下文增强系统',
    language: 'zh-CN',
    timezone: 'Asia/Shanghai',
    
    // 数据库设置
    dbConnectionString: 'postgresql://localhost:5432/ai_context',
    dbMaxConnections: 100,
    dbTimeout: 30,
    
    // AI模型设置
    embeddingModel: 'qwen3-embedding-8b',
    embeddingDimension: 768,
    maxTokensPerChunk: 512,
    chunkOverlap: 50,
    
    // 知识图谱设置
    graphDatabaseUrl: 'neo4j://localhost:7687',
    graphDatabaseUser: 'neo4j',
    maxGraphNodes: 10000,
    
    // 安全设置
    enableAuthentication: true,
    sessionTimeout: 3600,
    maxLoginAttempts: 5,
    enableApiRateLimit: true,
    apiRateLimit: 1000,
    
    // 性能设置
    cacheEnabled: true,
    cacheSize: 1000,
    enableCompression: true,
    logLevel: 'INFO'
  });

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      // 模拟保存设置
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSettings({ ...settings, ...values });
      message.success('设置保存成功');
    } catch (error) {
      message.error('保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
    message.info('已重置为默认值');
  };

  const handleTestConnection = async (type: string) => {
    message.loading('正在测试连接...', 0);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.destroy();
      message.success(`${type}连接测试成功`);
    } catch (error) {
      message.destroy();
      message.error(`${type}连接测试失败`);
    }
  };

  return (
    <div>
      <Card style={{ marginBottom: '16px' }}>
        <Title level={3}>
          <SettingOutlined /> 系统设置
        </Title>
        <Paragraph type="secondary">
          配置系统的各项参数和功能选项
        </Paragraph>
      </Card>

      <Form
        form={form}
        layout="vertical"
        initialValues={settings}
        onFinish={handleSave}
      >
        <Row gutter={[24, 16]}>
          <Col span={12}>
            {/* 基本设置 */}
            <Card title="基本设置" style={{ marginBottom: '16px' }}>
              <Form.Item
                label="系统名称"
                name="systemName"
                rules={[{ required: true, message: '请输入系统名称' }]}
              >
                <Input placeholder="输入系统名称" />
              </Form.Item>

              <Form.Item
                label="系统描述"
                name="systemDescription"
              >
                <TextArea rows={3} placeholder="输入系统描述" />
              </Form.Item>

              <Form.Item label="语言" name="language">
                <Select>
                  <Option value="zh-CN">简体中文</Option>
                  <Option value="en-US">English</Option>
                  <Option value="ja-JP">日本語</Option>
                </Select>
              </Form.Item>

              <Form.Item label="时区" name="timezone">
                <Select>
                  <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                  <Option value="UTC">UTC (UTC+0)</Option>
                  <Option value="America/New_York">America/New_York (UTC-5)</Option>
                </Select>
              </Form.Item>
            </Card>

            {/* AI模型设置 */}
            <Card 
              title={
                <Space>
                  <ThunderboltOutlined />
                  AI模型设置
                </Space>
              }
              style={{ marginBottom: '16px' }}
            >
              <Form.Item label="嵌入模型" name="embeddingModel">
                <Select>
                  <Option value="qwen3-embedding-8b">Qwen3-Embedding-8B</Option>
                  <Option value="text-embedding-ada-002">OpenAI Ada-002</Option>
                  <Option value="bge-large-zh-v1.5">BGE-Large-ZH-v1.5</Option>
                </Select>
              </Form.Item>

              <Form.Item label="嵌入维度" name="embeddingDimension">
                <InputNumber min={256} max={2048} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item label="最大分块Token数" name="maxTokensPerChunk">
                <InputNumber min={128} max={2048} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item label="分块重叠Token数" name="chunkOverlap">
                <InputNumber min={0} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Card>
          </Col>

          <Col span={12}>
            {/* 数据库设置 */}
            <Card 
              title={
                <Space>
                  <DatabaseOutlined />
                  数据库设置
                </Space>
              }
              extra={
                <Button 
                  size="small" 
                  onClick={() => handleTestConnection('数据库')}
                >
                  测试连接
                </Button>
              }
              style={{ marginBottom: '16px' }}
            >
              <Form.Item label="连接字符串" name="dbConnectionString">
                <Input placeholder="postgresql://user:pass@localhost:5432/dbname" />
              </Form.Item>

              <Form.Item label="最大连接数" name="dbMaxConnections">
                <InputNumber min={10} max={500} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item label="连接超时(秒)" name="dbTimeout">
                <InputNumber min={5} max={300} style={{ width: '100%' }} />
              </Form.Item>
            </Card>

            {/* 知识图谱设置 */}
            <Card 
              title="知识图谱设置"
              extra={
                <Button 
                  size="small" 
                  onClick={() => handleTestConnection('图数据库')}
                >
                  测试连接
                </Button>
              }
              style={{ marginBottom: '16px' }}
            >
              <Form.Item label="图数据库URL" name="graphDatabaseUrl">
                <Input placeholder="neo4j://localhost:7687" />
              </Form.Item>

              <Form.Item label="用户名" name="graphDatabaseUser">
                <Input placeholder="neo4j" />
              </Form.Item>

              <Form.Item label="最大节点数" name="maxGraphNodes">
                <InputNumber min={1000} max={100000} style={{ width: '100%' }} />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        {/* 安全设置 */}
        <Card 
          title={
            <Space>
              <SafetyOutlined />
              安全设置
            </Space>
          }
          style={{ marginBottom: '16px' }}
        >
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <Form.Item label="启用身份验证" name="enableAuthentication" valuePropName="checked">
                <Switch />
              </Form.Item>

              <Form.Item label="会话超时(秒)" name="sessionTimeout">
                <InputNumber min={300} max={86400} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item label="最大登录尝试次数" name="maxLoginAttempts">
                <InputNumber min={3} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item label="启用API限流" name="enableApiRateLimit" valuePropName="checked">
                <Switch />
              </Form.Item>

              <Form.Item label="API限流(次/分钟)" name="apiRateLimit">
                <InputNumber min={100} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 性能设置 */}
        <Card title="性能设置" style={{ marginBottom: '16px' }}>
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <Form.Item label="启用缓存" name="cacheEnabled" valuePropName="checked">
                <Switch />
              </Form.Item>

              <Form.Item label="缓存大小(MB)" name="cacheSize">
                <InputNumber min={100} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col span={12}>
              <Form.Item label="启用压缩" name="enableCompression" valuePropName="checked">
                <Switch />
              </Form.Item>

              <Form.Item label="日志级别" name="logLevel">
                <Select>
                  <Option value="DEBUG">DEBUG</Option>
                  <Option value="INFO">INFO</Option>
                  <Option value="WARNING">WARNING</Option>
                  <Option value="ERROR">ERROR</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* 操作按钮 */}
        <Card>
          <Alert
            message="配置提醒"
            description="修改配置后需要重启系统以使部分设置生效。请确保在低峰期进行配置变更。"
            type="info"
            style={{ marginBottom: '16px' }}
          />

          <Space>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={<SettingOutlined />}
            >
              保存设置
            </Button>
            <Button onClick={handleReset}>
              重置为默认值
            </Button>
            <Button 
              danger 
              onClick={() => {
                Modal.confirm({
                  title: '确认重启系统?',
                  content: '重启将应用新配置，但会中断当前所有服务',
                  onOk: () => {
                    message.success('系统重启指令已发送');
                  }
                });
              }}
            >
              重启系统
            </Button>
          </Space>
        </Card>
      </Form>
    </div>
  );
};

export default SystemSettings;