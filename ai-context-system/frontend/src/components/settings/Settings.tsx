/**
 * 系统设置组件（占位符）
 */

import React from 'react';
import { Card, Typography, Space, Alert } from 'antd';
import { SettingOutlined, DatabaseOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const Settings: React.FC = () => {
  return (
    <div className="settings">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined style={{ marginRight: 8 }} />
          系统设置
        </Title>
        <Paragraph type="secondary">
          配置系统参数、数据源连接和服务设置。
        </Paragraph>
      </div>

      <Alert
        message="功能开发中"
        description="系统设置功能正在开发中，即将为您提供完整的系统配置管理能力。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="基础设置" extra={<SettingOutlined />}>
          <Paragraph>
            即将支持的功能：
          </Paragraph>
          <ul>
            <li>系统基础参数配置</li>
            <li>界面主题设置</li>
            <li>语言本地化配置</li>
            <li>系统日志级别</li>
            <li>缓存策略配置</li>
          </ul>
        </Card>

        <Card title="数据源配置" extra={<DatabaseOutlined />}>
          <ul>
            <li>Neo4j图数据库连接</li>
            <li>向量数据库设置</li>
            <li>文档存储配置</li>
            <li>备份恢复策略</li>
            <li>数据同步设置</li>
          </ul>
        </Card>

        <Card title="AI模型配置">
          <ul>
            <li>Qwen3-Embedding模型设置</li>
            <li>文本分块策略配置</li>
            <li>知识抽取参数调优</li>
            <li>图谱构建算法选择</li>
            <li>模型性能监控</li>
          </ul>
        </Card>
      </Space>
    </div>
  );
};

export default Settings;