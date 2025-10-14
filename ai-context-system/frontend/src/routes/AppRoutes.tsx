/**
 * 应用路由配置
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LoginPage } from '../components/auth/LoginPage';
import { RegisterPage } from '../components/auth/RegisterPage';
import { MainLayout } from '../components/layout/MainLayout';
import DocumentManager from '../components/document/DocumentManager';
import { Dashboard } from '../components/dashboard/Dashboard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import LiveKnowledgeGraph from '../components/knowledge/LiveKnowledgeGraph';
import IntelligentQA from '../components/qa/IntelligentQA';
import AdvancedSearch from '../components/search/AdvancedSearch';
import SystemSettings from '../components/settings/SystemSettings';
import UserManager from '../components/users/UserManager';

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// 公共路由组件（仅在未登录时可访问）
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 公共路由 */}
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        } 
      />
      <Route 
        path="/register" 
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        } 
      />

      {/* 受保护的路由 */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* 嵌套路由 */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="documents" element={<DocumentManager />} />
        <Route path="search" element={<AdvancedSearch />} />
        <Route path="knowledge-graph" element={<LiveKnowledgeGraph />} />
        <Route path="qa" element={<IntelligentQA />} />
        <Route path="users" element={<UserManager />} />
        <Route path="settings" element={<SystemSettings />} />
      </Route>

      {/* 404页面 */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};