"""
通用服务模块
- 提供服务的通用功能和基类
- 抽象服务层的公共实现

主要类：
- BaseService: 服务基类
- ServiceConfig: 服务配置基类
- ServiceError: 服务异常基类

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .base_service import (
    BaseService,
    ServiceConfig,
    ServiceError,
    ServiceNotRunningError,
    ServiceConfigurationError
)

__all__ = [
    'BaseService',
    'ServiceConfig', 
    'ServiceError',
    'ServiceNotRunningError',
    'ServiceConfigurationError'
]
