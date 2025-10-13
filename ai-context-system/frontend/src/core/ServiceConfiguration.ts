/**
 * 服务配置 - 依赖注入配置
 */

import { DIContainer } from './DIContainer';
import { ApiClient } from '../services/ApiClient';
import { LocalTokenStorage } from '../services/TokenStorage';
import { AuthService } from '../services/AuthService';
// import { DocumentService } from '../services/DocumentService';
// import { ClassificationService } from '../services/ClassificationService';

export const configureServices = () => {
  const container = DIContainer.getInstance();

  // HTTP客户端配置
  container.registerSingleton('ApiClient', () => 
    new ApiClient({
      baseURL: process.env.REACT_APP_API_BASE_URL || '/api',
      timeout: 10000,
      withCredentials: true
    })
  );

  // Token存储配置
  container.registerSingleton('TokenStorage', () => 
    new LocalTokenStorage()
  );

  // 认证服务配置 - 使用真实API认证
  container.registerSingleton('IAuthService', () => 
    new AuthService(
      container.resolve('ApiClient'),
      container.resolve('TokenStorage')
    )
  );

  // 文档服务配置 - 暂时注释掉，稍后实现
  // container.registerSingleton('IDocumentService', () => 
  //   new DocumentService(
  //     container.resolve('ApiClient'),
  //     container.resolve('IAuthService')
  //   )
  // );

  // 分类服务配置 - 暂时注释掉，稍后实现
  // container.registerSingleton('IClassificationService', () => 
  //   new ClassificationService(
  //     container.resolve('ApiClient')
  //   )
  // );
};

// React Hook for DI
import { useMemo } from 'react';

export const useService = <T>(token: string): T => {
  return useMemo(() => {
    return DIContainer.getInstance().resolve<T>(token);
  }, [token]);
};