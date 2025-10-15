"""
通用组件模块
- 提供数据库、缓存、日志、服务等通用功能
- 为其他组件提供基础支持

主要子模块：
- database: 数据库相关功能
- cache: 缓存相关功能  
- logging: 日志相关功能
- service: 服务基类
- models: 基础数据模型

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

# 导入主要功能
from .service import BaseService, ServiceConfig
from .database.repository import BaseRepository, ExtendedBaseRepository
from .database.models import BaseModel

__all__ = [
    'BaseService',
    'ServiceConfig', 
    'BaseRepository',
    'ExtendedBaseRepository',
    'BaseModel'
]
