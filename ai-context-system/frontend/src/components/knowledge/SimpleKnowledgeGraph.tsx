/**
 * 简化的知识图谱展示组件
 */

import React, { useState } from 'react';
import { Card, Row, Col, Typography, Tag, Button, Space, Divider } from 'antd';
import { NodeIndexOutlined, FileTextOutlined, LinkOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface SimpleNode {
  id: string;
  label: string;
  type: 'document' | 'concept' | 'entity';
  description: string;
  category: string;
  connections: string[];
}

interface SimpleEdge {
  from: string;
  to: string;
  type: string;
  description: string;
}

const SimpleKnowledgeGraph: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // 简化的图数据
  const nodes: SimpleNode[] = [
    {
      id: '1',
      label: 'AI上下文系统',
      type: 'document',
      description: '基于Graph RAG技术的智能上下文增强系统',
      category: '系统',
      connections: ['2', '3', '4']
    },
    {
      id: '2',
      label: 'Graph RAG',
      type: 'concept',
      description: '结合图数据库和检索增强生成的技术',
      category: '技术',
      connections: ['1', '5', '6']
    },
    {
      id: '3',
      label: '知识图谱',
      type: 'entity',
      description: '结构化的知识存储和表示方式',
      category: '数据结构',
      connections: ['1', '2', '6']
    },
    {
      id: '4',
      label: '文档解析',
      type: 'entity',
      description: '自动解析和理解文档内容',
      category: '处理流程',
      connections: ['1', '5']
    },
    {
      id: '5',
      label: '向量嵌入',
      type: 'concept',
      description: '将文本转换为向量表示',
      category: 'AI技术',
      connections: ['2', '4', '6']
    },
    {
      id: '6',
      label: '语义检索',
      type: 'concept',
      description: '基于语义相似度的智能检索',
      category: 'AI技术',
      connections: ['2', '3', '5']
    }
  ];

  const edges: SimpleEdge[] = [
    { from: '1', to: '2', type: '依赖', description: '系统基于Graph RAG技术实现' },
    { from: '1', to: '3', type: '使用', description: '系统使用知识图谱存储知识' },
    { from: '1', to: '4', type: '包含', description: '系统包含文档解析功能' },
    { from: '2', to: '5', type: '关联', description: 'Graph RAG使用向量嵌入技术' },
    { from: '3', to: '6', type: '支持', description: '知识图谱支持语义检索' },
    { from: '4', to: '5', type: '生成', description: '文档解析生成向量嵌入' }
  ];

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'document': return '#1890ff';
      case 'concept': return '#52c41a';
      case 'entity': return '#722ed1';
      default: return '#d9d9d9';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'document': return <FileTextOutlined />;
      case 'concept': return <NodeIndexOutlined />;
      case 'entity': return <LinkOutlined />;
      default: return <NodeIndexOutlined />;
    }
  };

  const getConnectedNodes = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return [];
    return nodes.filter(n => node.connections.includes(n.id));
  };

  const getRelatedEdges = (nodeId: string) => {
    return edges.filter(e => e.from === nodeId || e.to === nodeId);
  };

  return (
    <div>
      <Card title="知识图谱可视化" style={{ marginBottom: '16px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Text type="secondary">
            点击节点查看详细信息和关联关系
          </Text>
        </div>

        {/* 节点网格展示 */}
        <Row gutter={[16, 16]}>
          {nodes.map(node => (
            <Col key={node.id} span={8}>
              <Card
                size="small"
                hoverable
                onClick={() => setSelectedNode(node.id)}
                style={{
                  borderColor: selectedNode === node.id ? getNodeColor(node.type) : '#d9d9d9',
                  borderWidth: selectedNode === node.id ? 2 : 1,
                  cursor: 'pointer'
                }}
                bodyStyle={{ padding: '12px' }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <span style={{ color: getNodeColor(node.type) }}>
                      {getTypeIcon(node.type)}
                    </span>
                    <Text strong>{node.label}</Text>
                  </Space>
                  
                  <Tag color={getNodeColor(node.type)} style={{ fontSize: '11px' }}>
                    {node.type === 'document' ? '文档' :
                     node.type === 'concept' ? '概念' : '实体'}
                  </Tag>
                  
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {node.description}
                  </Text>
                  
                  <div>
                    <Text type="secondary" style={{ fontSize: '11px' }}>
                      连接数: {node.connections.length}
                    </Text>
                  </div>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 节点详情和关系 */}
      {selectedNode && (
        <Card 
          title={
            <Space>
              <span>节点详情</span>
              <Button 
                size="small" 
                onClick={() => setSelectedNode(null)}
              >
                清除选择
              </Button>
            </Space>
          }
        >
          {(() => {
            const node = nodes.find(n => n.id === selectedNode);
            if (!node) return null;

            const connectedNodes = getConnectedNodes(selectedNode);
            const relatedEdges = getRelatedEdges(selectedNode);

            return (
              <Row gutter={[24, 16]}>
                <Col span={12}>
                  <Title level={4}>
                    <Space>
                      <span style={{ color: getNodeColor(node.type) }}>
                        {getTypeIcon(node.type)}
                      </span>
                      {node.label}
                    </Space>
                  </Title>
                  
                  <Space direction="vertical" size="small">
                    <div>
                      <Text strong>类型: </Text>
                      <Tag color={getNodeColor(node.type)}>
                        {node.type === 'document' ? '文档' :
                         node.type === 'concept' ? '概念' : '实体'}
                      </Tag>
                    </div>
                    
                    <div>
                      <Text strong>分类: </Text>
                      <Text>{node.category}</Text>
                    </div>
                    
                    <div>
                      <Text strong>描述: </Text>
                      <Paragraph>{node.description}</Paragraph>
                    </div>
                  </Space>
                </Col>

                <Col span={12}>
                  <Title level={5}>关联节点 ({connectedNodes.length})</Title>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {connectedNodes.map(connectedNode => (
                      <Card 
                        key={connectedNode.id}
                        size="small"
                        hoverable
                        onClick={() => setSelectedNode(connectedNode.id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <Space>
                          <span style={{ color: getNodeColor(connectedNode.type) }}>
                            {getTypeIcon(connectedNode.type)}
                          </span>
                          <div>
                            <Text strong>{connectedNode.label}</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {connectedNode.description.slice(0, 50)}...
                            </Text>
                          </div>
                        </Space>
                      </Card>
                    ))}
                  </Space>

                  <Divider />

                  <Title level={5}>关系详情 ({relatedEdges.length})</Title>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {relatedEdges.map((edge, index) => {
                      const fromNode = nodes.find(n => n.id === edge.from);
                      const toNode = nodes.find(n => n.id === edge.to);
                      return (
                        <div key={index} style={{ 
                          padding: '8px', 
                          background: '#fafafa',
                          borderRadius: '4px'
                        }}>
                          <Space direction="vertical" size="small">
                            <Text style={{ fontSize: '12px' }}>
                              <Text strong>{fromNode?.label}</Text>
                              <span style={{ margin: '0 8px', color: '#999' }}>
                                {edge.type}
                              </span>
                              <Text strong>{toNode?.label}</Text>
                            </Text>
                            <Text type="secondary" style={{ fontSize: '11px' }}>
                              {edge.description}
                            </Text>
                          </Space>
                        </div>
                      );
                    })}
                  </Space>
                </Col>
              </Row>
            );
          })()}
        </Card>
      )}
    </div>
  );
};

export default SimpleKnowledgeGraph;