"""
Go语言代码解析器
整合结构提取器和文档生成器，提供完整的Go代码解析功能
"""
import os
import re
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from interfaces.code_parser import CodeParserInterface
from implementations.parsers.go_structure_extractor import GoStructureExtractor
from implementations.parsers.go_document_generator import GoDocumentGenerator

class GoCodeParser(CodeParserInterface):
    """Go语言代码解析器"""
    
    def __init__(self):
        self.extractor = GoStructureExtractor()
        self.generator = GoDocumentGenerator()
        self.supported_exts = ['.go', '.mod', '.sum']
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_exts
    
    def parse_file(self, file_path: str) -> List[Document]:
        """解析Go代码文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.go':
            return self._parse_go_file(file_path)
        elif file_ext == '.mod':
            return self._parse_go_mod(file_path)
        elif file_ext == '.sum':
            return self._parse_go_sum(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
    
    def extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """提取Go文件元数据"""
        metadata = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': len(content)
        }
        
        # 提取包名
        package_match = re.search(r'^package\s+(\w+)', content, re.MULTILINE)
        metadata['package'] = package_match.group(1) if package_match else 'unknown'
        
        # 提取文件级注释
        metadata['file_comments'] = self._extract_file_comments(content)
        
        # 提取导入
        metadata['imports'] = self.extractor.extract_imports(content)
        
        # 生成内容预览
        metadata['content_preview'] = self._generate_content_preview(content)
        
        return metadata
    
    def _parse_go_file(self, file_path: str) -> List[Document]:
        """解析.go文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        documents = []
        
        # 提取文件元数据
        metadata = self.extract_metadata(content, file_path)
        
        # 提取结构体
        structs = self.extractor.extract_classes_or_structs(content, file_path)
        for struct in structs:
            doc = self.generator.generate_class_document(struct, file_path)
            documents.append(doc)
        
        # 提取接口
        interfaces = self.extractor.extract_interfaces(content, file_path)
        for interface in interfaces:
            doc = self.generator.generate_interface_document(interface, file_path)
            documents.append(doc)
        
        # 提取函数
        functions = self.extractor.extract_functions(content, file_path)
        for function in functions:
            doc = self.generator.generate_function_document(function, file_path)
            documents.append(doc)
        
        # 添加统计信息到元数据
        metadata['stats'] = {
            'struct_count': len(structs),
            'interface_count': len(interfaces),
            'function_count': len(functions),
            'file_size': len(content)
        }
        
        # 生成文件概览文档
        overview_doc = self.generator.generate_file_overview_document(metadata, file_path)
        documents.insert(0, overview_doc)
        
        # 如果没有提取到任何结构，至少返回文件概览
        if len(documents) == 1:  # 只有概览文档
            # 创建一个基本的文件内容文档
            basic_doc = self._create_basic_file_document(content, file_path)
            documents.append(basic_doc)
        
        return documents
    
    def _parse_go_mod(self, file_path: str) -> List[Document]:
        """解析go.mod文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取模块信息
        module_match = re.search(r'module\s+([^\s\n]+)', content)
        module_name = module_match.group(1) if module_match else "unknown"
        
        # 提取Go版本
        go_version_match = re.search(r'go\s+([\d.]+)', content)
        go_version = go_version_match.group(1) if go_version_match else "unknown"
        
        # 提取依赖
        require_matches = re.findall(r'require\s+([^\s]+)\s+([^\s\n]+)', content)
        
        # 提取replace指令
        replace_matches = re.findall(r'replace\s+([^\s]+)\s+=>\s+([^\s\n]+)', content)
        
        structured_content = f"""
## Go模块配置: go.mod

**文件**: {os.path.basename(file_path)}
**模块名**: {module_name}
**Go版本**: {go_version}

### 模块信息
- **模块路径**: {module_name}
- **Go版本要求**: {go_version}
- **依赖包数量**: {len(require_matches)}个
- **替换指令**: {len(replace_matches)}个

### 依赖包
```go
{chr(10).join([f"{pkg} {ver}" for pkg, ver in require_matches[:20]])}
{f"... 还有{len(require_matches)-20}个依赖" if len(require_matches) > 20 else ""}
```

{f'''### 替换指令
```go
{chr(10).join([f"{old} => {new}" for old, new in replace_matches])}
```''' if replace_matches else ""}

### 完整内容
```go
{content}
```
""".strip()
        
        return [Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'go_mod',
                'language': 'go',
                'name': 'go.mod',
                'module': module_name,
                'go_version': go_version,
                'dependencies': require_matches,
                'replaces': replace_matches
            }
        )]
    
    def _parse_go_sum(self, file_path: str) -> List[Document]:
        """解析go.sum文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        # 提取模块信息
        modules = set()
        for line in lines:
            parts = line.split(' ')
            if len(parts) >= 2:
                module_version = parts[0]
                module_name = module_version.split(' ')[0]
                modules.add(module_name)
        
        structured_content = f"""
## Go模块校验: go.sum

**文件**: {os.path.basename(file_path)}
**校验记录数**: {len(lines)}
**涉及模块数**: {len(modules)}

### 模块校验信息
- **校验文件总数**: {len(lines)}条记录
- **涉及模块数**: {len(modules)}个模块
- **文件作用**: 确保依赖包的完整性和一致性

### 主要模块 (前10个)
```
{chr(10).join(sorted(list(modules))[:10])}
{f"... 还有{len(modules)-10}个模块" if len(modules) > 10 else ""}
```

### 校验记录预览 (前5条)
```
{chr(10).join(lines[:5])}
{f"... 还有{len(lines)-5}条记录" if len(lines) > 5 else ""}
```
""".strip()
        
        return [Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'go_sum',
                'language': 'go',
                'name': 'go.sum',
                'checksum_count': len(lines),
                'module_count': len(modules),
                'modules': list(modules)
            }
        )]
    
    def _extract_file_comments(self, content: str) -> List[str]:
        """提取文件级注释"""
        lines = content.split('\n')
        file_comments = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('//'):
                file_comments.append(line[2:].strip())
            elif line.startswith('package'):
                break
            elif line and not line.startswith('/*'):
                # 遇到非注释的非空行，停止
                break
        
        return file_comments
    
    def _generate_content_preview(self, content: str) -> str:
        """生成内容预览"""
        lines = content.split('\n')
        preview_lines = []
        
        # 显示包声明和前几个import
        for i, line in enumerate(lines):
            if i >= 30:  # 限制预览长度
                preview_lines.append("// ... 内容较长，已省略")
                break
            preview_lines.append(line)
        
        return '\n'.join(preview_lines)
    
    def _create_basic_file_document(self, content: str, file_path: str) -> Document:
        """创建基本文件文档（当没有提取到结构时使用）"""
        file_name = os.path.basename(file_path)
        preview_content = content[:1500] + ('...' if len(content) > 1500 else '')
        
        structured_content = f"""
## Go文件内容: {file_name}

**文件**: {file_name}
**路径**: {file_path}
**大小**: {len(content)} 字符

### 文件内容
```go
{preview_content}
```
""".strip()
        
        return Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'file_content',
                'language': 'go',
                'name': file_name,
                'size': len(content)
            }
        )