/**
 * 依赖注入容器 - IoC Container
 */

export class DIContainer {
  private static instance: DIContainer;
  private services: Map<string, any> = new Map();
  private factories: Map<string, () => any> = new Map();
  private singletons: Map<string, any> = new Map();

  static getInstance(): DIContainer {
    if (!DIContainer.instance) {
      DIContainer.instance = new DIContainer();
    }
    return DIContainer.instance;
  }

  // 注册单例服务
  registerSingleton<T>(token: string, factory: () => T): void {
    this.factories.set(token, factory);
  }

  // 注册瞬态服务
  registerTransient<T>(token: string, factory: () => T): void {
    this.services.set(token, factory);
  }

  // 解析服务
  resolve<T>(token: string): T {
    // 先检查单例缓存
    if (this.singletons.has(token)) {
      return this.singletons.get(token);
    }

    // 检查单例工厂
    if (this.factories.has(token)) {
      const factory = this.factories.get(token);
      if (factory) {
        const instance = factory();
        this.singletons.set(token, instance);
        return instance;
      }
    }

    // 检查瞬态服务
    if (this.services.has(token)) {
      return this.services.get(token)();
    }

    throw new Error(`Service ${token} not registered`);
  }

  // 清除容器
  clear(): void {
    this.services.clear();
    this.factories.clear();
    this.singletons.clear();
  }
}