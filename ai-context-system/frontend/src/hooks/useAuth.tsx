/**
 * 认证相关的React Hook
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { IUser, IAuthService, LoginCredentials, RegisterCredentials, AuthResult } from '../interfaces/IAuthService';
import { DIContainer } from '../core/DIContainer';

interface AuthContextType {
  user: IUser | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<AuthResult>;
  register: (credentials: RegisterCredentials) => Promise<AuthResult>;
  logout: () => Promise<void>;
  hasPermission: (resource: string, action: string) => boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<IUser | null>(null);
  const [loading, setLoading] = useState(true);
  const authService = DIContainer.getInstance().resolve<IAuthService>('AuthService');

  useEffect(() => {
    checkAuthState();
  }, []);

  const checkAuthState = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials): Promise<AuthResult> => {
    setLoading(true);
    try {
      const result = await authService.login(credentials);
      if (result.success && result.user) {
        setUser(result.user);
      }
      return result;
    } catch (error) {
      return {
        success: false,
        error: '登录过程中发生错误'
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials): Promise<AuthResult> => {
    setLoading(true);
    try {
      const result = await authService.register(credentials);
      return result;
    } catch (error) {
      return {
        success: false,
        error: '注册过程中发生错误'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
      // 即使登出失败，也清除本地状态
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (resource: string, action: string): boolean => {
    return authService.hasPermission(resource, action);
  };

  const isAuthenticated = user !== null;

  const contextValue: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    hasPermission,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};