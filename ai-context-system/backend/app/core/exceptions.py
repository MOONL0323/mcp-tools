"""
自定义异常类
"""


class BaseAPIException(Exception):
    """API异常基类"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseAPIException):
    """认证错误"""
    pass


class AuthorizationError(BaseAPIException):
    """授权错误"""
    pass


class ValidationError(BaseAPIException):
    """数据验证错误"""
    pass


class NotFoundError(BaseAPIException):
    """资源未找到错误"""
    pass


class BusinessLogicError(BaseAPIException):
    """业务逻辑错误"""
    pass


class FileOperationError(BaseAPIException):
    """文件操作错误"""
    pass


class DatabaseError(BaseAPIException):
    """数据库错误"""
    pass


class CacheError(BaseAPIException):
    """缓存错误"""
    pass


class FileProcessingError(BaseAPIException):
    """文件处理错误"""
    pass


class LLMServiceError(BaseAPIException):
    """LLM服务错误"""
    pass


class VectorStoreError(BaseAPIException):
    """向量存储错误"""
    pass


class GraphDatabaseError(BaseAPIException):
    """图数据库错误"""
    pass