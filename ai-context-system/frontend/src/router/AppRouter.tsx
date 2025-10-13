/**
 * 主应用路由配置
 */

import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { AuthProvider } from '../hooks/useAuth';
import { PrivateRoute } from '../components/auth/PrivateRoute';
import { LoginPage } from '../components/auth/LoginPage';
import { RegisterPage } from '../components/auth/RegisterPage';
import { MainLayout } from '../components/layout/MainLayout';
import { Dashboard } from '../components/dashboard/Dashboard';
import { SimpleDocumentManager } from '../components/document/SimpleDocumentManager';
import RealDocumentManager from '../components/document/RealDocumentManager';

// 懒加载组件
const KnowledgeGraph = React.lazy(() => import('../components/knowledge/KnowledgeGraph'));
const UserManager = React.lazy(() => import('../components/user/UserManager'));
const Settings = React.lazy(() => import('../components/settings/Settings'));

// 加载中组件
const LoadingSpinner: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '200px' 
  }}>
    <Spin size="large" />
  </div>
);

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* 登录页面 */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* 注册页面 */}
            <Route path="/register" element={<RegisterPage />} />
            
            {/* 受保护的主应用路由 */}
            <Route path="/" element={
              <PrivateRoute>
                <MainLayout />
              </PrivateRoute>
            }>
              {/* 默认重定向到仪表板 */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              
              {/* 仪表板 */}
              <Route path="dashboard" element={<Dashboard />} />
              
              {/* 文档管理（Mock版本） */}
              <Route path="documents" element={<SimpleDocumentManager />} />
              
              {/* 文档管理（真实API版本） */}
              <Route path="documents-real" element={<RealDocumentManager />} />
              
              {/* 知识图谱 */}
              <Route path="knowledge-graph" element={<KnowledgeGraph />} />
              
              {/* 用户管理 */}
              <Route path="users" element={<UserManager />} />
              
              {/* 系统设置 */}
              <Route path="settings" element={<Settings />} />
            </Route>
            
            {/* 404 页面 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
};