import React from 'react';
import {
  Card,
  Statistic,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Tooltip,
  Tag,
  Collapse,
  List
} from 'antd';
import {
  DatabaseOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { SystemStatus as SystemStatusType } from '../services/api';

const { Text } = Typography;
const { Panel } = Collapse;

interface SystemStatusProps {
  status: SystemStatusType;
  onRefresh?: () => void;
  loading?: boolean;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ 
  status, 
  onRefresh, 
  loading = false 
}) => {
  // 格式化文件扩展名
  const formatExtensions = (extensions: string[]) => {
    return extensions.map(ext => ext.startsWith('.') ? ext : `.${ext}`);
  };

  // 获取系统健康状态
  const getHealthStatus = () => {
    if (status.document_count === 0) {
      return { color: 'orange', text: '无文档' };
    } else if (status.document_count < 10) {
      return { color: 'blue', text: '轻量级' };
    } else if (status.document_count < 100) {
      return { color: 'green', text: '正常' };
    } else {
      return { color: 'purple', text: '大规模' };
    }
  };

  const healthStatus = getHealthStatus();

  return (
    <Card 
      title={
        <Space>
          <DatabaseOutlined />
          <span>系统状态</span>
          <Tag color={healthStatus.color} style={{ fontSize: '11px' }}>
            {healthStatus.text}
          </Tag>
        </Space>
      }
      size="small"
      extra={
        <Tooltip title="刷新状态">
          <Button 
            type="text" 
            icon={<ReloadOutlined />} 
            onClick={onRefresh}
            loading={loading}
            size="small"
          />
        </Tooltip>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 核心统计 */}
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <Statistic
              title={
                <Space>
                  <FileTextOutlined style={{ color: '#1890ff' }} />
                  <Text style={{ fontSize: '12px' }}>文档数量</Text>
                </Space>
              }
              value={status.document_count}
              valueStyle={{ fontSize: '18px', color: '#1890ff' }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title={
                <Space>
                  <SettingOutlined style={{ color: '#52c41a' }} />
                  <Text style={{ fontSize: '12px' }}>向量维度</Text>
                </Space>
              }
              value={status.vector_dimension}
              valueStyle={{ fontSize: '18px', color: '#52c41a' }}
            />
          </Col>
        </Row>

        {/* 图结构统计 */}
        <Row gutter={[8, 8]}>
          <Col span={12}>
            <Statistic
              title={
                <Space>
                  <NodeIndexOutlined style={{ color: '#fa8c16' }} />
                  <Text style={{ fontSize: '12px' }}>图节点</Text>
                </Space>
              }
              value={status.graph_nodes}
              valueStyle={{ fontSize: '18px', color: '#fa8c16' }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title={
                <Space>
                  <BranchesOutlined style={{ color: '#722ed1' }} />
                  <Text style={{ fontSize: '12px' }}>图边</Text>
                </Space>
              }
              value={status.graph_edges}
              valueStyle={{ fontSize: '18px', color: '#722ed1' }}
            />
          </Col>
        </Row>

        {/* 详细信息 */}
        <Collapse ghost size="small">
          <Panel
            header={
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <InfoCircleOutlined style={{ marginRight: 4 }} />
                详细信息
              </Text>
            }
            key="details"
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              {/* 支持的文件格式 */}
              <div>
                <Text strong style={{ fontSize: '12px' }}>支持格式:</Text>
                <div style={{ marginTop: 4 }}>
                  {formatExtensions(status.supported_extensions).map(ext => (
                    <Tag key={ext} style={{ fontSize: '10px', margin: '2px' }}>
                      {ext}
                    </Tag>
                  ))}
                </div>
              </div>

              {/* 可用组件 */}
              {status.available_components && Object.keys(status.available_components).length > 0 && (
                <div>
                  <Text strong style={{ fontSize: '12px' }}>系统组件:</Text>
                  <List
                    size="small"
                    dataSource={Object.entries(status.available_components)}
                    renderItem={([category, components]) => (
                      <List.Item style={{ padding: '4px 0', borderBottom: 'none' }}>
                        <div style={{ width: '100%' }}>
                          <Text type="secondary" style={{ fontSize: '11px' }}>
                            {category}:
                          </Text>
                          <div style={{ marginTop: 2 }}>
                            {components.map(component => (
                              <Tag 
                                key={component} 
                                style={{ fontSize: '10px', margin: '1px' }}
                                color="blue"
                              >
                                {component}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      </List.Item>
                    )}
                  />
                </div>
              )}

              {/* 系统指标 */}
              <div>
                <Text strong style={{ fontSize: '12px' }}>系统指标:</Text>
                <div style={{ marginTop: 4, fontSize: '11px' }}>
                  <div style={{ marginBottom: 2 }}>
                    <Text type="secondary">图密度: </Text>
                    <Text>
                      {status.graph_nodes > 0 
                        ? (status.graph_edges / (status.graph_nodes * (status.graph_nodes - 1)) * 100).toFixed(3)
                        : 0
                      }%
                    </Text>
                  </div>
                  <div style={{ marginBottom: 2 }}>
                    <Text type="secondary">平均度: </Text>
                    <Text>
                      {status.graph_nodes > 0 
                        ? (status.graph_edges * 2 / status.graph_nodes).toFixed(2)
                        : 0
                      }
                    </Text>
                  </div>
                  <div>
                    <Text type="secondary">文档/节点比: </Text>
                    <Text>
                      {status.graph_nodes > 0 
                        ? (status.document_count / status.graph_nodes).toFixed(2)
                        : 0
                      }
                    </Text>
                  </div>
                </div>
              </div>
            </Space>
          </Panel>
        </Collapse>
      </Space>
    </Card>
  );
};

export default SystemStatus;