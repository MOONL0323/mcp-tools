/**
 * AI代码生成系统 - 核心应用
 * 专注原始方案的核心目标：为AI Agent提供团队上下文
 */

import React, { useState } from 'react';
import { Layout, Menu, Typography, Space, Tag, Alert, Button } from 'antd';
import {
  FileTextOutlined,
  UploadOutlined,
  UnorderedListOutlined,
  ApiOutlined,
  GithubOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import CoreDocumentUpload from './components/core/CoreDocumentUpload';
import CoreDocumentList from './components/core/CoreDocumentList';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;

const CoreApp: React.FC = () => {
  const [activeKey, setActiveKey] = useState('upload');

  const menuItems = [
    {
      key: 'upload',
      icon: <UploadOutlined />,
      label: '文档上传',
    },
    {
      key: 'list',
      icon: <UnorderedListOutlined />,
      label: '知识库',
    },
    {
      key: 'mcp',
      icon: <ApiOutlined />,
      label: 'MCP服务',
    },
  ];

  const renderContent = () => {
    switch (activeKey) {
      case 'upload':
        return <CoreDocumentUpload />;
      case 'list':
        return <CoreDocumentList />;
      case 'mcp':
        return (
          <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Title level={2}>
                <ApiOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                MCP服务配置
              </Title>
              
              <Alert
                message="MCP (Model Context Protocol) 服务"
                description="这是为AI Agent提供团队上下文的核心服务，通过MCP协议与Claude等AI工具集成。"
                type="info"
                showIcon
              />

              <div>
                <Title level={4}>服务状态</Title>
                <Space>
                  <Tag color="green">MCP服务器运行中</Tag>
                  <Tag color="blue">后端API正常</Tag>
                  <Tag color="orange">等待Claude配置</Tag>
                </Space>
              </div>

              <div>
                <Title level={4}>Claude Desktop 配置</Title>
                <Paragraph>
                  将以下配置添加到Claude Desktop的配置文件中：
                </Paragraph>
                <div style={{
                  backgroundColor: '#f6f6f6',
                  padding: 16,
                  borderRadius: 4,
                  fontFamily: 'monospace'
                }}>
                  <pre>{`{
  "mcpServers": {
    "ai-context-system": {
      "command": "node",
      "args": ["./mcp-server/dist/index.js"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}`}</pre>
                </div>
              </div>

              <div>
                <Title level={4}>可用的MCP工具</Title>
                <ul>
                  <li><strong>search_code_examples</strong> - 搜索团队的Demo代码</li>
                  <li><strong>get_design_docs</strong> - 获取相关业务设计文档</li>
                  <li><strong>get_coding_standards</strong> - 获取团队编码规范</li>
                  <li><strong>query_knowledge_graph</strong> - 查询知识图谱（待实现）</li>
                </ul>
              </div>

              <Alert
                message="使用方法"
                description={
                  <div>
                    <p>1. 确保后端服务运行在 localhost:8000</p>
                    <p>2. 启动MCP服务器: <code>npm run start</code></p>
                    <p>3. 在Claude Desktop中配置MCP服务器</p>
                    <p>4. 重启Claude Desktop，AI Agent即可访问团队上下文</p>
                  </div>
                }
                type="success"
                showIcon
              />
            </Space>
          </div>
        );
      default:
        return <CoreDocumentUpload />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FileTextOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 12 }} />
          <Title level={3} style={{ margin: 0 }}>
            AI代码生成系统
          </Title>
          <Tag color="blue" style={{ marginLeft: 12 }}>Graph RAG</Tag>
          <Tag color="green">MCP协议</Tag>
        </div>
        
        <Space>
          <Button
            type="link"
            icon={<GithubOutlined />}
            onClick={() => window.open('https://github.com/modelcontextprotocol/specification', '_blank')}
          >
            MCP协议
          </Button>
          <Button
            type="link"
            icon={<InfoCircleOutlined />}
          >
            系统说明
          </Button>
        </Space>
      </Header>

      <Layout>
        <Sider width={200} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <Menu
            mode="inline"
            selectedKeys={[activeKey]}
            onClick={({ key }) => setActiveKey(key)}
            items={menuItems}
            style={{ border: 'none', paddingTop: 16 }}
          />
        </Sider>

        <Content style={{ background: '#f5f5f5' }}>
          {renderContent()}
        </Content>
      </Layout>

      <div style={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        background: 'rgba(0,0,0,0.8)',
        color: 'white',
        padding: '8px 12px',
        borderRadius: 4,
        fontSize: 12
      }}>
        <Space>
          <Text style={{ color: 'white' }}>核心目标: 为AI Agent提供团队上下文</Text>
          <div style={{ width: 8, height: 8, backgroundColor: 'green', borderRadius: '50%' }}></div>
        </Space>
      </div>
    </Layout>
  );
};

export default CoreApp;