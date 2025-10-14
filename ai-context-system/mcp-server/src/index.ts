/**
 * AI上下文增强MCP服务器入口文件
 * 
 * 启动团队知识库的MCP服务器，为AI Agent提供上下文增强能力
 */

import { TeamContextMCPServer } from './server.js';
import { config, validateConfig } from './config/config.js';
import { logger, PerformanceMonitor } from './utils/logger.js';
import { getCacheInstance } from './services/cache-service.js';

/**
 * 主函数 - 启动MCP服务器
 */
async function main(): Promise<void> {
  try {
    // 验证配置
    logger.info('验证配置...');
    validateConfig();
    
    // 显示启动信息
    logger.info('================================');
    logger.info(`🚀 启动 ${config.serverName} v${config.serverVersion}`);
    logger.info(`📅 启动时间: ${new Date().toISOString()}`);
    logger.info(`🌍 环境: ${config.nodeEnv}`);
    logger.info(`🔗 RAG引擎: ${config.ragEngineUrl}`);
    logger.info(`📊 后端API: ${config.backendApiUrl}`);
    logger.info(`⚡ 缓存TTL: ${config.cacheTtl}s`);
    logger.info('================================');

    // 初始化缓存服务
    logger.info('初始化缓存服务...');
    const cacheService = getCacheInstance();
    logger.info('✅ 缓存服务已初始化');

    // 性能监控开始
    PerformanceMonitor.start('server_startup');

    // 创建并启动MCP服务器
    logger.info('创建MCP服务器实例...');
    const mcpServer = new TeamContextMCPServer();
    
    logger.info('启动MCP服务器...');
    await mcpServer.start();
    
    // 性能监控结束
    const startupTime = PerformanceMonitor.end('server_startup');
    logger.info(`🎉 MCP服务器启动成功！启动耗时: ${startupTime}ms`);

    // 显示服务器状态
    logger.info('🔧 服务器能力:');
    logger.info('   - 🔍 代码示例搜索');
    logger.info('   - 📋 设计文档查询');
    logger.info('   - 📏 编码规范获取');
    logger.info('   - 🕸️ 知识图谱遍历');

    logger.info('📖 可用资源:');
    logger.info('   - context://team-knowledge-base');
    logger.info('   - context://coding-standards');
    logger.info('   - context://design-patterns');

    // 定期输出状态信息
    const statusInterval = setInterval(() => {
      const cacheUsage = cacheService.getUsage();
      logger.info('服务器状态:', {
        uptime: Math.floor(process.uptime()),
        memory: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`,
        cache: `${cacheUsage.keys} keys, ${cacheUsage.hitRate}% hit rate`
      });
    }, 300000); // 每5分钟输出一次状态

    // 优雅关闭处理
    const gracefulShutdown = async (signal: string) => {
      logger.info(`收到 ${signal} 信号，正在优雅关闭服务器...`);
      
      // 清理定时器
      clearInterval(statusInterval);
      
      try {
        // 关闭MCP服务器
        await mcpServer.stop();
        
        // 清理缓存
        cacheService.flushAll();
        
        logger.info('✅ 服务器已优雅关闭');
        process.exit(0);
      } catch (error) {
        logger.error('关闭服务器时出错:', error);
        process.exit(1);
      }
    };

    // 注册信号处理器
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

    // 未捕获异常处理
    process.on('uncaughtException', (error) => {
      logger.error('未捕获的异常:', error);
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      logger.error('未处理的Promise拒绝:', { reason, promise });
      process.exit(1);
    });

    logger.info('✅ 服务器已启动，等待MCP连接...');
    logger.info('💡 提示: 在Claude Desktop中配置此MCP服务器以开始使用');
    logger.info('📚 配置说明: https://github.com/your-org/ai-context-system/blob/main/mcp-server/README.md');

  } catch (error) {
    logger.error('启动服务器失败:', error);
    
    if (error instanceof Error) {
      logger.error('错误详情:', {
        message: error.message,
        stack: error.stack
      });
    }
    
    process.exit(1);
  }
}

/**
 * 健康检查函数
 */
async function healthCheck(): Promise<boolean> {
  try {
    // 检查后端API连接
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(`${config.backendApiUrl}/health`, {
      method: 'GET',
      signal: controller.signal
    });
    
    if (!response.ok) {
      logger.warn('后端API健康检查失败:', response.status);
      return false;
    }

    // 检查缓存服务
    const cacheService = getCacheInstance();
    cacheService.set('health_check', Date.now(), 10);
    const testValue = cacheService.get('health_check');
    
    if (!testValue) {
      logger.warn('缓存服务健康检查失败');
      return false;
    }

    logger.debug('健康检查通过');
    return true;
  } catch (error) {
    logger.warn('健康检查出错:', error);
    return false;
  }
}

/**
 * 显示帮助信息
 */
function showHelp(): void {
  console.log(`
🤖 AI上下文增强MCP服务器

用法:
  npm start                 启动MCP服务器
  npm run dev              开发模式启动
  npm run build            构建TypeScript
  npm test                 运行测试

环境变量:
  SERVER_NAME              服务器名称 (默认: team-context-server)
  RAG_ENGINE_URL          RAG引擎地址 (默认: http://127.0.0.1:8000)
  BACKEND_API_URL         后端API地址 (默认: http://127.0.0.1:8000/api/v1)
  LOG_LEVEL               日志级别 (默认: info)
  CACHE_TTL               缓存TTL秒数 (默认: 300)

示例:
  # 启动服务器
  RAG_ENGINE_URL=http://localhost:8000 npm start
  
  # 开发模式
  LOG_LEVEL=debug npm run dev

配置Claude Desktop:
1. 打开Claude Desktop设置
2. 在MCP Settings中添加:
   {
     "team-context-server": {
       "command": "node",
       "args": ["path/to/mcp-server/dist/index.js"],
       "env": {
         "RAG_ENGINE_URL": "http://127.0.0.1:8000"
       }
     }
   }

更多信息: https://github.com/your-org/ai-context-system
  `);
}

// 检查命令行参数
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  showHelp();
  process.exit(0);
}

if (process.argv.includes('--health-check')) {
  healthCheck().then(healthy => {
    process.exit(healthy ? 0 : 1);
  });
} else {
  // 启动主程序
  main().catch(error => {
    console.error('启动失败:', error);
    process.exit(1);
  });
}

export { main, healthCheck, showHelp };