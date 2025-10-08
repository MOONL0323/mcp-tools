"""
Go语言代码结构提取器
专门负责从Go代码中提取各种结构信息
"""
import re
import os
from typing import List, Dict, Any, Optional
from interfaces.code_parser import CodeStructureExtractorInterface

class GoStructureExtractor(CodeStructureExtractorInterface):
    """Go语言结构提取器"""
    
    def extract_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取Go函数和方法"""
        functions = []
        
        # 匹配函数定义 (包括方法)
        # func (receiver) name(params) (returns) {
        function_pattern = r'func\s*(?:\([^)]*\))?\s*(\w+)\s*\([^)]*\)(?:\s*[^{]*?)?\s*\{'
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            start_pos = match.start()
            
            # 获取完整的函数签名
            func_start = content.rfind('\n', 0, start_pos) + 1
            brace_pos = content.find('{', start_pos)
            signature = content[func_start:brace_pos].strip()
            
            # 提取函数体 (限制长度)
            body = self._extract_function_body(content, brace_pos)
            
            # 提取注释
            comments = self.extract_comments(content, func_start)
            
            # 判断是否为方法
            is_method = '(' in signature and signature.index('(') < signature.index(func_name)
            
            # 提取接收者类型 (如果是方法)
            receiver_type = None
            if is_method:
                receiver_match = re.search(r'func\s*\(\s*\w*\s*\*?(\w+)\s*\)', signature)
                if receiver_match:
                    receiver_type = receiver_match.group(1)
            
            # 提取参数
            params = self._extract_function_params(signature)
            
            # 提取返回类型
            returns = self._extract_function_returns(signature)
            
            functions.append({
                'name': func_name,
                'signature': signature,
                'body': body,
                'comments': comments,
                'is_method': is_method,
                'receiver_type': receiver_type,
                'params': params,
                'returns': returns,
                'start_line': content[:func_start].count('\n') + 1,
                'type': 'method' if is_method else 'function'
            })
        
        return functions
    
    def extract_classes_or_structs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取Go结构体"""
        structs = []
        
        # 匹配结构体定义
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]*)\}'
        
        for match in re.finditer(struct_pattern, content, re.DOTALL):
            struct_name = match.group(1)
            struct_body = match.group(2)
            start_pos = match.start()
            
            # 提取字段
            fields = self._extract_struct_fields(struct_body)
            
            # 提取注释
            lines_before_start = content[:start_pos].rfind('\n')
            comments = self.extract_comments(content, lines_before_start)
            
            # 提取嵌入类型
            embedded_types = self._extract_embedded_types(struct_body)
            
            structs.append({
                'name': struct_name,
                'fields': fields,
                'embedded_types': embedded_types,
                'comments': comments,
                'raw_body': struct_body.strip(),
                'start_line': content[:start_pos].count('\n') + 1,
                'type': 'struct'
            })
        
        return structs
    
    def extract_interfaces(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取Go接口"""
        interfaces = []
        
        # 匹配接口定义
        interface_pattern = r'type\s+(\w+)\s+interface\s*\{([^}]*)\}'
        
        for match in re.finditer(interface_pattern, content, re.DOTALL):
            interface_name = match.group(1)
            interface_body = match.group(2)
            start_pos = match.start()
            
            # 提取方法
            methods = self._extract_interface_methods(interface_body)
            
            # 提取注释
            lines_before_start = content[:start_pos].rfind('\n')
            comments = self.extract_comments(content, lines_before_start)
            
            # 提取嵌入接口
            embedded_interfaces = self._extract_embedded_interfaces(interface_body)
            
            interfaces.append({
                'name': interface_name,
                'methods': methods,
                'embedded_interfaces': embedded_interfaces,
                'comments': comments,
                'raw_body': interface_body.strip(),
                'start_line': content[:start_pos].count('\n') + 1,
                'type': 'interface'
            })
        
        return interfaces
    
    def extract_imports(self, content: str) -> List[str]:
        """提取Go imports"""
        imports = []
        
        # 单行import
        single_imports = re.findall(r'import\s+"([^"]+)"', content)
        imports.extend(single_imports)
        
        # 多行import
        import_block_match = re.search(r'import\s*\(\s*(.*?)\s*\)', content, re.DOTALL)
        if import_block_match:
            import_lines = import_block_match.group(1).strip().split('\n')
            for line in import_lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    # 提取引号中的包名
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        package_path = match.group(1)
                        # 检查是否有别名
                        alias_match = re.search(r'^(\w+)\s+"', line.strip())
                        if alias_match:
                            alias = alias_match.group(1)
                            imports.append(f"{alias} \"{package_path}\"")
                        else:
                            imports.append(package_path)
        
        return imports
    
    def extract_comments(self, content: str, position: int) -> List[str]:
        """提取特定位置之前的注释"""
        if position <= 0:
            return []
        
        lines_before = content[:position].split('\n')
        comments = []
        
        # 从位置向前查找注释，直到遇到非注释行
        for line in reversed(lines_before[-10:]):  # 最多查找前10行
            line = line.strip()
            if line.startswith('//'):
                comments.insert(0, line[2:].strip())
            elif line.startswith('/*') and line.endswith('*/'):
                # 单行块注释
                comments.insert(0, line[2:-2].strip())
            elif line:
                # 遇到非空的非注释行，停止
                break
        
        return comments
    
    def _extract_function_body(self, content: str, brace_pos: int) -> str:
        """提取函数体"""
        lines = content[brace_pos:].split('\n')
        body_lines = []
        brace_count = 0
        
        for i, line in enumerate(lines):
            if i > 50:  # 限制长度
                body_lines.append('    // ... 函数体较长，已省略')
                break
            
            body_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            if brace_count <= 0 and i > 0:
                break
        
        return '\n'.join(body_lines)
    
    def _extract_function_params(self, signature: str) -> List[Dict[str, str]]:
        """提取函数参数"""
        params = []
        
        # 查找参数部分
        param_match = re.search(r'func\s*(?:\([^)]*\))?\s*\w+\s*\(([^)]*)\)', signature)
        if not param_match:
            return params
        
        param_str = param_match.group(1).strip()
        if not param_str:
            return params
        
        # 简单解析参数（这里可以进一步完善）
        param_parts = param_str.split(',')
        for part in param_parts:
            part = part.strip()
            if part:
                # 尝试分离参数名和类型
                words = part.split()
                if len(words) >= 2:
                    param_name = words[0]
                    param_type = ' '.join(words[1:])
                    params.append({'name': param_name, 'type': param_type})
                else:
                    params.append({'name': '', 'type': part})
        
        return params
    
    def _extract_function_returns(self, signature: str) -> List[str]:
        """提取函数返回类型"""
        returns = []
        
        # 查找返回类型部分
        # 匹配 ) 后面的内容，直到 {
        return_match = re.search(r'\)\s*([^{]*)\s*\{', signature)
        if not return_match:
            return returns
        
        return_str = return_match.group(1).strip()
        if not return_str:
            return returns
        
        # 处理多返回值 (type1, type2) 或单返回值 type
        if return_str.startswith('(') and return_str.endswith(')'):
            # 多返回值
            return_str = return_str[1:-1]
            returns = [r.strip() for r in return_str.split(',') if r.strip()]
        else:
            # 单返回值
            returns = [return_str]
        
        return returns
    
    def _extract_struct_fields(self, struct_body: str) -> List[Dict[str, Any]]:
        """提取结构体字段"""
        fields = []
        
        for line in struct_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 跳过嵌入类型（没有字段名）
            if not ' ' in line:
                continue
            
            # 解析字段
            parts = line.split()
            if len(parts) >= 2:
                field_name = parts[0]
                field_type = parts[1]
                
                # 提取标签
                tag = ''
                tag_match = re.search(r'`([^`]*)`', line)
                if tag_match:
                    tag = tag_match.group(1)
                
                # 提取行内注释
                comment = ''
                comment_match = re.search(r'//\s*(.*)$', line)
                if comment_match:
                    comment = comment_match.group(1).strip()
                
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'tag': tag,
                    'comment': comment
                })
        
        return fields
    
    def _extract_embedded_types(self, struct_body: str) -> List[str]:
        """提取嵌入类型"""
        embedded = []
        
        for line in struct_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 嵌入类型没有字段名，只有类型
            if ' ' not in line and not line.startswith('*'):
                embedded.append(line)
            elif line.startswith('*') and ' ' not in line[1:]:
                embedded.append(line)
        
        return embedded
    
    def _extract_interface_methods(self, interface_body: str) -> List[Dict[str, Any]]:
        """提取接口方法"""
        methods = []
        
        for line in interface_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 跳过嵌入接口
            if '(' not in line:
                continue
            
            # 解析方法签名
            method_match = re.match(r'(\w+)\s*\(([^)]*)\)(?:\s*(.*))?', line)
            if method_match:
                method_name = method_match.group(1)
                params_str = method_match.group(2).strip()
                returns_str = method_match.group(3).strip() if method_match.group(3) else ''
                
                # 解析参数
                params = []
                if params_str:
                    param_parts = params_str.split(',')
                    for part in param_parts:
                        part = part.strip()
                        if part:
                            params.append(part)
                
                # 解析返回类型
                returns = []
                if returns_str:
                    if returns_str.startswith('(') and returns_str.endswith(')'):
                        returns_str = returns_str[1:-1]
                        returns = [r.strip() for r in returns_str.split(',') if r.strip()]
                    else:
                        returns = [returns_str]
                
                methods.append({
                    'name': method_name,
                    'params': params,
                    'returns': returns,
                    'signature': line
                })
        
        return methods
    
    def _extract_embedded_interfaces(self, interface_body: str) -> List[str]:
        """提取嵌入接口"""
        embedded = []
        
        for line in interface_body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 嵌入接口没有参数括号
            if '(' not in line:
                embedded.append(line)
        
        return embedded