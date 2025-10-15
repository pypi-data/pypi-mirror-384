"""
框架接口定义模块
- component: 组件基础接口，定义组件的标准行为
- application: 应用接口，定义应用的标准行为
- plugin: 插件接口，支持插件扩展

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import ComponentInterface
from .application import ApplicationInterface
from .plugin import PluginInterface

__all__ = [
    "ComponentInterface",
    "ApplicationInterface",
    "PluginInterface",
]
