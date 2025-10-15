"""
Python模块化框架主包
- 提供框架的核心功能和接口
- 支持组件管理和依赖注入
- 提供应用生命周期管理

主要模块：
- core: 核心功能模块
- interfaces: 接口定义模块

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .core.application import Application
from .core.container import Container
from .core.config import Config
from .interfaces.component import ComponentInterface
from .interfaces.application import ApplicationInterface

__version__ = "0.1.0"
__author__ = "开发团队"
__email__ = "dev@example.com"

__all__ = [
    "Application",
    "Container",
    "Config",
    "ComponentInterface",
    "ApplicationInterface",
]
