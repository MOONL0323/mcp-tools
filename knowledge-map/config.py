"""
配置文件
包含所有可配置的参数和路径
"""
import os
from typing import Dict, Any

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")
GRAPHS_DIR = os.path.join(DATA_DIR, "graphs")
MODELS_DIR = os.path.join(DATA_DIR, "models")  # 本地模型存储目录

# 本地模型路径配置 - 统一使用BGE中文模型
LOCAL_MODELS = {
    # 主要推荐模型：BGE中文基础版 (768维)
    "bge-base-zh-v1.5": "data/models/BAAI/bge-base-zh-v1.5",
    # 备用选项：BGE中文大型版 (1024维，需要更多资源)
    "bge-large-zh-v1.5": "data/models/BAAI/bge-large-zh-v1.5"
}

# 默认使用的模型
DEFAULT_EMBEDDING_MODEL = "bge-base-zh-v1.5"

# 支持的文件类型
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']

# 日志配置
LOG_LEVEL = "INFO"

# 组件配置
DEFAULT_CONFIG = {
    # 使用的组件实现
    'document_parser': 'default',
    'embedding_provider': 'advanced',  # 使用新的先进embedding模型
    'vector_store': 'local',
    'knowledge_graph': 'local',
    
    # 文档解析器配置
    'document_parser_config': {
        'chunk_size': 512,  # 增加chunk大小以配合先进模型
        'chunk_overlap': 64,
        'supported_extensions': SUPPORTED_EXTENSIONS
    },
    
    # 向量化服务配置 - 先进模型
    'embedding_config': {
        # 模型选择策略：
        # 1. 如果本地有BGE模型，优先使用本地模型
        # 2. 否则尝试在线下载
        # 3. 最后fallback到TF-IDF
        'model_name': LOCAL_MODELS.get('bge-base-zh', 'BAAI/bge-base-zh-v1.5'),  # 优先本地模型
        'device': 'auto',  # 自动选择设备
        'batch_size': 32,
        'dimension': 768,  # 会根据实际模型调整
        'cache_dir': MODELS_DIR,
        'trust_remote_code': True,
        
        # 本地模型配置
        'local_models': LOCAL_MODELS,
        'prefer_local': True,  # 优先使用本地模型
        
        # fallback配置
        'enable_fallback': True,  # 启用TF-IDF fallback
        'fallback_model': 'tfidf'
    },
    
    # 向量存储配置
    'vector_store_config': {
        'persist_directory': VECTOR_STORE_DIR
    },
    
    # 知识图谱配置
    'knowledge_graph_config': {
        'min_keyword_freq': 2,
        'max_keywords_per_doc': 20,
        'similarity_threshold': 0.7
    }
}

# 离线模式配置
OFFLINE_CONFIG = {
    # 使用的组件实现（与DEFAULT_CONFIG相同）
    'document_parser': 'default',
    'embedding_provider': 'local',
    'vector_store': 'local',
    'knowledge_graph': 'local',
    
    # 文档解析器配置
    'document_parser_config': {
        'chunk_size': 500,
        'chunk_overlap': 50,
        'supported_extensions': SUPPORTED_EXTENSIONS
    },
    
    # 向量化服务配置（强制离线）
    'embedding_config': {
        'model_name': 'simple_tfidf',  # 强制使用简单向量化
        'device': 'cpu',
        'offline_mode': True,
        'fallback_to_simple': True
    },
    
    # 向量存储配置
    'vector_store_config': {
        'storage_path': VECTOR_STORE_DIR,
        'persist_documents': True
    },
    
    # 知识图谱配置
    'knowledge_graph_config': {
        'min_keyword_freq': 2,
        'max_keywords_per_doc': 10,
        'use_jieba': True,
        'graph_file_path': GRAPHS_DIR
    },
    
    # 环境变量设置
    'env_vars': {
        'HF_HUB_DISABLE_TELEMETRY': '1',
        'TRANSFORMERS_OFFLINE': '1',
        'HF_DATASETS_OFFLINE': '1',
        'TOKENIZERS_PARALLELISM': 'false'
    },
    
    # 本地模型路径映射
    'local_models': {
        'sentence-transformers': {
            'paraphrase-multilingual-MiniLM-L12-v2': os.path.join(MODELS_DIR, 'sentence-transformers', 'paraphrase-multilingual-MiniLM-L12-v2'),
            'distiluse-base-multilingual-cased-v1': os.path.join(MODELS_DIR, 'sentence-transformers', 'distiluse-base-multilingual-cased-v1')
        }
    },
    
    # 简单向量化配置（当模型不可用时的回退方案）
    'simple_vectorizer': {
        'dimension': 100,
        'use_jieba': True,
        'vocab_size': 1000
    }
}


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()


def get_offline_config() -> Dict[str, Any]:
    """获取离线配置"""
    return OFFLINE_CONFIG.copy()


def setup_offline_environment():
    """设置离线环境变量"""
    offline_config = get_offline_config()
    for key, value in offline_config['env_vars'].items():
        os.environ[key] = value


def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [
        DATA_DIR,
        UPLOADS_DIR,
        VECTOR_STORE_DIR,
        GRAPHS_DIR,
        MODELS_DIR,
        os.path.join(MODELS_DIR, 'sentence-transformers')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# 自动设置离线环境和创建目录
setup_offline_environment()
ensure_directories()


def get_default_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()


def get_offline_config():
    """获取离线配置"""
    return OFFLINE_CONFIG.copy()


# 保持向后兼容性的旧配置变量
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DEVICE = "cpu"
COLLECTION_NAME = "knowledge_documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MIN_KEYWORD_FREQ = 2
MAX_KEYWORDS_PER_DOC = 20
SIMILARITY_THRESHOLD = 0.7
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"