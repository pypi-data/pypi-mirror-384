"""
插件接口定义
- 定义插件系统的标准接口
- 支持动态插件加载和管理
- 提供插件生命周期控制

主要接口：
- PluginInterface: 插件基础接口
- PluginManager: 插件管理器接口
- PluginInfo: 插件信息接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass
from framework.interfaces.component import ComponentInterface


class PluginStatus(Enum):
    """插件状态枚举"""

    UNLOADED = "unloaded"  # 未加载
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    ACTIVATING = "activating"  # 激活中
    ACTIVE = "active"  # 激活状态
    DEACTIVATING = "deactivating"  # 停用中
    DEACTIVE = "deactive"  # 停用状态
    UNLOADING = "unloading"  # 卸载中
    ERROR = "error"  # 错误状态


@dataclass
class PluginInfo:
    """插件信息数据类"""

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    entry_point: str
    status: PluginStatus
    metadata: Dict[str, Any]


class PluginInterface(ABC):
    """
    插件基础接口

    所有插件都必须实现此接口，提供标准的插件行为。
    插件可以扩展应用功能，提供额外的组件或服务。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        获取插件名称

        Returns:
            str: 插件名称
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """
        获取插件版本

        Returns:
            str: 插件版本号
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        获取插件描述

        Returns:
            str: 插件描述信息
        """

    @property
    @abstractmethod
    def author(self) -> str:
        """
        获取插件作者

        Returns:
            str: 插件作者信息
        """

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """
        获取插件依赖列表

        Returns:
            List[str]: 依赖的插件或组件名称列表
        """

    @abstractmethod
    def load(self, config: Dict[str, Any]) -> None:
        """
        加载插件

        Args:
            config (Dict[str, Any]): 插件配置参数

        Raises:
            PluginError: 加载失败时抛出异常
        """

    @abstractmethod
    def activate(self) -> None:
        """
        激活插件

        插件加载完成后调用，开始提供功能。

        Raises:
            PluginError: 激活失败时抛出异常
        """

    @abstractmethod
    def deactivate(self) -> None:
        """
        停用插件

        停止插件功能，但保持加载状态。

        Raises:
            PluginError: 停用失败时抛出异常
        """

    @abstractmethod
    def unload(self) -> None:
        """
        卸载插件

        完全移除插件，释放所有资源。

        Raises:
            PluginError: 卸载失败时抛出异常
        """

    @abstractmethod
    def get_status(self) -> PluginStatus:
        """
        获取插件当前状态

        Returns:
            PluginStatus: 插件当前状态
        """

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """
        获取插件详细信息

        Returns:
            PluginInfo: 插件信息对象
        """

    @abstractmethod
    def get_components(self) -> List[ComponentInterface]:
        """
        获取插件提供的组件列表

        Returns:
            List[ComponentInterface]: 插件提供的组件列表
        """

    @abstractmethod
    def get_commands(self) -> Dict[str, Callable]:
        """
        获取插件提供的命令列表

        Returns:
            Dict[str, Callable]: 命令名称到处理函数的映射
        """

    @abstractmethod
    def get_hooks(self) -> Dict[str, List[Callable]]:
        """
        获取插件提供的钩子函数列表

        Returns:
            Dict[str, List[Callable]]: 钩子名称到处理函数列表的映射
        """


class PluginManagerInterface(ABC):
    """
    插件管理器接口

    负责插件的加载、管理和生命周期控制。
    """

    @abstractmethod
    def load_plugin(
        self, plugin_path: str, config: Optional[Dict[str, Any]] = None
    ) -> PluginInterface:
        """
        加载插件

        Args:
            plugin_path (str): 插件路径
            config (Optional[Dict[str, Any]]): 插件配置

        Returns:
            PluginInterface: 加载的插件实例

        Raises:
            PluginError: 加载失败时抛出异常
        """

    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> None:
        """
        卸载插件

        Args:
            plugin_name (str): 插件名称

        Raises:
            PluginError: 卸载失败时抛出异常
        """

    @abstractmethod
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        获取插件实例

        Args:
            plugin_name (str): 插件名称

        Returns:
            Optional[PluginInterface]: 插件实例，如果不存在则返回None
        """

    @abstractmethod
    def list_plugins(self) -> List[str]:
        """
        获取所有已加载的插件名称列表

        Returns:
            List[str]: 插件名称列表
        """

    @abstractmethod
    def activate_plugin(self, plugin_name: str) -> None:
        """
        激活插件

        Args:
            plugin_name (str): 插件名称

        Raises:
            PluginError: 激活失败时抛出异常
        """

    @abstractmethod
    def deactivate_plugin(self, plugin_name: str) -> None:
        """
        停用插件

        Args:
            plugin_name (str): 插件名称

        Raises:
            PluginError: 停用失败时抛出异常
        """

    @abstractmethod
    def discover_plugins(self, plugin_dir: str) -> List[str]:
        """
        发现插件目录中的插件

        Args:
            plugin_dir (str): 插件目录路径

        Returns:
            List[str]: 发现的插件路径列表
        """


class PluginError(Exception):
    """插件异常基类"""

    def __init__(
        self, plugin_name: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化插件异常

        Args:
            plugin_name (str): 插件名称
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.plugin_name = plugin_name
        self.details = details or {}
        super().__init__(f"Plugin '{plugin_name}': {message}")


class PluginLoadError(PluginError):
    """插件加载异常"""



class PluginActivationError(PluginError):
    """插件激活异常"""



class PluginDeactivationError(PluginError):
    """插件停用异常"""



class PluginUnloadError(PluginError):
    """插件卸载异常"""



class PluginNotFoundError(PluginError):
    """插件未找到异常"""



class PluginDependencyError(PluginError):
    """插件依赖异常"""

