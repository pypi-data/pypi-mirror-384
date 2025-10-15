"""
应用主类实现
- 提供应用的核心功能，包括组件管理和生命周期控制
- 实现ApplicationInterface接口
- 支持依赖注入和配置管理

主要功能：
- 组件注册和管理
- 应用生命周期控制
- 依赖解析和注入
- 配置管理
- 健康检查和监控

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import time
from typing import Any, Dict, Optional, List, Type
from framework.interfaces.application import (
    ApplicationInterface,
    ApplicationStatus,
    ApplicationError,
    ApplicationConfigurationError,
    ApplicationStartError,
    ApplicationStopError,
    ComponentRegistrationError,
    ComponentNotFoundError,
    DependencyResolutionError,
)
from framework.interfaces.component import ComponentInterface, ComponentInfo
from framework.core.container import Container, set_current_container
from framework.core.config import Config
from framework.core.lifecycle import LifecycleManager
from framework.core.dependency_resolver import DependencyResolver, ComponentDiscovery


class Application(ApplicationInterface):
    """
    应用主类

    负责管理应用的整体生命周期，包括组件注册、配置管理、
    依赖解析、启动停止等功能。
    """

    def __init__(self, name: str = "default-app", version: str = "1.0.0"):
        """
        初始化应用

        Args:
            name (str): 应用名称
            version (str): 应用版本
        """
        self._name = name
        self._version = version
        self._status = ApplicationStatus.CREATED
        self._config = Config()
        self._container = Container()
        self._lifecycle_manager = LifecycleManager()
        self._components: Dict[str, ComponentInterface] = {}
        self._component_dependencies: Dict[str, List[str]] = {}
        self._startup_time: Optional[float] = None
        self._shutdown_time: Optional[float] = None

        # 初始化依赖解析器和组件发现器
        self._dependency_resolver = DependencyResolver()
        self._component_discovery = ComponentDiscovery()
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []

        # 设置全局容器
        set_current_container(self._container)

        # 注册生命周期事件处理器
        self._setup_lifecycle_handlers()

    @property
    def name(self) -> str:
        """获取应用名称"""
        return self._name

    @property
    def version(self) -> str:
        """获取应用版本"""
        return self._version

    def _setup_lifecycle_handlers(self) -> None:
        """设置生命周期事件处理器"""

        def on_component_error(event_data):
            print(f"Component error: {event_data.component_name} - {event_data.data}")

        self._lifecycle_manager.add_event_handler(
            self._lifecycle_manager._emit_event.__globals__["LifecycleEvent"].ERROR,
            on_component_error,
        )

    def register_component(self, name: str, component: ComponentInterface) -> None:
        """
        注册组件

        Args:
            name (str): 组件名称
            component (ComponentInterface): 组件实例

        Raises:
            ComponentRegistrationError: 注册失败时抛出异常
        """
        if self._status not in [
            ApplicationStatus.CREATED,
            ApplicationStatus.CONFIGURED,
        ]:
            raise ComponentRegistrationError(
                self._name,
                f"Cannot register component '{name}' in status {self._status}",
            )

        if name in self._components:
            raise ComponentRegistrationError(
                self._name, f"Component '{name}' is already registered"
            )

        # 验证组件
        if not isinstance(component, ComponentInterface):
            raise ComponentRegistrationError(
                self._name, f"Component '{name}' does not implement ComponentInterface"
            )

        # 注册组件
        self._components[name] = component
        self._component_dependencies[name] = component.dependencies.copy()

        # 注册到生命周期管理器
        self._lifecycle_manager.register_component(name, component)

        # 注册到容器（使用组件名称作为键）
        self._container.register_singleton(
            type(component), instance=component, name=name
        )

        # 添加到依赖解析器
        self._dependency_resolver.add_component(
            name=name,
            component_type=type(component),
            dependencies=component.dependencies,
            is_required=True,
            metadata={"version": component.get_info().version},
        )

    def unregister_component(self, name: str) -> None:
        """
        注销组件

        Args:
            name (str): 组件名称

        Raises:
            ComponentNotFoundError: 组件不存在时抛出异常
        """
        if name not in self._components:
            raise ComponentNotFoundError(
                self._name, f"Component '{name}' is not registered"
            )

        # 从生命周期管理器注销
        self._lifecycle_manager.unregister_component(name)

        # 从容器中移除
        component = self._components[name]
        # 注意：这里需要根据实际的容器实现来移除服务

        # 从组件字典中移除
        del self._components[name]
        del self._component_dependencies[name]

        # 从依赖解析器中移除
        self._dependency_resolver.remove_component(name)

    def get_component(self, name: str) -> Optional[ComponentInterface]:
        """
        获取组件实例

        Args:
            name (str): 组件名称

        Returns:
            Optional[ComponentInterface]: 组件实例，如果不存在则返回None
        """
        return self._components.get(name)

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
        for component in self._components.values():
            if isinstance(component, component_type):
                return component
        return None

    def list_components(self) -> List[str]:
        """
        获取所有已注册的组件名称列表

        Returns:
            List[str]: 组件名称列表
        """
        return list(self._components.keys())

    def get_component_info(self, name: str) -> Optional[ComponentInfo]:
        """
        获取组件信息

        Args:
            name (str): 组件名称

        Returns:
            Optional[ComponentInfo]: 组件信息，如果不存在则返回None
        """
        component = self._components.get(name)
        if component:
            return component.get_info()
        return None

    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置应用

        Args:
            config (Dict[str, Any]): 应用配置参数

        Raises:
            ApplicationConfigurationError: 配置失败时抛出异常
        """
        if self._status not in [ApplicationStatus.CREATED]:
            raise ApplicationConfigurationError(
                self._name, f"Cannot configure application in status {self._status}"
            )

        try:
            self._status = ApplicationStatus.CONFIGURING

            # 更新配置
            for key, value in config.items():
                self._config.set(key, value)

            # 自动发现和注册组件（在配置完成后）
            self._component_configs = config.get("components", {})

            # 配置已注册的组件
            for name, component in self._components.items():
                component_config = config.get(name, {})
                if component_config:
                    component.update_config(component_config)

            self._status = ApplicationStatus.CONFIGURED

            # 配置完成后自动发现和注册组件
            if hasattr(self, "_component_configs") and self._component_configs:
                self._auto_discover_components(self._component_configs)
            else:
                # 如果没有组件配置，则自动扫描components目录
                self._auto_discover_components()

        except Exception as e:
            self._status = ApplicationStatus.ERROR
            raise ApplicationConfigurationError(
                self._name, f"Failed to configure application: {e}"
            )

    def get_config(self) -> Dict[str, Any]:
        """
        获取应用当前配置

        Returns:
            Dict[str, Any]: 应用配置字典
        """
        return self._config.to_dict()

    def start(self) -> None:
        """
        启动应用

        按依赖顺序启动所有已注册的组件。

        Raises:
            ApplicationStartError: 启动失败时抛出异常
        """
        if self._status not in [ApplicationStatus.CONFIGURED]:
            raise ApplicationStartError(
                self._name, f"Cannot start application in status {self._status}"
            )

        try:
            self._status = ApplicationStatus.STARTING
            self._startup_time = time.time()

            # 解析依赖关系
            self._resolve_dependencies()

            # 按依赖顺序初始化组件
            for component_name in self._startup_order:
                if component_name in self._components:
                    component = self._components[component_name]
                    try:
                        component.initialize(self._config.get(component_name, {}))
                        print(f"Initialized component: {component_name}")
                    except Exception as e:
                        print(f"Failed to initialize component '{component_name}': {e}")
                        raise

            # 按依赖顺序启动组件
            for component_name in self._startup_order:
                if component_name in self._components:
                    component = self._components[component_name]
                    try:
                        component.start()
                        print(f"Started component: {component_name}")
                    except Exception as e:
                        print(f"Failed to start component '{component_name}': {e}")
                        raise

            self._status = ApplicationStatus.RUNNING

        except Exception as e:
            self._status = ApplicationStatus.ERROR
            raise ApplicationStartError(self._name, f"Failed to start application: {e}")

    def stop(self) -> None:
        """
        停止应用

        按相反顺序停止所有组件。

        Raises:
            ApplicationStopError: 停止失败时抛出异常
        """
        if self._status not in [ApplicationStatus.RUNNING]:
            return  # 应用没有在运行

        try:
            self._status = ApplicationStatus.STOPPING
            self._shutdown_time = time.time()

            # 按相反顺序停止组件
            for component_name in self._shutdown_order:
                if component_name in self._components:
                    component = self._components[component_name]
                    try:
                        component.stop()
                        print(f"Stopped component: {component_name}")
                    except Exception as e:
                        print(f"Failed to stop component '{component_name}': {e}")
                        # 继续停止其他组件，不抛出异常

            self._status = ApplicationStatus.STOPPED

        except Exception as e:
            self._status = ApplicationStatus.ERROR
            raise ApplicationStopError(self._name, f"Failed to stop application: {e}")

    def restart(self) -> None:
        """
        重启应用

        先停止应用，再重新启动。

        Raises:
            ApplicationError: 重启失败时抛出异常
        """
        try:
            self.stop()
            self.start()
        except Exception as e:
            raise ApplicationError(self._name, f"Failed to restart application: {e}")

    def get_status(self) -> ApplicationStatus:
        """
        获取应用当前状态

        Returns:
            ApplicationStatus: 应用当前状态
        """
        return self._status

    def health_check(self) -> Dict[str, Any]:
        """
        应用健康检查

        检查应用和所有组件的健康状态。

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "application": {
                "name": self._name,
                "version": self._version,
                "status": self._status.value,
                "uptime": self._get_uptime(),
            },
            "components": {},
            "overall": "healthy",
        }

        # 检查组件健康状态
        component_health = self._lifecycle_manager.health_check()
        health_status["components"] = component_health["components"]

        # 确定整体健康状态
        if component_health["overall"] != "healthy":
            health_status["overall"] = "unhealthy"

        if self._status != ApplicationStatus.RUNNING:
            health_status["overall"] = "unhealthy"
            health_status["application"][
                "message"
            ] = f"Application is not running: {self._status.value}"

        return health_status

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取应用指标

        返回应用的性能指标和统计信息。

        Returns:
            Dict[str, Any]: 应用指标数据
        """
        metrics = {
            "application": {
                "name": self._name,
                "version": self._version,
                "status": self._status.value,
                "uptime": self._get_uptime(),
                "startup_time": self._startup_time,
                "shutdown_time": self._shutdown_time,
            },
            "components": {
                "total": len(self._components),
                "registered": list(self._components.keys()),
            },
            "timestamp": time.time(),
        }

        # 添加组件指标
        for name, component in self._components.items():
            try:
                component_info = component.get_info()
                metrics["components"][name] = {
                    "status": component.get_status().value,
                    "version": component_info.version,
                    "dependencies": component_info.dependencies,
                }
            except Exception:
                metrics["components"][name] = {
                    "status": "error",
                    "error": "Failed to get component info",
                }

        return metrics

    def _resolve_dependencies(self) -> None:
        """
        解析组件依赖关系

        检查依赖关系并确保启动顺序正确。

        Raises:
            DependencyResolutionError: 依赖解析失败时抛出异常
        """
        try:
            # 检测循环依赖
            self._dependency_resolver.detect_circular_dependency()

            # 验证依赖关系
            validation_result = self._dependency_resolver.validate_dependencies()
            if validation_result:
                missing_deps = []
                for component, missing in validation_result.items():
                    missing_deps.append(f"{component}: {', '.join(missing)}")
                raise DependencyResolutionError(
                    "missing_dependencies",
                    f"Missing dependencies: {'; '.join(missing_deps)}",
                )

            # 获取启动和关闭顺序
            self._startup_order = self._dependency_resolver.get_startup_order()
            self._shutdown_order = self._dependency_resolver.get_shutdown_order()

        except Exception as e:
            if isinstance(e, DependencyResolutionError):
                raise
            else:
                raise DependencyResolutionError(
                    "dependency_resolution", f"Failed to resolve dependencies: {e}"
                )

    def _auto_discover_components(
        self, component_configs: Dict[str, Any] = None
    ) -> None:
        """
        自动发现和注册组件

        Args:
            component_configs (Dict[str, Any]): 组件配置字典，如果为None则自动扫描
        """
        # 发现组件类型
        discovered_components = self._component_discovery.discover_components(
            component_configs
        )

        # 注册发现的组件
        for component_name, component_type in discovered_components.items():
            if component_name not in self._components:
                try:
                    # 创建组件实例
                    component = component_type(name=component_name)

                    # 注册组件
                    self.register_component(component_name, component)

                    print(f"Auto-discovered and registered component: {component_name}")

                except Exception as e:
                    print(
                        f"Failed to register auto-discovered component '{component_name}': {e}"
                    )
                    continue

    def get_dependency_graph(self) -> Dict[str, Any]:
        """
        获取依赖关系图

        Returns:
            Dict[str, Any]: 依赖关系图数据
        """
        return self._dependency_resolver.get_dependency_graph()

    def get_startup_order(self) -> List[str]:
        """
        获取组件启动顺序

        Returns:
            List[str]: 组件启动顺序列表
        """
        return self._startup_order.copy()

    def get_shutdown_order(self) -> List[str]:
        """
        获取组件关闭顺序

        Returns:
            List[str]: 组件关闭顺序列表
        """
        return self._shutdown_order.copy()

    def _get_uptime(self) -> Optional[float]:
        """
        获取应用运行时间

        Returns:
            Optional[float]: 运行时间（秒），如果未启动则返回None
        """
        if self._startup_time:
            return time.time() - self._startup_time
        return None

    def discover_components(self) -> List[str]:
        """
        发现并注册所有可用组件

        Returns:
            List[str]: 发现的组件名称列表
        """
        # 自动发现组件
        self._auto_discover_components()

        # 返回发现的组件列表
        return self._component_discovery.list_available_components()

    def get_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        获取组件注册表

        Returns:
            Dict[str, Dict[str, Any]]: 组件注册表
        """
        return self._component_discovery.get_component_registry()

    def get_component_metadata(self, component_name: str) -> Dict[str, Any]:
        """
        获取组件元数据

        Args:
            component_name (str): 组件名称

        Returns:
            Dict[str, Any]: 组件元数据
        """
        return self._component_discovery.get_component_metadata(component_name)

    def is_component_available(self, component_name: str) -> bool:
        """
        检查组件是否可用

        Args:
            component_name (str): 组件名称

        Returns:
            bool: 组件是否可用
        """
        return self._component_discovery.is_component_discovered(component_name)
