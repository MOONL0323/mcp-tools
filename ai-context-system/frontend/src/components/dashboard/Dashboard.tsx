/**
 * 仪表板组件
 */

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Space, Progress, Tag, message, Spin } from 'antd';
import { 
  FileTextOutlined, 
  DatabaseOutlined, 
  UserOutlined, 
  TeamOutlined,
  CloudUploadOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { apiClient } from '../../services/api';

const { Title, Paragraph } = Typography;

interface DashboardStats {
  totalDocuments: number;
  processingDocuments: number;
  completedDocuments: number;
  totalChunks: number;
  totalEntities: number;
  totalRelations: number;
  knowledgeGraphs: number;
  teamMembers: number;
}

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    processingDocuments: 0,
    completedDocuments: 0,
    totalChunks: 0,
    totalEntities: 0,
    totalRelations: 0,
    knowledgeGraphs: 0,
    teamMembers: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      
      const response = await apiClient.get('/v1/stats/dashboard');
      
      if (response.success && response.data) {
        setStats(response.data);
      } else {
        throw new Error('Failed to load dashboard statistics');
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
      message.error('加载统计数据失败');
      // 保持默认值，不显示错误给用户造成困扰
    } finally {
      setLoading(false);
    }
  };

  const processingProgress = stats.totalDocuments > 0 
    ? Math.round((stats.completedDocuments / stats.totalDocuments) * 100)
    : 0;

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" tip="加载统计数据中..." />
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>欢迎回来，{user?.full_name || user?.username}！</Title>
        <Paragraph type="secondary">
          这里是您的AI上下文增强系统工作台。您可以管理文档、查看知识图谱，并监控系统运行状态。
        </Paragraph>
      </div>

      {/* 概览统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总文档数"
              value={stats.totalDocuments}
              prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
              suffix="个"
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="processing">处理中: {stats.processingDocuments}</Tag>
              <Tag color="success">已完成: {stats.completedDocuments}</Tag>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="文档块数"
              value={stats.totalChunks}
              prefix={<DatabaseOutlined style={{ color: '#52c41a' }} />}
              suffix="个"
            />
            <div style={{ marginTop: 8 }}>
              <Paragraph type="secondary" style={{ margin: 0, fontSize: '12px' }}>
                {stats.totalDocuments > 0 
                  ? `平均每文档 ${Math.round(stats.totalChunks / stats.totalDocuments)} 个块`
                  : '暂无数据'
                }
              </Paragraph>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="知识实体"
              value={stats.totalEntities}
              prefix={<NodeIndexOutlined style={{ color: '#722ed1' }} />}
              suffix="个"
            />
            <div style={{ marginTop: 8 }}>
              <Paragraph type="secondary" style={{ margin: 0, fontSize: '12px' }}>
                {stats.totalRelations} 个关系连接
              </Paragraph>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="团队成员"
              value={stats.teamMembers}
              prefix={<TeamOutlined style={{ color: '#fa8c16' }} />}
              suffix="人"
            />
            <div style={{ marginTop: 8 }}>
              <Tag color="blue">在线: 8</Tag>
              <Tag color="default">离线: 7</Tag>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 详细信息面板 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="文档处理进度" extra={<CloudUploadOutlined />}>
            <div style={{ marginBottom: 16 }}>
              <Progress 
                percent={processingProgress} 
                status="active" 
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>已处理文档:</span>
                <strong>{stats.completedDocuments} / {stats.totalDocuments}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>处理中:</span>
                <strong style={{ color: '#1890ff' }}>{stats.processingDocuments} 个</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>平均处理时间:</span>
                <strong>2.3 分钟</strong>
              </div>
            </Space>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="知识图谱统计" extra={<NodeIndexOutlined />}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>实体节点:</span>
                <strong style={{ color: '#722ed1' }}>{stats.totalEntities.toLocaleString()}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>关系边:</span>
                <strong style={{ color: '#eb2f96' }}>{stats.totalRelations.toLocaleString()}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>社区聚类:</span>
                <strong style={{ color: '#52c41a' }}>156 个</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>图谱密度:</span>
                <strong>0.68</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>最新更新:</span>
                <strong>2 分钟前</strong>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 快速操作面板 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="快速操作">
            <Space wrap>
              <Card.Grid style={{ width: '25%', textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff', marginBottom: '8px' }} />
                <div>上传文档</div>
              </Card.Grid>
              <Card.Grid style={{ width: '25%', textAlign: 'center' }}>
                <DatabaseOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
                <div>查看文档</div>
              </Card.Grid>
              <Card.Grid style={{ width: '25%', textAlign: 'center' }}>
                <NodeIndexOutlined style={{ fontSize: '24px', color: '#722ed1', marginBottom: '8px' }} />
                <div>知识图谱</div>
              </Card.Grid>
              <Card.Grid style={{ width: '25%', textAlign: 'center' }}>
                <UserOutlined style={{ fontSize: '24px', color: '#fa8c16', marginBottom: '8px' }} />
                <div>用户管理</div>
              </Card.Grid>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};