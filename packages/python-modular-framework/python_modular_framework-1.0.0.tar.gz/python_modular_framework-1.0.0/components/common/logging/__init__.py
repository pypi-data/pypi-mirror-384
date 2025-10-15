"""
日志组件包
- 提供统一的日志管理功能
- 支持多种日志级别和输出格式
- 支持日志轮转和结构化日志

主要组件：
- LoggingComponent: 日志组件主类
- LoggingConfig: 日志配置类
- LoggingFormatter: 日志格式化器

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import LoggingComponent
from .config import LoggingConfig
from .formatter import LoggingFormatter

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    "LoggingComponent",
    "LoggingConfig",
    "LoggingFormatter",
]
