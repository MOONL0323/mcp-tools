# 模型下载指南

## 推荐使用的 Embedding 模型

### 🎯 主要推荐：BGE中文模型（北京智源研究院）
- **模型名**: `BAAI/bge-base-zh-v1.5`
- **大小**: 约400MB
- **维度**: 768
- **优势**: 中文效果最佳，支持中英双语

### 📁 本地存储路径
请将下载的模型文件放置在：
```
data/models/bge-base-zh-v1.5/
```

### 📥 下载地址
从以下任一镜像下载所有文件到上述目录：

#### 国内镜像（推荐）
**HF-Mirror**: `https://hf-mirror.com/BAAI/bge-base-zh-v1.5/tree/main`

#### 需要下载的文件列表
```
config.json              (约1KB)
pytorch_model.bin         (约400MB) ⭐ 最大文件
tokenizer.json           (约2MB)
tokenizer_config.json    (约1KB)
vocab.txt               (约230KB)
modules.json            (约1KB)
sentence_bert_config.json (约1KB)
```

### 🔗 直接下载链接
```
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/config.json
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/pytorch_model.bin
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/tokenizer.json
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/tokenizer_config.json
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/vocab.txt
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/modules.json
https://hf-mirror.com/BAAI/bge-base-zh-v1.5/resolve/main/sentence_bert_config.json
```

### ✅ 验证下载
下载完成后，目录结构应该是：
```
data/models/bge-base-zh-v1.5/
├── config.json
├── pytorch_model.bin
├── tokenizer.json  
├── tokenizer_config.json
├── vocab.txt
├── modules.json
└── sentence_bert_config.json
```

如果没有模型，系统会自动使用TF-IDF备用模型。