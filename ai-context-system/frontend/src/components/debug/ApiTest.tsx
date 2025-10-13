/**
 * API测试组件 - 用于调试网络请求
 */

import React, { useState } from 'react';
import { Button, Card, Typography, Space, Input, message } from 'antd';
import { ApiClient } from '../../services/ApiClient';

const { Title, Text, Paragraph } = Typography;

export const ApiTest: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');
  
  const apiClient = new ApiClient();

  const testHealthCheck = async () => {
    setLoading(true);
    try {
      console.log('Environment variables:', {
        REACT_APP_API_BASE_URL: process.env.REACT_APP_API_BASE_URL,
        NODE_ENV: process.env.NODE_ENV
      });
      
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setResult(`Health check success: ${JSON.stringify(data, null, 2)}`);
      message.success('Health check 成功');
    } catch (error) {
      console.error('Health check error:', error);
      setResult(`Health check error: ${error}`);
      message.error('Health check 失败');
    } finally {
      setLoading(false);
    }
  };

  const testApiClient = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/health');
      setResult(`API Client success: ${JSON.stringify(response, null, 2)}`);
      message.success('API Client 测试成功');
    } catch (error) {
      console.error('API Client error:', error);
      setResult(`API Client error: ${error}`);
      message.error('API Client 测试失败');
    } finally {
      setLoading(false);
    }
  };

  const testRegister = async () => {
    setLoading(true);
    try {
      const testData = {
        username: `test${Date.now()}`,
        email: `test${Date.now()}@test.com`,
        password: 'test123456',
        full_name: 'Test User'
      };
      
      const response = await apiClient.post('/auth/register', testData);
      setResult(`Register success: ${JSON.stringify(response, null, 2)}`);
      message.success('注册测试成功');
    } catch (error) {
      console.error('Register error:', error);
      setResult(`Register error: ${error}`);
      message.error('注册测试失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="API 连接测试" style={{ margin: '20px' }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Title level={4}>环境变量:</Title>
          <Text code>REACT_APP_API_BASE_URL: {process.env.REACT_APP_API_BASE_URL || '未设置'}</Text>
        </div>
        
        <Space>
          <Button onClick={testHealthCheck} loading={loading} type="primary">
            测试 Health Check (直接fetch)
          </Button>
          <Button onClick={testApiClient} loading={loading}>
            测试 API Client
          </Button>
          <Button onClick={testRegister} loading={loading}>
            测试注册接口
          </Button>
        </Space>
        
        {result && (
          <Card title="测试结果" size="small">
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
              {result}
            </pre>
          </Card>
        )}
      </Space>
    </Card>
  );
};