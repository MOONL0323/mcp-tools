import React, { useState, useEffect } from 'react';
import { Layout, Tabs, message, Spin, Alert, Button, Card, Row, Col, Statistic } from 'antd';
import { 
  FileSearchOutlined, 
  ReloadOutlined, 
  ApartmentOutlined, 
  SearchOutlined, 
  UploadOutlined, 
  FileTextOutlined, 
  CodeOutlined,
  DatabaseOutlined,
  CloudServerOutlined
} from '@ant-design/icons';
import { KnowledgeGraphApi, SystemStatus as SystemStatusType } from './services/api_v2';
import EnhancedDocumentUpload from './components/EnhancedDocumentUpload';
import EnhancedCodeUpload from './components/EnhancedCodeUpload';
import EnhancedDocumentSearch from './components/EnhancedDocumentSearch';
import EnhancedCodeSearch from './components/EnhancedCodeSearch';
import UnifiedSearch from './components/UnifiedSearch';
import ContentManager from './components/ContentManager';
import SystemStatus from './components/SystemStatus';
import './App.css';

const { Header, Content } = Layout;

interface AppState {
  loading: boolean;
  connected: boolean;
  error: string | null;
  systemStatus: SystemStatusType | null;
}

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    loading: true,
    connected: false,
    error: null,
    systemStatus: null
  });
  const [activeTab, setActiveTab] = useState('unified-search');

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
        systemStatus: status
      });
      
      message.success('系统连接成功！');
      
    } catch (error: any) {
      setState({
        loading: false,
        connected: false,
        error: error.message,
        systemStatus: null
      });
      
      message.error(`连接失败: ${error.message}`);
    }
  };

  // 刷新系统状态
  const refreshStatus = async () => {
    try {
      const status = await KnowledgeGraphApi.getSystemStatus();
      setState(prev => ({ ...prev, systemStatus: status }));
      message.success('状态已刷新');
    } catch (error: any) {
      message.error(`刷新失败: ${error.message}`);
    }
  };

  // 初始化时测试连接
  useEffect(() => {
    testConnection();
  }, []);

  // 如果系统未连接，显示连接界面
  if (!state.connected) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ 
          background: '#001529', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between' 
        }}>
          <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
            <CloudServerOutlined style={{ marginRight: 8 }} />
            AI Agent 知识管理系统
          </div>
          <div style={{ color: 'white' }}>
            v2.0.0
          </div>
        </Header>
        
        <Content style={{ 
          padding: '50px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          background: '#f0f2f5'
        }}>
          <Card style={{ width: 500, textAlign: 'center' }}>
            <Spin spinning={state.loading} size="large">
              <div style={{ padding: '20px 0' }}>
                {state.error ? (
                  <>
                    <Alert
                      type="error"
                      message="连接失败"
                      description={state.error}
                      style={{ marginBottom: 20 }}
                    />
                    <Button 
                      type="primary" 
                      icon={<ReloadOutlined />}
                      onClick={testConnection}
                    >
                      重新连接
                    </Button>
                  </>
                ) : (
                  <>
                    <CloudServerOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
                    <h2>正在连接系统...</h2>
                    <p>请确保后端服务已启动 (http://localhost:8000)</p>
                  </>
                )}
              </div>
            </Spin>
          </Card>
        </Content>
      </Layout>
    );
  }

  // 主界面
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#001529', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between' 
      }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
          <CloudServerOutlined style={{ marginRight: 8 }} />
          AI Agent 知识管理系统
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button 
            type="text" 
            icon={<ReloadOutlined />}
            onClick={refreshStatus}
            style={{ color: 'white' }}
          >
            刷新状态
          </Button>
          <div style={{ color: 'white' }}>v2.0.0</div>
        </div>
      </Header>

      <Content style={{ padding: '20px', background: '#f0f2f5' }}>
        {/* 系统概览 */}
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="文档总数"
                value={state.systemStatus?.total_documents || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="代码文件"
                value={state.systemStatus?.total_code_files || 0}
                prefix={<CodeOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="文档片段"
                value={state.systemStatus?.total_document_chunks || 0}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="代码块"
                value={state.systemStatus?.total_code_blocks || 0}
                prefix={<ApartmentOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* 主要功能标签页 */}
        <Card>
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            items={[
              {
                key: 'unified-search',
                label: (
                  <span>
                    <SearchOutlined />
                    统一搜索
                  </span>
                ),
                children: <UnifiedSearch />
              },
              {
                key: 'doc-upload',
                label: (
                  <span>
                    <UploadOutlined />
                    文档上传
                  </span>
                ),
                children: <EnhancedDocumentUpload onUploadSuccess={refreshStatus} />
              },
              {
                key: 'code-upload',
                label: (
                  <span>
                    <CodeOutlined />
                    代码上传
                  </span>
                ),
                children: <EnhancedCodeUpload onUploadSuccess={refreshStatus} />
              },
              {
                key: 'doc-search',
                label: (
                  <span>
                    <FileTextOutlined />
                    文档搜索
                  </span>
                ),
                children: <EnhancedDocumentSearch />
              },
              {
                key: 'code-search',
                label: (
                  <span>
                    <FileSearchOutlined />
                    代码搜索
                  </span>
                ),
                children: <EnhancedCodeSearch />
              },
              {
                key: 'content-manager',
                label: (
                  <span>
                    <DatabaseOutlined />
                    内容管理
                  </span>
                ),
                children: <ContentManager onUpdate={refreshStatus} />
              },
              {
                key: 'system-status',
                label: (
                  <span>
                    <ApartmentOutlined />
                    系统状态
                  </span>
                ),
                children: <SystemStatus systemStatus={state.systemStatus} />
              }
            ]}
          />
        </Card>
      </Content>
    </Layout>
  );
};

export default App;