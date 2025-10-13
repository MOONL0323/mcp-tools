/**
 * 认证服务实现
 */

import { 
  IAuthService, 
  IUser, 
  LoginCredentials, 
  RegisterCredentials,
  AuthResult,
  TokenStorage 
} from '../interfaces/IAuthService';
import { ApiClient } from './ApiClient';

export class AuthService implements IAuthService {
  private apiClient: ApiClient;
  private tokenStorage: TokenStorage;
  private currentUser: IUser | null = null;
  private permissions: string[] = [];

  constructor(apiClient: ApiClient, tokenStorage: TokenStorage) {
    this.apiClient = apiClient;
    this.tokenStorage = tokenStorage;
  }

  async login(credentials: LoginCredentials): Promise<AuthResult> {
    try {
      const response = await this.apiClient.post('/auth/login', credentials);
      
      // 后端返回 SimpleLoginResponse: { success: boolean, message: string, user: UserInfo }
      if (response.success && response.data && response.data.success) {
        // 简化版本不使用JWT，直接保存用户信息
        this.currentUser = response.data.user;
        this.permissions = ['documents:read', 'documents:write'];
        
        // 保存一个简单的标识到localStorage
        localStorage.setItem('user_logged_in', 'true');
        localStorage.setItem('current_user', JSON.stringify(response.data.user));
        
        return {
          success: true,
          user: this.currentUser || undefined,
          permissions: this.permissions
        };
      }
      
      return { 
        success: false, 
        error: response.data?.message || response.error || '用户名或密码错误' 
      };
    } catch (error: any) {
      return { 
        success: false, 
        error: error?.response?.data?.detail || error?.message || '登录失败，请重试' 
      };
    }
  }

  async register(credentials: RegisterCredentials): Promise<AuthResult> {
    try {
      const response = await this.apiClient.post('/auth/register', credentials);
      
      // 后端注册成功时直接返回 UserInfo 对象
      if (response.success && response.data) {
        return {
          success: true,
          user: response.data,
          permissions: ['documents:read', 'documents:write']
        };
      }
      
      return { 
        success: false, 
        error: response.error || '注册失败' 
      };
    } catch (error: any) {
      return { 
        success: false, 
        error: error?.response?.data?.detail || error?.message || '注册失败，请重试' 
      };
    }
  }

  async logout(): Promise<void> {
    try {
      // 清除本地状态
      localStorage.removeItem('user_logged_in');
      localStorage.removeItem('current_user');
      this.currentUser = null;
      this.permissions = [];
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }

  async getCurrentUser(): Promise<IUser | null> {
    // 如果已经缓存了用户信息，直接返回
    if (this.currentUser) {
      return this.currentUser;
    }

    try {
      // 从localStorage恢复用户信息
      const isLoggedIn = localStorage.getItem('user_logged_in');
      const userData = localStorage.getItem('current_user');
      
      if (isLoggedIn === 'true' && userData) {
        this.currentUser = JSON.parse(userData);
        this.permissions = ['documents:read', 'documents:write'];
        return this.currentUser;
      }

      return null;
    } catch (error) {
      // 清除损坏的数据
      localStorage.removeItem('user_logged_in');
      localStorage.removeItem('current_user');
      return null;
    }
  }

  async refreshToken(): Promise<string> {
    // 简化版本不支持token刷新
    throw new Error('Token refresh not supported in simplified auth');
  }

  async getAccessToken(): Promise<string | null> {
    // 简化版本不使用token
    const isLoggedIn = localStorage.getItem('user_logged_in');
    return isLoggedIn === 'true' ? 'simplified_auth' : null;
  }

  hasPermission(resource: string, action: string): boolean {
    if (!this.currentUser) {
      return false;
    }

    // 管理员拥有所有权限
    if (this.currentUser.role === 'admin') {
      return true;
    }

    // 检查具体权限
    const permission = `${resource}:${action}`;
    return this.permissions.includes(permission);
  }

  isAuthenticated(): boolean {
    const isLoggedIn = localStorage.getItem('user_logged_in') === 'true';
    return isLoggedIn && this.currentUser !== null;
  }

  // 同步获取当前用户（仅用于已缓存的情况）
  getCurrentUserSync(): IUser | null {
    return this.currentUser;
  }
}