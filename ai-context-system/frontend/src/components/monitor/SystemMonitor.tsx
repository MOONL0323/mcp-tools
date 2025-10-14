/**
 * 系统监控面板  
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  MonitorService, 
  ServiceStatus as MonitorServiceStatus, 
  SystemEvent as MonitorSystemEvent 
} from '../../services/monitorService';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Timeline,
  Alert,
  Badge,
  Space,
  Typography,
  Switch,
  Button,
  List,
  Tag,
  Divider
} from 'antd';
import {
  DashboardOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  BugOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons';
import { Line, Area, Column } from '@ant-design/plots';

const { Title, Text } = Typography;

// 系统指标接口
interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  activeUsers: number;
  totalRequests: number;
  errorRate: number;
  responseTime: number;
}

// 系统事件接口 - 本地定义
interface LocalSystemEvent {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  category: string;
  message: string;
  details?: string;
}

// 服务状态接口 - 本地定义
interface LocalServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error' | 'warning';  // 添加 'warning' 支持
  uptime: string;
  lastCheck: string;
  url?: string;
}

const SystemMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 45,
    memory: 62,
    disk: 38,
    network: 28,
    activeUsers: 125,
    totalRequests: 8934,
    errorRate: 0.5,
    responseTime: 245
  });

  const [events, setEvents] = useState<LocalSystemEvent[]>([]);
  const [services, setServices] = useState<LocalServiceStatus[]>([]);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [chartData, setChartData] = useState<any[]>([]);
  const intervalRef = useRef<NodeJS.Timeout>();

  // 模拟服务状态
  const mockServices: LocalServiceStatus[] = [
    {
      name: 'Web服务器',
      status: 'running',
      uptime: '7天 3小时 25分钟',
      lastCheck: new Date().toISOString(),
      url: 'http://localhost:3000'
    },
    {
      name: 'API服务器',
      status: 'running',
      uptime: '6天 18小时 42分钟',
      lastCheck: new Date().toISOString(),
      url: 'http://localhost:8000'
    },
    {
      name: 'PostgreSQL数据库',
      status: 'running',
      uptime: '15天 6小时 12分钟',
      lastCheck: new Date().toISOString()
    },
    {
      name: 'Neo4j图数据库',
      status: 'running',
      uptime: '12天 9小时 35分钟',
      lastCheck: new Date().toISOString()
    },
    {
      name: 'Redis缓存',
      status: 'running',
      uptime: '8天 14小时 20分钟',
      lastCheck: new Date().toISOString()
    },
    {
      name: 'AI模型服务',
      status: 'error',
      uptime: '0分钟',
      lastCheck: new Date().toISOString()
    }
  ];

  // 模拟系统事件
  const mockEvents: LocalSystemEvent[] = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      level: 'error',
      category: 'AI服务',
      message: 'AI模型服务连接失败',
      details: '无法连接到嵌入模型服务，请检查服务状态'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
      level: 'warning',
      category: '性能',
      message: 'CPU使用率过高',
      details: 'CPU使用率达到85%，建议检查高负载进程'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      level: 'info',
      category: '用户',
      message: '新用户注册',
      details: '用户"张三"成功注册并加入前端团队'
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
      level: 'info',
      category: '文档',
      message: '文档处理完成',
      details: '《系统架构文档》已完成解析，生成了128个知识块'
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
      level: 'warning',
      category: '存储',
      message: '磁盘空间不足',
      details: '系统磁盘使用率达到75%，建议清理临时文件'
    }
  ];

  // 生成图表数据
  const generateChartData = () => {
    const now = Date.now();
    const data = [];
    for (let i = 29; i >= 0; i--) {
      data.push({
        time: new Date(now - i * 60 * 1000).toLocaleTimeString(),
        cpu: Math.random() * 30 + 30,
        memory: Math.random() * 20 + 50,
        network: Math.random() * 40 + 10,
        requests: Math.floor(Math.random() * 100 + 50)
      });
    }
    return data;
  };

  // 更新系统指标
  const updateMetrics = async () => {
    try {
      const systemMetrics = await MonitorService.getSystemMetrics();
      
      setMetrics(prev => ({
        ...prev,
        cpu: systemMetrics.cpu_usage,
        memory: systemMetrics.memory_usage,
        disk: systemMetrics.disk_usage,
        network: (systemMetrics.network_in + systemMetrics.network_out) / 2,
        activeUsers: systemMetrics.active_connections,
        totalRequests: prev.totalRequests + Math.floor(Math.random() * 50), // 累计请求数
        errorRate: systemMetrics.error_rate,
        responseTime: systemMetrics.response_time
      }));
    } catch (error) {
      console.error('更新指标失败:', error);
      // 降级到随机更新
      setMetrics(prev => ({
        ...prev,
        cpu: Math.max(10, Math.min(90, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(20, Math.min(85, prev.memory + (Math.random() - 0.5) * 8)),
        network: Math.max(5, Math.min(60, prev.network + (Math.random() - 0.5) * 15)),
        activeUsers: prev.activeUsers + Math.floor((Math.random() - 0.5) * 10),
        totalRequests: prev.totalRequests + Math.floor(Math.random() * 50),
        responseTime: Math.max(100, Math.min(500, prev.responseTime + (Math.random() - 0.5) * 50))
      }));
    }

    // 更新图表数据
    setChartData(prev => {
      const newData = [...prev];
      if (newData.length >= 30) {
        newData.shift();
      }
      newData.push({
        time: new Date().toLocaleTimeString(),
        cpu: metrics.cpu,
        memory: metrics.memory,
        network: metrics.network,
        requests: Math.floor(Math.random() * 100 + 50)
      });
      return newData;
    });
  };

  // 初始化和实时更新
  useEffect(() => {
    loadInitialData();

    if (realTimeEnabled) {
      intervalRef.current = setInterval(updateMetrics, 3000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [realTimeEnabled]);

  // 加载初始数据
  const loadInitialData = async () => {
    try {
      const [serviceData, eventData, performanceData] = await Promise.all([
        MonitorService.getServiceStatus(),
        MonitorService.getSystemEvents(20),
        MonitorService.getPerformanceHistory(24)
      ]);
      
      // 转换服务数据为本地类型
      setServices(serviceData as LocalServiceStatus[]);
      // 转换事件数据为本地类型
      setEvents(eventData.map((event: MonitorSystemEvent) => ({
        id: event.id,
        timestamp: event.timestamp,
        level: event.type === 'success' ? 'info' : event.type,  // 映射 success 到 info
        category: event.service || '系统',
        message: event.message,
        details: event.details
      })));
      setChartData(performanceData);
    } catch (error) {
      console.error('加载监控数据失败:', error);
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  // 获取事件级别颜色
  const getEventLevelColor = (level: string) => {
    switch (level) {
      case 'info': return 'blue';
      case 'warning': return 'orange';
      case 'error': return 'red';
      default: return 'default';
    }
  };

  // 获取事件级别图标
  const getEventLevelIcon = (level: string) => {
    switch (level) {
      case 'info': return <CheckCircleOutlined />;
      case 'warning': return <ExclamationCircleOutlined />;
      case 'error': return <CloseCircleOutlined />;
      default: return <CheckCircleOutlined />;
    }
  };

  // 性能图表配置
  const performanceChartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'cpu',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: ['#1890ff', '#52c41a', '#faad14'],
  };

  // 请求量图表配置
  const requestChartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'requests',
    smooth: true,
    color: '#722ed1',
    areaStyle: {
      fill: 'l(270) 0:#ffffff 0.5:#722ed1 1:#722ed1',
    },
  };

  return (
    <div>
      {/* 控制面板 */}
      <Card style={{ marginBottom: '16px' }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Title level={3}>
              <DashboardOutlined /> 系统监控面板
            </Title>
          </Col>
          <Col>
            <Space>
              <Text>实时更新:</Text>
              <Switch
                checked={realTimeEnabled}
                onChange={setRealTimeEnabled}
                checkedChildren="开启"
                unCheckedChildren="关闭"
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  updateMetrics();
                  setChartData(generateChartData());
                }}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 系统概览指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU使用率"
              value={metrics.cpu}
              precision={1}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                color: metrics.cpu > 80 ? '#f5222d' : metrics.cpu > 60 ? '#fa8c16' : '#52c41a' 
              }}
            />
            <Progress 
              percent={metrics.cpu} 
              size="small" 
              status={metrics.cpu > 80 ? 'exception' : 'active'}
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={metrics.memory}
              precision={1}
              suffix="%"
              prefix={<DatabaseOutlined />}
              valueStyle={{ 
                color: metrics.memory > 80 ? '#f5222d' : metrics.memory > 60 ? '#fa8c16' : '#52c41a' 
              }}
            />
            <Progress 
              percent={metrics.memory} 
              size="small" 
              status={metrics.memory > 80 ? 'exception' : 'active'}
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={metrics.activeUsers}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="响应时间"
              value={metrics.responseTime}
              suffix="ms"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                color: metrics.responseTime > 400 ? '#f5222d' : metrics.responseTime > 200 ? '#fa8c16' : '#52c41a'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        {/* 性能图表 */}
        <Col span={16}>
          <Card title="系统性能趋势" style={{ height: '400px' }}>
            <Line {...performanceChartConfig} height={320} />
          </Card>
        </Col>

        {/* 服务状态 */}
        <Col span={8}>
          <Card title="服务状态" style={{ height: '400px' }}>
            <List
              dataSource={services}
              renderItem={(service) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Badge 
                        status={getStatusColor(service.status)} 
                        dot 
                      />
                    }
                    title={
                      <Space>
                        <Text strong>{service.name}</Text>
                        <Tag color={getStatusColor(service.status)}>
                          {service.status === 'running' ? '运行中' :
                           service.status === 'stopped' ? '已停止' : '错误'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          运行时间: {service.uptime}
                        </Text>
                        {service.url && (
                          <div>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              地址: {service.url}
                            </Text>
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
              style={{ maxHeight: '320px', overflowY: 'auto' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 请求量图表 */}
        <Col span={12}>
          <Card title="API请求量" style={{ height: '350px' }}>
            <Area {...requestChartConfig} height={270} />
          </Card>
        </Col>

        {/* 系统事件 */}
        <Col span={12}>
          <Card title="系统事件" style={{ height: '350px' }}>
            <Timeline
              style={{ maxHeight: '270px', overflowY: 'auto' }}
              items={events.map(event => ({
                dot: getEventLevelIcon(event.level),
                color: getEventLevelColor(event.level),
                children: (
                  <div>
                    <div style={{ marginBottom: '4px' }}>
                      <Space>
                        <Text strong>{event.message}</Text>
                        <Tag color={getEventLevelColor(event.level)} style={{ fontSize: '11px' }}>
                          {event.category}
                        </Tag>
                      </Space>
                    </div>
                    {event.details && (
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {event.details}
                      </Text>
                    )}
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        {new Date(event.timestamp).toLocaleString()}
                      </Text>
                    </div>
                  </div>
                )
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* 警告信息 */}
      {metrics.cpu > 80 || metrics.memory > 80 || services.some(s => s.status === 'error') ? (
        <Alert
          message="系统警告"
          description={
            <div>
              {metrics.cpu > 80 && <div>• CPU使用率过高({metrics.cpu.toFixed(1)}%)</div>}
              {metrics.memory > 80 && <div>• 内存使用率过高({metrics.memory.toFixed(1)}%)</div>}
              {services.filter(s => s.status === 'error').map(service => (
                <div key={service.name}>• {service.name}服务异常</div>
              ))}
            </div>
          }
          type="warning"
          showIcon
          style={{ marginTop: '16px' }}
        />
      ) : null}
    </div>
  );
};

export default SystemMonitor;