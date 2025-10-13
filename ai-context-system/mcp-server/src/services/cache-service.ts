/**
 * 缓存服务
 */

import NodeCache from 'node-cache';
import { config } from '../config/config.js';

export class CacheService {
  private cache: NodeCache;

  constructor() {
    this.cache = new NodeCache({
      stdTTL: config.cacheTtl, // 默认TTL
      maxKeys: config.cacheMaxKeys, // 最大key数量
      checkperiod: 60, // 每60秒清理过期key
      useClones: false // 性能优化：不克隆对象
    });

    // 监听缓存事件
    this.cache.on('set', (key: string, value: any) => {
      console.log(`缓存设置: ${key}`);
    });

    this.cache.on('del', (key: string, value: any) => {
      console.log(`缓存删除: ${key}`);
    });

    this.cache.on('expired', (key: string, value: any) => {
      console.log(`缓存过期: ${key}`);
    });
  }

  /**
   * 获取缓存值
   */
  get<T = any>(key: string): T | undefined {
    return this.cache.get<T>(key);
  }

  /**
   * 设置缓存值
   */
  set<T = any>(key: string, value: T, ttl?: number): boolean {
    return this.cache.set(key, value, ttl || config.cacheTtl);
  }

  /**
   * 删除缓存
   */
  del(key: string | string[]): number {
    return this.cache.del(key);
  }

  /**
   * 检查key是否存在
   */
  has(key: string): boolean {
    return this.cache.has(key);
  }

  /**
   * 获取所有keys
   */
  keys(): string[] {
    return this.cache.keys();
  }

  /**
   * 清空所有缓存
   */
  flushAll(): void {
    this.cache.flushAll();
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): NodeCache.Stats {
    return this.cache.getStats();
  }

  /**
   * 获取或设置缓存（如果不存在则执行函数并缓存结果）
   */
  async getOrSet<T = any>(
    key: string,
    fn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key);
    if (cached !== undefined) {
      return cached;
    }

    const result = await fn();
    this.set(key, result, ttl);
    return result;
  }

  /**
   * 批量获取
   */
  mget<T = any>(keys: string[]): { [key: string]: T } {
    return this.cache.mget(keys);
  }

  /**
   * 批量设置
   */
  mset<T = any>(keyValuePairs: Array<{ key: string; val: T; ttl?: number }>): boolean {
    return this.cache.mset(keyValuePairs);
  }

  /**
   * 生成缓存键
   */
  static generateKey(...parts: (string | number | boolean)[]): string {
    return parts
      .map(part => String(part).replace(/[^a-zA-Z0-9]/g, '_'))
      .join(':');
  }

  /**
   * 根据前缀删除缓存
   */
  deleteByPrefix(prefix: string): number {
    const keysToDelete = this.keys().filter(key => key.startsWith(prefix));
    return this.del(keysToDelete);
  }

  /**
   * 获取缓存使用情况
   */
  getUsage(): {
    keys: number;
    hits: number;
    misses: number;
    hitRate: number;
    memoryUsage: string;
  } {
    const stats = this.getStats();
    const hitRate = stats.hits + stats.misses > 0 
      ? (stats.hits / (stats.hits + stats.misses)) * 100 
      : 0;

    return {
      keys: stats.keys,
      hits: stats.hits,
      misses: stats.misses,
      hitRate: Math.round(hitRate * 100) / 100,
      memoryUsage: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`
    };
  }
}

// 单例模式的缓存实例
let cacheInstance: CacheService | null = null;

export function getCacheInstance(): CacheService {
  if (!cacheInstance) {
    cacheInstance = new CacheService();
  }
  return cacheInstance;
}