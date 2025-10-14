"""
快速初始化知识图谱数据
运行此脚本后，刷新前端即可看到图谱数据
"""
import requests
import json

API_BASE = "http://localhost:8080/api/v1"

print("🚀 初始化知识图谱数据...")
print("="*60)

# 测试数据1: Python Calculator类
python_code_1 = """
class Calculator:
    '''基础计算器类'''
    
    def __init__(self, name: str = "Calculator"):
        self.name = name
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        '''加法运算'''
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: int, b: int) -> int:
        '''减法运算'''
        return a - b
    
    def multiply(self, a: int, b: int) -> int:
        '''乘法运算'''
        return a * b

class ScientificCalculator(Calculator):
    '''科学计算器，继承自Calculator'''
    
    def power(self, base: float, exp: float) -> float:
        '''幂运算'''
        return base ** exp
    
    def sqrt(self, x: float) -> float:
        '''平方根'''
        import math
        return math.sqrt(x)

def format_result(value: float, precision: int = 2) -> str:
    '''格式化计算结果'''
    return f"{value:.{precision}f}"

import math
from typing import List, Dict, Optional
"""

# 测试数据2: Python User服务
python_code_2 = """
class UserService:
    '''用户服务类'''
    
    def __init__(self, database):
        self.database = database
        self.cache = {}
    
    def get_user(self, user_id: int) -> dict:
        '''获取用户信息'''
        if user_id in self.cache:
            return self.cache[user_id]
        user = self.database.fetch(user_id)
        self.cache[user_id] = user
        return user
    
    def create_user(self, username: str, email: str) -> int:
        '''创建新用户'''
        user_id = self.database.insert({
            'username': username,
            'email': email
        })
        return user_id

class UserRepository:
    '''用户数据仓库'''
    
    def __init__(self, connection):
        self.connection = connection
    
    def find_by_id(self, user_id: int):
        '''根据ID查找用户'''
        return self.connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )

def validate_email(email: str) -> bool:
    '''验证邮箱格式'''
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

import hashlib
from datetime import datetime
"""

# 测试数据3: 文本文档
text_doc = """
Python Programming Language Guide

Python is a high-level, interpreted programming language known for its simplicity and readability.
It supports multiple programming paradigms including object-oriented, procedural, and functional programming.

Machine learning and artificial intelligence are major application areas for Python.
Popular libraries include TensorFlow, PyTorch, scikit-learn for machine learning,
and pandas, numpy for data analysis and scientific computing.

Web development frameworks like Django and Flask make Python ideal for building APIs and web applications.
The asyncio library enables asynchronous programming for handling concurrent operations efficiently.
"""

def init_graph_data():
    """初始化图谱数据"""
    
    # 1. 添加Calculator代码
    print("\n[1] 添加Calculator代码到图谱...")
    try:
        response = requests.post(
            f"{API_BASE}/entities/extract",
            json={"content": python_code_1, "content_type": "python"}
        )
        if response.status_code == 200:
            result = response.json()
            entities = result.get('entities', {})
            print(f"   ✅ 提取: {len(entities.get('classes', []))}个类, "
                  f"{len(entities.get('functions', []))}个函数")
            
            # 存入图谱
            from app.services.graph_service import get_graph_service
            graph = get_graph_service()
            graph.store_python_entities(
                1001, 
                entities, 
                result.get('relationships', [])
            )
            print(f"   ✅ 已存入图谱")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 2. 添加UserService代码
    print("\n[2] 添加UserService代码到图谱...")
    try:
        response = requests.post(
            f"{API_BASE}/entities/extract",
            json={"content": python_code_2, "content_type": "python"}
        )
        if response.status_code == 200:
            result = response.json()
            entities = result.get('entities', {})
            print(f"   ✅ 提取: {len(entities.get('classes', []))}个类, "
                  f"{len(entities.get('functions', []))}个函数")
            
            from app.services.graph_service import get_graph_service
            graph = get_graph_service()
            graph.store_python_entities(
                1002, 
                entities, 
                result.get('relationships', [])
            )
            print(f"   ✅ 已存入图谱")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 3. 添加文本文档关键词
    print("\n[3] 添加文本文档关键词到图谱...")
    try:
        response = requests.post(
            f"{API_BASE}/entities/extract",
            json={"content": text_doc, "content_type": "text"}
        )
        if response.status_code == 200:
            result = response.json()
            keywords = result.get('keywords', [])
            print(f"   ✅ 提取: {len(keywords)}个关键词")
            
            from app.services.graph_service import get_graph_service
            graph = get_graph_service()
            graph.store_keywords(1003, keywords)
            print(f"   ✅ 已存入图谱")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 4. 显示最终统计
    print("\n[4] 图谱最终统计...")
    try:
        response = requests.get(f"{API_BASE}/graph/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ 后端: {stats.get('backend')}")
            print(f"   ✅ 总节点: {stats.get('total_nodes')}")
            print(f"   ✅ 总关系: {stats.get('total_relationships')}")
            print(f"   ✅ 节点分布: {stats.get('nodes')}")
            print(f"   ✅ 关系分布: {stats.get('relationships')}")
    except Exception as e:
        print(f"   ❌ 获取统计失败: {e}")
    
    print("\n" + "="*60)
    print("✅ 初始化完成！")
    print("\n💡 现在可以:")
    print("   1. 刷新前端页面 http://localhost:3000/knowledge-graph")
    print("   2. 查看图谱统计（应该显示40+节点）")
    print("   3. 搜索实体：Calculator, ScientificCalculator, UserService")
    print("   4. 探索关系：点击相关实体继续浏览")

if __name__ == "__main__":
    import sys
    sys.path.append("backend")
    init_graph_data()
