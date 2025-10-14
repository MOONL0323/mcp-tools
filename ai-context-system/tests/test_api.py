"""
AI Context System - 功能测试脚本
测试完整的文档处理流程
"""

import requests
import json
import os
from pathlib import Path

# API配置
BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_health():
    """测试健康检查"""
    print_header("1. 健康检查测试")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200

def test_upload_document():
    """测试文档上传"""
    print_header("2. 文档上传测试")
    
    # 创建测试文档
    test_content = """
# Python编程指南

## 函数定义
在Python中，使用def关键字定义函数：

```python
def greet(name):
    return f"Hello, {name}!"
```

## 类定义
使用class关键字定义类：

```python
class Person:
    def __init__(self, name):
        self.name = name
```

这是一个关于Python编程的简单示例。
"""
    
    test_file = Path("test_document.md")
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.md', f, 'text/markdown')}
            data = {
                'title': 'Python编程测试文档',
                'doc_type': 'code'
            }
            response = requests.post(f"{API_V1}/docs/upload", files=files, data=data)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"文档ID: {result.get('id')}")
            print(f"标题: {result.get('title')}")
            print(f"处理状态: {result.get('status')}")
            return result.get('id')
        else:
            print(f"错误: {response.text}")
            return None
    finally:
        test_file.unlink(missing_ok=True)

def test_list_documents():
    """测试文档列表"""
    print_header("3. 文档列表测试")
    response = requests.get(f"{API_V1}/docs/")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        docs = response.json()
        print(f"文档总数: {len(docs)}")
        for doc in docs:
            print(f"  - {doc.get('title')} (ID: {doc.get('id')})")
        return docs
    return []

def test_get_document(doc_id):
    """测试获取文档详情"""
    print_header("4. 文档详情测试")
    response = requests.get(f"{API_V1}/docs/{doc_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        doc = response.json()
        print(f"标题: {doc.get('title')}")
        print(f"类型: {doc.get('doc_type')}")
        print(f"大小: {doc.get('file_size')} bytes")
        print(f"状态: {doc.get('status')}")
        return doc
    return None

def test_search_documents(query):
    """测试向量搜索"""
    print_header("5. 向量搜索测试")
    data = {
        'query': query,
        'top_k': 5
    }
    response = requests.post(f"{API_V1}/docs/search", json=data)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"搜索查询: '{query}'")
        print(f"找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"\n  结果 {i}:")
            print(f"    文档: {result.get('document_title')}")
            print(f"    相似度: {result.get('score', 0):.4f}")
            print(f"    内容预览: {result.get('content', '')[:100]}...")
        return results
    return []

def test_get_chunks(doc_id):
    """测试获取文档分块"""
    print_header("6. 文档分块测试")
    response = requests.get(f"{API_V1}/docs/{doc_id}/chunks")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        chunks = response.json()
        print(f"分块数量: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3], 1):  # 只显示前3个
            print(f"\n  分块 {i}:")
            print(f"    序号: {chunk.get('chunk_index')}")
            print(f"    内容: {chunk.get('content', '')[:100]}...")
        return chunks
    return []

def test_get_entities(doc_id):
    """测试获取实体"""
    print_header("7. 实体提取测试")
    response = requests.get(f"{API_V1}/docs/{doc_id}/entities")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        entities = response.json()
        print(f"实体数量: {len(entities)}")
        entity_types = {}
        for entity in entities:
            entity_type = entity.get('entity_type', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
        print("\n实体类型统计:")
        for etype, count in entity_types.items():
            print(f"  - {etype}: {count}")
        
        print("\n实体示例:")
        for entity in entities[:5]:  # 显示前5个
            print(f"  - {entity.get('name')} ({entity.get('entity_type')})")
        return entities
    return []

def main():
    """主测试流程"""
    print("\n🚀 AI Context System - 功能测试")
    print("="*60)
    
    # 1. 健康检查
    if not test_health():
        print("\n❌ 服务未启动或无法访问！")
        return
    
    # 2. 上传文档
    doc_id = test_upload_document()
    if not doc_id:
        print("\n❌ 文档上传失败！")
        return
    
    # 等待处理（在实际场景中，应该轮询状态）
    import time
    print("\n⏳ 等待文档处理...")
    time.sleep(3)
    
    # 3. 列出文档
    test_list_documents()
    
    # 4. 获取文档详情
    test_get_document(doc_id)
    
    # 5. 向量搜索
    test_search_documents("Python函数定义")
    
    # 6. 获取分块
    test_get_chunks(doc_id)
    
    # 7. 获取实体
    test_get_entities(doc_id)
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
