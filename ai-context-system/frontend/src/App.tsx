/**
 * 应用主入口组件
 */

import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AppRouter } from './router/AppRouter';
import { DIContainer } from './core/DIContainer';
import { AuthService } from './services/AuthService';
import { ApiClient } from './services/ApiClient';
import { LocalTokenStorage } from './services/TokenStorage';
import { SimpleDocumentService } from './services/SimpleDocumentService';
import { SimpleClassificationService } from './services/SimpleClassificationService';
import 'antd/dist/reset.css';
import './App.css';

// 注册服务到DI容器
const container = DIContainer.getInstance();

// 创建API客户端和Token存储
const apiClient = new ApiClient();
const tokenStorage = new LocalTokenStorage();

// 注册真正的认证服务
container.registerSingleton('AuthService', () => new AuthService(apiClient, tokenStorage));
container.registerSingleton('DocumentService', () => new SimpleDocumentService());
container.registerSingleton('ClassificationService', () => new SimpleClassificationService());

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <div className="App">
        <AppRouter />
      </div>
    </ConfigProvider>
  );
};

export default App;