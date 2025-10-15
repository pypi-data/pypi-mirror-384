"""
依赖注入容器实现
- 提供服务的注册、获取和生命周期管理
- 支持单例模式和工厂模式
- 支持依赖解析和循环依赖检测

主要功能：
- 服务注册和获取
- 依赖解析
- 生命周期管理
- 循环依赖检测

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Any, Dict, Type, TypeVar, Callable, Optional, Set, List
from functools import wraps
import threading
import inspect
from enum import Enum
from dataclasses import dataclass

T = TypeVar("T")


class ServiceLifetime(Enum):
    """服务生命周期枚举"""

    SINGLETON = "singleton"  # 单例模式
    TRANSIENT = "transient"  # 瞬态模式
    SCOPED = "scoped"  # 作用域模式


@dataclass
class ServiceRegistration:
    """服务注册信息"""

    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: List[Type] = None


class Container:
    """
    依赖注入容器

    负责管理服务的注册、创建和生命周期。支持单例、瞬态和作用域三种生命周期模式。
    """

    def __init__(self):
        """
        初始化容器

        创建线程锁和内部存储结构。
        """
        self._lock = threading.RLock()
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._resolving: Set[Type] = set()

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        instance: Optional[T] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        注册单例服务

        Args:
            service_type (Type[T]): 服务类型
            implementation_type (Optional[Type[T]]): 实现类型
            instance (Optional[T]): 服务实例
            name (Optional[str]): 服务名称，用于区分同类型的多个实例

        Raises:
            ContainerError: 注册失败时抛出异常
        """
        with self._lock:
            service_key = (service_type, name) if name else service_type

            if service_key in self._services:
                raise ContainerError(
                    f"Service {service_type.__name__} is already registered"
                )

            self._services[service_key] = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                instance=instance,
                lifetime=ServiceLifetime.SINGLETON,
            )

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> None:
        """
        注册瞬态服务

        Args:
            service_type (Type[T]): 服务类型
            implementation_type (Optional[Type[T]]): 实现类型
            factory (Optional[Callable[[], T]]): 工厂函数

        Raises:
            ContainerError: 注册失败时抛出异常
        """
        with self._lock:
            if service_type in self._services:
                raise ContainerError(
                    f"Service {service_type.__name__} is already registered"
                )

            self._services[service_type] = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                lifetime=ServiceLifetime.TRANSIENT,
            )

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
    ) -> None:
        """
        注册作用域服务

        Args:
            service_type (Type[T]): 服务类型
            implementation_type (Optional[Type[T]]): 实现类型
            factory (Optional[Callable[[], T]]): 工厂函数

        Raises:
            ContainerError: 注册失败时抛出异常
        """
        with self._lock:
            if service_type in self._services:
                raise ContainerError(
                    f"Service {service_type.__name__} is already registered"
                )

            self._services[service_type] = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                lifetime=ServiceLifetime.SCOPED,
            )

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """
        注册工厂函数

        Args:
            service_type (Type[T]): 服务类型
            factory (Callable[[], T]): 工厂函数
            lifetime (ServiceLifetime): 生命周期模式

        Raises:
            ContainerError: 注册失败时抛出异常
        """
        with self._lock:
            if service_type in self._services:
                raise ContainerError(
                    f"Service {service_type.__name__} is already registered"
                )

            self._services[service_type] = ServiceRegistration(
                service_type=service_type, factory=factory, lifetime=lifetime
            )

    def get(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """
        获取服务实例

        Args:
            service_type (Type[T]): 服务类型
            name (Optional[str]): 服务名称

        Returns:
            T: 服务实例

        Raises:
            ContainerError: 获取失败时抛出异常
        """
        with self._lock:
            service_key = (service_type, name) if name else service_type

            if service_key not in self._services:
                raise ContainerError(
                    f"Service {service_type.__name__} is not registered"
                )

            registration = self._services[service_key]

            # 检查循环依赖
            if service_type in self._resolving:
                cycle = list(self._resolving) + [service_type]
                raise ContainerError(
                    f"Circular dependency detected: {' -> '.join(t.__name__ for t in cycle)}"
                )

            self._resolving.add(service_type)

            try:
                return self._create_instance(registration)
            finally:
                self._resolving.discard(service_type)

    def get_optional(self, service_type: Type[T]) -> Optional[T]:
        """
        获取服务实例（可选）

        Args:
            service_type (Type[T]): 服务类型

        Returns:
            Optional[T]: 服务实例，如果未注册则返回None
        """
        try:
            return self.get(service_type)
        except ContainerError:
            return None

    def is_registered(self, service_type: Type) -> bool:
        """
        检查服务是否已注册

        Args:
            service_type (Type): 服务类型

        Returns:
            bool: 是否已注册
        """
        return service_type in self._services

    def create_scope(self, scope_name: str) -> "ContainerScope":
        """
        创建作用域

        Args:
            scope_name (str): 作用域名称

        Returns:
            ContainerScope: 作用域对象
        """
        return ContainerScope(self, scope_name)

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """
        创建服务实例

        Args:
            registration (ServiceRegistration): 服务注册信息

        Returns:
            Any: 服务实例
        """
        service_type = registration.service_type

        # 单例模式
        if registration.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._instances:
                return self._instances[service_type]

            instance = self._instantiate_service(registration)
            self._instances[service_type] = instance
            return instance

        # 作用域模式
        elif registration.lifetime == ServiceLifetime.SCOPED:
            if self._current_scope is None:
                raise ContainerError("No active scope for scoped service")

            if self._current_scope not in self._scoped_instances:
                self._scoped_instances[self._current_scope] = {}

            scope_instances = self._scoped_instances[self._current_scope]
            if service_type in scope_instances:
                return scope_instances[service_type]

            instance = self._instantiate_service(registration)
            scope_instances[service_type] = instance
            return instance

        # 瞬态模式
        else:
            return self._instantiate_service(registration)

    def _instantiate_service(self, registration: ServiceRegistration) -> Any:
        """
        实例化服务

        Args:
            registration (ServiceRegistration): 服务注册信息

        Returns:
            Any: 服务实例
        """
        # 如果已有实例，直接返回
        if registration.instance is not None:
            return registration.instance

        # 如果有工厂函数，使用工厂函数
        if registration.factory is not None:
            return registration.factory()

        # 使用实现类型创建实例
        implementation_type = (
            registration.implementation_type or registration.service_type
        )

        # 解析构造函数依赖
        constructor = implementation_type.__init__
        signature = inspect.signature(constructor)

        dependencies = []
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            if param.annotation != inspect.Parameter.empty:
                dependencies.append(self.get(param.annotation))
            else:
                dependencies.append(None)

        return implementation_type(*dependencies)

    def clear(self) -> None:
        """
        清空容器

        移除所有注册的服务和实例。
        """
        with self._lock:
            self._services.clear()
            self._instances.clear()
            self._scoped_instances.clear()
            self._resolving.clear()
            self._current_scope = None


class ContainerScope:
    """
    容器作用域

    用于管理作用域服务的生命周期。
    """

    def __init__(self, container: Container, scope_name: str):
        """
        初始化作用域

        Args:
            container (Container): 容器实例
            scope_name (str): 作用域名称
        """
        self.container = container
        self.scope_name = scope_name
        self._previous_scope = None

    def __enter__(self) -> "ContainerScope":
        """进入作用域"""
        self._previous_scope = self.container._current_scope
        self.container._current_scope = self.scope_name
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出作用域"""
        self.container._current_scope = self._previous_scope
        # 清理作用域实例
        if self.scope_name in self.container._scoped_instances:
            del self.container._scoped_instances[self.scope_name]


def inject(service_type: Type[T]) -> T:
    """
    依赖注入装饰器

    Args:
        service_type (Type[T]): 服务类型

    Returns:
        T: 服务实例
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里需要从全局容器获取服务
            # 实际实现中可能需要传入容器实例
            container = get_current_container()
            service = container.get(service_type)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator


# 全局容器实例
_current_container: Optional[Container] = None


def get_current_container() -> Container:
    """
    获取当前容器实例

    Returns:
        Container: 当前容器实例

    Raises:
        ContainerError: 如果没有设置容器则抛出异常
    """
    if _current_container is None:
        raise ContainerError("No container is set. Call set_current_container() first.")
    return _current_container


def set_current_container(container: Container) -> None:
    """
    设置当前容器实例

    Args:
        container (Container): 容器实例
    """
    global _current_container
    _current_container = container


class ContainerError(Exception):
    """容器异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化容器异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class CircularDependencyError(ContainerError):
    """循环依赖异常"""



class ServiceNotFoundError(ContainerError):
    """服务未找到异常"""



class ServiceRegistrationError(ContainerError):
    """服务注册异常"""

