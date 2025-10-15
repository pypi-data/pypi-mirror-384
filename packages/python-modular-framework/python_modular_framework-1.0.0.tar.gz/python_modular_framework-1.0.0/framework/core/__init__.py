"""
框架核心功能模块
- application: 应用主类，负责应用组装和生命周期管理
- container: 依赖注入容器，管理组件实例
- config: 配置管理，支持多种配置源
- lifecycle: 生命周期管理，控制组件启动和停止

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .application import Application
from .container import Container
from .config import Config
from .lifecycle import LifecycleManager

__all__ = [
    "Application",
    "Container",
    "Config",
    "LifecycleManager",
]
