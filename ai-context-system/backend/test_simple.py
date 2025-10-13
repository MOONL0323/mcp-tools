"""
AI Context System 基础功能测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # 测试基础导入
    from app.core.config import get_settings
    print("✅ 配置模块导入成功")
    
    # 测试配置
    settings = get_settings()
    print(f"✅ 配置加载成功: {settings.ENVIRONMENT}")
    print(f"   - 数据库: {settings.DATABASE_URL}")
    print(f"   - 端口: {settings.PORT}")
    print(f"   - 调试模式: {settings.DEBUG}")
    
    # 测试核心模块
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("测试日志功能")
    print("✅ 日志模块导入成功")
    
    # 测试数据模型
    from app.models.database import User, Document
    print("✅ 数据模型导入成功")
    
    # 测试Pydantic模式
    from app.schemas import UserCreate, DocumentUpload
    test_user = UserCreate(
        username="testuser",
        email="test@example.com", 
        password="password123",
        full_name="Test User"
    )
    print("✅ Pydantic模式验证成功")
    
    # 测试FastAPI
    from fastapi import FastAPI
    from app.api import api_router
    app = FastAPI()
    app.include_router(api_router, prefix="/api")
    print("✅ FastAPI和路由导入成功")
    
    print("\n🎉 所有基础组件测试通过！")
    print("\n📋 下一步:")
    print("1. 启动开发服务器: python -m app.main")
    print("2. 访问API文档: http://localhost:8000/docs") 
    print("3. 健康检查: http://localhost:8000/health")
    
    print("\n📁 项目结构:")
    print("backend/")
    print("├── app/                    # 应用主目录")
    print("│   ├── api/               # API路由")
    print("│   ├── core/              # 核心模块")
    print("│   ├── models/            # 数据模型")
    print("│   ├── schemas/           # Pydantic模式")
    print("│   ├── services/          # 业务逻辑")
    print("│   └── main.py            # 应用入口")
    print("├── requirements.txt       # 依赖包")
    print("├── .env                   # 环境配置")
    print("└── README.md              # 项目说明")
    
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("\n🔧 解决方案:")
    print("1. 确保已安装所有依赖: pip install -r requirements.txt")
    print("2. 检查Python路径设置")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    print("\n🔧 请检查配置和依赖")