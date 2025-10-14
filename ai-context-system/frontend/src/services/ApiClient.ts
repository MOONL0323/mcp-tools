/**
 * HTTP客户端封装
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export class ApiClient {
  private client: AxiosInstance;

  constructor(config?: AxiosRequestConfig) {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api',
      timeout: 10000,
      withCredentials: false, // 修复CORS问题：当后端使用通配符时不能使用withCredentials
      headers: {
        'Content-Type': 'application/json',
      },
      ...config
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        // 只在非登录注册页面处理401跳转
        if (error.response?.status === 401 && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get(url, config);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post(url, data, config);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put(url, data, config);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.delete(url, config);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  async request<T = any>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.request(config);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  private handleResponse<T>(response: AxiosResponse): ApiResponse<T> {
    return {
      success: true,
      data: response.data,
      message: 'Success'
    };
  }

  private handleError(error: any): ApiResponse {
    if (error.response) {
      // 服务器响应了错误状态码
      const status = error.response.status;
      const errorData = error.response.data;
      
      let errorMessage = '请求失败';
      
      if (errorData?.detail) {
        errorMessage = errorData.detail;
      } else if (errorData?.message) {
        errorMessage = errorData.message;
      } else {
        switch (status) {
          case 400:
            errorMessage = '请求参数错误';
            break;
          case 401:
            errorMessage = '未授权，请先登录';
            break;
          case 403:
            errorMessage = '权限不足';
            break;
          case 404:
            errorMessage = '请求的资源不存在';
            break;
          case 500:
            errorMessage = '服务器内部错误';
            break;
          default:
            errorMessage = error.response.statusText || '请求失败';
        }
      }
      
      return {
        success: false,
        error: errorMessage,
        message: `请求失败 (${status})`
      };
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return {
        success: false,
        error: '网络连接错误，请检查网络设置',
        message: '网络请求失败'
      };
    } else {
      // 请求配置出错
      return {
        success: false,
        error: '请求配置错误',
        message: '客户端错误'
      };
    }
  }

  // 设置认证令牌
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // 清除认证令牌
  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }
}