"""
测试分类API
验证分类数据是否正确返回
"""

import requests
import json

BASE_URL = "http://localhost:8080/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_classifications():
    """测试分类API"""
    
    print_section("测试1: 获取Demo代码分类")
    response = requests.get(f"{BASE_URL}/v1/classifications/dev-types?category=demo_code")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"成功获取 {len(data.get('data', []))} 个Demo代码分类:")
        for item in data.get('data', []):
            print(f"  - {item['display_name']}: {item['description']}")
    else:
        print(f"错误: {response.text}")
    
    print_section("测试2: 获取业务文档分类")
    response = requests.get(f"{BASE_URL}/v1/classifications/dev-types?category=business_doc")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"成功获取 {len(data.get('data', []))} 个业务文档分类:")
        for item in data.get('data', []):
            print(f"  - {item['display_name']}: {item['description']}")
    else:
        print(f"错误: {response.text}")
    
    print_section("测试3: 获取团队列表")
    response = requests.get(f"{BASE_URL}/v1/classifications/teams")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"成功获取 {len(data.get('data', []))} 个团队:")
        for item in data.get('data', []):
            print(f"  - {item['display_name']}: {item['description']}")
    else:
        print(f"错误: {response.text}")
    
    print_section("测试4: 获取所有分类选项（一次性）")
    response = requests.get(f"{BASE_URL}/v1/classifications/options")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result = data.get('data', {})
        print(f"Demo代码分类: {len(result.get('demo_code_types', []))} 个")
        print(f"业务文档分类: {len(result.get('business_doc_types', []))} 个")
        print(f"团队: {len(result.get('teams', []))} 个")
        
        # 详细显示所有内容
        print("\n📦 Demo代码分类:")
        for item in result.get('demo_code_types', []):
            print(f"  - {item['display_name']}: {item['description']}")
        
        print("\n📄 业务文档分类:")
        for item in result.get('business_doc_types', []):
            print(f"  - {item['display_name']}: {item['description']}")
        
        print("\n🏢 团队:")
        for item in result.get('teams', []):
            print(f"  - {item['display_name']}: {item['description']}")
    else:
        print(f"错误: {response.text}")
    
    print_section("✅ 测试完成")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("  🚀 开始测试分类API")
        print("=" * 60)
        print(f"后端地址: {BASE_URL}")
        print("请确保后端服务已启动 (python -m uvicorn app.main:app)")
        
        # 等待用户确认
        input("\n按回车键开始测试...")
        
        test_classifications()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务，请确保后端已启动")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
