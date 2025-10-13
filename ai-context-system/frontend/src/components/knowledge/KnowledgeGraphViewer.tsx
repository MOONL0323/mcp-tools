/**
 * 知识图谱可视化组件
 * 使用React Flow实现交互式知识图谱展示
 */

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Controls,
  Background,
  MiniMap,
  Panel,
  ReactFlowProvider,
  useReactFlow,
  MarkerType
} from 'reactflow';
import { Card, Button, Select, Spin, message, Drawer, Typography, Descriptions, Tag, Space } from 'antd';
import { SearchOutlined, ExpandOutlined, CompressOutlined, ReloadOutlined } from '@ant-design/icons';
import 'reactflow/dist/style.css';

const { Title, Text } = Typography;
const { Option } = Select;

// 节点类型定义
interface KnowledgeNodeData {
  label: string;
  type: 'document' | 'entity' | 'concept' | 'relation';
  metadata?: {
    id: string;
    title?: string;
    description?: string;
    category?: string;
    importance?: number;
    references?: string[];
    properties?: Record<string, any>;
  };
}

type KnowledgeNode = Node<KnowledgeNodeData>;

// 边类型定义
interface KnowledgeEdgeData {
  type: 'semantic' | 'reference' | 'dependency' | 'similarity';
  strength: number;
  description?: string;
}

type KnowledgeEdge = Edge<KnowledgeEdgeData>;

// 图谱数据接口
interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

