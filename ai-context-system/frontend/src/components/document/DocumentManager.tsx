import React, { useState, useEffect } from 'react';
import { Card, Tabs, Row, Col, Statistic, Space, Typography } from 'antd';
import { FileTextOutlined, CodeOutlined, TeamOutlined, DatabaseOutlined, CloudUploadOutlined, UnorderedListOutlined } from '@ant-design/icons';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';

const { Title } = Typography;

interface Stats {
  totalDocs: number;
  businessDocs: number;
  demoCodes: number;
  teams: number;
  totalChunks: number;
}

const DocumentManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [stats, setStats] = useState<Stats>({ totalDocs: 0, businessDocs: 0, demoCodes: 0, teams: 0, totalChunks: 0 });
  const [refreshKey, setRefreshKey] = useState(0);

  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:8080/api/v1/stats/dashboard');
      if (response.ok) {
        const data = await response.json();
        setStats({
          totalDocs: data.total_documents || 0,
          businessDocs: data.business_doc_count || 0,
          demoCodes: data.demo_code_count || 0,
          teams: data.active_teams || 0,
          totalChunks: data.total_chunks || 0,
        });
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  useEffect(() => { loadStats(); }, [refreshKey]);

  const handleUploadSuccess = () => {
    setRefreshKey((prev) => prev + 1);
    setActiveTab('list');
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}><DatabaseOutlined /> 文档管理中心</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="总文档数" value={stats.totalDocs} prefix={<DatabaseOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="项目文档" value={stats.businessDocs} prefix={<FileTextOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="Demo代码" value={stats.demoCodes} prefix={<CodeOutlined />} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="活跃团队" value={stats.teams} prefix={<TeamOutlined />} /></Card></Col>
      </Row>
      <Card><Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'upload', label: <Space><CloudUploadOutlined /><span>上传文档</span></Space>, children: <DocumentUpload onSuccess={handleUploadSuccess} /> },
        { key: 'list', label: <Space><UnorderedListOutlined /><span>文档列表</span></Space>, children: <DocumentList refresh={refreshKey} /> },
      ]} /></Card>
    </div>
  );
};

export default DocumentManager;
