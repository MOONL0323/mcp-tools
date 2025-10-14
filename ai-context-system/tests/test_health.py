"""快速健康检查"""
import requests

try:
    print("测试健康检查...")
    response = requests.get("http://localhost:8080/health", timeout=5)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print("✅ 后端正常运行！")
except Exception as e:
    print(f"❌ 后端连接失败: {e}")
