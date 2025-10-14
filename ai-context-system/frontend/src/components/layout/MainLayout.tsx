/**
 * 主布局组件
 */

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Typography, Badge, Button, Drawer } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  SearchOutlined,
  MessageOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

export const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [notificationDrawerVisible, setNotificationDrawerVisible] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: '文档管理',
    },
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: '高级搜索',
    },
    {
      key: '/knowledge-graph',
      icon: <NodeIndexOutlined />,
      label: '知识图谱',
    },
    {
      key: '/qa',
      icon: <MessageOutlined />,
      label: '智能问答',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // 获取当前页面标题
  const getCurrentPageTitle = () => {
    const currentItem = menuItems.find(item => item.key === location.pathname);
    return currentItem?.label || 'AI上下文增强系统';
  };

  // 模拟通知数据
  const notifications = [
    {
      id: '1',
      title: '文档处理完成',
      content: '《技术方案文档》已完成处理，生成了 45 个知识块',
      time: '2 分钟前',
      type: 'success'
    },
    {
      id: '2', 
      title: '新用户注册',
      content: '用户 "张三" 已成功注册并加入团队',
      time: '10 分钟前',
      type: 'info'
    },
    {
      id: '3',
      title: '系统更新',
      content: '知识图谱算法已更新到 v2.1，处理效率提升 30%',
      time: '1 小时前',
      type: 'warning'
    }
  ];

  return (
    <Layout className="main-layout">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="main-sider"
        width={240}
      >
        <div className="logo">
          <NodeIndexOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">AI上下文系统</span>}
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="main-menu"
        />
      </Sider>

      <Layout>
        {/* 顶部导航栏 */}
        <Header className="main-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="collapse-button"
            />
            <Title level={4} className="page-title">
              {getCurrentPageTitle()}
            </Title>
          </div>

          <div className="header-right">
            <Space size="large">
              {/* 搜索按钮 */}
              <Button
                type="text"
                icon={<SearchOutlined />}
                className="header-action-button"
                onClick={() => {
                  // TODO: 实现全局搜索
                  console.log('全局搜索');
                }}
              />

              {/* 通知按钮 */}
              <Badge count={notifications.length} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  className="header-action-button"
                  onClick={() => setNotificationDrawerVisible(true)}
                />
              </Badge>

              {/* 用户下拉菜单 */}
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <div className="user-info">
                  <Avatar 
                    size="small" 
                    icon={<UserOutlined />}
                    className="user-avatar"
                  />
                  <span className="user-name">
                    {user?.full_name || user?.username || '用户'}
                  </span>
                </div>
              </Dropdown>
            </Space>
          </div>
        </Header>

        {/* 主内容区域 */}
        <Content className="main-content">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </Content>
      </Layout>

      {/* 通知抽屉 */}
      <Drawer
        title="通知中心"
        placement="right"
        open={notificationDrawerVisible}
        onClose={() => setNotificationDrawerVisible(false)}
        width={400}
      >
        <div className="notifications">
          {notifications.map(notification => (
            <div key={notification.id} className="notification-item">
              <div className="notification-header">
                <span className="notification-title">{notification.title}</span>
                <span className="notification-time">{notification.time}</span>
              </div>
              <div className="notification-content">
                {notification.content}
              </div>
            </div>
          ))}
        </div>
      </Drawer>
    </Layout>
  );
};