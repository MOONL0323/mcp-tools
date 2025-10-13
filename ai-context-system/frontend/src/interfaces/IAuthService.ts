/**
 * 用户认证相关接口定义
 */

export interface IUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'developer';
  avatar_url?: string;
  created_at: string;
  last_login_at?: string;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResult {
  success: boolean;
  user?: IUser;
  permissions?: string[];
  error?: string;
}

export interface IAuthService {
  login(credentials: LoginCredentials): Promise<AuthResult>;
  register(credentials: RegisterCredentials): Promise<AuthResult>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<IUser | null>;
  refreshToken(): Promise<string>;
  getAccessToken(): Promise<string | null>;
  hasPermission(resource: string, action: string): boolean;
  isAuthenticated(): boolean;
}

export interface TokenStorage {
  getAccessToken(): Promise<string | null>;
  getRefreshToken(): Promise<string | null>;
  setTokens(tokens: { accessToken: string; refreshToken: string }): Promise<void>;
  clearTokens(): Promise<void>;
  getTokens?(): Promise<{ accessToken: string; refreshToken: string } | null>;
}