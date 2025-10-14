"""
测试 Qwen3-Embedding-8B API 调用
根据API调用手册测试不同的配置
"""

import asyncio
import httpx
import socket

async def test_embedding_api():
    # 根据手册：使用第二个key支持qwen3系列
    api_url = "https://oneapi.sangfor.com/v1/embeddings"
    api_key = "sk-KskGcDMEQWGncNHr6bE2Ee61F22b40F8A1C09c8b150968Ff"
    
    # 尝试不同的模型名
    model_names = [
        "qwen3-embedding-8b",
        "Qwen3-Embedding-8B",
        "qwen-embedding",
        "embedding"
    ]
    
    test_texts = [
        "这是一个测试文本",
        "Python是一种编程语言"
    ]
    
    # 首先测试域名解析
    print("🔍 步骤1: 测试域名解析...")
    try:
        host = "oneapi.sangfor.com"
        ip = socket.gethostbyname(host)
        print(f"✅ 域名解析成功: {host} -> {ip}")
    except socket.gaierror as e:
        print(f"❌ 域名解析失败: {e}")
        print(f"   这可能意味着:")
        print(f"   1. 需要连接内网或VPN")
        print(f"   2. 域名不可访问")
        print(f"   3. 网络配置问题")
        return
    
    # 测试不同的模型名
    print(f"\n🔍 步骤2: 测试 Embedding API...")
    print(f"API URL: {api_url}")
    print(f"测试文本数: {len(test_texts)}")
    
    for model in model_names:
        print(f"\n--- 尝试模型: {model} ---")
    
    for model in model_names:
        print(f"\n--- 尝试模型: {model} ---")
    
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "input": test_texts,
                        "encoding_format": "float"
                    }
                )
                
                print(f"HTTP状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ API调用成功! 模型 '{model}' 可用")
                    print(f"\n响应结构:")
                    print(f"  - Keys: {list(result.keys())}")
                    
                    if "data" in result:
                        print(f"  - Data条目数: {len(result['data'])}")
                        
                        for i, item in enumerate(result['data']):
                            embedding = item['embedding']
                            print(f"\n  文本 {i}:")
                            print(f"    - Index: {item.get('index')}")
                            print(f"    - 向量维度: {len(embedding)}")
                            print(f"    - 向量前5个值: {embedding[:5]}")
                    
                    if "usage" in result:
                        print(f"\n  Token使用:")
                        print(f"    - {result['usage']}")
                    
                    print(f"\n✅ 找到可用模型: {model}")
                    break  # 找到可用模型就停止
                        
                else:
                    print(f"❌ 状态码 {response.status_code}")
                    print(f"   响应: {response.text[:200]}")
                    
        except httpx.ConnectError as e:
            print(f"❌ 连接错误: {str(e)}")
            print(f"   提示: 可能需要连接内网/VPN")
            break  # 连接错误就不继续尝试其他模型了
        except Exception as e:
            print(f"❌ 调用失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding_api())
