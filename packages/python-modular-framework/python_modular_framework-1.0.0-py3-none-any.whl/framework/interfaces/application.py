"""
应用基础接口定义
- 定义应用的标准行为和接口
- 提供组件管理和应用生命周期控制
- 支持应用配置和状态管理

主要接口：
- ApplicationInterface: 应用基础接口
- ApplicationStatus: 应用状态枚举
- ApplicationConfig: 应用配置接口

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, List, Type
from framework.interfaces.component import ComponentInterface, ComponentInfo


class ApplicationStatus(Enum):
    """应用状态枚举"""

    CREATED = "created"  # 已创建
    CONFIGURING = "configuring"  # 配置中
    CONFIGURED = "configured"  # 已配置
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


class ApplicationInterface(ABC):
    """
    应用基础接口

    定义应用的标准行为，包括组件管理、配置管理、
    生命周期控制等功能。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        获取应用名称

        Returns:
            str: 应用名称
        """

    @property
    @abstractmethod
    def version(self) -> str:
        """
        获取应用版本

        Returns:
            str: 应用版本号
        """

    @abstractmethod
    def register_component(self, name: str, component: ComponentInterface) -> None:
        """
        注册组件

        Args:
            name (str): 组件名称
            component (ComponentInterface): 组件实例

        Raises:
            ApplicationError: 注册失败时抛出异常
        """

    @abstractmethod
    def unregister_component(self, name: str) -> None:
        """
        注销组件

        Args:
            name (str): 组件名称

        Raises:
            ApplicationError: 注销失败时抛出异常
        """

    @abstractmethod
    def get_component(self, name: str) -> Optional[ComponentInterface]:
        """
        获取组件实例

        Args:
            name (str): 组件名称

        Returns:
            Optional[ComponentInterface]: 组件实例，如果不存在则返回None
        """

    @abstractmethod
    def get_component_by_type(
        self, component_type: Type[ComponentInterface]
    ) -> Optional[ComponentInterface]:
        """
        根据类型获取组件实例

        Args:
            component_type (Type[ComponentInterface]): 组件类型

        Returns:
            Optional[ComponentInterface]: 组件实例，如果不存在则返回None
        """

    @abstractmethod
    def list_components(self) -> List[str]:
        """
        获取所有已注册的组件名称列表

        Returns:
            List[str]: 组件名称列表
        """

    @abstractmethod
    def get_component_info(self, name: str) -> Optional[ComponentInfo]:
        """
        获取组件信息

        Args:
            name (str): 组件名称

        Returns:
            Optional[ComponentInfo]: 组件信息，如果不存在则返回None
        """

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置应用

        Args:
            config (Dict[str, Any]): 应用配置参数

        Raises:
            ApplicationError: 配置失败时抛出异常
        """

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        获取应用当前配置

        Returns:
            Dict[str, Any]: 应用配置字典
        """

    @abstractmethod
    def start(self) -> None:
        """
        启动应用

        按依赖顺序启动所有已注册的组件。

        Raises:
            ApplicationError: 启动失败时抛出异常
        """

    @abstractmethod
    def stop(self) -> None:
        """
        停止应用

        按相反顺序停止所有组件。

        Raises:
            ApplicationError: 停止失败时抛出异常
        """

    @abstractmethod
    def restart(self) -> None:
        """
        重启应用

        先停止应用，再重新启动。

        Raises:
            ApplicationError: 重启失败时抛出异常
        """

    @abstractmethod
    def get_status(self) -> ApplicationStatus:
        """
        获取应用当前状态

        Returns:
            ApplicationStatus: 应用当前状态
        """

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        应用健康检查

        检查应用和所有组件的健康状态。

        Returns:
            Dict[str, Any]: 健康检查结果
                - status: 整体健康状态 (healthy/unhealthy)
                - components: 各组件健康状态
                - message: 状态描述
        """

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取应用指标

        返回应用的性能指标和统计信息。

        Returns:
            Dict[str, Any]: 应用指标数据
        """


class ApplicationError(Exception):
    """应用异常基类"""

    def __init__(
        self,
        application_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化应用异常

        Args:
            application_name (str): 应用名称
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.application_name = application_name
        self.details = details or {}
        super().__init__(f"Application '{application_name}': {message}")


class ApplicationConfigurationError(ApplicationError):
    """应用配置异常"""



class ApplicationStartError(ApplicationError):
    """应用启动异常"""



class ApplicationStopError(ApplicationError):
    """应用停止异常"""



class ComponentRegistrationError(ApplicationError):
    """组件注册异常"""



class ComponentNotFoundError(ApplicationError):
    """组件未找到异常"""



class DependencyResolutionError(ApplicationError):
    """依赖解析异常"""

