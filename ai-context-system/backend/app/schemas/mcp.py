"""
MCP相关的数据模型和Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class SearchType(str, Enum):
    """搜索类型枚举"""
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"

class MCPSearchRequest(BaseModel):
    """MCP搜索请求模型"""
    query: str = Field(..., description="搜索查询文本")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="搜索类型")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="返回结果数量限制")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="搜索过滤器")
    include_metadata: bool = Field(default=True, description="是否包含元数据")

class MCPSearchResult(BaseModel):
    """搜索结果项"""
    id: str = Field(..., description="结果唯一标识")
    title: str = Field(..., description="结果标题")
    content: str = Field(..., description="结果内容")
    description: Optional[str] = Field(None, description="结果描述")
    file_path: Optional[str] = Field(None, description="文件路径")
    score: float = Field(..., ge=0.0, le=1.0, description="相关度分数")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

class MCPSearchResponse(BaseModel):
    """MCP搜索响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: List[MCPSearchResult] = Field(..., description="搜索结果列表")
    total: int = Field(..., description="结果总数")
    query_analysis: Optional[Dict[str, Any]] = Field(None, description="查询分析信息")
    error: Optional[str] = Field(None, description="错误信息")

class MCPGraphQueryRequest(BaseModel):
    """知识图谱查询请求"""
    entity: str = Field(..., description="要查询的实体名称")
    relation_type: Optional[str] = Field(None, description="关系类型过滤")
    depth: Optional[int] = Field(default=2, ge=1, le=5, description="查询深度")
    include_examples: bool = Field(default=True, description="是否包含使用示例")

class MCPEntityInfo(BaseModel):
    """实体信息"""
    id: str = Field(..., description="实体ID")
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    properties: Dict[str, Any] = Field(..., description="实体属性")
    description: Optional[str] = Field(None, description="实体描述")

class MCPRelationship(BaseModel):
    """关系信息"""
    id: str = Field(..., description="关系ID")
    source: str = Field(..., description="源实体")
    target: str = Field(..., description="目标实体")
    relation_type: str = Field(..., description="关系类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")

class MCPUsageExample(BaseModel):
    """使用示例"""
    context: str = Field(..., description="使用上下文")
    code: str = Field(..., description="代码示例")
    language: str = Field(..., description="编程语言")
    explanation: Optional[str] = Field(None, description="示例说明")

