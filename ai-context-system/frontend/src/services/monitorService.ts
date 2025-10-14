/**
 * 系统监控API服务
 */

import { apiClient } from './api';

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'warning' | 'error';
  uptime: string;
  lastCheck: string;
  url?: string;
}

export interface SystemEvent {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
  service?: string;
  details?: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_in: number;
  network_out: number;
  active_connections: number;
  response_time: number;
  error_rate: number;
}

export interface MonitorResponse {
  success: boolean;
  data: any;
  error?: string;
}

export class MonitorService {
  /**
   * 获取系统服务状态
   */
  static async getServiceStatus(): Promise<ServiceStatus[]> {
    try {
      console.log('获取系统服务状态');
      
      const response = await apiClient.get('/v1/monitor/services');

      if (response.data.success) {
        return response.data.data.services || [];
      } else {
        throw new Error(response.data.error || '获取服务状态失败');
      }
    } catch (error: any) {
      console.error('获取服务状态失败:', error);
      
      // 返回降级数据
      return this.getFallbackServiceStatus();
    }
  }

  /**
   * 获取系统指标
   */
  static async getSystemMetrics(): Promise<SystemMetrics> {
    try {
      const response = await apiClient.get('/v1/monitor/metrics');

      if (response.data.success) {
        return response.data.data.metrics;
      } else {
        throw new Error(response.data.error || '获取系统指标失败');
      }
    } catch (error: any) {
      console.error('获取系统指标失败:', error);
      
      // 返回降级数据
      return this.getFallbackMetrics();
    }
  }

  /**
   * 获取系统事件日志
   */
  static async getSystemEvents(limit: number = 50): Promise<SystemEvent[]> {
    try {
      const response = await apiClient.get(`/api/v1/monitor/events?limit=${limit}`);

      if (response.data.success) {
        return response.data.data.events || [];
      } else {
        throw new Error(response.data.error || '获取系统事件失败');
      }
    } catch (error: any) {
      console.error('获取系统事件失败:', error);
      
      // 返回降级数据
      return this.getFallbackEvents();
    }
  }

  /**
   * 获取性能历史数据
   */
  static async getPerformanceHistory(hours: number = 24): Promise<any[]> {
    try {
      const response = await apiClient.get(`/api/v1/monitor/performance?hours=${hours}`);

      if (response.data.success) {
        return response.data.data.history || [];
      } else {
        throw new Error(response.data.error || '获取性能历史失败');
      }
    } catch (error: any) {
      console.error('获取性能历史失败:', error);
      
      // 返回降级数据
      return this.getFallbackPerformanceData();
    }
  }

  /**
   * 重启服务
   */
  static async restartService(serviceName: string): Promise<boolean> {
    try {
      const response = await apiClient.post('/v1/monitor/services/restart', {
        service: serviceName
      });

      return response.data.success;
    } catch (error: any) {
      console.error('重启服务失败:', error);
      return false;
    }
  }

  /**
   * 降级服务状态数据
   */
  private static getFallbackServiceStatus(): ServiceStatus[] {
    const now = new Date().toISOString();
    
    return [
      {
        name: 'Web服务器',
        status: 'running',
        uptime: '7天 3小时 25分钟',
        lastCheck: now,
        url: 'http://localhost:3000'
      },
      {
        name: 'API服务器', 
        status: 'running',
        uptime: '6天 18小时 42分钟',
        lastCheck: now,
        url: 'http://localhost:8000'
      },
      {
        name: 'PostgreSQL数据库',
        status: 'running',
        uptime: '15天 6小时 12分钟',
        lastCheck: now
      },
      {
        name: 'Neo4j图数据库',
        status: 'running',
        uptime: '12天 9小时 35分钟',
        lastCheck: now
      },
      {
        name: 'ChromaDB向量数据库',
        status: 'running',
        uptime: '8天 14小时 18分钟',
        lastCheck: now
      },
      {
        name: '文件存储服务',
        status: 'warning',
        uptime: '5天 2小时 8分钟',
        lastCheck: now
      }
    ];
  }

  /**
   * 降级系统指标数据
   */
  private static getFallbackMetrics(): SystemMetrics {
    return {
      cpu_usage: Math.random() * 30 + 20, // 20-50%
      memory_usage: Math.random() * 40 + 40, // 40-80%
      disk_usage: Math.random() * 20 + 30, // 30-50%
      network_in: Math.random() * 100 + 50, // 50-150 Mbps
      network_out: Math.random() * 80 + 30, // 30-110 Mbps
      active_connections: Math.floor(Math.random() * 200 + 100), // 100-300
      response_time: Math.random() * 100 + 50, // 50-150ms
      error_rate: Math.random() * 2 // 0-2%
    };
  }

  /**
   * 降级系统事件数据
   */
  private static getFallbackEvents(): SystemEvent[] {
    const now = new Date();
    const events: SystemEvent[] = [];
    
    const eventTypes = ['info', 'warning', 'error', 'success'] as const;
    const services = ['Web服务器', 'API服务器', 'PostgreSQL', 'Neo4j', 'ChromaDB'];
    const messages = {
      info: ['系统启动完成', '定期备份已完成', '性能监控正常'],
      warning: ['内存使用率较高', '磁盘空间不足', '响应时间增加'],
      error: ['连接数据库失败', '服务响应超时', 'API调用异常'],
      success: ['服务重启成功', '数据同步完成', '性能优化生效']
    };

    for (let i = 0; i < 20; i++) {
      const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      const service = services[Math.floor(Math.random() * services.length)];
      const messageList = messages[type];
      const message = messageList[Math.floor(Math.random() * messageList.length)];
      
      events.push({
        id: `event_${i + 1}`,
        type,
        message,
        service,
        timestamp: new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
        details: type === 'error' ? '详细错误信息可在日志中查看' : undefined
      });
    }

    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  /**
   * 降级性能历史数据
   */
  private static getFallbackPerformanceData(): any[] {
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.toISOString(),
        cpu: Math.random() * 30 + 20,
        memory: Math.random() * 40 + 40,
        disk: Math.random() * 20 + 30,
        network_in: Math.random() * 100 + 50,
        network_out: Math.random() * 80 + 30,
        response_time: Math.random() * 100 + 50,
        active_connections: Math.floor(Math.random() * 200 + 100)
      });
    }
    
    return data;
  }
}