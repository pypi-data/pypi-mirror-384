"""
缓存组件包
- 提供统一的缓存管理功能
- 支持内存缓存和Redis缓存
- 支持多种缓存策略和过期机制

主要组件：
- CacheComponent: 缓存组件主类
- CacheConfig: 缓存配置类
- CacheStrategy: 缓存策略接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import CacheComponent
from .config import CacheConfig
from .strategy import CacheStrategy, LRUStrategy, LFUStrategy, FIFOStrategy

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    "CacheComponent",
    "CacheConfig",
    "CacheStrategy",
    "LRUStrategy",
    "LFUStrategy",
    "FIFOStrategy",
]
