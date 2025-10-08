#!/usr/bin/env python3
"""
验证本地BGE模型
"""
import os
from pathlib import Path

def check_model_files():
    """检查模型文件是否完整"""
    model_path = Path("./data/models/bge-base-zh-v1.5")
    
    if not model_path.exists():
        print("❌ 模型目录不存在，请先下载模型")
        print("   参考 MODEL_DOWNLOAD.md 文件")
        return False
    
    required_files = [
        "config.json",
        "pytorch_model.bin", 
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt"
    ]
    
    print(f"📁 检查模型目录: {model_path.absolute()}")
    
    missing_files = []
    for file_name in required_files:
        file_path = model_path / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {file_name} ({size_mb:.1f} MB)")
        else:
            missing_files.append(file_name)
            print(f"❌ {file_name} (缺失)")
    
    if missing_files:
        print(f"\n❌ 缺少必需文件: {missing_files}")
        print("请下载所有必需文件到 data/models/bge-base-zh-v1.5/ 目录")
        return False
    else:
        print("\n✅ 所有模型文件完整")
        return True

def test_model_loading():
    """测试模型加载"""
    try:
        print("\n🔄 测试模型加载...")
        from sentence_transformers import SentenceTransformer
        
        model_path = os.path.abspath("./data/models/bge-base-zh-v1.5")
        print(f"   模型绝对路径: {model_path}")
        
        # 尝试不同的加载方式
        try:
            # 方式1：使用绝对路径
            model = SentenceTransformer(model_path)
        except:
            try:
                # 方式2：使用 trust_remote_code
                model = SentenceTransformer(model_path, trust_remote_code=True)
            except:
                # 方式3：直接使用transformers库
                from transformers import AutoTokenizer, AutoModel
                tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                model_hf = AutoModel.from_pretrained(model_path, trust_remote_code=True)
                
                # 简单测试
                inputs = tokenizer("测试文本", return_tensors="pt")
                outputs = model_hf(**inputs)
                print(f"✅ 使用transformers加载成功！")
                print(f"   输出维度: {outputs.last_hidden_state.shape[-1]}")
                return True
        
        # 测试编码
        test_texts = ['这是一个测试', 'AI Agent测试', '人工智能']
        embeddings = model.encode(test_texts)
        
        print(f"✅ 模型加载成功！")
        print(f"   向量维度: {embeddings.shape[1]}")
        print(f"   测试文本数: {len(test_texts)}")
        return True
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BGE模型验证工具")
    print("=" * 40)
    
    # 检查文件
    if not check_model_files():
        exit(1)
    
    # 测试加载
    if not test_model_loading():
        exit(1)
        
    print("\n🎉 BGE模型验证通过！可以正常使用。")