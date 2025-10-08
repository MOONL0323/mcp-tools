#!/usr/bin/env python3
"""
知识图谱系统 - 数据管理工具
提供删除、重置等数据管理功能
"""

import os
import sys
import argparse
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_default_config
from core.factory import get_factory
from loguru import logger


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.factory = get_factory()
        self.config = get_default_config()
        self.vector_store = self.factory.create_vector_store()
        self.knowledge_graph = self.factory.create_knowledge_graph()
        
    def list_documents(self):
        """列出所有文档"""
        print("\n" + "="*60)
        print("📚 已存储的文档")
        print("="*60 + "\n")
        
        stats = self.vector_store.get_collection_info()
        print(f"文档总数: {stats.get('document_count', 0)}")
        
        # 获取示例文档
        sample_docs = stats.get('sample_documents', [])
        if sample_docs:
            print("\n示例文档:")
            for i, doc in enumerate(sample_docs[:10], 1):
                metadata = doc.get('metadata', {})
                source = metadata.get('source', 'unknown')
                source_file = metadata.get('source_file', source)
                print(f"{i}. {Path(source_file).name}")
                print(f"   内容预览: {doc.get('content', '')[:100]}...")
                print()
    
    def list_sources(self):
        """列出所有来源文件"""
        print("\n" + "="*60)
        print("📁 文档来源文件")
        print("="*60 + "\n")
        
        stats = self.vector_store.get_collection_info()
        sample_docs = stats.get('sample_documents', [])
        
        # 收集所有来源文件
        sources = set()
        for doc in sample_docs:
            metadata = doc.get('metadata', {})
            source = metadata.get('source_file', metadata.get('source', 'unknown'))
            sources.add(source)
        
        sources = sorted(sources)
        for i, source in enumerate(sources, 1):
            print(f"{i}. {Path(source).name}")
            print(f"   完整路径: {source}")
            print()
        
        print(f"\n共 {len(sources)} 个来源文件\n")
        return list(sources)
    
    def delete_by_source(self, source_file: str):
        """
        根据来源文件删除文档
        
        Args:
            source_file: 源文件路径或文件名
        """
        print(f"\n🗑️  准备删除来源为 '{source_file}' 的文档...")
        
        # 确认
        confirm = input("确认删除？(y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消删除")
            return
        
        # 这里需要实现具体的删除逻辑
        # 由于当前实现是基于pickle的简单存储，我们需要：
        # 1. 加载所有文档
        # 2. 过滤掉指定来源的文档
        # 3. 重新保存
        
        print("⚠️  当前版本暂不支持选择性删除")
        print("    建议使用 --reset 清空所有数据后重新添加")
    
    def reset_all(self):
        """重置所有数据"""
        print("\n⚠️  警告：这将删除所有文档和知识图谱数据！")
        confirm = input("确认重置？(y/N): ").strip().lower()
        
        if confirm != 'y':
            print("已取消重置")
            return
        
        print("\n正在重置数据...")
        
        try:
            # 重置向量存储
            self.vector_store.reset_collection()
            logger.info("向量存储已重置")
            
            # 清空知识图谱
            from config import GRAPHS_DIR
            if os.path.exists(GRAPHS_DIR):
                import shutil
                for file in os.listdir(GRAPHS_DIR):
                    file_path = os.path.join(GRAPHS_DIR, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"已删除: {file}")
            
            print("\n✅ 所有数据已重置")
            
        except Exception as e:
            logger.error(f"重置失败: {e}")
            print(f"\n❌ 重置失败: {e}")
    
    def get_statistics(self):
        """显示统计信息"""
        print("\n" + "="*60)
        print("📊 系统统计")
        print("="*60 + "\n")
        
        # 向量存储统计
        vector_stats = self.vector_store.get_collection_info()
        print("📚 向量存储:")
        print(f"  - 文档数量: {vector_stats.get('document_count', 0)}")
        print(f"  - 向量维度: {vector_stats.get('dimension', 0)}")
        print(f"  - 存储类型: {vector_stats.get('storage_type', 'unknown')}")
        
        # 知识图谱统计
        graph_stats = self.knowledge_graph.get_graph_statistics()
        print(f"\n🕸️  知识图谱:")
        print(f"  - 节点数量: {graph_stats.get('nodes', 0)}")
        print(f"  - 边数量: {graph_stats.get('edges', 0)}")
        print(f"  - 平均度: {graph_stats.get('avg_degree', 0):.2f}")
        
        # 存储空间
        from config import DATA_DIR
        if os.path.exists(DATA_DIR):
            import shutil
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(DATA_DIR):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            
            size_mb = total_size / (1024 * 1024)
            print(f"\n💾 存储空间:")
            print(f"  - 数据大小: {size_mb:.2f} MB")
        
        print("\n" + "="*60 + "\n")
    
    def clean_cache(self):
        """清理缓存文件"""
        print("\n🧹 清理缓存...")
        
        cleaned = 0
        
        # 清理__pycache__
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                import shutil
                cache_dir = os.path.join(root, '__pycache__')
                shutil.rmtree(cache_dir)
                print(f"删除: {cache_dir}")
                cleaned += 1
        
        # 清理.pyc文件
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
                    cleaned += 1
        
        print(f"\n✅ 清理完成，删除了 {cleaned} 个缓存项\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="知识图谱系统数据管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 查看统计信息
  python manage_data.py --stats
  
  # 列出所有文档
  python manage_data.py --list
  
  # 列出来源文件
  python manage_data.py --sources
  
  # 重置所有数据
  python manage_data.py --reset
  
  # 清理缓存
  python manage_data.py --clean-cache
        """
    )
    
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--list', action='store_true', help='列出所有文档')
    parser.add_argument('--sources', action='store_true', help='列出来源文件')
    parser.add_argument('--delete-source', type=str, help='删除指定来源的文档')
    parser.add_argument('--reset', action='store_true', help='重置所有数据')
    parser.add_argument('--clean-cache', action='store_true', help='清理缓存文件')
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        manager = DataManager()
        
        if args.stats:
            manager.get_statistics()
        
        if args.list:
            manager.list_documents()
        
        if args.sources:
            manager.list_sources()
        
        if args.delete_source:
            manager.delete_by_source(args.delete_source)
        
        if args.reset:
            manager.reset_all()
        
        if args.clean_cache:
            manager.clean_cache()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消\n")
        return 1
    
    except Exception as e:
        logger.error(f"错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
