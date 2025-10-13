/**
 * 简单的身份验证服务实现（用于测试）
 */

import { IAuthService, IUser, LoginCredentials, RegisterCredentials, AuthResult } from '../interfaces/IAuthService';

export class SimpleAuthService implements IAuthService {
  private currentUser: IUser | null = null;

  async register(credentials: RegisterCredentials): Promise<AuthResult> {
    // 简单的注册逻辑 - 仅用于开发测试
    try {
      // 模拟注册成功
      const newUser: IUser = {
        id: String(Date.now()),
        username: credentials.username,
        email: credentials.email,
        full_name: credentials.full_name,
        role: 'developer',
        is_active: true,
        created_at: new Date().toISOString(),
        last_login_at: new Date().toISOString()
      };
      
      return {
        success: true,
        user: newUser,
        permissions: ['documents:read', 'documents:write']
      };
    } catch (error) {
      return {
        success: false,
        error: '注册过程中发生错误'
      };
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResult> {
    // 模拟登录逻辑 - 仅用于开发测试
    try {
      // 简单的用户名密码验证
      if (credentials.username === 'admin' && credentials.password === 'admin') {
        this.currentUser = {
          id: '1',
          username: 'admin',
          email: 'admin@example.com',
          full_name: '系统管理员',
          role: 'admin',
          is_active: true,
          created_at: new Date().toISOString(),
          last_login_at: new Date().toISOString()
        };
        
        // 保存到localStorage
        localStorage.setItem('access_token', 'mock-access-token');
        localStorage.setItem('refresh_token', 'mock-refresh-token');
        
        return {
          success: true,
          user: this.currentUser || undefined,
          permissions: ['*'] // 管理员拥有所有权限
        };
      } else {
        return {
          success: false,
          error: '用户名或密码错误'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: '登录过程中发生错误'
      };
    }
  }

  async logout(): Promise<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.currentUser = null;
  }

  async getCurrentUser(): Promise<IUser | null> {
    if (this.currentUser) {
      return this.currentUser;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }

    // 模拟从token恢复用户信息
    this.currentUser = {
      id: '1',
      username: 'admin',
      email: 'admin@example.com',
      full_name: '系统管理员',
      role: 'admin',
      is_active: true,
      created_at: new Date().toISOString(),
      last_login_at: new Date().toISOString()
    };

    return this.currentUser;
  }

  async refreshToken(): Promise<string> {
    // 模拟刷新token
    const newToken = 'new-mock-access-token';
    localStorage.setItem('access_token', newToken);
    return newToken;
  }

  async getAccessToken(): Promise<string | null> {
    return localStorage.getItem('access_token');
  }

  hasPermission(resource: string, action: string): boolean {
    // 简单权限检查 - 管理员拥有所有权限
    return this.currentUser?.role === 'admin';
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null && !!localStorage.getItem('access_token');
  }
}