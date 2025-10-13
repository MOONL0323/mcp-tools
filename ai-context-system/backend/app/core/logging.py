"""
日志配置
"""

import sys
import os
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory
import logging

from app.core.config import get_settings

settings = get_settings()


def get_logger(name: str = None):
    """获取logger实例"""
    if name is None:
        name = __name__
    return structlog.get_logger(name)


def setup_logging() -> None:
    """配置应用日志"""
    
    # 基础日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 配置标准库logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # 禁用一些第三方库的详细日志
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    
    # 开发环境和生产环境使用不同的处理器
    if settings.is_development:
        processors = [
            # 添加调用信息
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # 开发环境使用彩色输出
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        processors = [
            # 生产环境使用JSON格式
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    
    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def log_request(self, request_data: Dict[str, Any]) -> None:
        """记录请求日志"""
        self.logger.info(
            "API请求",
            method=request_data.get("method"),
            path=request_data.get("path"),
            query_params=request_data.get("query_params"),
            user_id=request_data.get("user_id"),
            request_id=request_data.get("request_id"),
            ip_address=request_data.get("ip_address"),
            user_agent=request_data.get("user_agent")
        )
    
    def log_response(self, response_data: Dict[str, Any]) -> None:
        """记录响应日志"""
        self.logger.info(
            "API响应",
            status_code=response_data.get("status_code"),
            response_time=response_data.get("response_time"),
            response_size=response_data.get("response_size"),
            request_id=response_data.get("request_id")
        )
    
    def log_error(self, error_data: Dict[str, Any]) -> None:
        """记录错误日志"""
        self.logger.error(
            "API错误",
            error_type=error_data.get("error_type"),
            error_message=error_data.get("error_message"),
            stack_trace=error_data.get("stack_trace"),
            request_id=error_data.get("request_id"),
            user_id=error_data.get("user_id"),
            path=error_data.get("path"),
            method=error_data.get("method")
        )


class BusinessLogger:
    """业务日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def log_user_action(self, action_data: Dict[str, Any]) -> None:
        """记录用户操作日志"""
        self.logger.info(
            "用户操作",
            action=action_data.get("action"),
            user_id=action_data.get("user_id"),
            resource_type=action_data.get("resource_type"),
            resource_id=action_data.get("resource_id"),
            details=action_data.get("details"),
            ip_address=action_data.get("ip_address"),
            request_id=action_data.get("request_id")
        )
    
    def log_document_processing(self, processing_data: Dict[str, Any]) -> None:
        """记录文档处理日志"""
        self.logger.info(
            "文档处理",
            document_id=processing_data.get("document_id"),
            processing_type=processing_data.get("processing_type"),
            status=processing_data.get("status"),
            duration=processing_data.get("duration"),
            chunk_count=processing_data.get("chunk_count"),
            entity_count=processing_data.get("entity_count"),
            error_message=processing_data.get("error_message")
        )
    
    def log_llm_request(self, llm_data: Dict[str, Any]) -> None:
        """记录LLM请求日志"""
        self.logger.info(
            "LLM请求",
            model=llm_data.get("model"),
            prompt_length=llm_data.get("prompt_length"),
            response_length=llm_data.get("response_length"),
            duration=llm_data.get("duration"),
            token_usage=llm_data.get("token_usage"),
            request_id=llm_data.get("request_id"),
            user_id=llm_data.get("user_id")
        )
    
    def log_cache_operation(self, cache_data: Dict[str, Any]) -> None:
        """记录缓存操作日志"""
        if settings.LOG_LEVEL.upper() == "DEBUG":
            self.logger.debug(
                "缓存操作",
                operation=cache_data.get("operation"),
                key=cache_data.get("key"),
                hit=cache_data.get("hit"),
                duration=cache_data.get("duration"),
                size=cache_data.get("size")
            )


class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def log_authentication(self, auth_data: Dict[str, Any]) -> None:
        """记录认证日志"""
        self.logger.info(
            "用户认证",
            success=auth_data.get("success"),
            username=auth_data.get("username"),
            ip_address=auth_data.get("ip_address"),
            user_agent=auth_data.get("user_agent"),
            failure_reason=auth_data.get("failure_reason"),
            request_id=auth_data.get("request_id")
        )
    
    def log_authorization(self, authz_data: Dict[str, Any]) -> None:
        """记录授权日志"""
        self.logger.info(
            "权限检查",
            success=authz_data.get("success"),
            user_id=authz_data.get("user_id"),
            resource=authz_data.get("resource"),
            action=authz_data.get("action"),
            reason=authz_data.get("reason"),
            request_id=authz_data.get("request_id")
        )
    
    def log_security_event(self, event_data: Dict[str, Any]) -> None:
        """记录安全事件"""
        self.logger.warning(
            "安全事件",
            event_type=event_data.get("event_type"),
            severity=event_data.get("severity"),
            user_id=event_data.get("user_id"),
            ip_address=event_data.get("ip_address"),
            details=event_data.get("details"),
            request_id=event_data.get("request_id")
        )


# 全局日志记录器实例
request_logger = RequestLogger()
business_logger = BusinessLogger()
security_logger = SecurityLogger()