/**
 * 登录页面组件
 */

import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert, Typography, Space, message } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { LoadingSpinner } from '../common/LoadingSpinner';
import './LoginPage.css';

const { Title, Text } = Typography;

interface LoginFormData {
  username: string;
  password: string;
}

export const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // 获取重定向路径，默认为首页
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (values: LoginFormData) => {
    setLoading(true);
    setError(null);

    try {
      // 使用 useAuth 的 login 方法，它会自动更新 Context 状态
      const result = await login({
        username: values.username,
        password: values.password
      });

      if (result.success) {
        message.success('登录成功！');
        // 登录成功后跳转到目标页面
        navigate(from, { replace: true });
      } else {
        setError(result.error || '登录失败，请检查用户名和密码');
      }
    } catch (err) {
      console.error('登录错误:', err);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <Card className="login-card" bordered={false}>
          <div className="login-header">
            <Title level={2} style={{ textAlign: 'center', marginBottom: 8 }}>
              AI Context System
            </Title>
            <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 32 }}>
              智能上下文增强系统
            </Text>
          </div>

          {error && (
            <Alert 
              message={error} 
              type="error" 
              showIcon 
              style={{ marginBottom: 24 }} 
              closable
              onClose={() => setError(null)}
            />
          )}
          
          <Form
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            size="large"
            layout="vertical"
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' }
              ]}
            >
              <Input 
                prefix={<UserOutlined style={{ color: '#bfbfbf' }} />} 
                placeholder="请输入用户名" 
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' }
              ]}
            >
              <Input.Password 
                prefix={<LockOutlined style={{ color: '#bfbfbf' }} />} 
                placeholder="请输入密码" 
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                disabled={loading}
                style={{ width: '100%', height: '48px' }}
                icon={!loading && <LoginOutlined />}
              >
                {loading ? '登录中...' : '登录'}
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <Space>
              <Text type="secondary">没有账户？</Text>
              <Link to="/register">
                <Button type="link" style={{ padding: 0 }}>
                  立即注册
                </Button>
              </Link>
            </Space>
          </div>

          <div className="login-footer">
            <Space direction="vertical" align="center" style={{ width: '100%' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                基于 Graph RAG 的智能知识管理平台
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                © 2025 AI Context System. All rights reserved.
              </Text>
            </Space>
          </div>
        </Card>
      </div>

      {loading && (
        <div className="login-loading-overlay">
          <LoadingSpinner tip="正在登录..." />
        </div>
      )}
    </div>
  );
};