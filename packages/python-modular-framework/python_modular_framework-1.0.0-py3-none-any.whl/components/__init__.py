"""
组件包层主模块
- 提供可复用的功能组件
- 支持独立安装和使用
- 通过接口进行组件间通信

主要组件：
- user: 用户管理组件
- auth: 权限管理组件
- payment: 支付处理组件
- common: 通用组件（日志、缓存、数据库等）

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

__version__ = "0.1.0"
__author__ = "开发团队"
__email__ = "dev@example.com"

# 组件版本信息
COMPONENT_VERSIONS = {
    "user": "0.1.0",
    "auth": "0.1.0",
    "payment": "0.1.0",
    "common": "0.1.0",
}

# 组件依赖关系
COMPONENT_DEPENDENCIES = {
    "auth": ["user"],
    "payment": ["user"],
}

__all__ = [
    "COMPONENT_VERSIONS",
    "COMPONENT_DEPENDENCIES",
]
