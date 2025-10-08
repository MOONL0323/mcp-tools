import React, { useState, useEffect } from 'react';
import { Layout, Tabs, message, Spin, Alert, Button } from 'antd';
import { FileSearchOutlined, ReloadOutlined, ApartmentOutlined, SearchOutlined, UploadOutlined, FileTextOutlined, CodeOutlined } from '@ant-design/icons';
import { KnowledgeGraphApi, SystemStatus as SystemStatusType } from './services/api';
import { FileUploadComplete } from './components/FileUploadComplete';
import SystemStatus from './components/SystemStatus';
import GraphVisualization from './components/GraphVisualization';
import DocumentUpload from './components/DocumentUpload';
import CodeUpload from './components/CodeUpload';
import DocumentSearch from './components/DocumentSearch';
import CodeSearch from './components/CodeSearch';
import './App.css';

const { Header, Content } = Layout;

interface AppState {
  loading: boolean;
  connected: boolean;
  error: string | null;
  apiTest: string;
  showMainApp: boolean;
  systemStatus: SystemStatusType | null;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    loading: true,
    connected: false,
    error: null,
    apiTest: '',
    showMainApp: false,
    systemStatus: null
  });
  const [activeTab, setActiveTab] = useState('doc-search');

  // 测试API连接
  const testConnection = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // 测试健康检查
      await KnowledgeGraphApi.healthCheck();
      
      // 测试系统状态
      const status = await KnowledgeGraphApi.getSystemStatus();
      
      setState({
        loading: false,
        connected: true,
        error: null,
        apiTest: `API连接成功！文档数量: ${status.document_count}, 图节点: ${status.graph_nodes}`,
        showMainApp: false,
        systemStatus: status
      });
      
      message.success('API连接成功');
    } catch (error) {
      console.error('API测试失败:', error);
      setState({
        loading: false,
        connected: false,
        error: error instanceof Error ? error.message : '连接失败',
        apiTest: '',
        showMainApp: false,
        systemStatus: null
      });
      
      message.error('API连接失败，请确保后端服务已启动');
    }
  };

  // 刷新系统状态
  const refreshStatus = async () => {
    try {
      const status = await KnowledgeGraphApi.getSystemStatus();
      setState(prev => ({ ...prev, systemStatus: status }));
      message.success('状态已刷新');
    } catch (error) {
      message.error('刷新状态失败');
    }
  };

  // 页面加载时自动测试连接
  useEffect(() => {
    testConnection();
  }, []);

  // 显示主应用
  const handleShowMainApp = () => {
    setState(prev => ({ ...prev, showMainApp: true }));
  };

  // 如果正在加载
  if (state.loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Spin size="large" />
        <div>正在连接API服务...</div>
      </div>
    );
  }

  // 如果未连接且未显示主应用
  if (!state.connected && !state.showMainApp) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        padding: '24px'
      }}>
        <Alert
          message="API连接失败"
          description={
            <div>
              <p>{state.error}</p>
              <p>请确保后端服务已启动（端口8001）</p>
              <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                <Button type="primary" icon={<ReloadOutlined />} onClick={testConnection}>
                  重新连接
                </Button>
                <Button onClick={handleShowMainApp}>
                  仍然继续
                </Button>
              </div>
            </div>
          }
          type="error"
          showIcon
          style={{ maxWidth: '500px' }}
        />
      </div>
    );
  }

  // 标签页配置
  const tabItems = [
    {
      key: 'doc-search',
      label: (
        <span>
          <SearchOutlined />
          文档搜索
        </span>
      ),
      children: (
        <Layout style={{ height: 'calc(100vh - 120px)' }}>
          <Layout.Sider 
            width={400} 
            className="app-sider"
            breakpoint="lg"
            collapsedWidth="0"
            style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}
          >
            <div className="sider-content" style={{ padding: '16px' }}>
              <FileUploadComplete />
              {state.systemStatus && (
                <SystemStatus 
                  status={state.systemStatus} 
                  onRefresh={refreshStatus}
                />
              )}
            </div>
          </Layout.Sider>
          
          <Layout className="main-layout">
            <Content className="app-content" style={{ padding: '16px' }}>
              <DocumentSearch />
            </Content>
          </Layout>
        </Layout>
      )
    },
    {
      key: 'code-search',
      label: (
        <span>
          <CodeOutlined />
          代码搜索
        </span>
      ),
      children: (
        <Layout style={{ height: 'calc(100vh - 120px)' }}>
          <Layout.Sider 
            width={400} 
            className="app-sider"
            breakpoint="lg"
            collapsedWidth="0"
            style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}
          >
            <div className="sider-content" style={{ padding: '16px' }}>
              <FileUploadComplete />
              {state.systemStatus && (
                <SystemStatus 
                  status={state.systemStatus} 
                  onRefresh={refreshStatus}
                />
              )}
            </div>
          </Layout.Sider>
          
          <Layout className="main-layout">
            <Content className="app-content" style={{ padding: '16px' }}>
              <CodeSearch />
            </Content>
          </Layout>
        </Layout>
      )
    },
    {
      key: 'graph',
      label: (
        <span>
          <ApartmentOutlined />
          图谱可视化
        </span>
      ),
      children: <GraphVisualization />
    },
    {
      key: 'documents',
      label: (
        <span>
          <FileTextOutlined />
          文档上传
        </span>
      ),
      children: (
        <div>
          <DocumentUpload 
            onUploadSuccess={refreshStatus}
            onUploadError={(error) => message.error(error)}
          />
          {state.systemStatus && (
            <div style={{ padding: '0 24px 24px' }}>
              <SystemStatus 
                status={state.systemStatus} 
                onRefresh={refreshStatus}
              />
            </div>
          )}
        </div>
      )
    },
    {
      key: 'code',
      label: (
        <span>
          <CodeOutlined />
          代码上传
        </span>
      ),
      children: (
        <div>
          <CodeUpload 
            onUploadSuccess={refreshStatus}
            onUploadError={(error) => message.error(error)}
          />
          {state.systemStatus && (
            <div style={{ padding: '0 24px 24px' }}>
              <SystemStatus 
                status={state.systemStatus} 
                onRefresh={refreshStatus}
              />
            </div>
          )}
        </div>
      )
    },
    {
      key: 'upload',
      label: (
        <span>
          <UploadOutlined />
          文档管理（兼容）
        </span>
      ),
      children: (
        <div style={{ padding: '24px' }}>
          <FileUploadComplete />
          {state.systemStatus && (
            <div style={{ marginTop: '24px' }}>
              <SystemStatus 
                status={state.systemStatus} 
                onRefresh={refreshStatus}
              />
            </div>
          )}
        </div>
      )
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#001529', 
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          color: '#fff',
          fontSize: '18px',
          fontWeight: 600
        }}>
          <FileSearchOutlined style={{ 
            fontSize: '24px', 
            marginRight: '12px',
            color: '#1890ff'
          }} />
          <span>知识图谱系统</span>
        </div>
        
        <div style={{ color: '#fff' }}>
          <Button 
            type="text" 
            icon={<ReloadOutlined />} 
            onClick={refreshStatus}
            style={{ color: '#fff' }}
          >
            刷新状态
          </Button>
        </div>
      </Header>

      <Content style={{ background: '#f0f2f5' }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          style={{ padding: '0 24px' }}
          size="large"
        />
      </Content>
    </Layout>
  );
};

export default App;
