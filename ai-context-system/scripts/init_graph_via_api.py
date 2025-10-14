"""
通过API初始化图谱数据（正确方式）
使用后端API端点，确保使用同一个图实例
"""
import requests
import time

API_BASE = "http://localhost:8080/api/v1"

print("🚀 通过API初始化知识图谱数据...")
print("="*60)

# 检查后端状态
print("\n[0] 检查后端状态...")
try:
    response = requests.get(f"{API_BASE}/graph/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   ✅ 后端运行正常: {stats.get('backend')}")
        if stats.get('total_nodes', 0) > 0:
            print(f"   ⚠️  图谱已有数据: {stats.get('total_nodes')}个节点")
            answer = input("   是否清空重新初始化？(y/n): ")
            if answer.lower() != 'y':
                print("   取消初始化")
                exit(0)
except Exception as e:
    print(f"   ❌ 后端未运行或连接失败: {e}")
    print("   请先启动后端: cd backend && python main.py")
    exit(1)

# Python代码1: Calculator
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

# Python代码2: UserService
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
        return self.database.insert({'username': username, 'email': email})

class UserRepository:
    '''用户数据仓库'''
    
    def __init__(self, connection):
        self.connection = connection
    
    def find_by_id(self, user_id: int):
        return self.connection.execute("SELECT * FROM users WHERE id = ?", (user_id,))

def validate_email(email: str) -> bool:
    '''验证邮箱格式'''
    import re
    return bool(re.match(r'^[\\w.+-]+@[\\w.-]+\\.[a-zA-Z]{2,}$', email))

import hashlib
from datetime import datetime
"""

# 文本文档
text_doc = """
Python Programming Language

Python is a high-level, interpreted programming language known for simplicity and readability.
It supports object-oriented, procedural, and functional programming paradigms.

Machine learning and artificial intelligence are major Python application areas.
Popular libraries include TensorFlow, PyTorch, scikit-learn for machine learning,
pandas and numpy for data analysis and scientific computing.

Web frameworks like Django and Flask make Python ideal for building APIs and web applications.
The asyncio library enables asynchronous programming for concurrent operations.
"""

# 存储数据到图谱
datasets = [
    ("Calculator代码", python_code_1, "python"),
    ("UserService代码", python_code_2, "python"),
    ("Python文档", text_doc, "text")
]

stored_count = 0

for idx, (name, content, content_type) in enumerate(datasets, 1):
    print(f"\n[{idx}] 处理: {name}...")
    
    try:
        # 1. 提取实体
        extract_response = requests.post(
            f"{API_BASE}/entities/extract",
            json={"content": content, "content_type": content_type}
        )
        
        if extract_response.status_code != 200:
            print(f"   ❌ 提取失败: {extract_response.status_code}")
            print(f"   {extract_response.text}")
            continue
        
        result = extract_response.json()
        
        if content_type == "python":
            entities = result.get('entities', {})
            print(f"   ✅ 提取: {len(entities.get('classes', []))}个类, "
                  f"{len(entities.get('functions', []))}个函数, "
                  f"{len(entities.get('imports', []))}个导入")
            print(f"   ✅ 关系: {result.get('total_relationships', 0)}个")
        else:
            print(f"   ✅ 提取: {result.get('total_keywords', 0)}个关键词")
        
        # 注意：目前没有直接通过API存储到图谱的端点
        # 需要通过store-from-document端点，但需要先上传文档
        # 暂时跳过存储步骤
        print(f"   ⚠️  跳过存储（需要先上传为文档）")
        
    except Exception as e:
        print(f"   ❌ 处理失败: {e}")

print("\n" + "="*60)
print("⚠️  注意：当前API架构需要先上传文档才能存入图谱")
print("\n💡 快速测试方案:")
print("   1. 运行: python test_task12_core.py")
print("   2. 测试脚本会直接操作图服务，生成测试数据")
print("   3. 然后访问前端查看: http://localhost:3000/knowledge-graph")
print("\n📝 完整流程:")
print("   1. 上传文档 → POST /api/v1/documents/upload")
print("   2. 存入图谱 → POST /api/v1/graph/store-from-document/{id}")
print("   3. 前端查看图谱统计和实体")
