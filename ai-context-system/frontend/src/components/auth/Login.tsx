/**
 * 登录页面
 */

import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../../services/api';

const { Title, Text } = Typography;

interface LoginFormValues {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (values: LoginFormValues) => {
    try {
      setLoading(true);
      
      const response = await apiClient.post('/v1/auth/login', values);
      
      if (response.success && response.data) {
        // 存储用户信息
        localStorage.setItem('user', JSON.stringify(response.data.user));
        localStorage.setItem('isAuthenticated', 'true');
        
        message.success('登录成功！');
        
        // 跳转到首页
        setTimeout(() => {
          navigate('/dashboard');
        }, 500);
      } else {
        message.error(response.error || '登录失败');
      }
    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card
        style={{
          width: 400,
          boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
          borderRadius: 8
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              AI上下文增强系统
            </Title>
            <Text type="secondary">为团队AI代码生成提供上下文支持</Text>
          </div>

          <Form
            form={form}
            name="login"
            onFinish={handleLogin}
            size="large"
            autoComplete="off"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{ height: 42 }}
              >
                登录
              </Button>
            </Form.Item>

            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">
                还没有账号？{' '}
                <Link to="/register">立即注册</Link>
              </Text>
            </div>
          </Form>
        </Space>
      </Card>
    </div>
  );
};

export default Login;
