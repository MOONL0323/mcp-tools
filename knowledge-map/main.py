"""
知识图谱主程序 - 重构版本
使用抽象接口和工厂模式，支持组件替换
"""
import os
import sys
import argparse
from typing import List, Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_default_config, get_offline_config
from core.factory import get_factory
from interfaces import (
    DocumentParserInterface,
    EmbeddingProviderInterface,
    VectorStoreInterface,
    KnowledgeGraphInterface
)
from loguru import logger
import time

def setup_logging(level="INFO"):
    """设置日志"""
    logger.remove()
    logger.add(sys.stderr, level=level)

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_supported_files(directory):
    """获取支持的文件列表"""
    supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.go', '.mod', '.sum']
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in supported_extensions):
                files.append(os.path.join(root, filename))
    return files

class ProgressTracker:
    """进度跟踪器"""
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.start_time = time.time()
    
    def update(self, step=1):
        self.current += step
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
            print(f"进度: {self.current}/{self.total} ({self.current/self.total*100:.1f}%) ETA: {eta:.1f}s")
    
    def finish(self):
        elapsed = time.time() - self.start_time
        print(f"完成! 总用时: {elapsed:.1f}s")


class ModularKnowledgeMapPipeline:
    """模块化知识图谱构建流水线"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化流水线
        
        Args:
            config: 配置字典，如果为None则使用默认配置
        """
        # 设置日志
        setup_logging("INFO")
        
        # 获取配置
        self.config = config if config is not None else get_default_config()
        
        # 获取工厂实例
        self.factory = get_factory(self.config)
        
        # 创建组件实例
        self._create_components()
        
        logger.info("模块化知识图谱流水线初始化完成")
    
    def _create_components(self):
        """创建所有组件实例"""
        try:
            # 创建文档解析器
            self.document_parser = self.factory.create_document_parser()
            
            # 创建向量化服务
            self.embedding_provider = self.factory.create_embedding_provider()
            
            # 创建向量存储
            self.vector_store = self.factory.create_vector_store()
            # 为向量存储配置embedding服务
            self.vector_store.configure(embedding_provider=self.embedding_provider)
            
            # 创建知识图谱
            self.knowledge_graph = self.factory.create_knowledge_graph()
            # 为知识图谱配置embedding服务
            self.knowledge_graph.configure(embedding_provider=self.embedding_provider)
            
            logger.info("所有组件创建完成")
            
        except Exception as e:
            logger.error(f"组件创建失败: {str(e)}")
            raise
    
    def process_file(self, file_path: str, save_graph: bool = True) -> dict:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            save_graph: 是否保存图谱
            
        Returns:
            处理结果字典
        """
        logger.info(f"开始处理文件: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = format_file_size(os.path.getsize(file_path))
        logger.info(f"文件大小: {file_size}")
        
        # 1. 检查文件是否支持
        if not self.document_parser.is_supported(file_path):
            raise ValueError(f"不支持的文件类型: {file_path}")
        
        # 2. 解析文件
        logger.info("步骤 1/4: 解析文件内容...")
        documents = self.document_parser.parse_file(file_path)
        doc_info = self.document_parser.get_document_info(documents)
        
        # 3. 向量化并存储
        logger.info("步骤 2/4: 向量化并存储文档...")
        doc_ids = self.vector_store.add_documents(documents)
        
        # 4. 构建知识图谱
        logger.info("步骤 3/4: 构建知识图谱...")
        graph = self.knowledge_graph.build_from_documents(documents)
        graph_stats = self.knowledge_graph.get_graph_statistics()
        
        # 5. 保存结果
        if save_graph:
            logger.info("步骤 4/4: 保存知识图谱...")
            filename = Path(file_path).stem
            from config import GRAPHS_DIR
            graph_path = os.path.join(GRAPHS_DIR, f"{filename}_graph.pkl")
            self.knowledge_graph.save_graph(graph_path)
        
        # 构建结果
        result = {
            "file_path": file_path,
            "file_size": file_size,
            "document_info": doc_info,
            "graph_statistics": graph_stats,
            "vector_store_info": self.vector_store.get_collection_info(),
            "success": True
        }
        
        logger.info("文件处理完成!")
        return result
    
    def process_directory(self, directory_path: str, recursive: bool = True, save_graph: bool = True) -> dict:
        """
        处理目录中的所有文件
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归处理子目录
            save_graph: 是否保存图谱
            
        Returns:
            处理结果字典
        """
        logger.info(f"开始处理目录: {directory_path}")
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        # 获取所有支持的文件
        supported_extensions = self.document_parser.get_supported_extensions()
        file_paths = get_supported_files(directory_path, supported_extensions, recursive)
        
        if not file_paths:
            logger.warning("目录中没有找到支持的文件")
            return {"success": False, "message": "没有找到支持的文件"}
        
        logger.info(f"找到 {len(file_paths)} 个支持的文件")
        
        # 进度跟踪
        progress = ProgressTracker(len(file_paths), "处理文件")
        
        all_documents = []
        processed_files = []
        failed_files = []
        
        # 逐个处理文件
        for file_path in file_paths:
            try:
                logger.info(f"处理文件: {os.path.basename(file_path)}")
                
                # 解析文件
                documents = self.document_parser.parse_file(file_path)
                all_documents.extend(documents)
                
                processed_files.append({
                    "path": file_path,
                    "chunks": len(documents),
                    "size": format_file_size(os.path.getsize(file_path))
                })
                
                progress.update()
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {str(e)}")
                failed_files.append({"path": file_path, "error": str(e)})
                progress.update()
                continue
        
        progress.finish()
        
        if not all_documents:
            logger.warning("没有成功解析任何文档")
            return {"success": False, "message": "没有成功解析任何文档"}
        
        logger.info(f"总共解析了 {len(all_documents)} 个文档块")
        
        # 向量化并存储
        logger.info("向量化并存储所有文档...")
        doc_ids = self.vector_store.add_documents(all_documents)
        
        # 构建知识图谱
        logger.info("构建知识图谱...")
        graph = self.knowledge_graph.build_from_documents(all_documents)
        graph_stats = self.knowledge_graph.get_graph_statistics()
        
        # 保存结果
        if save_graph:
            logger.info("保存知识图谱...")
            dir_name = os.path.basename(directory_path.rstrip(os.sep))
            from config import GRAPHS_DIR
            graph_path = os.path.join(GRAPHS_DIR, f"{dir_name}_graph.pkl")
            self.knowledge_graph.save_graph(graph_path)
        
        # 构建结果
        result = {
            "directory_path": directory_path,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "total_documents": len(all_documents),
            "graph_statistics": graph_stats,
            "vector_store_info": self.vector_store.get_collection_info(),
            "success": True
        }
        
        logger.info("目录处理完成!")
        return result
    
    def search_knowledge(self, query: str, k: int = 5) -> dict:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            搜索结果
        """
        logger.info(f"搜索知识库: '{query}'")
        
        # 向量搜索
        vector_results = self.vector_store.similarity_search(query, k=k)
        
        # 关键词搜索（如果图中存在）
        keyword_results = []
        try:
            related_keywords = self.knowledge_graph.find_related_keywords(query, max_results=5)
            related_docs = self.knowledge_graph.find_related_documents(query)
            if related_keywords or related_docs:
                keyword_results = {
                    "related_keywords": related_keywords,
                    "related_documents": related_docs
                }
        except Exception as e:
            logger.warning(f"关键词搜索失败: {str(e)}")
        
        result = {
            "query": query,
            "vector_search_results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": score
                }
                for doc, score in vector_results
            ],
            "keyword_search_results": keyword_results
        }
        
        logger.info(f"搜索完成，返回 {len(vector_results)} 个向量搜索结果")
        return result
    
    def get_system_status(self) -> dict:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        return {
            "vector_store": self.vector_store.get_collection_info(),
            "knowledge_graph": self.knowledge_graph.get_graph_statistics(),
            "supported_extensions": self.document_parser.get_supported_extensions(),
            "embedding_info": self.embedding_provider.get_model_info(),
            "available_components": self.factory.list_available_components(),
            "config": self.config
        }
    
    def replace_component(self, component_type: str, component_name: str):
        """
        替换组件
        
        Args:
            component_type: 组件类型 ('document_parser', 'embedding_provider', 'vector_store', 'knowledge_graph')
            component_name: 组件名称
        """
        logger.info(f"替换组件: {component_type} -> {component_name}")
        
        if component_type == 'document_parser':
            self.document_parser = self.factory.create_document_parser(component_name)
        elif component_type == 'embedding_provider':
            self.embedding_provider = self.factory.create_embedding_provider(component_name)
            # 重新配置依赖组件
            self.vector_store.configure(embedding_provider=self.embedding_provider)
            self.knowledge_graph.configure(embedding_provider=self.embedding_provider)
        elif component_type == 'vector_store':
            self.vector_store = self.factory.create_vector_store(component_name)
            self.vector_store.configure(embedding_provider=self.embedding_provider)
        elif component_type == 'knowledge_graph':
            self.knowledge_graph = self.factory.create_knowledge_graph(component_name)
            self.knowledge_graph.configure(embedding_provider=self.embedding_provider)
        else:
            raise ValueError(f"未知的组件类型: {component_type}")
        
        logger.info(f"组件 {component_type} 已替换为 {component_name}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="模块化知识图谱构建工具")
    parser.add_argument("--file", "-f", type=str, help="处理单个文件")
    parser.add_argument("--directory", "-d", type=str, help="处理目录")
    parser.add_argument("--recursive", "-r", action="store_true", default=True, help="递归处理子目录")
    parser.add_argument("--search", "-s", type=str, help="搜索知识库")
    parser.add_argument("--status", action="store_true", help="显示系统状态")
    parser.add_argument("--no-save", action="store_true", help="不保存图谱文件")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--components", action="store_true", help="列出可用组件")
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config = None
        if args.config:
            import json
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 初始化流水线
        pipeline = ModularKnowledgeMapPipeline(config)
        
        if args.components:
            # 显示可用组件
            components = pipeline.factory.list_available_components()
            print("\\n=== 可用组件 ===")
            for component_type, component_list in components.items():
                print(f"{component_type}: {', '.join(component_list)}")
        
        elif args.status:
            # 显示系统状态
            status = pipeline.get_system_status()
            print("\\n=== 系统状态 ===")
            for key, value in status.items():
                if key != 'config':  # 配置信息太长，不在这里显示
                    print(f"{key}: {value}")
        
        elif args.search:
            # 搜索知识库
            results = pipeline.search_knowledge(args.search)
            print(f"\\n=== 搜索结果: '{args.search}' ===")
            
            # 显示向量搜索结果
            print("\\n向量搜索结果:")
            for i, result in enumerate(results["vector_search_results"], 1):
                print(f"\\n{i}. 相似度: {result['similarity']:.4f}")
                print(f"   内容: {result['content'][:200]}...")
                print(f"   来源: {result['metadata'].get('source_file', 'unknown')}")
            
            # 显示关键词搜索结果
            if results["keyword_search_results"]:
                print("\\n关键词搜索结果:")
                kw_results = results["keyword_search_results"]
                if kw_results.get("related_keywords"):
                    print("  相关关键词:")
                    for kw, weight, rel_type in kw_results["related_keywords"]:
                        print(f"    - {kw} (权重: {weight:.3f}, 类型: {rel_type})")
        
        elif args.file:
            # 处理单个文件
            result = pipeline.process_file(args.file, save_graph=not args.no_save)
            print("\\n=== 处理结果 ===")
            print(f"文件: {result['file_path']}")
            print(f"大小: {result['file_size']}")
            print(f"文档块数: {result['document_info']['total_chunks']}")
            print(f"图节点数: {result['graph_statistics']['nodes']}")
            print(f"图边数: {result['graph_statistics']['edges']}")
        
        elif args.directory:
            # 处理目录
            result = pipeline.process_directory(
                args.directory, 
                recursive=args.recursive, 
                save_graph=not args.no_save
            )
            print("\\n=== 处理结果 ===")
            print(f"目录: {result['directory_path']}")
            print(f"处理文件数: {len(result['processed_files'])}")
            print(f"失败文件数: {len(result['failed_files'])}")
            print(f"总文档块数: {result['total_documents']}")
            print(f"图节点数: {result['graph_statistics']['nodes']}")
            print(f"图边数: {result['graph_statistics']['edges']}")
            
            if result['failed_files']:
                print("\\n失败的文件:")
                for failed in result['failed_files']:
                    print(f"  - {failed['path']}: {failed['error']}")
        
        else:
            # 显示帮助信息
            parser.print_help()
            print("\\n示例用法:")
            print("  python main_modular.py --file document.pdf")
            print("  python main_modular.py --directory ./documents --recursive")
            print("  python main_modular.py --search '机器学习是什么'")
            print("  python main_modular.py --status")
            print("  python main_modular.py --components")
    
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())