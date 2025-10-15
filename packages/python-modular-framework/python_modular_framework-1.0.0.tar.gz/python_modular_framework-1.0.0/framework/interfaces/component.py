"""
组件基础接口定义
- 定义所有组件必须实现的标准接口
- 提供组件的生命周期管理接口
- 支持组件的状态查询和配置管理

主要接口：
- ComponentInterface: 组件基础接口
- ComponentStatus: 组件状态枚举
- ComponentConfig: 组件配置接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


class ComponentStatus(Enum):
    """组件状态枚举"""

    UNINITIALIZED = "uninitialized"  # 未初始化
    INITIALIZING = "initializing"  # 初始化中
    INITIALIZED = "initialized"  # 已初始化
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


@dataclass
class ComponentInfo:
    """组件信息数据类"""

    name: str
    version: str
    description: str
    dependencies: List[str]
    status: ComponentStatus
    config: Dict[str, Any]
    metadata: Dict[str, Any]


class ComponentInterface(ABC):
    """
    组件基础接口

    所有组件都必须实现此接口，提供标准的组件行为。
    包括初始化、启动、停止、状态查询等功能。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        获取组件名称

        Returns:
            str: 组件名称
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """
        获取组件版本

        Returns:
            str: 组件版本号
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        获取组件描述

        Returns:
            str: 组件描述信息
        """

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """
        获取组件依赖列表

        Returns:
            List[str]: 依赖的组件名称列表
        """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentError: 初始化失败时抛出异常
        """

    @abstractmethod
    def start(self) -> None:
        """
        启动组件

        在组件初始化完成后调用，开始组件的正常运行。

        Raises:
            ComponentError: 启动失败时抛出异常
        """

    @abstractmethod
    def stop(self) -> None:
        """
        停止组件

        优雅地停止组件，释放资源。

        Raises:
            ComponentError: 停止失败时抛出异常
        """

    @abstractmethod
    def get_status(self) -> ComponentStatus:
        """
        获取组件当前状态

        Returns:
            ComponentStatus: 组件当前状态
        """

    @abstractmethod
    def get_info(self) -> ComponentInfo:
        """
        获取组件详细信息

        Returns:
            ComponentInfo: 组件信息对象
        """

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        获取组件当前配置

        Returns:
            Dict[str, Any]: 组件配置字典
        """

    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置

        Args:
            config (Dict[str, Any]): 新的配置参数

        Raises:
            ComponentError: 配置更新失败时抛出异常
        """

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        检查组件是否正常运行，返回健康状态信息。

        Returns:
            Dict[str, Any]: 健康检查结果
                - status: 健康状态 (healthy/unhealthy)
                - message: 状态描述
                - details: 详细信息
        """


class ComponentError(Exception):
    """组件异常基类"""

    def __init__(
        self,
        component_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化组件异常

        Args:
            component_name (str): 组件名称
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.component_name = component_name
        self.details = details or {}
        super().__init__(f"Component '{component_name}': {message}")


class ComponentInitializationError(ComponentError):
    """组件初始化异常"""



class ComponentStartError(ComponentError):
    """组件启动异常"""



class ComponentStopError(ComponentError):
    """组件停止异常"""



class ComponentConfigError(ComponentError):
    """组件配置异常"""

