#!/usr/bin/env python3
"""
测试文档上传API
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8080/api/v1"

def test_upload_txt():
    """测试上传TXT文件"""
    print("\n=== 测试上传TXT文件 ===")
    
    # 创建测试文件
    test_content = """# 测试文档

这是一个测试文档，用于验证文件上传功能。

## 功能列表
1. 文件上传
2. 文件解析
3. 内容提取
"""
    
    test_file = Path("test_upload.txt")
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.txt', f, 'text/plain')}
            data = {
                'doc_type': 'business_doc',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'tags': json.dumps(['测试', 'TXT']),
                'team_role': 'backend',
                'uploaded_by': 'admin'
            }
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ TXT文件上传成功")
            return True
        else:
            print("❌ TXT文件上传失败")
            return False
            
    except Exception as e:
        print(f"❌ 上传出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_file.exists():
            test_file.unlink()


def test_upload_pdf():
    """测试上传PDF文件"""
    print("\n=== 测试上传PDF文件 ===")
    
    # 创建一个简单的PDF（需要reportlab）
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        test_file = Path("test_upload.pdf")
        
        c = canvas.Canvas(str(test_file), pagesize=letter)
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 730, "This is a test PDF file.")
        c.save()
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.pdf', f, 'application/pdf')}
            data = {
                'doc_type': 'business_doc',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'tags': json.dumps(['测试', 'PDF']),
                'team_role': 'backend',
                'uploaded_by': 'admin'
            }
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if test_file.exists():
            test_file.unlink()
        
        if response.status_code == 200:
            print("✅ PDF文件上传成功")
            return True
        else:
            print("❌ PDF文件上传失败")
            return False
            
    except ImportError:
        print("⚠️  未安装reportlab，跳过PDF测试")
        return None
    except Exception as e:
        print(f"❌ PDF上传出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_csv():
    """测试上传CSV文件"""
    print("\n=== 测试上传CSV文件 ===")
    
    # 创建测试CSV
    test_content = """ID,名称,数量,价格
1,产品A,100,29.99
2,产品B,200,49.99
3,产品C,150,39.99
"""
    
    test_file = Path("test_upload.csv")
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload.csv', f, 'text/csv')}
            data = {
                'doc_type': 'business_doc',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'tags': json.dumps(['测试', 'CSV', '数据']),
                'team_role': 'backend',
                'uploaded_by': 'admin'
            }
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if test_file.exists():
            test_file.unlink()
        
        if response.status_code == 200:
            print("✅ CSV文件上传成功")
            return True
        else:
            print("❌ CSV文件上传失败")
            return False
            
    except Exception as e:
        print(f"❌ CSV上传出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_json():
    """测试上传JSON文件"""
    print("\n=== 测试上传JSON文件 ===")
    
    # 创建测试JSON
    test_content = {
        "name": "测试配置",
        "version": "1.0.0",
        "settings": {
            "debug": True,
            "port": 8080
        }
    }
    
    test_file = Path("test_config.json")
    test_file.write_text(json.dumps(test_content, indent=2, ensure_ascii=False), encoding='utf-8')
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_config.json', f, 'application/json')}
            data = {
                'doc_type': 'demo_code',
                'team_name': 'xaas开发组',
                'project_name': '测试项目',
                'tags': json.dumps(['测试', 'JSON', '配置']),
                'team_role': 'backend',
                'code_function': 'other',
                'uploaded_by': 'admin'
            }
            
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if test_file.exists():
            test_file.unlink()
        
        if response.status_code == 200:
            print("✅ JSON文件上传成功")
            return True
        else:
            print("❌ JSON文件上传失败")
            return False
            
    except Exception as e:
        print(f"❌ JSON上传出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("  文档上传API测试")
    print("="*60)
    
    results = []
    
    # 测试各种格式
    results.append(("TXT", test_upload_txt()))
    results.append(("PDF", test_upload_pdf()))
    results.append(("CSV", test_upload_csv()))
    results.append(("JSON", test_upload_json()))
    
    # 统计结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    
    for format_name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️  跳过"
        print(f"{format_name:10} {status}")
    
    success_count = sum(1 for _, r in results if r is True)
    total_count = len([r for r in results if r is not None])
    
    print(f"\n通过率: {success_count}/{total_count}")


if __name__ == "__main__":
    main()
