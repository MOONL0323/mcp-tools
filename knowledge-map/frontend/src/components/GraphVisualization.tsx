import React, { useState, useEffect, useCallback, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Card, Input, Button, Space, Modal, Descriptions, message, Spin, Tag, Select, Slider } from 'antd';
import { SearchOutlined, ReloadOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Search } = Input;
const { Option } = Select;

interface Node {
  id: string;
  label: string;
  type: string;
  frequency: number;
  documents: string[];
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface Edge {
  source: string;
  target: string;
  weight: number;
  type: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  statistics: {
    node_count: number;
    edge_count: number;
    document_count: number;
    avg_degree: number;
  };
}

const GraphVisualization: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [nodeSize, setNodeSize] = useState(5);
  const [linkWidth, setLinkWidth] = useState(1);
  const [filterType, setFilterType] = useState<string>('all');
  const [minFrequency, setMinFrequency] = useState(0);
  
  const fgRef = useRef<any>();

  // 加载图数据
  const loadGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8001/api/graph/data');
      const apiData = response.data;
      
      if (apiData.success && apiData.data) {
        setGraphData(apiData.data);
        message.success(`加载成功: ${apiData.data.statistics.node_count} 个节点, ${apiData.data.statistics.edge_count} 条边`);
      } else {
        throw new Error(apiData.message || '加载失败');
      }
    } catch (error) {
      console.error('加载图数据失败:', error);
      message.error('加载图数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  // 搜索节点
  const handleSearch = useCallback((value: string) => {
    if (!value || !graphData) {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
      return;
    }

    const searchLower = value.toLowerCase();
    const nodes = new Set<string>();
    const links = new Set<string>();

    // 查找匹配的节点
    graphData.nodes.forEach(node => {
      if (node.label.toLowerCase().includes(searchLower)) {
        nodes.add(node.id);
      }
    });

    // 查找连接到高亮节点的边
    graphData.edges.forEach(edge => {
      if (nodes.has(edge.source) || nodes.has(edge.target)) {
        links.add(`${edge.source}-${edge.target}`);
      }
    });

    setHighlightNodes(nodes);
    setHighlightLinks(links);

    // 聚焦到第一个匹配的节点
    if (nodes.size > 0 && fgRef.current) {
      const firstNode = graphData.nodes.find(n => nodes.has(n.id));
      if (firstNode) {
        fgRef.current.centerAt(firstNode.x, firstNode.y, 1000);
        fgRef.current.zoom(3, 1000);
      }
    }
  }, [graphData]);

  // 删除节点
  const handleDeleteNode = useCallback(async (nodeId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除节点 "${nodeId}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.delete(`http://localhost:8001/api/graph/node/${encodeURIComponent(nodeId)}`);
          message.success('节点已删除');
          loadGraphData(); // 重新加载数据
        } catch (error) {
          console.error('删除节点失败:', error);
          message.error('删除节点失败');
        }
      }
    });
  }, [loadGraphData]);

  // 重置图
  const handleResetGraph = useCallback(() => {
    Modal.confirm({
      title: '确认重置',
      content: '确定要重置整个知识图谱吗？此操作将清空所有节点和边，不可恢复。',
      okText: '重置',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.post('http://localhost:8001/api/graph/reset');
          message.success('知识图谱已重置');
          loadGraphData();
        } catch (error) {
          console.error('重置图谱失败:', error);
          message.error('重置图谱失败');
        }
      }
    });
  }, [loadGraphData]);

  // 节点点击事件
  const handleNodeClick = useCallback((node: Node) => {
    setSelectedNode(node);
    setModalVisible(true);
  }, []);

  // 节点右键菜单
  const handleNodeRightClick = useCallback((node: Node) => {
    handleDeleteNode(node.id);
  }, [handleDeleteNode]);

  // 过滤节点
  const getFilteredData = useCallback(() => {
    if (!graphData) return null;

    let filteredNodes = graphData.nodes;
    let filteredEdges = graphData.edges;

    // 按类型过滤
    if (filterType !== 'all') {
      filteredNodes = filteredNodes.filter(node => node.type === filterType);
    }

    // 按频率过滤
    if (minFrequency > 0) {
      filteredNodes = filteredNodes.filter(node => node.frequency >= minFrequency);
    }

    // 过滤边：只保留两端节点都存在的边
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    filteredEdges = filteredEdges.filter(edge => 
      nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return {
      nodes: filteredNodes,
      links: filteredEdges
    };
  }, [graphData, filterType, minFrequency]);

  // 节点颜色
  const getNodeColor = useCallback((node: Node) => {
    if (highlightNodes.has(node.id)) {
      return '#ff4d4f';
    }
    
    // 根据频率设置颜色深浅
    const intensity = Math.min(node.frequency / 10, 1);
    const baseColor = node.type === 'keyword' ? [24, 144, 255] : [82, 196, 26];
    return `rgba(${baseColor[0]}, ${baseColor[1]}, ${baseColor[2]}, ${0.3 + intensity * 0.7})`;
  }, [highlightNodes]);

  // 节点大小
  const getNodeSize = useCallback((node: Node) => {
    const baseSize = highlightNodes.has(node.id) ? nodeSize * 2 : nodeSize;
    return baseSize * (1 + Math.log(node.frequency + 1) / 2);
  }, [highlightNodes, nodeSize]);

  // 边颜色
  const getLinkColor = useCallback((link: any) => {
    const linkId = `${link.source.id || link.source}-${link.target.id || link.target}`;
    return highlightLinks.has(linkId) ? '#ff4d4f' : 'rgba(200, 200, 200, 0.3)';
  }, [highlightLinks]);

  // 边宽度
  const getLinkWidth = useCallback((link: any) => {
    const linkId = `${link.source.id || link.source}-${link.target.id || link.target}`;
    const baseWidth = highlightLinks.has(linkId) ? linkWidth * 2 : linkWidth;
    return baseWidth * (link.weight || 1);
  }, [highlightLinks, linkWidth]);

  const filteredData = getFilteredData();

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <Card style={{ margin: 16, marginBottom: 0 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 统计信息 */}
          {graphData && (
            <div>
              <Space size="large">
                <Tag color="blue">节点: {graphData.statistics.node_count}</Tag>
                <Tag color="green">边: {graphData.statistics.edge_count}</Tag>
                <Tag color="orange">文档: {graphData.statistics.document_count}</Tag>
                <Tag color="purple">平均度数: {graphData.statistics.avg_degree.toFixed(2)}</Tag>
              </Space>
            </div>
          )}
          
          {/* 搜索和操作 */}
          <Space wrap>
            <Search
              placeholder="搜索节点..."
              allowClear
              prefix={<SearchOutlined />}
              style={{ width: 300 }}
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleSearch('')}
            />
            
            <Select
              value={filterType}
              onChange={setFilterType}
              style={{ width: 120 }}
            >
              <Option value="all">所有类型</Option>
              <Option value="keyword">关键词</Option>
              <Option value="entity">实体</Option>
            </Select>
            
            <span>最小频率:</span>
            <Slider
              min={0}
              max={20}
              value={minFrequency}
              onChange={setMinFrequency}
              style={{ width: 150 }}
            />
            
            <span>节点大小:</span>
            <Slider
              min={2}
              max={10}
              value={nodeSize}
              onChange={setNodeSize}
              style={{ width: 100 }}
            />
            
            <span>边宽度:</span>
            <Slider
              min={0.5}
              max={3}
              step={0.5}
              value={linkWidth}
              onChange={setLinkWidth}
              style={{ width: 100 }}
            />
            
            <Button icon={<ReloadOutlined />} onClick={loadGraphData}>
              刷新
            </Button>
            
            <Button 
              icon={<DeleteOutlined />} 
              danger 
              onClick={handleResetGraph}
            >
              重置图谱
            </Button>
          </Space>
          
          {/* 提示信息 */}
          <div style={{ color: '#666', fontSize: 12 }}>
            <Space>
              <InfoCircleOutlined />
              <span>左键点击节点查看详情 | 右键点击节点删除 | 鼠标滚轮缩放 | 拖拽移动画布</span>
            </Space>
          </div>
        </Space>
      </Card>

      {/* 图可视化区域 */}
      <div style={{ flex: 1, position: 'relative' }}>
        {loading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%' 
          }}>
            <Spin size="large" tip="加载中..." />
          </div>
        ) : filteredData ? (
          <ForceGraph2D
            ref={fgRef}
            graphData={filteredData}
            nodeLabel={(node: any) => `${node.label} (频率: ${node.frequency})`}
            nodeColor={getNodeColor}
            nodeVal={getNodeSize}
            linkColor={getLinkColor}
            linkWidth={getLinkWidth}
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={(link: any) => highlightLinks.has(`${link.source.id || link.source}-${link.target.id || link.target}`) ? 2 : 0}
            onNodeClick={handleNodeClick}
            onNodeRightClick={handleNodeRightClick}
            cooldownTime={3000}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
        ) : (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            color: '#999'
          }}>
            暂无数据
          </div>
        )}
      </div>

      {/* 节点详情模态框 */}
      <Modal
        title="节点详情"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="delete" danger onClick={() => {
            if (selectedNode) {
              handleDeleteNode(selectedNode.id);
              setModalVisible(false);
            }
          }}>
            删除节点
          </Button>,
          <Button key="close" onClick={() => setModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {selectedNode && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="节点ID">{selectedNode.id}</Descriptions.Item>
            <Descriptions.Item label="标签">{selectedNode.label}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={selectedNode.type === 'keyword' ? 'blue' : 'green'}>
                {selectedNode.type}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="出现频率">{selectedNode.frequency}</Descriptions.Item>
            <Descriptions.Item label="关联文档数">{selectedNode.documents.length}</Descriptions.Item>
            <Descriptions.Item label="关联文档">
              <div style={{ maxHeight: 200, overflow: 'auto' }}>
                {selectedNode.documents.map((doc, idx) => (
                  <div key={idx} style={{ marginBottom: 4 }}>
                    <Tag>{doc}</Tag>
                  </div>
                ))}
              </div>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default GraphVisualization;
