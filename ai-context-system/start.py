#!/usr/bin/env python3
"""
智能启动脚本
根据配置自动启动所有必需的服务
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.core.smart_env_loader import load_smart_env


def print_banner():
    """打印启动横幅"""
    print("\n" + "=" * 70)
    print("  AI Context System - 智能启动器")
    print("=" * 70 + "\n")


def check_dependencies(env_vars):
    """检查并启动必需的依赖服务"""
    environment = env_vars.get('ENVIRONMENT')
    
    print("[检查依赖服务]\n")
    
    dependencies = []
    
    # Neo4j
    if env_vars.get('NEO4J_ENABLED') == 'true':
        dependencies.append({
            'name': 'Neo4j',
            'check': check_neo4j,
            'start': start_neo4j if environment == 'development' else None
        })
    
    # Redis (生产环境或明确启用时)
    if env_vars.get('REDIS_ENABLED') == 'true':
        dependencies.append({
            'name': 'Redis',
            'check': check_redis,
            'start': start_redis if environment == 'development' else None
        })
    
    # ChromaDB
    if env_vars.get('CHROMA_ENABLED') == 'true':
        dependencies.append({
            'name': 'ChromaDB',
            'check': check_chroma,
            'start': start_chroma if environment == 'development' else None
        })
    
    # 检查并启动依赖
    for dep in dependencies:
        print(f"   检查 {dep['name']}...", end=' ')
        
        if dep['check']():
            print("[运行中]")
        elif dep['start']:
            print("[未运行] 尝试启动...")
            if dep['start']():
                print(f"      > {dep['name']} 已启动")
            else:
                print(f"      > {dep['name']} 启动失败，某些功能可能不可用")
        else:
            print("[未运行] 需要手动启动")
    
    print()


def check_neo4j():
    """检查 Neo4j 是否运行"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 7687))
        s.close()
        return result == 0
    except:
        return False


def start_neo4j():
    """启动 Neo4j（测试环境）"""
    return False


def check_redis():
    """检查 Redis 是否运行"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 6379))
        s.close()
        return result == 0
    except:
        return False


def start_redis():
    """启动 Redis（测试环境）"""
    return False


def check_chroma():
    """检查 ChromaDB 是否运行"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('localhost', 8001))
        s.close()
        return result == 0
    except:
        return False


def start_chroma():
    """启动 ChromaDB（测试环境）"""
    return False


def install_dependencies(env_vars):
    """安装 Python 依赖"""
    network_env = env_vars.get('NETWORK_ENV')
    
    print("[检查 Python 依赖]\n")
    
    # 基础依赖
    requirements_file = project_root / 'backend' / 'requirements.txt'
    
    if requirements_file.exists():
        print(f"   安装基础依赖...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', '-r', str(requirements_file)],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"   > 基础依赖已安装")
        else:
            print(f"   > 基础依赖安装失败")
    
    # 外网环境需要本地 Embedding 模型依赖
    if network_env == 'internet':
        print(f"   检查 Embedding 模型依赖...")
        try:
            import sentence_transformers
            print(f"   > Embedding 依赖已安装")
        except:
            print(f"   > Embedding 依赖检查跳过（开发模式可选）")
    
    print()


def start_backend(env_vars):
    """启动 Backend 服务"""
    print("[启动 Backend 服务]\n")
    
    backend_dir = project_root / 'backend'
    port = env_vars.get('BACKEND_PORT', '8000')
    
    os.chdir(backend_dir)
    
    # 启动 FastAPI
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', port
    ]
    
    # 开发环境启用热重载
    if env_vars.get('RELOAD') == 'true':
        cmd.append('--reload')
    
    print(f"   命令：{' '.join(cmd)}")
    print(f"   访问：http://localhost:{port}")
    print(f"   文档：http://localhost:{port}/docs")
    print()
    
    subprocess.Popen(cmd)


