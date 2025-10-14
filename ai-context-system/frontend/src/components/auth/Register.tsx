/**
 * 注册页面
 */

import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../../services/api';

const { Title, Text } = Typography;

interface RegisterFormValues {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
}

const Register: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (values: RegisterFormValues) => {
    try {
      setLoading(true);
      
      const { confirmPassword, ...registerData } = values;
      
      const response = await apiClient.post('/v1/auth/register', registerData);
      
      if (response.success) {
        message.success('注册成功！请登录');
        
        // 跳转到登录页
        setTimeout(() => {
          navigate('/login');
        }, 1000);
      } else {
        message.error(response.error || '注册失败');
      }
    } catch (error: any) {
      console.error('注册失败:', error);
      message.error(error.response?.data?.detail || '注册失败，请稍后重试');
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
          width: 450,
          boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
          borderRadius: 8
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              创建账号
            </Title>
            <Text type="secondary">加入团队，开始使用AI上下文增强系统</Text>
          </div>

          <Form
            form={form}
            name="register"
            onFinish={handleRegister}
            size="large"
            autoComplete="off"
            layout="vertical"
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
                { max: 50, message: '用户名最多50个字符' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
              />
            </Form.Item>

            <Form.Item
              name="full_name"
              label="姓名"
              rules={[
                { required: true, message: '请输入姓名' },
                { min: 2, message: '姓名至少2个字符' }
              ]}
            >
              <Input
                prefix={<IdcardOutlined />}
                placeholder="真实姓名"
              />
            </Form.Item>

            <Form.Item
              name="email"
              label="邮箱"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="邮箱地址"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="确认密码"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="再次输入密码"
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
                注册
              </Button>
            </Form.Item>

            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">
                已有账号？{' '}
                <Link to="/login">立即登录</Link>
              </Text>
            </div>
          </Form>
        </Space>
      </Card>
    </div>
  );
};

export default Register;
