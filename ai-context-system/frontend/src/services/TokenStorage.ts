/**
 * Token存储服务
 */

import { TokenStorage } from '../interfaces/IAuthService';

export class LocalTokenStorage implements TokenStorage {
  private readonly ACCESS_TOKEN_KEY = 'ai_context_access_token';
  private readonly REFRESH_TOKEN_KEY = 'ai_context_refresh_token';

  async getAccessToken(): Promise<string | null> {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  async getRefreshToken(): Promise<string | null> {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  async setTokens(tokens: { accessToken: string; refreshToken: string }): Promise<void> {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refreshToken);
  }

  async clearTokens(): Promise<void> {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  async getTokens(): Promise<{ accessToken: string; refreshToken: string } | null> {
    const accessToken = await this.getAccessToken();
    const refreshToken = await this.getRefreshToken();
    
    if (accessToken && refreshToken) {
      return { accessToken, refreshToken };
    }
    
    return null;
  }
}