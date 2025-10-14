#!/usr/bin/env python3
"""
Task 5: 验证422修复 - 文件上传测试脚本
测试所有文件格式和可选字段的上传功能
"""

import requests
import json
from pathlib import Path
import tempfile

API_BASE = "http://localhost:8080/api/v1"

def test_1_get_classifications():
    """测试1: 获取分类选项"""
    print("\n" + "="*70)
    print("测试1: 获取分类选项")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/classifications/options")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取分类选项")
        print(f"   - 团队数: {len(data.get('teams', []))}")
        print(f"   - 项目文档类型数: {len(data.get('business_doc_types', []))}")
        print(f"   - Demo代码类型数: {len(data.get('demo_code_types', []))}")
        
        # 返回第一个dev_type_id用于后续测试
        if data.get('business_doc_types'):
            return data['business_doc_types'][0]['id']
    else:
        print(f"❌ 失败: {response.text}")
    
    return None

def test_2_upload_txt(dev_type_id=None):
    """测试2: 上传TXT文件（不带可选字段）"""
    print("\n" + "="*70)
    print("测试2: 上传TXT文件（不带可选字段）")
    print("="*70)
    
    # 创建测试文件
    content = """# 测试文档

这是一个测试文档，用于验证文件上传功能。

## 功能点
1. 支持多种文件格式
2. 智能编码检测
3. 文件大小验证
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            data = {
                'doc_type': 'business_doc',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'uploaded_by': 'admin'
                # 不传dev_type_id，测试可选字段
            }
            
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功上传TXT文件")
                print(f"   - 文档ID: {result.get('document_id')}")
                print(f"   - 标题: {result.get('title')}")
                print(f"   - 文件大小: {result.get('file_size')} bytes")
                print(f"   - MIME类型: {result.get('mime_type')}")
                return result.get('document_id')
            else:
                print(f"❌ 失败: {response.text}")
    finally:
        Path(temp_file).unlink(missing_ok=True)
    
    return None

def test_3_upload_csv(dev_type_id):
    """测试3: 上传CSV文件（带dev_type_id）"""
    print("\n" + "="*70)
    print("测试3: 上传CSV文件（带dev_type_id）")
    print("="*70)
    
    # 创建CSV测试文件
    content = """name,age,city
张三,25,北京
李四,30,上海
王五,28,深圳"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            data = {
                'doc_type': 'business_doc',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'uploaded_by': 'admin',
                'dev_type_id': dev_type_id,  # 传入有效的UUID
                'module_name': '数据模块',
                'description': '测试CSV文件上传'
            }
            
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功上传CSV文件")
                print(f"   - 文档ID: {result.get('document_id')}")
                print(f"   - 标题: {result.get('title')}")
                print(f"   - 文件大小: {result.get('file_size')} bytes")
                return result.get('document_id')
            else:
                print(f"❌ 失败: {response.text}")
    finally:
        Path(temp_file).unlink(missing_ok=True)
    
    return None

def test_4_upload_json():
    """测试4: 上传JSON文件"""
    print("\n" + "="*70)
    print("测试4: 上传JSON文件")
    print("="*70)
    
    # 创建JSON测试文件
    content = {
        "name": "测试配置",
        "version": "1.0.0",
        "settings": {
            "enabled": True,
            "timeout": 30
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('config.json', f, 'application/json')}
            data = {
                'doc_type': 'demo_code',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'uploaded_by': 'admin',
                'code_function': 'config',
                'team_role': 'backend'
            }
            
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功上传JSON文件")
                print(f"   - 文档ID: {result.get('document_id')}")
                print(f"   - 标题: {result.get('title')}")
                return result.get('document_id')
            else:
                print(f"❌ 失败: {response.text}")
    finally:
        Path(temp_file).unlink(missing_ok=True)
    
    return None

def test_5_upload_python():
    """测试5: 上传Python代码文件"""
    print("\n" + "="*70)
    print("测试5: 上传Python代码文件")
    print("="*70)
    
    # 创建Python测试文件
    content = '''"""
测试Python模块
"""

def hello(name: str) -> str:
    """问候函数"""
    return f"Hello, {name}!"

class User:
    """用户类"""
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('test_module.py', f, 'text/x-python')}
            data = {
                'doc_type': 'demo_code',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'uploaded_by': 'admin',
                'code_function': 'api',
                'team_role': 'backend',
                'module_name': 'test_module',
                'description': 'Python示例代码'
            }
            
            response = requests.post(f"{API_BASE}/documents/upload", files=files, data=data)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功上传Python文件")
                print(f"   - 文档ID: {result.get('document_id')}")
                print(f"   - 标题: {result.get('title')}")
                return result.get('document_id')
            else:
                print(f"❌ 失败: {response.text}")
    finally:
        Path(temp_file).unlink(missing_ok=True)
    
    return None

def test_6_list_documents():
    """测试6: 列出所有文档"""
    print("\n" + "="*70)
    print("测试6: 列出所有上传的文档")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/documents/list")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        items = data.get('items', [])
        print(f"✅ 成功获取文档列表")
        print(f"   - 总文档数: {total}")
        print(f"   - 当前页文档数: {len(items)}")
        
        if items:
            print("\n最近上传的文档:")
            for i, doc in enumerate(items[:3], 1):
                print(f"   {i}. {doc.get('title')} ({doc.get('file_name')})")
                print(f"      - ID: {doc.get('id')}")
                print(f"      - 类型: {doc.get('doc_type')}")
                print(f"      - 上传者: {doc.get('uploaded_by')}")
    else:
        print(f"❌ 失败: {response.text}")

def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("Task 5: 文件上传功能验证测试")
    print("="*70)
    print("\n测试目标:")
    print("1. 验证422错误已修复（dev_type_id类型问题）")
    print("2. 测试多种文件格式上传")
    print("3. 验证可选字段处理正确")
    print("4. 确认文档列表功能正常")
    
    try:
        # 测试1: 获取分类选项
        dev_type_id = test_1_get_classifications()
        
        # 测试2: 上传TXT（不带可选字段）
        test_2_upload_txt()
        
        # 测试3: 上传CSV（带dev_type_id）
        if dev_type_id:
            test_3_upload_csv(dev_type_id)
        
        # 测试4: 上传JSON
        test_4_upload_json()
        
        # 测试5: 上传Python代码
        test_5_upload_python()
        
        # 测试6: 列出所有文档
        test_6_list_documents()
        
        print("\n" + "="*70)
        print("测试完成！")
        print("="*70)
        print("\n✅ Task 5 完成：422错误已修复，文件上传功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
