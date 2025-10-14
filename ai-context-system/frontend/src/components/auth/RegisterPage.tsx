/**
 * 用户注册页面
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Form, 
  Input, 
  Button, 
  Card, 
  Typography, 
  message,
  Row,
  Col,
  Space
} from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { RegisterCredentials } from '../../interfaces/IAuthService';

const { Title, Text } = Typography;

export const RegisterPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      // 直接调用API
      const { confirmPassword, ...registerData } = values;
      
      const response = await fetch('http://localhost:8080/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData)
      });

      const data = await response.json();
      
      if (response.ok) {
        message.success('注册成功！请登录');
        navigate('/login');
      } else {
        message.error(data.detail || '注册失败');
      }
    } catch (error) {
      console.error('注册错误:', error);
      message.error('注册过程中发生错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Row justify="center" style={{ width: '100%' }}>
        <Col xs={24} sm={16} md={12} lg={8} xl={6}>
          <Card
            style={{
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            }}
          >
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
                AI Context System
              </Title>
              <Text type="secondary">创建新账户</Text>
            </div>

            <Form
              name="register"
              onFinish={onFinish}
              layout="vertical"
              size="large"
            >
              <Form.Item
                label="用户名"
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { max: 50, message: '用户名最多50个字符' }
                ]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="请输入用户名" 
                />
              </Form.Item>

              <Form.Item
                label="邮箱"
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input 
                  prefix={<MailOutlined />} 
                  placeholder="请输入邮箱" 
                />
              </Form.Item>

              <Form.Item
                label="姓名"
                name="full_name"
                rules={[
                  { required: true, message: '请输入姓名' },
                  { min: 2, message: '姓名至少2个字符' },
                  { max: 100, message: '姓名最多100个字符' }
                ]}
              >
                <Input 
                  prefix={<IdcardOutlined />} 
                  placeholder="请输入真实姓名" 
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
                  prefix={<LockOutlined />} 
                  placeholder="请输入密码" 
                />
              </Form.Item>

              <Form.Item
                label="确认密码"
                name="confirmPassword"
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
                  placeholder="请再次输入密码" 
                />
              </Form.Item>

              <Form.Item style={{ marginBottom: '16px' }}>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={loading}
                  block
                  style={{ height: '45px' }}
                >
                  注册
                </Button>
              </Form.Item>
            </Form>

            <div style={{ textAlign: 'center' }}>
              <Space>
                <Text type="secondary">已有账户？</Text>
                <Link to="/login">
                  <Button type="link" style={{ padding: 0 }}>
                    立即登录
                  </Button>
                </Link>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};