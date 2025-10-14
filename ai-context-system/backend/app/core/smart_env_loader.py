"""
智能环境配置加载器
根据 .env 中的设置自动加载对应的配置文件
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SmartEnvLoader:
    """智能环境配置加载器"""
    
    def __init__(self, project_root: Path = None):
        """初始化加载器"""
        if project_root is None:
            # 查找项目根目录
            current = Path(__file__).resolve().parent
            while current.parent != current:
                if (current / '.env').exists():
                    project_root = current
                    break
                current = current.parent
            else:
                project_root = Path.cwd()
        
        self.project_root = project_root
        self.env_vars: Dict[str, str] = {}
        
    def load(self) -> Dict[str, str]:
        """
        智能加载环境变量
        
        加载顺序：
        1. 读取主配置 .env
        2. 根据 ENVIRONMENT 加载对应配置（development/production）
        3. 根据 NETWORK_ENV 加载对应配置（intranet/internet）
        4. 加载敏感信息 .env.secrets
        
        Returns:
            环境变量字典
        """
        print("\n" + "=" * 70)
        print("  AI Context System - 智能配置加载器")
        print("=" * 70 + "\n")
        
        # 步骤 1：加载主配置
        self._load_main_config()
        
        # 步骤 2：加载环境配置
        self._load_environment_config()
        
        # 步骤 3：加载网络配置
        self._load_network_config()
        
        # 步骤 4：加载敏感信息
        self._load_secrets()
        
        # 步骤 5：设置衍生配置
        self._set_derived_config()
        
        # 步骤 6：应用到环境变量
        self._apply_to_env()
        
        # 步骤 7：打印配置摘要
        self._print_summary()
        
        return self.env_vars
    
    def _load_main_config(self):
        """加载主配置文件 .env"""
        main_config = self.project_root / '.env'
        
        if not main_config.exists():
            print(f"[错误] 找不到主配置文件 .env")
            print(f"   路径：{main_config}")
            raise FileNotFoundError("缺少 .env 文件")
        
        print(f"[步骤 1/7] 加载主配置")
        print(f"   文件：.env")
        
        vars_loaded = self._parse_env_file(main_config)
        self.env_vars.update(vars_loaded)
        
        # 检查必需配置
        required = ['ENVIRONMENT', 'NETWORK_ENV']
        missing = [k for k in required if k not in self.env_vars]
        if missing:
            print(f"   [错误] 缺少必需配置：{', '.join(missing)}")
            raise ValueError(f"缺少配置：{', '.join(missing)}")
        
        print(f"   > 环境：{self.env_vars['ENVIRONMENT']}")
        print(f"   > 网络：{self.env_vars['NETWORK_ENV']}")
        print()
    
    def _load_environment_config(self):
        """根据 ENVIRONMENT 加载对应配置"""
        environment = self.env_vars.get('ENVIRONMENT', 'development')
        config_file = self.project_root / 'config' / f'config.{environment}.env'
        
        print(f"[步骤 2/7] 加载环境配置")
        print(f"   文件：config/config.{environment}.env")
        
        if not config_file.exists():
            print(f"   [警告] 配置文件不存在，跳过")
            print()
            return
        
        vars_loaded = self._parse_env_file(config_file)
        self.env_vars.update(vars_loaded)
        
        print(f"   > 已加载 {len(vars_loaded)} 个配置项")
        print()
    
    def _load_network_config(self):
        """根据 NETWORK_ENV 加载对应配置"""
        network_env = self.env_vars.get('NETWORK_ENV', 'intranet')
        config_file = self.project_root / 'config' / f'config.{network_env}.env'
        
        print(f"[步骤 3/7] 加载网络配置")
        print(f"   文件：config/config.{network_env}.env")
        
        if not config_file.exists():
            print(f"   [警告] 配置文件不存在，跳过")
            print()
            return
        
        vars_loaded = self._parse_env_file(config_file)
        self.env_vars.update(vars_loaded)
        
        # 设置 Embedding Provider
        provider = self.env_vars.get('EMBEDDING_PROVIDER', 'unknown')
        print(f"   > Embedding Provider: {provider}")
        print()
    
    def _load_secrets(self):
        """加载敏感信息"""
        secrets_file = self.project_root / '.env.secrets'
        
        print(f"[步骤 4/7] 加载敏感信息")
        print(f"   文件：.env.secrets")
        
        if not secrets_file.exists():
            print(f"   [警告] 敏感信息文件不存在")
            print(f"   [警告] 某些功能可能无法使用（如 LLM API）")
            print()
            return
        
        vars_loaded = self._parse_env_file(secrets_file)
        self.env_vars.update(vars_loaded)
        
        # 检查关键密钥
        has_llm_key = bool(self.env_vars.get('LLM_API_KEY'))
        print(f"   > LLM API Key: {'已配置' if has_llm_key else '未配置'}")
        print()
    
    def _set_derived_config(self):
        """设置衍生配置"""
        print(f"[步骤 5/7] 设置衍生配置")
        
        # 根据环境设置部署模式
        environment = self.env_vars.get('ENVIRONMENT')
        if environment == 'production':
            self.env_vars.setdefault('DEPLOY_MODE', 'k8s')
            print(f"   > 部署模式：K8s（自动）")
        else:
            self.env_vars.setdefault('DEPLOY_MODE', 'local')
            print(f"   > 部署模式：本地（自动）")
        
        # 设置日志级别
        if 'LOG_LEVEL' not in self.env_vars:
            self.env_vars['LOG_LEVEL'] = 'DEBUG' if environment == 'development' else 'INFO'
            print(f"   > 日志级别：{self.env_vars['LOG_LEVEL']}（自动）")
        
        print()
    
    def _parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """
        解析 .env 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            环境变量字典
        """
        env_vars = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析 KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 去除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # 变量扩展（支持 ${VAR} 语法）
                    value = self._expand_variables(value)
                    
                    env_vars[key] = value
        
        return env_vars
    
    def _expand_variables(self, value: str) -> str:
        """
        扩展变量引用
        
        Args:
            value: 原始值
            
        Returns:
            扩展后的值
        """
        import re
        
        # 匹配 ${VAR} 或 $VAR 格式
        pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        
        def replace(match):
            var_name = match.group(1) or match.group(2)
            return self.env_vars.get(var_name, os.environ.get(var_name, ''))
        
        return re.sub(pattern, replace, value)
    
    def _apply_to_env(self):
        """将配置应用到环境变量"""
        print(f"[步骤 6/7] 应用配置到环境变量")
        print(f"   > 已设置 {len(self.env_vars)} 个环境变量")
        
        for key, value in self.env_vars.items():
            os.environ[key] = value
        
        print()
    
    def _print_summary(self):
        """打印配置摘要"""
        print(f"[步骤 7/7] 配置摘要")
        print()
        print("   核心配置：")
        print(f"     - 环境：{self.env_vars.get('ENVIRONMENT')}")
        print(f"     - 网络：{self.env_vars.get('NETWORK_ENV')}")
        print(f"     - 部署：{self.env_vars.get('DEPLOY_MODE')}")
        print()
        
        print("   服务端口：")
        print(f"     - Backend：{self.env_vars.get('BACKEND_PORT', '8000')}")
        print(f"     - Frontend：{self.env_vars.get('FRONTEND_PORT', '3000')}")
        print(f"     - MCP：{self.env_vars.get('MCP_PORT', '3001')}")
        print()
        
        print("   数据库配置：")
        db_type = self.env_vars.get('DATABASE_TYPE', 'unknown')
        print(f"     - 类型：{db_type}")
        if db_type == 'postgresql':
            print(f"     - Host：{self.env_vars.get('POSTGRES_HOST')}")
            print(f"     - Port：{self.env_vars.get('POSTGRES_PORT')}")
        elif db_type == 'sqlite':
            print(f"     - 文件：{self.env_vars.get('SQLITE_DB_PATH')}")
        print()
        
        print("   Embedding 配置：")
        provider = self.env_vars.get('EMBEDDING_PROVIDER')
        print(f"     - Provider：{provider}")
        if provider == 'api':
            print(f"     - API：{self.env_vars.get('EMBEDDING_API_BASE')}")
            print(f"     - Model：{self.env_vars.get('EMBEDDING_MODEL')}")
        elif provider == 'local':
            print(f"     - Model：{self.env_vars.get('EMBEDDING_MODEL_NAME')}")
            print(f"     - Device：{self.env_vars.get('EMBEDDING_DEVICE')}")
        print()
        
        print("=" * 70)
        print("  配置加载完成")
        print("=" * 70)
        print()


def load_smart_env() -> Dict[str, str]:
    """
    加载智能环境配置的便捷函数
    
    Returns:
        环境变量字典
    """
    loader = SmartEnvLoader()
    return loader.load()


if __name__ == '__main__':
    # 测试配置加载
    try:
        env_vars = load_smart_env()
        print(f"成功加载 {len(env_vars)} 个配置项")
    except Exception as e:
        print(f"配置加载失败：{e}")
        sys.exit(1)