class MCPGraphQueryResponse(BaseModel):
    """知识图谱查询响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Dict[str, Any] = Field(..., description="查询结果数据")
    error: Optional[str] = Field(None, description="错误信息")

class MCPCodingStandardsRequest(BaseModel):
    """编码规范请求"""
    language: str = Field(..., description="编程语言")
    category: Optional[str] = Field(None, description="规范类别")
    team: Optional[str] = Field(None, description="团队标识")
    project: Optional[str] = Field(None, description="项目标识")

class MCPNamingConventions(BaseModel):
    """命名规范"""
    variables: str = Field(..., description="变量命名规范")
    functions: str = Field(..., description="函数命名规范")
    classes: str = Field(..., description="类命名规范")
    constants: str = Field(..., description="常量命名规范")
    files: Optional[str] = Field(None, description="文件命名规范")

class MCPCodeStructure(BaseModel):
    """代码结构规范"""
    indentation: str = Field(..., description="缩进规范")
    line_length: str = Field(..., description="行长度限制")
    imports: str = Field(..., description="导入语句规范")
    comments: str = Field(..., description="注释规范")

class MCPToolInfo(BaseModel):
    """工具信息"""
    formatters: List[str] = Field(..., description="代码格式化工具")
    linters: List[str] = Field(..., description="代码检查工具")
    test_frameworks: List[str] = Field(..., description="测试框架")

class MCPCodingStandardsData(BaseModel):
    """编码规范数据"""
    language: str = Field(..., description="编程语言")
    naming_conventions: MCPNamingConventions = Field(..., description="命名规范")
    code_structure: MCPCodeStructure = Field(..., description="代码结构规范")
    best_practices: List[str] = Field(..., description="最佳实践列表")
    code_templates: Dict[str, str] = Field(..., description="代码模板")
    linting_rules: Dict[str, Any] = Field(..., description="代码检查规则")
    testing_guidelines: List[str] = Field(..., description="测试指导原则")
    tools: MCPToolInfo = Field(..., description="推荐工具")

class MCPCodingStandardsResponse(BaseModel):
    """编码规范响应"""
    success: bool = Field(..., description="请求是否成功")
    data: MCPCodingStandardsData = Field(..., description="编码规范数据")
    error: Optional[str] = Field(None, description="错误信息")

class MCPKnowledgeBaseStats(BaseModel):
    """知识库统计信息"""
    total_documents: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="文档块总数")
    total_entities: int = Field(..., description="实体总数")
    total_relations: int = Field(..., description="关系总数")
    languages: List[str] = Field(..., description="支持的编程语言")
    teams: List[str] = Field(..., description="团队列表")
    projects: List[str] = Field(..., description="项目列表")
    last_updated: str = Field(..., description="最后更新时间")

class MCPKnowledgeBaseStatsResponse(BaseModel):
    """知识库统计响应"""
    success: bool = Field(..., description="请求是否成功")
    data: MCPKnowledgeBaseStats = Field(..., description="统计数据")
    error: Optional[str] = Field(None, description="错误信息")

# 通用响应模型
class MCPBaseResponse(BaseModel):
    """MCP基础响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")

class MCPErrorResponse(MCPBaseResponse):
    """MCP错误响应模型"""
    error_code: str = Field(..., description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

# 扩展模型 - 设计文档相关
class MCPDesignDocRequest(BaseModel):
    """设计文档请求"""
    topic: str = Field(..., description="设计主题")
    component: Optional[str] = Field(None, description="组件名称")
    team: Optional[str] = Field(None, description="团队标识")
    doc_type: Optional[str] = Field(None, description="文档类型")

class MCPDesignDocument(BaseModel):
    """设计文档"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    document_type: str = Field(..., description="文档类型")
    team: Optional[str] = Field(None, description="所属团队")
    project: Optional[str] = Field(None, description="所属项目")
    tags: List[str] = Field(default=[], description="文档标签")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

class MCPDesignDocResponse(BaseModel):
    """设计文档响应"""
    success: bool = Field(..., description="请求是否成功")
    data: List[MCPDesignDocument] = Field(..., description="设计文档列表")
    total: int = Field(..., description="文档总数")
    error: Optional[str] = Field(None, description="错误信息")

# 代码示例相关模型
class MCPCodeExample(BaseModel):
    """代码示例"""
    id: str = Field(..., description="示例ID")
    title: str = Field(..., description="示例标题")
    description: str = Field(..., description="示例描述")
    code: str = Field(..., description="代码内容")
    language: str = Field(..., description="编程语言")
    tags: List[str] = Field(default=[], description="标签")
    difficulty: Optional[str] = Field(None, description="难度级别")
    use_case: Optional[str] = Field(None, description="使用场景")

class MCPCodeExampleRequest(BaseModel):
    """代码示例请求"""
    query: str = Field(..., description="搜索查询")
    language: Optional[str] = Field(None, description="编程语言过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    difficulty: Optional[str] = Field(None, description="难度过滤")
    limit: Optional[int] = Field(default=10, description="结果数量限制")

class MCPCodeExampleResponse(BaseModel):
    """代码示例响应"""
    success: bool = Field(..., description="请求是否成功")
    data: List[MCPCodeExample] = Field(..., description="代码示例列表")
    total: int = Field(..., description="示例总数")
    query_suggestions: Optional[List[str]] = Field(None, description="查询建议")
    error: Optional[str] = Field(None, description="错误信息")