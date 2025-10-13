/**
 * 用户管理组件（占位符）
 */

import React from 'react';
import { Card, Typography, Space, Alert } from 'antd';
import { UserOutlined, TeamOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const UserManager: React.FC = () => {
  return (
    <div className="user-manager">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <UserOutlined style={{ marginRight: 8 }} />
          用户管理
        </Title>
        <Paragraph type="secondary">
          管理系统用户、权限和团队协作设置。
        </Paragraph>
      </div>

      <Alert
        message="功能开发中"
        description="用户管理功能正在开发中，即将为您提供完整的用户与权限管理能力。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="用户管理" extra={<UserOutlined />}>
          <Paragraph>
            即将支持的功能：
          </Paragraph>
          <ul>
            <li>用户创建、编辑、删除</li>
            <li>角色权限分配</li>
            <li>用户状态管理</li>
            <li>登录日志查看</li>
            <li>批量用户操作</li>
          </ul>
        </Card>

        <Card title="团队协作" extra={<TeamOutlined />}>
          <ul>
            <li>团队创建与管理</li>
            <li>成员邀请与移除</li>
            <li>项目权限控制</li>
            <li>协作审批流程</li>
            <li>团队活动监控</li>
          </ul>
        </Card>
      </Space>
    </div>
  );
};

export default UserManager;