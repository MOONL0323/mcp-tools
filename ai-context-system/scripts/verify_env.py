#!/usr/bin/env python3
"""
环境变量验证脚本
验证所有必需的环境变量是否正确配置
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    # 加载环境变量
    load_dotenv(project_root / '.env.secrets')
    load_dotenv(project_root / '.env.development')
    load_dotenv(project_root / '.env')
except ImportError:
    print("⚠️  警告: python-dotenv 未安装，只能检查系统环境变量")
    print("   安装方法: pip install python-dotenv")

# 颜色代码
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# 必需的环境变量
REQUIRED_VARS = {
    'LLM_API_KEY': '⚠️  Graph RAG 核心配置',
    'LLM_API_BASE': 'LLM API 基础URL',
    'DATABASE_URL': '数据库连接字符串',
    'JWT_SECRET_KEY': 'JWT 密钥',
}

# 可选但推荐的环境变量
RECOMMENDED_VARS = {
    'REDIS_URL': 'Redis 缓存（推荐启用）',
    'NEO4J_URI': 'Neo4j 图数据库',
    'CHROMA_HOST': 'ChromaDB 向量数据库',
    'SENTRY_DSN': '错误追踪（生产环境推荐）',
}

# 敏感变量的不安全默认值
UNSAFE_DEFAULTS = {
    'JWT_SECRET_KEY': ['dev-jwt-secret', 'change-this', 'your-super-secret'],
    'POSTGRES_PASSWORD': ['password', '123456', 'postgres', 'change_this'],
    'REDIS_PASSWORD': ['password', '123456', 'redis'],
    'NEO4J_PASSWORD': ['password', 'neo4j', 'change_this'],
    'LLM_API_KEY': ['sk-xxx', 'your-api-key', 'change-this'],
}

# 环境特定检查
PRODUCTION_REQUIREMENTS = {
    'DEBUG': 'false',
    'ENVIRONMENT': 'production',
    'SECURE_COOKIES': 'true',
    'HTTPS_ONLY': 'true',
    'ENABLE_SWAGGER': 'false',
}


def check_required_vars() -> Tuple[List[str], List[str]]:
    """检查必需的环境变量"""
    missing = []
    present = []
    
    print(f"\n{Colors.BOLD}📋 检查必需的环境变量{Colors.ENDC}")
    print("-" * 60)
    
    for var, description in REQUIRED_VARS.items():
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"{Colors.RED}❌ {var:20s} - 缺失{Colors.ENDC}")
            print(f"   {description}")
        else:
            present.append(var)
            masked_value = mask_sensitive_value(var, value)
            print(f"{Colors.GREEN}✓ {var:20s} - {masked_value}{Colors.ENDC}")
    
    return missing, present


def check_recommended_vars() -> List[str]:
    """检查推荐的环境变量"""
    missing = []
    
    print(f"\n{Colors.BOLD}💡 检查推荐的环境变量{Colors.ENDC}")
    print("-" * 60)
    
    for var, description in RECOMMENDED_VARS.items():
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"{Colors.YELLOW}⚠️  {var:20s} - 未配置{Colors.ENDC}")
            print(f"   {description}")
        else:
            masked_value = mask_sensitive_value(var, value)
            print(f"{Colors.GREEN}✓ {var:20s} - {masked_value}{Colors.ENDC}")
    
    return missing


def check_unsafe_defaults() -> List[Tuple[str, str]]:
    """检查是否使用了不安全的默认值"""
    warnings = []
    
    print(f"\n{Colors.BOLD}🔒 检查安全配置{Colors.ENDC}")
    print("-" * 60)
    
    for var, unsafe_values in UNSAFE_DEFAULTS.items():
        value = os.getenv(var, '').lower()
        if value and any(unsafe in value for unsafe in unsafe_values):
            warnings.append((var, '使用了不安全的默认值'))
            print(f"{Colors.RED}❌ {var:20s} - 不安全的默认值{Colors.ENDC}")
        elif value:
            print(f"{Colors.GREEN}✓ {var:20s} - 安全{Colors.ENDC}")
    
    return warnings


def check_production_readiness() -> List[str]:
    """检查生产环境就绪状态"""
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment != 'production':
        return []
    
    print(f"\n{Colors.BOLD}🏭 生产环境检查{Colors.ENDC}")
    print("-" * 60)
    
    issues = []
    
    for var, expected_value in PRODUCTION_REQUIREMENTS.items():
        actual_value = os.getenv(var, '').lower()
        if actual_value != expected_value.lower():
            issues.append(f"{var} 应设置为 {expected_value}，当前为 {actual_value or '未设置'}")
            print(f"{Colors.RED}❌ {var:20s} - 应为 {expected_value}{Colors.ENDC}")
        else:
            print(f"{Colors.GREEN}✓ {var:20s} - {expected_value}{Colors.ENDC}")
    
    return issues


def check_file_exists() -> Dict[str, bool]:
    """检查配置文件是否存在"""
    print(f"\n{Colors.BOLD}📁 检查配置文件{Colors.ENDC}")
    print("-" * 60)
    
    files_to_check = {
        '.env': '主配置文件',
        '.env.secrets': '敏感信息配置',
        '.env.development': '开发环境配置',
        '.env.production': '生产环境配置',
    }
    
    results = {}
    
    for filename, description in files_to_check.items():
        filepath = project_root / filename
        exists = filepath.exists()
        results[filename] = exists
        
        if exists:
            print(f"{Colors.GREEN}✓ {filename:20s} - 存在{Colors.ENDC}")
        else:
            status = Colors.YELLOW if filename in ['.env', '.env.secrets'] else Colors.BLUE
            symbol = "⚠️ " if filename in ['.env', '.env.secrets'] else "ℹ️ "
            print(f"{status}{symbol} {filename:20s} - 不存在{Colors.ENDC}")
            print(f"   {description}")
    
    return results


def mask_sensitive_value(var_name: str, value: str) -> str:
    """遮盖敏感信息"""
    sensitive_keywords = ['key', 'secret', 'password', 'token']
    
    if any(keyword in var_name.lower() for keyword in sensitive_keywords):
        if len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        else:
            return "***"
    
    # URL 类型显示完整
    if 'url' in var_name.lower() or 'uri' in var_name.lower():
        return value
    
    return value if len(value) < 50 else f"{value[:47]}..."


def print_summary(missing_required: List[str], 
                 missing_recommended: List[str],
                 security_warnings: List[Tuple[str, str]],
                 production_issues: List[str]) -> bool:
    """打印总结"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}📊 验证总结{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")
    
    all_ok = True
    
    # 必需变量
    if missing_required:
        all_ok = False
        print(f"{Colors.RED}{Colors.BOLD}❌ 缺少 {len(missing_required)} 个必需的环境变量:{Colors.ENDC}")
        for var in missing_required:
            print(f"   - {var}")
        print()
    else:
        print(f"{Colors.GREEN}✅ 所有必需的环境变量已配置{Colors.ENDC}\n")
    
    # 推荐变量
    if missing_recommended:
        print(f"{Colors.YELLOW}⚠️  缺少 {len(missing_recommended)} 个推荐的环境变量{Colors.ENDC}")
        for var in missing_recommended:
            print(f"   - {var}")
        print()
    
    # 安全警告
    if security_warnings:
        all_ok = False
        print(f"{Colors.RED}{Colors.BOLD}🔒 发现 {len(security_warnings)} 个安全问题:{Colors.ENDC}")
        for var, issue in security_warnings:
            print(f"   - {var}: {issue}")
        print()
    else:
        print(f"{Colors.GREEN}✅ 安全配置正确{Colors.ENDC}\n")
    
    # 生产环境问题
    if production_issues:
        all_ok = False
        print(f"{Colors.RED}{Colors.BOLD}🏭 生产环境配置问题:{Colors.ENDC}")
        for issue in production_issues:
            print(f"   - {issue}")
        print()
    
    return all_ok