const KnowledgeGraphViewer: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [nodeDrawerVisible, setNodeDrawerVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // 模拟文档列表
  const documentOptions = [
    { value: 'all', label: '所有文档' },
    { value: 'doc1', label: '需求文档 - AI上下文系统' },
    { value: 'doc2', label: '设计文档 - 知识图谱架构' },
    { value: 'doc3', label: '代码示例 - React组件' }
  ];

  // 生成模拟图谱数据
  const generateMockGraphData = useCallback((documentId: string): GraphData => {
    const mockNodes: Node[] = [
      {
        id: '1',
        type: 'default',
        position: { x: 250, y: 5 },
        data: {
          label: 'AI上下文系统',
          type: 'document',
          metadata: {
            id: '1',
            title: 'AI上下文增强系统',
            description: '基于Graph RAG技术的智能上下文增强系统',
            category: 'system',
            importance: 0.9,
            references: ['2', '3', '4']
          }
        },
        style: {
          background: '#1890ff',
          color: 'white',
          border: '2px solid #1890ff',
          borderRadius: '8px',
          width: 180,
          fontSize: '14px',
          fontWeight: 'bold'
        }
      },
      {
        id: '2',
        type: 'default',
        position: { x: 100, y: 100 },
        data: {
          label: 'Graph RAG',
          type: 'concept',
          metadata: {
            id: '2',
            title: 'Graph RAG技术',
            description: '结合图数据库和检索增强生成的技术',
            category: 'technology',
            importance: 0.8
          }
        },
        style: {
          background: '#52c41a',
          color: 'white',
          border: '2px solid #52c41a',
          borderRadius: '8px',
          width: 120
        }
      },
      {
        id: '3',
        type: 'default',
        position: { x: 400, y: 100 },
        data: {
          label: '知识图谱',
          type: 'entity',
          metadata: {
            id: '3',
            title: '知识图谱',
            description: '结构化的知识存储和表示方式',
            category: 'data',
            importance: 0.7
          }
        },
        style: {
          background: '#722ed1',
          color: 'white',
          border: '2px solid #722ed1',
          borderRadius: '8px',
          width: 120
        }
      },
      {
        id: '4',
        type: 'default',
        position: { x: 250, y: 200 },
        data: {
          label: '文档解析',
          type: 'entity',
          metadata: {
            id: '4',
            title: '智能文档解析',
            description: '自动解析和理解文档内容',
            category: 'process',
            importance: 0.6
          }
        },
        style: {
          background: '#fa8c16',
          color: 'white',
          border: '2px solid #fa8c16',
          borderRadius: '8px',
          width: 120
        }
      },
      {
        id: '5',
        type: 'default',
        position: { x: 50, y: 300 },
        data: {
          label: '向量嵌入',
          type: 'concept',
          metadata: {
            id: '5',
            title: '向量嵌入技术',
            description: '将文本转换为向量表示',
            category: 'ai',
            importance: 0.5
          }
        },
        style: {
          background: '#13c2c2',
          color: 'white',
          border: '2px solid #13c2c2',
          borderRadius: '8px',
          width: 120
        }
      },
      {
        id: '6',
        type: 'default',
        position: { x: 450, y: 300 },
        data: {
          label: '语义检索',
          type: 'concept',
          metadata: {
            id: '6',
            title: '语义检索',
            description: '基于语义相似度的智能检索',
            category: 'ai',
            importance: 0.6
          }
        },
        style: {
          background: '#f5222d',
          color: 'white',
          border: '2px solid #f5222d',
          borderRadius: '8px',
          width: 120
        }
      }
    ];

    const mockEdges: Edge[] = [
      {
        id: 'e1-2',
        source: '1',
        target: '2',
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#1890ff', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#1890ff'
        },
        data: {
          type: 'dependency',
          strength: 0.9,
          description: '系统基于Graph RAG技术实现'
        }
      },
      {
        id: 'e1-3',
        source: '1',
        target: '3',
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#722ed1', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#722ed1'
        },
        data: {
          type: 'dependency',
          strength: 0.8,
          description: '系统使用知识图谱存储知识'
        }
      },
      {
        id: 'e1-4',
        source: '1',
        target: '4',
        type: 'smoothstep',
        style: { stroke: '#fa8c16', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#fa8c16'
        },
        data: {
          type: 'dependency',
          strength: 0.7,
          description: '系统包含文档解析功能'
        }
      },
      {
        id: 'e2-5',
        source: '2',
        target: '5',
        type: 'smoothstep',
        style: { stroke: '#13c2c2', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#13c2c2'
        },
        data: {
          type: 'reference',
          strength: 0.6,
          description: 'Graph RAG使用向量嵌入技术'
        }
      },
      {
        id: 'e3-6',
        source: '3',
        target: '6',
        type: 'smoothstep',
        style: { stroke: '#f5222d', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#f5222d'
        },
        data: {
          type: 'reference',
          strength: 0.7,
          description: '知识图谱支持语义检索'
        }
      },
      {
        id: 'e4-5',
        source: '4',
        target: '5',
        type: 'smoothstep',
        style: { stroke: '#52c41a', strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#52c41a'
        },
        data: {
          type: 'reference',
          strength: 0.5,
          description: '文档解析生成向量嵌入'
        }
      }
    ];

    return {
      nodes: mockNodes,
      edges: mockEdges
    };
  }, []);

  // 加载图谱数据
  const loadGraphData = useCallback(async (documentId: string) => {
    setLoading(true);
    try {
      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const graphData = generateMockGraphData(documentId);
      setNodes(graphData.nodes);
      setEdges(graphData.edges);
      
      message.success('知识图谱加载成功');
    } catch (error) {
      message.error('加载知识图谱失败');
    } finally {
      setLoading(false);
    }
  }, [generateMockGraphData, setNodes, setEdges]);

  // 初始化加载
  useEffect(() => {
    loadGraphData('all');
  }, [loadGraphData]);

  // 连接边的回调
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds: Edge[]) => addEdge(params, eds)),
    [setEdges]
  );

  // 节点点击事件
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setNodeDrawerVisible(true);
  }, []);

  // 文档选择变化
  const onDocumentChange = (value: string) => {
    setSelectedDocument(value);
    loadGraphData(value);
  };

  // 全屏切换
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // 刷新图谱
  const refreshGraph = () => {
    loadGraphData(selectedDocument || 'all');
  };

  const graphStyle = isFullscreen ? {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
    background: 'white'
  } : {
    height: '600px'
  };

  return (
    <div style={graphStyle}>
      <Card 
        title="知识图谱可视化" 
        style={{ height: '100%' }}
        bodyStyle={{ height: 'calc(100% - 60px)', padding: 0 }}
        extra={
          <Space>
            <Select
              value={selectedDocument}
              onChange={onDocumentChange}
              style={{ width: 200 }}
              placeholder="选择文档"
            >
              {documentOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={refreshGraph} />
            <Button 
              icon={isFullscreen ? <CompressOutlined /> : <ExpandOutlined />} 
              onClick={toggleFullscreen} 
            />
          </Space>
        }
      >
        <Spin spinning={loading} style={{ height: '100%' }}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              fitView
              attributionPosition="bottom-left"
            >
              <Background />
              <Controls />
              <MiniMap 
                position="top-right"
                style={{
                  background: '#f0f0f0',
                  border: '1px solid #d9d9d9'
                }}
              />
              <Panel position="top-left">
                <div style={{ 
                  background: 'rgba(255, 255, 255, 0.9)', 
                  padding: '8px', 
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  <div><span style={{ color: '#1890ff' }}>●</span> 文档节点</div>
                  <div><span style={{ color: '#52c41a' }}>●</span> 概念节点</div>
                  <div><span style={{ color: '#722ed1' }}>●</span> 实体节点</div>
                </div>
              </Panel>
            </ReactFlow>
          </ReactFlowProvider>
        </Spin>
      </Card>

      {/* 节点详情抽屉 */}
      <Drawer
        title="节点详情"
        placement="right"
        closable={true}
        onClose={() => setNodeDrawerVisible(false)}
        open={nodeDrawerVisible}
        width={400}
      >
        {selectedNode && (
          <div>
            <Title level={4}>{selectedNode.data.label}</Title>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="类型">
                <Tag color={
                  selectedNode.data.type === 'document' ? 'blue' :
                  selectedNode.data.type === 'concept' ? 'green' :
                  selectedNode.data.type === 'entity' ? 'purple' : 'orange'
                }>
                  {selectedNode.data.type === 'document' ? '文档' :
                   selectedNode.data.type === 'concept' ? '概念' :
                   selectedNode.data.type === 'entity' ? '实体' : '关系'}
                </Tag>
              </Descriptions.Item>
              {selectedNode.data.metadata?.title && (
                <Descriptions.Item label="标题">
                  {selectedNode.data.metadata.title}
                </Descriptions.Item>
              )}
              {selectedNode.data.metadata?.description && (
                <Descriptions.Item label="描述">
                  {selectedNode.data.metadata.description}
                </Descriptions.Item>
              )}
              {selectedNode.data.metadata?.category && (
                <Descriptions.Item label="分类">
                  <Tag>{selectedNode.data.metadata.category}</Tag>
                </Descriptions.Item>
              )}
              {selectedNode.data.metadata?.importance && (
                <Descriptions.Item label="重要性">
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div 
                      style={{ 
                        width: '100px', 
                        height: '6px', 
                        background: '#f0f0f0', 
                        borderRadius: '3px',
                        marginRight: '8px'
                      }}
                    >
                      <div 
                        style={{ 
                          width: `${selectedNode.data.metadata.importance * 100}%`, 
                          height: '100%', 
                          background: '#1890ff', 
                          borderRadius: '3px'
                        }}
                      />
                    </div>
                    <Text>{(selectedNode.data.metadata.importance * 100).toFixed(0)}%</Text>
                  </div>
                </Descriptions.Item>
              )}
            </Descriptions>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default KnowledgeGraphViewer;