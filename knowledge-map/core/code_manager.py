"""
增强的代码管理系统
支持代码上传、智能解析、块化存储，按函数/类/模块等逻辑单元进行存储
为AI Agent提供精确的代码检索服务
"""
import os
import re
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import pickle
import ast
from loguru import logger

from interfaces.embedding_provider import EmbeddingProviderInterface
from interfaces.vector_store import VectorStoreInterface


@dataclass
class CodeBlock:
    """代码块数据类"""
    block_id: str
    content: str
    block_type: str  # function, class, method, variable, import, comment, etc.
    name: str  # 函数名、类名等
    source_file: str
    source_path: str
    file_type: str
    language: str
    start_line: int
    end_line: int
    dependencies: List[str]  # 依赖的其他代码块
    docstring: Optional[str] = None
    signature: Optional[str] = None
    complexity: int = 1  # 代码复杂度
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CodeFileInfo:
    """代码文件信息数据类"""
    file_id: str
    filename: str
    file_path: str
    language: str
    file_size: int
    file_hash: str
    total_blocks: int
    upload_time: str
    processed: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.upload_time is None:
            self.upload_time = datetime.now().isoformat()


class EnhancedCodeManager:
    """增强的代码管理器"""
    
    def __init__(
        self,
        embedding_provider: EmbeddingProviderInterface,
        vector_store: VectorStoreInterface,
        storage_path: str = "data/code"
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 索引文件
        self.files_index_file = self.storage_path / "code_files_index.json"
        self.blocks_file = self.storage_path / "code_blocks.pkl"
        
        # 内存缓存
        self.files_index: Dict[str, CodeFileInfo] = {}
        self.code_blocks: Dict[str, CodeBlock] = {}
        
        # 支持的编程语言
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.vue': 'vue',
            '.sh': 'bash',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown'
        }
        
        # 加载现有数据
        self._load_files_index()
        self._load_blocks()
        
        logger.info(f"代码管理器初始化完成，已加载 {len(self.files_index)} 个文件，{len(self.code_blocks)} 个代码块")

    def _load_files_index(self):
        """加载文件索引"""
        if self.files_index_file.exists():
            try:
                with open(self.files_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.files_index = {
                        k: CodeFileInfo(**v) for k, v in data.items()
                    }
                logger.info(f"已加载代码文件索引: {len(self.files_index)} 个文件")
            except Exception as e:
                logger.error(f"加载代码文件索引失败: {e}")
                self.files_index = {}
    
    def _save_files_index(self):
        """保存文件索引"""
        try:
            data = {k: asdict(v) for k, v in self.files_index.items()}
            with open(self.files_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存代码文件索引失败: {e}")
    
    def _load_blocks(self):
        """加载代码块"""
        if self.blocks_file.exists():
            try:
                with open(self.blocks_file, 'rb') as f:
                    self.code_blocks = pickle.load(f)
                logger.info(f"已加载代码块: {len(self.code_blocks)} 个块")
            except Exception as e:
                logger.error(f"加载代码块失败: {e}")
                self.code_blocks = {}
    
    def _save_blocks(self):
        """保存代码块"""
        try:
            with open(self.blocks_file, 'wb') as f:
                pickle.dump(self.code_blocks, f)
        except Exception as e:
            logger.error(f"保存代码块失败: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return ""

    def _detect_language(self, file_path: str) -> str:
        """检测编程语言"""
        file_ext = Path(file_path).suffix.lower()
        return self.supported_languages.get(file_ext, 'text')

    def upload_code_file(self, file_path: str, filename: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        上传并处理代码文件
        
        Returns:
            (success, message, file_id)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, f"文件不存在: {file_path}", None
            
            if filename is None:
                filename = file_path.name
            
            # 检测语言
            language = self._detect_language(str(file_path))
            if language == 'text':
                return False, f"不支持的文件类型: {file_path.suffix}", None
            
            # 生成文件ID
            file_id = str(uuid.uuid4())
            
            # 计算文件信息
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(str(file_path))
            
            # 检查是否已存在相同文件
            existing_file = self._find_file_by_hash(file_hash)
            if existing_file:
                return False, f"文件已存在: {existing_file.filename}", existing_file.file_id
            
            # 创建文件信息
            file_info = CodeFileInfo(
                file_id=file_id,
                filename=filename,
                file_path=str(file_path),
                language=language,
                file_size=file_size,
                file_hash=file_hash,
                total_blocks=0,
                upload_time=datetime.now().isoformat()
            )
            
            # 解析代码文件
            try:
                blocks = self._parse_code_file(str(file_path), file_info)
                logger.info(f"代码解析完成，共 {len(blocks)} 个代码块")
                
                # 向量化代码块
                self._vectorize_blocks(blocks)
                
                # 存储到向量数据库
                self._store_blocks(blocks)
                
                # 更新文件信息
                file_info.total_blocks = len(blocks)
                file_info.processed = True
                self.files_index[file_id] = file_info
                
                # 保存
                self._save_files_index()
                self._save_blocks()
                
                logger.success(f"代码文件上传成功: {filename} ({len(blocks)} 个代码块)")
                return True, f"代码文件上传成功，共处理 {len(blocks)} 个代码块", file_id
                
            except Exception as e:
                file_info.error_message = str(e)
                file_info.processed = False
                self.files_index[file_id] = file_info
                self._save_files_index()
                logger.error(f"代码处理失败: {e}")
                return False, f"代码处理失败: {e}", file_id
                
        except Exception as e:
            logger.error(f"代码文件上传失败: {e}")
            return False, f"代码文件上传失败: {e}", None

    def _find_file_by_hash(self, file_hash: str) -> Optional[CodeFileInfo]:
        """根据文件哈希查找文件"""
        for file_info in self.files_index.values():
            if file_info.file_hash == file_hash:
                return file_info
        return None

    def _parse_code_file(self, file_path: str, file_info: CodeFileInfo) -> List[CodeBlock]:
        """解析代码文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        language = file_info.language
        
        # 根据语言选择解析器
        if language == 'python':
            return self._parse_python_file(content, file_info)
        elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
            return self._parse_js_file(content, file_info)
        elif language == 'java':
            return self._parse_java_file(content, file_info)
        elif language in ['cpp', 'c']:
            return self._parse_c_file(content, file_info)
        else:
            # 通用解析器
            return self._parse_generic_file(content, file_info)

    def _parse_python_file(self, content: str, file_info: CodeFileInfo) -> List[CodeBlock]:
        """解析Python文件"""
        blocks = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 函数定义
                    block = self._create_python_function_block(node, lines, file_info)
                    if block:
                        blocks.append(block)
                        
                elif isinstance(node, ast.ClassDef):
                    # 类定义
                    block = self._create_python_class_block(node, lines, file_info)
                    if block:
                        blocks.append(block)
                        
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    # 导入语句
                    block = self._create_python_import_block(node, lines, file_info)
                    if block:
                        blocks.append(block)
                        
        except SyntaxError as e:
            logger.warning(f"Python语法错误，使用通用解析器: {e}")
            return self._parse_generic_file(content, file_info)
        
        # 如果没有找到任何结构，按函数划分
        if not blocks:
            blocks = self._parse_generic_file(content, file_info)
            
        return blocks

    def _create_python_function_block(self, node: ast.FunctionDef, lines: List[str], file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建Python函数代码块"""
        try:
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            
            # 获取函数内容
            content_lines = lines[start_line-1:end_line]
            content = '\n'.join(content_lines)
            
            # 获取docstring
            docstring = None
            if (node.body and isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                docstring = node.body[0].value.value
            
            # 获取函数签名
            signature = f"def {node.name}("
            args = []
            for arg in node.args.args:
                args.append(arg.arg)
            signature += ", ".join(args) + ")"
            
            # 计算复杂度（简单估算）
            complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))])
            
            block_id = f"{file_info.file_id}_func_{node.name}_{start_line}"
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='function',
                name=node.name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=docstring,
                signature=signature,
                complexity=complexity,
                metadata={
                    'args': [arg.arg for arg in node.args.args],
                    'returns': 'unknown',  # 需要进一步分析
                    'decorators': [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                }
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建Python函数块失败: {e}")
            return None

    def _create_python_class_block(self, node: ast.ClassDef, lines: List[str], file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建Python类代码块"""
        try:
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            
            content_lines = lines[start_line-1:end_line]
            content = '\n'.join(content_lines)
            
            # 获取docstring
            docstring = None
            if (node.body and isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                docstring = node.body[0].value.value
            
            # 获取基类
            bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
            
            # 获取方法列表
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            
            block_id = f"{file_info.file_id}_class_{node.name}_{start_line}"
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='class',
                name=node.name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=docstring,
                signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
                complexity=len(methods),
                metadata={
                    'bases': bases,
                    'methods': methods,
                    'decorators': [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]
                }
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建Python类块失败: {e}")
            return None

    def _create_python_import_block(self, node, lines: List[str], file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建Python导入代码块"""
        try:
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            
            content_lines = lines[start_line-1:end_line]
            content = '\n'.join(content_lines)
            
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
                import_type = 'import'
            else:  # ImportFrom
                names = [alias.name for alias in node.names]
                import_type = 'from_import'
                module = node.module or ''
            
            block_id = f"{file_info.file_id}_import_{start_line}"
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='import',
                name=f"import_{start_line}",
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=content.strip(),
                complexity=1,
                metadata={
                    'import_type': import_type,
                    'names': names,
                    'module': module if isinstance(node, ast.ImportFrom) else None
                }
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建Python导入块失败: {e}")
            return None

    def _parse_js_file(self, content: str, file_info: CodeFileInfo) -> List[CodeBlock]:
        """解析JavaScript/TypeScript文件"""
        blocks = []
        lines = content.split('\n')
        
        # 简单的函数识别（正则表达式）
        function_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>)|(\w+)\s*:\s*(?:function|\([^)]*\)\s*=>))'
        class_pattern = r'class\s+(\w+)'
        
        current_line = 0
        for i, line in enumerate(lines):
            func_match = re.search(function_pattern, line)
            class_match = re.search(class_pattern, line)
            
            if func_match:
                func_name = func_match.group(1) or func_match.group(2) or func_match.group(3)
                # 尝试找到函数结束位置
                end_line = self._find_js_block_end(lines, i)
                block_content = '\n'.join(lines[i:end_line+1])
                
                block = self._create_js_function_block(
                    block_content, func_name, i+1, end_line+1, file_info
                )
                if block:
                    blocks.append(block)
                    
            elif class_match:
                class_name = class_match.group(1)
                end_line = self._find_js_block_end(lines, i)
                block_content = '\n'.join(lines[i:end_line+1])
                
                block = self._create_js_class_block(
                    block_content, class_name, i+1, end_line+1, file_info
                )
                if block:
                    blocks.append(block)
        
        # 如果没有找到结构化代码，使用通用解析器
        if not blocks:
            blocks = self._parse_generic_file(content, file_info)
        
        return blocks

    def _parse_java_file(self, content: str, file_info: CodeFileInfo) -> List[CodeBlock]:
        """解析Java文件"""
        blocks = []
        lines = content.split('\n')
        
        # Java类和方法识别
        class_pattern = r'(?:public|private|protected)?\s*class\s+(\w+)'
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*{'
        
        for i, line in enumerate(lines):
            class_match = re.search(class_pattern, line)
            method_match = re.search(method_pattern, line)
            
            if class_match:
                class_name = class_match.group(1)
                end_line = self._find_java_block_end(lines, i)
                block_content = '\n'.join(lines[i:end_line+1])
                
                block = self._create_java_class_block(
                    block_content, class_name, i+1, end_line+1, file_info
                )
                if block:
                    blocks.append(block)
                    
            elif method_match and not class_match:  # 避免重复处理类内方法
                method_name = method_match.group(1)
                end_line = self._find_java_block_end(lines, i)
                block_content = '\n'.join(lines[i:end_line+1])
                
                block = self._create_java_method_block(
                    block_content, method_name, i+1, end_line+1, file_info
                )
                if block:
                    blocks.append(block)
        
        if not blocks:
            blocks = self._parse_generic_file(content, file_info)
        
        return blocks

    def _parse_c_file(self, content: str, file_info: CodeFileInfo) -> List[CodeBlock]:
        """解析C/C++文件"""
        blocks = []
        lines = content.split('\n')
        
        # C/C++函数识别
        function_pattern = r'(?:[\w\s\*]+)\s+(\w+)\s*\([^)]*\)\s*{'
        
        for i, line in enumerate(lines):
            func_match = re.search(function_pattern, line)
            
            if func_match and not line.strip().startswith('//'):
                func_name = func_match.group(1)
                end_line = self._find_c_block_end(lines, i)
                block_content = '\n'.join(lines[i:end_line+1])
                
                block = self._create_c_function_block(
                    block_content, func_name, i+1, end_line+1, file_info
                )
                if block:
                    blocks.append(block)
        
        if not blocks:
            blocks = self._parse_generic_file(content, file_info)
        
        return blocks

    def _find_js_block_end(self, lines: List[str], start: int) -> int:
        """找到JavaScript代码块结束位置"""
        brace_count = 0
        for i in range(start, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and i > start:
                return i
        return len(lines) - 1

    def _find_java_block_end(self, lines: List[str], start: int) -> int:
        """找到Java代码块结束位置"""
        brace_count = 0
        for i in range(start, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and i > start:
                return i
        return len(lines) - 1

    def _find_c_block_end(self, lines: List[str], start: int) -> int:
        """找到C代码块结束位置"""
        brace_count = 0
        for i in range(start, len(lines)):
            line = lines[i]
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and i > start:
                return i
        return len(lines) - 1

    def _create_js_function_block(self, content: str, name: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建JavaScript函数代码块"""
        try:
            block_id = f"{file_info.file_id}_func_{name}_{start_line}"
            
            # 提取签名
            first_line = content.split('\n')[0]
            signature = first_line.strip()
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='function',
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=signature,
                complexity=content.count('\n') // 5 + 1,
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建JS函数块失败: {e}")
            return None

    def _create_js_class_block(self, content: str, name: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建JavaScript类代码块"""
        try:
            block_id = f"{file_info.file_id}_class_{name}_{start_line}"
            
            first_line = content.split('\n')[0]
            signature = first_line.strip()
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='class',
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=signature,
                complexity=content.count('function') + content.count('=>'),
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建JS类块失败: {e}")
            return None

    def _create_java_class_block(self, content: str, name: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建Java类代码块"""
        try:
            block_id = f"{file_info.file_id}_class_{name}_{start_line}"
            
            first_line = content.split('\n')[0]
            signature = first_line.strip()
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='class',
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=signature,
                complexity=content.count('public ') + content.count('private '),
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建Java类块失败: {e}")
            return None

    def _create_java_method_block(self, content: str, name: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建Java方法代码块"""
        try:
            block_id = f"{file_info.file_id}_method_{name}_{start_line}"
            
            first_line = content.split('\n')[0]
            signature = first_line.strip()
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='method',
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=signature,
                complexity=content.count('if ') + content.count('for ') + content.count('while '),
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建Java方法块失败: {e}")
            return None

    def _create_c_function_block(self, content: str, name: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建C函数代码块"""
        try:
            block_id = f"{file_info.file_id}_func_{name}_{start_line}"
            
            first_line = content.split('\n')[0]
            signature = first_line.strip()
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type='function',
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=signature,
                complexity=content.count('if(') + content.count('for(') + content.count('while('),
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建C函数块失败: {e}")
            return None
        """通用文件解析器"""
        blocks = []
        lines = content.split('\n')
        
        # 按照语言特征进行简单分块
        current_block_lines = []
        current_start_line = 1
        
        for i, line in enumerate(lines, 1):
            current_block_lines.append(line)
            
            # 简单的分块逻辑：遇到空行或特定模式就分块
            if (not line.strip() and len(current_block_lines) > 10) or \
               (line.strip().startswith('//') and len(current_block_lines) > 5) or \
               (line.strip().startswith('#') and len(current_block_lines) > 5):
                
                if len(current_block_lines) > 1:
                    block_content = '\n'.join(current_block_lines[:-1])
                    if block_content.strip():
                        block = self._create_generic_block(
                            block_content, current_start_line, i-1, file_info
                        )
                        if block:
                            blocks.append(block)
                
                current_block_lines = [line] if line.strip() else []
                current_start_line = i + 1
        
        # 处理最后一个块
        if current_block_lines:
            block_content = '\n'.join(current_block_lines)
            if block_content.strip():
                block = self._create_generic_block(
                    block_content, current_start_line, len(lines), file_info
                )
                if block:
                    blocks.append(block)
        
        # 如果没有生成任何块，将整个文件作为一个块
        if not blocks:
            block = self._create_generic_block(content, 1, len(lines), file_info)
            if block:
                blocks.append(block)
        
        return blocks

    def _create_generic_block(self, content: str, start_line: int, end_line: int, file_info: CodeFileInfo) -> Optional[CodeBlock]:
        """创建通用代码块"""
        try:
            if not content.strip():
                return None
            
            # 尝试识别块类型
            block_type = 'code'
            name = f"block_{start_line}"
            
            # 简单的类型识别
            if 'function' in content.lower() or 'def ' in content:
                block_type = 'function'
                # 尝试提取函数名
                match = re.search(r'(?:function\s+|def\s+)(\w+)', content)
                if match:
                    name = match.group(1)
                    
            elif 'class' in content.lower():
                block_type = 'class'
                match = re.search(r'class\s+(\w+)', content)
                if match:
                    name = match.group(1)
            
            elif content.strip().startswith(('import', 'from', '#include', 'using')):
                block_type = 'import'
                name = f"import_{start_line}"
            
            elif content.strip().startswith(('//','#', '/*', '"""', "'''")):
                block_type = 'comment'
                name = f"comment_{start_line}"
            
            block_id = f"{file_info.file_id}_{block_type}_{start_line}"
            
            block = CodeBlock(
                block_id=block_id,
                content=content,
                block_type=block_type,
                name=name,
                source_file=file_info.filename,
                source_path=file_info.file_path,
                file_type=Path(file_info.filename).suffix,
                language=file_info.language,
                start_line=start_line,
                end_line=end_line,
                dependencies=[],
                docstring=None,
                signature=None,
                complexity=content.count('\n') // 10 + 1,  # 简单的复杂度估算
                metadata={}
            )
            
            self.code_blocks[block_id] = block
            return block
            
        except Exception as e:
            logger.error(f"创建通用代码块失败: {e}")
            return None

    def _vectorize_blocks(self, blocks: List[CodeBlock]):
        """向量化代码块"""
        if not blocks:
            return
        
        try:
            # 为每个代码块创建描述性文本
            texts = []
            for block in blocks:
                # 组合多种信息用于向量化
                text_parts = []
                
                # 基本信息
                text_parts.append(f"类型: {block.block_type}")
                text_parts.append(f"名称: {block.name}")
                
                # 签名
                if block.signature:
                    text_parts.append(f"签名: {block.signature}")
                
                # 文档字符串
                if block.docstring:
                    text_parts.append(f"文档: {block.docstring}")
                
                # 代码内容（截取部分以避免过长）
                content_preview = block.content[:500] + "..." if len(block.content) > 500 else block.content
                text_parts.append(f"代码: {content_preview}")
                
                # 语言和文件信息
                text_parts.append(f"语言: {block.language}")
                text_parts.append(f"文件: {block.source_file}")
                
                combined_text = " ".join(text_parts)
                texts.append(combined_text)
            
            # 批量向量化
            embeddings = self.embedding_provider.embed_texts(texts)
            
            # 分配向量到代码块
            for block, embedding in zip(blocks, embeddings):
                block.embedding = embedding
                
            logger.info(f"代码块向量化完成: {len(blocks)} 个块")
            
        except Exception as e:
            logger.error(f"代码块向量化失败: {e}")
            raise

    def _store_blocks(self, blocks: List[CodeBlock]):
        """存储代码块到向量数据库"""
        for block in blocks:
            if block.embedding:
                self.vector_store.add_vector(
                    vector_id=block.block_id,
                    vector=block.embedding,
                    metadata={
                        'content': block.content,
                        'block_type': block.block_type,
                        'name': block.name,
                        'source_file': block.source_file,
                        'source_path': block.source_path,
                        'file_type': block.file_type,
                        'language': block.language,
                        'start_line': block.start_line,
                        'end_line': block.end_line,
                        'signature': block.signature,
                        'docstring': block.docstring,
                        'complexity': block.complexity,
                        **block.metadata
                    }
                )

    def search_code(
        self, 
        query: str, 
        top_k: int = 10, 
        language: str = None,
        block_type: str = None
    ) -> List[Dict[str, Any]]:
        """搜索代码"""
        try:
            # 向量化查询
            query_embedding = self.embedding_provider.embed_query(query)
            if not query_embedding:
                return []
            
            # 搜索向量数据库
            results = self.vector_store.search(query_embedding, top_k * 2)
            
            # 过滤结果
            filtered_results = []
            for result in results:
                metadata = result.get('metadata', {})
                
                # 语言过滤
                if language and metadata.get('language', '').lower() != language.lower():
                    continue
                
                # 块类型过滤
                if block_type and metadata.get('block_type', '').lower() != block_type.lower():
                    continue
                
                # 构建结果
                search_result = {
                    'block_id': result.get('vector_id'),
                    'content': metadata.get('content', ''),
                    'block_type': metadata.get('block_type', ''),
                    'name': metadata.get('name', ''),
                    'source_file': metadata.get('source_file', ''),
                    'source_path': metadata.get('source_path', ''),
                    'language': metadata.get('language', ''),
                    'start_line': metadata.get('start_line', 0),
                    'end_line': metadata.get('end_line', 0),
                    'signature': metadata.get('signature', ''),
                    'docstring': metadata.get('docstring', ''),
                    'complexity': metadata.get('complexity', 1),
                    'similarity': result.get('similarity', 0.0),
                    'metadata': metadata
                }
                
                filtered_results.append(search_result)
                
                if len(filtered_results) >= top_k:
                    break
            
            logger.info(f"代码搜索完成: 查询'{query}', 返回 {len(filtered_results)} 个结果")
            return filtered_results
            
        except Exception as e:
            logger.error(f"代码搜索失败: {e}")
            return []

    def get_file_info(self, file_id: str) -> Optional[CodeFileInfo]:
        """获取文件信息"""
        return self.files_index.get(file_id)

    def list_files(self) -> List[CodeFileInfo]:
        """列出所有代码文件"""
        return list(self.files_index.values())

    def list_blocks_by_file(self, file_id: str) -> List[CodeBlock]:
        """列出文件的所有代码块"""
        return [block for block in self.code_blocks.values() 
                if block.block_id.startswith(file_id)]

    def delete_file(self, file_id: str) -> Tuple[bool, str]:
        """删除代码文件"""
        try:
            if file_id not in self.files_index:
                return False, "文件不存在"
            
            file_info = self.files_index[file_id]
            
            # 删除相关的代码块
            blocks_to_delete = [block_id for block_id in self.code_blocks.keys() 
                              if block_id.startswith(file_id)]
            
            for block_id in blocks_to_delete:
                # 从向量数据库删除
                self.vector_store.delete_vector(block_id)
                # 从内存删除
                del self.code_blocks[block_id]
            
            # 删除文件记录
            del self.files_index[file_id]
            
            # 保存
            self._save_files_index()
            self._save_blocks()
            
            logger.info(f"代码文件已删除: {file_info.filename}")
            return True, f"代码文件已删除: {file_info.filename}"
            
        except Exception as e:
            logger.error(f"删除代码文件失败: {e}")
            return False, f"删除代码文件失败: {e}"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_files = len(self.files_index)
        processed_files = sum(1 for file in self.files_index.values() if file.processed)
        total_blocks = len(self.code_blocks)
        
        languages = {}
        block_types = {}
        
        for file_info in self.files_index.values():
            lang = file_info.language
            languages[lang] = languages.get(lang, 0) + 1
        
        for block in self.code_blocks.values():
            block_type = block.block_type
            block_types[block_type] = block_types.get(block_type, 0) + 1
        
        return {
            'total_files': total_files,
            'processed_files': processed_files,
            'total_blocks': total_blocks,
            'languages': languages,
            'block_types': block_types,
            'supported_languages': list(self.supported_languages.values()),
            'embedding_dimension': self.embedding_provider.get_embedding_dimension()
        }