def print_next_steps(missing_required: List[str], file_status: Dict[str, bool]):
    """打印后续步骤"""
    print(f"\n{Colors.BOLD}📝 后续步骤{Colors.ENDC}")
    print("-" * 60)
    
    if not file_status.get('.env.secrets'):
        print(f"{Colors.YELLOW}1. 创建敏感信息配置:{Colors.ENDC}")
        print(f"   cp .env.secrets.template .env.secrets")
        print(f"   nano .env.secrets")
        print()
    
    if not file_status.get('.env'):
        print(f"{Colors.YELLOW}2. 创建主配置文件:{Colors.ENDC}")
        print(f"   cp .env.development .env")
        print()
    
    if missing_required:
        print(f"{Colors.YELLOW}3. 配置缺失的环境变量:{Colors.ENDC}")
        for var in missing_required:
            print(f"   export {var}=<your-value>")
        print()
    
    print(f"{Colors.BLUE}4. 查看完整文档:{Colors.ENDC}")
    print(f"   docs/ENV_MANAGEMENT.md")
    print()


def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  AI Context System - 环境变量验证工具")
    print("=" * 60)
    print(f"{Colors.ENDC}\n")
    
    # 检查配置文件
    file_status = check_file_exists()
    
    # 检查必需变量
    missing_required, present_required = check_required_vars()
    
    # 检查推荐变量
    missing_recommended = check_recommended_vars()
    
    # 检查安全配置
    security_warnings = check_unsafe_defaults()
    
    # 检查生产环境就绪
    production_issues = check_production_readiness()
    
    # 打印总结
    all_ok = print_summary(missing_required, missing_recommended, 
                          security_warnings, production_issues)
    
    # 打印后续步骤
    if not all_ok or missing_recommended:
        print_next_steps(missing_required, file_status)
    
    # 返回状态码
    if all_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ 环境变量验证通过！{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ 环境变量验证失败，请修复上述问题{Colors.ENDC}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