def start_frontend(env_vars):
    """启动 Frontend 服务"""
    print("[启动 Frontend 服务]\n")
    
    frontend_dir = project_root / 'frontend'
    port = env_vars.get('FRONTEND_PORT', '3000')
    
    os.chdir(frontend_dir)
    
    # 启动 React (Windows 使用 npm.cmd)
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    cmd = [npm_cmd, 'start']
    
    print(f"   命令：{' '.join(cmd)}")
    print(f"   访问：http://localhost:{port}")
    print()
    
    # 设置环境变量
    env = os.environ.copy()
    env['PORT'] = port
    
    subprocess.Popen(cmd, env=env)


def start_mcp(env_vars):
    """启动 MCP Server"""
    print("[启动 MCP Server]\n")
    
    mcp_dir = project_root / 'mcp-server'
    port = env_vars.get('MCP_PORT', '3001')
    
    os.chdir(mcp_dir)
    
    # 启动 MCP Server (Windows 使用 npm.cmd)
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    cmd = [npm_cmd, 'run', 'dev' if env_vars.get('RELOAD') == 'true' else 'start']
    
    print(f"   命令：{' '.join(cmd)}")
    print(f"   访问：http://localhost:{port}")
    print()
    
    subprocess.Popen(cmd)


def deploy_k8s(env_vars):
    """使用 K8s 部署（生产环境）"""
    print("[K8s 部署]\n")
    
    k8s_dir = project_root / 'k8s'
    
    if not k8s_dir.exists():
        print("   [错误] 找不到 k8s/ 目录")
        return
    
    # 应用 K8s 配置
    configs = [
        'namespace.yaml',
        'configmap.yaml',
        'secrets.yaml',
        'postgres.yaml',
        'redis.yaml',
        'neo4j.yaml',
        'chroma.yaml',
        'backend.yaml',
        'frontend.yaml',
        'mcp-server.yaml',
        'ingress.yaml'
    ]
    
    for config in configs:
        config_file = k8s_dir / config
        if config_file.exists():
            print(f"   应用配置：{config}")
            subprocess.run(['kubectl', 'apply', '-f', str(config_file)])
    
    print()
    print("   > K8s 部署完成")
    print("   查看状态：kubectl get pods -n ai-context-system")
    print()


def main():
    """主函数"""
    print_banner()
    
    # 加载环境配置
    try:
        env_vars = load_smart_env()
    except Exception as e:
        print(f"[错误] 配置加载失败：{e}")
        sys.exit(1)
    
    environment = env_vars.get('ENVIRONMENT')
    
    # 测试环境：本地启动
    if environment == 'development':
        # 检查依赖服务
        check_dependencies(env_vars)
        
        # 安装 Python 依赖
        install_dependencies(env_vars)
        
        # 启动服务
        print("[启动服务]\n")
        print("=" * 70)
        print()
        
        start_backend(env_vars)
        time.sleep(2)
        
        start_frontend(env_vars)
        time.sleep(2)
        
        start_mcp(env_vars)
        
        print()
        print("=" * 70)
        print("  所有服务已启动")
        print("=" * 70)
        print()
        print("  访问地址：")
        print(f"     Frontend: http://localhost:{env_vars.get('FRONTEND_PORT')}")
        print(f"     Backend:  http://localhost:{env_vars.get('BACKEND_PORT')}")
        print(f"     MCP:      http://localhost:{env_vars.get('MCP_PORT')}")
        print(f"     API 文档: http://localhost:{env_vars.get('BACKEND_PORT')}/docs")
        print()
        print("  按 Ctrl+C 停止所有服务")
        print()
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n  正在停止服务...")
            print()
    
    # 生产环境：K8s 部署
    elif environment == 'production':
        deploy_k8s(env_vars)
    
    else:
        print(f"[错误] 未知的环境：{environment}")
        sys.exit(1)


if __name__ == '__main__':
    main()
