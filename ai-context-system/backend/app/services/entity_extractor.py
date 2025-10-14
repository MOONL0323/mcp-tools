"""
实体提取服务 - 从代码和文档中提取实体
支持Python代码解析和文本关键词提取
"""
import ast
import re
from typing import List, Dict, Set
import structlog

logger = structlog.get_logger()


class EntityExtractor:
    """实体提取器"""
    
    def extract_from_python_code(self, code: str) -> Dict[str, List[Dict]]:
        """
        从Python代码提取实体
        
        Returns:
            {
                "classes": [{"name": "...", "line": ..., "docstring": "..."}],
                "functions": [{"name": "...", "line": ..., "params": [...]}],
                "imports": [{"module": "...", "names": [...]}],
                "variables": [{"name": "...", "line": ...}]
            }
        """
        try:
            tree = ast.parse(code)
            entities = {
                "classes": [],
                "functions": [],
                "imports": [],
                "variables": []
            }
            
            for node in ast.walk(tree):
                # 类定义
                if isinstance(node, ast.ClassDef):
                    entities["classes"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node) or "",
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        "bases": [self._get_name(base) for base in node.bases]
                    })
                
                # 函数定义
                elif isinstance(node, ast.FunctionDef):
                    entities["functions"].append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node) or "",
                        "params": [arg.arg for arg in node.args.args],
                        "returns": self._get_name(node.returns) if node.returns else None
                    })
                
                # Import语句
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        entities["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                
                # From Import语句
                elif isinstance(node, ast.ImportFrom):
                    entities["imports"].append({
                        "module": node.module or "",
                        "names": [alias.name for alias in node.names],
                        "line": node.lineno
                    })
                
                # 全局变量赋值
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            entities["variables"].append({
                                "name": target.id,
                                "line": node.lineno
                            })
            
            logger.info(
                "Python代码实体提取完成",
                classes=len(entities["classes"]),
                functions=len(entities["functions"]),
                imports=len(entities["imports"]),
                variables=len(entities["variables"])
            )
            
            return entities
            
        except Exception as e:
            logger.error(f"Python代码解析失败", error=str(e))
            return {"classes": [], "functions": [], "imports": [], "variables": []}
    
    def extract_from_text(self, text: str, top_k: int = 20) -> List[Dict]:
        """
        从文本提取关键词实体（基于TF-IDF）
        
        Returns:
            [{"term": "...", "score": 0.xx, "frequency": n}]
        """
        try:
            # 分词（简单版：按空格和标点分割）
            words = re.findall(r'\b[a-zA-Z_]\w+\b', text.lower())
            
            # 过滤停用词
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                         'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                         'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                         'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
            
            words = [w for w in words if w not in stop_words and len(w) > 2]
            
            # 计算词频
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 简单评分（词频 * 长度）
            scored_terms = []
            for word, freq in word_freq.items():
                score = freq * len(word) / 10.0  # 归一化
                scored_terms.append({
                    "term": word,
                    "score": round(score, 3),
                    "frequency": freq
                })
            
            # 排序并取top_k
            scored_terms.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(
                "文本实体提取完成",
                total_words=len(words),
                unique_terms=len(word_freq),
                top_k=min(top_k, len(scored_terms))
            )
            
            return scored_terms[:top_k]
            
        except Exception as e:
            logger.error(f"文本实体提取失败", error=str(e))
            return []
    
    def extract_relationships(self, entities: Dict) -> List[Dict]:
        """
        从实体中提取关系
        
        Returns:
            [{"source": "...", "target": "...", "relation": "...", "type": "..."}]
        """
        relationships = []
        
        try:
            # 类继承关系
            for cls in entities.get("classes", []):
                for base in cls.get("bases", []):
                    if base:
                        relationships.append({
                            "source": cls["name"],
                            "target": base,
                            "relation": "inherits_from",
                            "type": "class_inheritance"
                        })
            
            # 类-方法关系
            for cls in entities.get("classes", []):
                for method in cls.get("methods", []):
                    relationships.append({
                        "source": cls["name"],
                        "target": method,
                        "relation": "has_method",
                        "type": "class_method"
                    })
            
            # Import关系
            for imp in entities.get("imports", []):
                module = imp.get("module", "")
                if module:
                    for name in imp.get("names", [module]):
                        relationships.append({
                            "source": "current_module",
                            "target": name,
                            "relation": "imports",
                            "type": "import",
                            "from_module": module
                        })
            
            logger.info(f"提取关系完成", count=len(relationships))
            
            return relationships
            
        except Exception as e:
            logger.error(f"关系提取失败", error=str(e))
            return []
    
    @staticmethod
    def _get_name(node):
        """获取AST节点名称"""
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{EntityExtractor._get_name(node.value)}.{node.attr}"
        return str(node)


# 全局单例
_entity_extractor = None


def get_entity_extractor() -> EntityExtractor:
    """获取实体提取器单例"""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
