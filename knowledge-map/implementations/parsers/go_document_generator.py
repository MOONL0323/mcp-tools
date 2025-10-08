"""
Go语言文档生成器
负责将提取的Go代码结构转换为结构化文档
"""
import os
from typing import Dict, Any, List
from langchain.schema import Document
from interfaces.code_parser import DocumentGeneratorInterface

class GoDocumentGenerator(DocumentGeneratorInterface):
    """Go语言文档生成器"""
    
    def generate_function_document(self, func_info: Dict[str, Any], file_path: str) -> Document:
        """生成Go函数/方法文档"""
        func_name = func_info['name']
        func_type = "方法" if func_info['is_method'] else "函数"
        
        # 构建签名显示
        signature_display = func_info['signature']
        
        # 构建参数描述
        params_desc = self._format_params(func_info.get('params', []))
        
        # 构建返回值描述
        returns_desc = self._format_returns(func_info.get('returns', []))
        
        # 构建接收者描述（如果是方法）
        receiver_desc = ""
        if func_info['is_method'] and func_info.get('receiver_type'):
            receiver_desc = f"\n**接收者**: {func_info['receiver_type']}"
        
        # 构建注释描述
        comments_desc = ""
        if func_info.get('comments'):
            comments_desc = f"\n### 说明\n{' '.join(func_info['comments'])}"
        
        structured_content = f"""
## {func_type}: {func_name}

**文件**: {os.path.basename(file_path)}
**语言**: Go
**行号**: {func_info.get('start_line', 'unknown')}{receiver_desc}
{params_desc}
{returns_desc}
{comments_desc}

### 签名
```go
{signature_display}
```

### 实现
```go
{func_info.get('body', '// 函数体未提取')}
```
""".strip()
        
        return Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': func_info['type'],
                'language': 'go',
                'name': func_name,
                'signature': func_info['signature'],
                'is_method': func_info['is_method'],
                'receiver_type': func_info.get('receiver_type'),
                'params': func_info.get('params', []),
                'returns': func_info.get('returns', []),
                'comments': func_info.get('comments', []),
                'start_line': func_info.get('start_line')
            }
        )
    
    def generate_class_document(self, struct_info: Dict[str, Any], file_path: str) -> Document:
        """生成Go结构体文档"""
        struct_name = struct_info['name']
        
        # 构建字段描述
        fields_desc = self._format_struct_fields(struct_info.get('fields', []))
        
        # 构建嵌入类型描述
        embedded_desc = ""
        if struct_info.get('embedded_types'):
            embedded_list = '\n'.join([f"- {t}" for t in struct_info['embedded_types']])
            embedded_desc = f"\n### 嵌入类型\n{embedded_list}"
        
        # 构建注释描述
        comments_desc = ""
        if struct_info.get('comments'):
            comments_desc = f"\n### 说明\n{' '.join(struct_info['comments'])}"
        
        structured_content = f"""
## 结构体: {struct_name}

**文件**: {os.path.basename(file_path)}
**语言**: Go
**行号**: {struct_info.get('start_line', 'unknown')}
{comments_desc}
{fields_desc}
{embedded_desc}

### 完整定义
```go
type {struct_name} struct {{
{struct_info.get('raw_body', '')}
}}
```
""".strip()
        
        return Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'struct',
                'language': 'go',
                'name': struct_name,
                'fields': struct_info.get('fields', []),
                'embedded_types': struct_info.get('embedded_types', []),
                'comments': struct_info.get('comments', []),
                'start_line': struct_info.get('start_line')
            }
        )
    
    def generate_interface_document(self, interface_info: Dict[str, Any], file_path: str) -> Document:
        """生成Go接口文档"""
        interface_name = interface_info['name']
        
        # 构建方法描述
        methods_desc = self._format_interface_methods(interface_info.get('methods', []))
        
        # 构建嵌入接口描述
        embedded_desc = ""
        if interface_info.get('embedded_interfaces'):
            embedded_list = '\n'.join([f"- {i}" for i in interface_info['embedded_interfaces']])
            embedded_desc = f"\n### 嵌入接口\n{embedded_list}"
        
        # 构建注释描述
        comments_desc = ""
        if interface_info.get('comments'):
            comments_desc = f"\n### 说明\n{' '.join(interface_info['comments'])}"
        
        structured_content = f"""
## 接口: {interface_name}

**文件**: {os.path.basename(file_path)}
**语言**: Go
**行号**: {interface_info.get('start_line', 'unknown')}
{comments_desc}
{methods_desc}
{embedded_desc}

### 完整定义
```go
type {interface_name} interface {{
{interface_info.get('raw_body', '')}
}}
```
""".strip()
        
        return Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'interface',
                'language': 'go',
                'name': interface_name,
                'methods': interface_info.get('methods', []),
                'embedded_interfaces': interface_info.get('embedded_interfaces', []),
                'comments': interface_info.get('comments', []),
                'start_line': interface_info.get('start_line')
            }
        )
    
    def generate_file_overview_document(self, metadata: Dict[str, Any], file_path: str) -> Document:
        """生成Go文件概览文档"""
        file_name = os.path.basename(file_path)
        
        # 构建导入包描述
        imports_desc = ""
        if metadata.get('imports'):
            import_list = '\n'.join([f'import "{imp}"' for imp in metadata['imports'][:10]])
            if len(metadata['imports']) > 10:
                import_list += f"\n// ... 还有{len(metadata['imports'])-10}个包"
            imports_desc = f"\n### 导入的包\n```go\n{import_list}\n```"
        
        # 构建文件注释描述
        file_comments_desc = ""
        if metadata.get('file_comments'):
            file_comments_desc = f"\n### 文件说明\n{' '.join(metadata['file_comments'])}"
        
        # 构建统计信息
        stats = metadata.get('stats', {})
        stats_desc = f"""
### 统计信息
- 📦 包名: {metadata.get('package', 'unknown')}
- 📥 导入包: {len(metadata.get('imports', []))}个
- 🏗️ 结构体: {stats.get('struct_count', 0)}个
- 🔌 接口: {stats.get('interface_count', 0)}个
- ⚙️ 函数/方法: {stats.get('function_count', 0)}个
- 📄 文件大小: {stats.get('file_size', 0)} 字符"""
        
        # 构建文件内容预览
        content_preview = ""
        if metadata.get('content_preview'):
            content_preview = f"\n### 文件结构预览\n```go\n{metadata['content_preview']}\n```"
        
        structured_content = f"""
## Go文件: {file_name}

**路径**: {file_path}
**包名**: {metadata.get('package', 'unknown')}
**语言**: Go
{file_comments_desc}
{stats_desc}
{imports_desc}
{content_preview}
""".strip()
        
        return Document(
            page_content=structured_content,
            metadata={
                'source': file_path,
                'type': 'file_overview',
                'language': 'go',
                'name': file_name,
                'package': metadata.get('package'),
                'imports': metadata.get('imports', []),
                'file_comments': metadata.get('file_comments', []),
                'stats': stats
            }
        )
    
    def _format_params(self, params: List[Dict[str, str]]) -> str:
        """格式化参数描述"""
        if not params:
            return "\n**参数**: 无参数"
        
        param_lines = []
        for param in params:
            name = param.get('name', '匿名')
            param_type = param.get('type', 'unknown')
            param_lines.append(f"- `{name}` {param_type}")
        
        return f"\n**参数**:\n{chr(10).join(param_lines)}"
    
    def _format_returns(self, returns: List[str]) -> str:
        """格式化返回值描述"""
        if not returns:
            return "\n**返回值**: 无返回值"
        
        if len(returns) == 1:
            return f"\n**返回值**: `{returns[0]}`"
        else:
            return_lines = [f"- `{ret}`" for ret in returns]
            return f"\n**返回值**:\n{chr(10).join(return_lines)}"
    
    def _format_struct_fields(self, fields: List[Dict[str, Any]]) -> str:
        """格式化结构体字段"""
        if not fields:
            return "\n### 字段\n无字段"
        
        field_lines = []
        for field in fields:
            name = field.get('name', 'unknown')
            field_type = field.get('type', 'unknown')
            tag = field.get('tag', '')
            comment = field.get('comment', '')
            
            field_desc = f"- **{name}** `{field_type}`"
            if tag:
                field_desc += f" `{tag}`"
            if comment:
                field_desc += f" // {comment}"
            
            field_lines.append(field_desc)
        
        return f"\n### 字段\n{chr(10).join(field_lines)}"
    
    def _format_interface_methods(self, methods: List[Dict[str, Any]]) -> str:
        """格式化接口方法"""
        if not methods:
            return "\n### 方法\n无方法"
        
        method_lines = []
        for method in methods:
            name = method.get('name', 'unknown')
            params = method.get('params', [])
            returns = method.get('returns', [])
            
            method_desc = f"- **{name}**"
            if params:
                method_desc += f"({', '.join(params)})"
            else:
                method_desc += "()"
            
            if returns:
                if len(returns) == 1:
                    method_desc += f" {returns[0]}"
                else:
                    method_desc += f" ({', '.join(returns)})"
            
            method_lines.append(method_desc)
        
        return f"\n### 方法\n{chr(10).join(method_lines)}"