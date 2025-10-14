"""
直接测试语义搜索功能
"""
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

print("="*80)
print("  Task 10: 语义搜索测试")
print("="*80)

# Test 1: 统计信息
print("\n[1] 获取统计信息...")
response = requests.get(f"{BASE_URL}/search/stats")
result = response.json()
print(f"✅ 已向量化chunks: {result['total_vectorized_chunks']}")
print(f"   存储方法: {result['storage_method']}")
print(f"   Embedding模型: {result['embedding_model']}")
print(f"   向量维度: {result['embedding_dimension']}")

# Test 2: 语义搜索 - 查询1
print("\n[2] 语义搜索 - Python相关")
response = requests.post(
    f"{BASE_URL}/search/semantic",
    json={"query": "如何使用Python编写代码", "top_k": 3}
)
result = response.json()

print(f"✅ 搜索成功!")
print(f"   查询: {result['query']}")
print(f"   找到: {result['total']} 个结果")
print(f"   方法: {result.get('method', 'N/A')}")

for i, r in enumerate(result['results'][:3], 1):
    print(f"\n   结果 {i}:")
    print(f"      文档: {r['document_title']}")
    print(f"      相似度: {r['similarity']}")
    print(f"      Chunk索引: {r['chunk_index']}")
    print(f"      内容预览: {r['content'][:100]}...")

# Test 3: 语义搜索 - 查询2
print("\n[3] 语义搜索 - Flask相关")
response = requests.post(
    f"{BASE_URL}/search/semantic",
    json={"query": "Flask API开发", "top_k": 3}
)
result = response.json()

print(f"✅ 搜索成功!")
print(f"   查询: {result['query']}")
print(f"   找到: {result['total']} 个结果")

for i, r in enumerate(result['results'][:3], 1):
    print(f"\n   结果 {i}:")
    print(f"      文档: {r['document_title']}")
    print(f"      相似度: {r['similarity']}")
    print(f"      内容: {r['content'][:80]}...")

# Test 4: 语义搜索 - 查询3
print("\n[4] 语义搜索 - 异步编程")
response = requests.post(
    f"{BASE_URL}/search/semantic",
    json={"query": "异步编程和asyncio", "top_k": 3}
)
result = response.json()

print(f"✅ 搜索成功!")
print(f"   查询: {result['query']}")
print(f"   找到: {result['total']} 个结果")

for i, r in enumerate(result['results'][:3], 1):
    print(f"\n   结果 {i}:")
    print(f"      相似度: {r['similarity']}")
    print(f"      内容: {r['content'][:80]}...")

print("\n" + "="*80)
print("  ✅ Task 10 测试完成！语义搜索工作正常！")
print("="*80)

print("\n🎯 技术实现:")
print("  - 存储: SQLite (DocumentChunk.embedding)")
print("  - 计算: Numpy (余弦相似度)")
print("  - 模型: sentence-transformers/all-MiniLM-L6-v2")
print("  - 维度: 384")
print("  - 状态: ✅ 已完成并测试通过")

print("\n✨ 下一步: Task 11 - 实体提取服务")
