/**
 * 实时知识图谱可视化组件
 * 连接Task 12后端API，展示真实的图谱数据
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Statistic, Typography, Button, Space, Spin, 
  message, Select, Drawer, Descriptions, Tag, Alert, Divider 
} from 'antd';
import { 
  NodeIndexOutlined, ApiOutlined, ReloadOutlined, 
  SearchOutlined, LinkOutlined, FileTextOutlined 
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface GraphStats {
  backend: string;
  nodes: Record<string, number>;
  relationships: Record<string, number>;
  total_nodes: number;
  total_relationships: number;
}

interface Entity {
  name: string;
  type: string;
  document_id?: number;
  docstring?: string;
  line?: number;
  relationships?: Array<{
    relation: string;
    target: string;
  }>;
}

interface RelatedEntity {
  name: string;
  type?: string;
  distance: number;
  labels?: string[];
}

const LiveKnowledgeGraph: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<string>('');
  const [entityDetail, setEntityDetail] = useState<Entity | null>(null);
  const [relatedEntities, setRelatedEntities] = useState<RelatedEntity[]>([]);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchDepth, setSearchDepth] = useState(2);

  const API_BASE = 'http://localhost:8080/api/v1';

  // 加载图统计
  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/graph/stats`);
      const data = response.data;
      
      // 兼容不同的响应格式
      if (data.success !== undefined) {
        setStats(data);
      } else {
        // 直接使用数据（后端可能直接返回统计对象）
        setStats({
          backend: data.backend || 'Unknown',
          nodes: data.nodes || {},
          relationships: data.relationships || {},
          total_nodes: data.total_nodes || 0,
          total_relationships: data.total_relationships || 0
        } as GraphStats);
      }
      
      console.log('图谱统计加载成功:', data);
      message.success('图谱统计加载成功');
    } catch (error: any) {
      console.error('加载图谱统计失败:', error);
      message.error(`加载失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 查询实体
  const queryEntity = async (name: string) => {
    if (!name) {
      message.warning('请输入实体名称');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/graph/entity/${encodeURIComponent(name)}`);
      const data = response.data;
      
      // 兼容不同的响应格式
      const entity = data.success ? data.entity : data;
      
      if (entity) {
        setEntityDetail(entity);
        setDrawerVisible(true);
        message.success(`找到实体: ${name}`);
        
        // 查询相关实体
        await findRelated(name);
      }
    } catch (error: any) {
      console.error('查询实体失败:', error);
      if (error.response?.status === 404) {
        message.warning(`实体 "${name}" 不存在`);
      } else {
        message.error(`查询失败: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 查找相关实体
  const findRelated = async (name: string) => {
    try {
      const response = await axios.get(
        `${API_BASE}/graph/related/${encodeURIComponent(name)}?max_depth=${searchDepth}`
      );
      const data = response.data;
      const related = data.success ? data.related : data;
      
      if (Array.isArray(related)) {
        setRelatedEntities(related);
      }
    } catch (error) {
      console.error('查找相关实体失败:', error);
      setRelatedEntities([]);
    }
  };

  // 从文档创建图谱
  const storeDocument = async (docId: number) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/graph/store-from-document/${docId}`);
      if (response.data.success) {
        message.success('文档已存入图谱');
        await loadStats(); // 刷新统计
      }
    } catch (error) {
      message.error('存储失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('LiveKnowledgeGraph mounted, loading stats...');
    loadStats();
  }, []);

  // 获取节点类型颜色
  const getNodeTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      document: 'blue',
      class: 'green',
      function: 'orange',
      module: 'purple',
      keyword: 'cyan'
    };
    return colors[type] || 'default';
  };

  // 获取关系类型颜色
  const getRelationColor = (relation: string) => {
    const colors: Record<string, string> = {
      CONTAINS: 'blue',
      INHERITS_FROM: 'green',
      HAS_METHOD: 'orange',
      IMPORTS: 'purple',
      HAS_KEYWORD: 'cyan'
    };
    return colors[relation] || 'default';
  };

  // 推荐实体列表（从统计中提取）
  const suggestedEntities = [
    'Calculator', 'ScientificCalculator', 'format_number',
    'UserService', 'DataProcessor', 'SimpleVectorSearch'
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <NodeIndexOutlined /> 实时知识图谱
      </Title>
      <Paragraph type="secondary">
        基于NetworkX内存图的实时知识图谱，展示文档中的实体和关系
      </Paragraph>

      {/* 图谱统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总节点数"
              value={stats?.total_nodes || 0}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总关系数"
              value={stats?.total_relationships || 0}
              prefix={<LinkOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="节点类型"
              value={Object.keys(stats?.nodes || {}).length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="后端引擎"
              value={stats?.backend || 'N/A'}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 控制面板 */}
      <Card title="图谱操作" extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadStats} loading={loading}>
            刷新统计
          </Button>
          <Button 
            type="primary"
            onClick={async () => {
              try {
                await axios.post(`${API_BASE}/graph/init-test-data`);
                message.success('测试数据初始化成功');
                await loadStats();
              } catch (error) {
                message.error('初始化失败');
              }
            }}
          >
            初始化测试数据
          </Button>
        </Space>
      }>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 实体查询 */}
          <div>
            <Text strong>查询实体：</Text>
            <Space style={{ marginTop: 8, width: '100%' }}>
              <Select
                showSearch
                placeholder="选择或输入实体名称"
                style={{ width: 300 }}
                value={selectedEntity}
                onChange={setSelectedEntity}
                options={suggestedEntities.map(name => ({ label: name, value: name }))}
              />
              <Select
                value={searchDepth}
                onChange={setSearchDepth}
                style={{ width: 120 }}
              >
                <Option value={1}>深度: 1</Option>
                <Option value={2}>深度: 2</Option>
                <Option value={3}>深度: 3</Option>
              </Select>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={() => queryEntity(selectedEntity)}
                loading={loading}
              >
                查询
              </Button>
            </Space>
          </div>

          {/* 提示信息 */}
          {stats && stats.total_nodes === 0 && (
            <Alert
              message="图谱为空"
              description="请先上传文档并存入图谱，或运行测试脚本生成数据"
              type="info"
              showIcon
            />
          )}
        </Space>
      </Card>

      {/* 节点类型分布 */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="节点类型分布">
            {stats && Object.entries(stats.nodes).map(([type, count]) => (
              <div key={type} style={{ marginBottom: 12 }}>
                <Space>
                  <Tag color={getNodeTypeColor(type)}>{type}</Tag>
                  <Text strong>{count}</Text>
                  <Text type="secondary">个节点</Text>
                </Space>
              </div>
            ))}
            {(!stats || Object.keys(stats.nodes).length === 0) && (
              <Text type="secondary">暂无数据</Text>
            )}
          </Card>
        </Col>

        <Col span={12}>
          <Card title="关系类型分布">
            {stats && Object.entries(stats.relationships).map(([type, count]) => (
              <div key={type} style={{ marginBottom: 12 }}>
                <Space>
                  <Tag color={getRelationColor(type)}>{type}</Tag>
                  <Text strong>{count}</Text>
                  <Text type="secondary">条关系</Text>
                </Space>
              </div>
            ))}
            {(!stats || Object.keys(stats.relationships).length === 0) && (
              <Text type="secondary">暂无数据</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* 实体详情抽屉 */}
      <Drawer
        title={<><NodeIndexOutlined /> 实体详情</>}
        placement="right"
        width={500}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {entityDetail && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="名称">
                <Text strong>{entityDetail.name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={getNodeTypeColor(entityDetail.type)}>
                  {entityDetail.type}
                </Tag>
              </Descriptions.Item>
              {entityDetail.document_id && (
                <Descriptions.Item label="文档ID">
                  {entityDetail.document_id}
                </Descriptions.Item>
              )}
              {entityDetail.line && (
                <Descriptions.Item label="行号">
                  {entityDetail.line}
                </Descriptions.Item>
              )}
              {entityDetail.docstring && (
                <Descriptions.Item label="文档字符串">
                  <Text code>{entityDetail.docstring}</Text>
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* 直接关系 */}
            {entityDetail.relationships && entityDetail.relationships.length > 0 && (
              <>
                <Divider>直接关系 ({entityDetail.relationships.length})</Divider>
                {entityDetail.relationships.map((rel, idx) => (
                  <Card key={idx} size="small">
                    <Space>
                      <Tag color={getRelationColor(rel.relation)}>{rel.relation}</Tag>
                      <Text>→</Text>
                      <Text strong>{rel.target}</Text>
                    </Space>
                  </Card>
                ))}
              </>
            )}

            {/* 相关实体 */}
            {relatedEntities.length > 0 && (
              <>
                <Divider>相关实体 ({relatedEntities.length})</Divider>
                {relatedEntities.map((entity, idx) => (
                  <Card 
                    key={idx} 
                    size="small"
                    hoverable
                    onClick={() => queryEntity(entity.name)}
                  >
                    <Space>
                      <Tag color={getNodeTypeColor(entity.type || 'unknown')}>
                        {entity.type || 'entity'}
                      </Tag>
                      <Text strong>{entity.name}</Text>
                      <Tag color="blue">距离: {entity.distance}</Tag>
                    </Space>
                  </Card>
                ))}
              </>
            )}
          </Space>
        )}
      </Drawer>

      {/* 快速指南 */}
      <Card title="使用指南" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>
            <Text strong>方法1 - 前端初始化：</Text>
            点击上方"初始化测试数据"按钮
          </Text>
          <Text>
            <Text strong>方法2 - 脚本初始化：</Text>
            在终端运行 <Text code>python quick_init_graph.py</Text>
          </Text>
          <Text>
            <Text strong>查询实体：</Text>
            选择或输入实体名称（如 Calculator, ScientificCalculator），点击查询按钮
          </Text>
          <Text>
            <Text strong>浏览关系：</Text>
            查看实体的直接关系和相关实体，点击相关实体可继续探索
          </Text>
          
          <Divider />
          
          {/* 调试信息 */}
          <details>
            <summary style={{ cursor: 'pointer', userSelect: 'none' }}>
              <Text type="secondary">🔍 调试信息（点击展开）</Text>
            </summary>
            <div style={{ marginTop: 12, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text><Text strong>API地址:</Text> {API_BASE}</Text>
                <Text><Text strong>统计端点:</Text> {API_BASE}/graph/stats</Text>
                <Text><Text strong>当前数据:</Text></Text>
                <pre style={{ fontSize: 12, background: '#fff', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(stats, null, 2)}
                </pre>
              </Space>
            </div>
          </details>
        </Space>
      </Card>
    </div>
  );
};

export default LiveKnowledgeGraph;
