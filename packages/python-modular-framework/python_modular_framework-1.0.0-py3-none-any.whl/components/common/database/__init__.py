"""
数据库组件包
- 提供统一的数据库管理功能
- 支持多种数据库类型（SQLite、PostgreSQL、MySQL）
- 支持连接池管理和事务处理

主要组件：
- DatabaseComponent: 数据库组件主类
- DatabaseConfig: 数据库配置类
- ConnectionPool: 连接池管理
- BaseModel: 数据库模型基类
- BaseRepository: Repository基类

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import DatabaseComponent
from .config import DatabaseConfig
from .pool import ConnectionPool

try:
    from .models import Base, BaseModel, TimestampMixin
    from .repository import BaseRepository, transactional, RepositoryError
    MODELS_AVAILABLE = True
except ImportError:
    Base = None
    BaseModel = None
    TimestampMixin = None
    BaseRepository = None
    transactional = None
    RepositoryError = None
    MODELS_AVAILABLE = False

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    "DatabaseComponent",
    "DatabaseConfig",
    "ConnectionPool",
    "Base",
    "BaseModel",
    "TimestampMixin",
    "BaseRepository",
    "transactional",
    "RepositoryError",
]
