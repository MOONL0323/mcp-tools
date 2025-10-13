/**
 * 知识图谱组件（占位符）
 */

import React from 'react';
import { Card, Typography, Space, Button, Alert } from 'antd';
import { NodeIndexOutlined, ExperimentOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const KnowledgeGraph: React.FC = () => {
  return (
    <div className="knowledge-graph">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <NodeIndexOutlined style={{ marginRight: 8 }} />
          知识图谱
        </Title>
        <Paragraph type="secondary">
          智能知识图谱可视化与分析系统，基于Graph RAG技术构建文档知识网络。
        </Paragraph>
      </div>

      <Alert
        message="功能开发中"
        description="知识图谱功能正在开发中，即将为您提供强大的知识可视化与智能分析能力。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="图谱概览" extra={<ExperimentOutlined />}>
          <Paragraph>
            即将支持的功能：
          </Paragraph>
          <ul>
            <li>文档实体关系图谱可视化</li>
            <li>智能知识聚类与社区发现</li>
            <li>语义相似度分析</li>
            <li>知识路径推理</li>
            <li>图谱查询与检索</li>
          </ul>
        </Card>

        <Card title="技术特性">
          <ul>
            <li>基于Neo4j图数据库存储</li>
            <li>使用Qwen3-Embedding进行向量化</li>
            <li>支持多模态知识融合</li>
            <li>实时图谱更新与索引</li>
            <li>交互式3D图谱展示</li>
          </ul>
        </Card>
      </Space>
    </div>
  );
};

export default KnowledgeGraph;