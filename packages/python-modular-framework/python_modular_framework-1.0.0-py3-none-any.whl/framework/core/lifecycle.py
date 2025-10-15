"""
生命周期管理模块
- 提供组件和应用的生命周期管理功能
- 支持启动、停止、重启等操作
- 提供生命周期事件和钩子

主要功能：
- 组件生命周期管理
- 应用生命周期管理
- 生命周期事件处理
- 优雅关闭支持

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""
import signal
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from framework.interfaces.component import ComponentInterface, ComponentStatus


class LifecycleEvent(Enum):
    """生命周期事件枚举"""

    BEFORE_INITIALIZE = "before_initialize"
    AFTER_INITIALIZE = "after_initialize"
    BEFORE_START = "before_start"
    AFTER_START = "after_start"
    BEFORE_STOP = "before_stop"
    AFTER_STOP = "after_stop"
    ERROR = "error"


@dataclass
class LifecycleEventData:
    """生命周期事件数据"""

    event: LifecycleEvent
    component_name: Optional[str] = None
    timestamp: float = 0.0
    data: Optional[Dict[str, Any]] = None


class LifecycleManager:
    """
    生命周期管理器

    负责管理组件和应用的完整生命周期，包括初始化、启动、停止等操作。
    """

    def __init__(self):
        """
        初始化生命周期管理器

        创建事件处理器和状态跟踪。
        """
        self._event_handlers: Dict[LifecycleEvent, List[Callable]] = {}
        self._components: Dict[str, ComponentInterface] = {}
        self._component_status: Dict[str, ComponentStatus] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        self._lock = threading.RLock()
        self._shutdown_timeout: float = 30.0
        self._startup_timeout: float = 60.0

        # 注册信号处理器
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """
        设置信号处理器

        注册SIGINT和SIGTERM信号处理器，实现优雅关闭。
        """

        def signal_handler(signum, frame):
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def register_component(self, name: str, component: ComponentInterface) -> None:
        """
        注册组件

        Args:
            name (str): 组件名称
            component (ComponentInterface): 组件实例

        Raises:
            LifecycleError: 注册失败时抛出异常
        """
        with self._lock:
            if name in self._components:
                raise LifecycleError(f"Component '{name}' is already registered")

            self._components[name] = component
            self._component_status[name] = ComponentStatus.UNINITIALIZED
            self._startup_order.append(name)
            self._shutdown_order.insert(0, name)  # 反向顺序

    def unregister_component(self, name: str) -> None:
        """
        注销组件

        Args:
            name (str): 组件名称

        Raises:
            LifecycleError: 注销失败时抛出异常
        """
        with self._lock:
            if name not in self._components:
                raise LifecycleError(f"Component '{name}' is not registered")

            # 如果组件正在运行，先停止
            if self._component_status[name] in [
                ComponentStatus.RUNNING,
                ComponentStatus.STARTING,
            ]:
                self._stop_component(name)

            del self._components[name]
            del self._component_status[name]
            self._startup_order.remove(name)
            self._shutdown_order.remove(name)

    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """
        获取组件状态

        Args:
            name (str): 组件名称

        Returns:
            Optional[ComponentStatus]: 组件状态，如果不存在则返回None
        """
        return self._component_status.get(name)

    def get_all_status(self) -> Dict[str, ComponentStatus]:
        """
        获取所有组件状态

        Returns:
            Dict[str, ComponentStatus]: 组件名称到状态的映射
        """
        return self._component_status.copy()

    def add_event_handler(
        self, event: LifecycleEvent, handler: Callable[[LifecycleEventData], None]
    ) -> None:
        """
        添加事件处理器

        Args:
            event (LifecycleEvent): 生命周期事件
            handler (Callable[[LifecycleEventData], None]): 事件处理函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def remove_event_handler(
        self, event: LifecycleEvent, handler: Callable[[LifecycleEventData], None]
    ) -> None:
        """
        移除事件处理器

        Args:
            event (LifecycleEvent): 生命周期事件
            handler (Callable[[LifecycleEventData], None]): 事件处理函数
        """
        if event in self._event_handlers:
            try:
                self._event_handlers[event].remove(handler)
            except ValueError:
                pass

    def _emit_event(
        self,
        event: LifecycleEvent,
        component_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        发送生命周期事件

        Args:
            event (LifecycleEvent): 生命周期事件
            component_name (Optional[str]): 组件名称
            data (Optional[Dict[str, Any]]): 事件数据
        """
        event_data = LifecycleEventData(
            event=event,
            component_name=component_name,
            timestamp=time.time(),
            data=data or {},
        )

        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(event_data)
                except Exception as e:
                    # 记录错误但不中断流程
                    print(f"Error in lifecycle event handler: {e}")

    def initialize_all(self) -> None:
        """
        初始化所有组件

        按注册顺序初始化所有组件。

        Raises:
            LifecycleError: 初始化失败时抛出异常
        """
        with self._lock:
            for name in self._startup_order:
                self._initialize_component(name)

    def start_all(self) -> None:
        """
        启动所有组件

        按注册顺序启动所有组件。

        Raises:
            LifecycleError: 启动失败时抛出异常
        """
        with self._lock:
            for name in self._startup_order:
                self._start_component(name)

    def stop_all(self) -> None:
        """
        停止所有组件

        按相反顺序停止所有组件。

        Raises:
            LifecycleError: 停止失败时抛出异常
        """
        with self._lock:
            for name in self._shutdown_order:
                self._stop_component(name)

    def shutdown(self) -> None:
        """
        关闭生命周期管理器

        停止所有组件并清理资源。
        """
        try:
            self.stop_all()
        except Exception as e:
            print(f"Error during shutdown: {e}")

    def _initialize_component(self, name: str) -> None:
        """
        初始化单个组件

        Args:
            name (str): 组件名称

        Raises:
            LifecycleError: 初始化失败时抛出异常
        """
        if name not in self._components:
            raise LifecycleError(f"Component '{name}' is not registered")

        component = self._components[name]
        current_status = self._component_status[name]

        if current_status != ComponentStatus.UNINITIALIZED:
            return  # 已经初始化过了

        try:
            self._component_status[name] = ComponentStatus.INITIALIZING
            self._emit_event(LifecycleEvent.BEFORE_INITIALIZE, name)

            # 获取组件配置
            config = component.get_config()
            component.initialize(config)

            self._component_status[name] = ComponentStatus.INITIALIZED
            self._emit_event(LifecycleEvent.AFTER_INITIALIZE, name)

        except Exception as e:
            self._component_status[name] = ComponentStatus.ERROR
            self._emit_event(LifecycleEvent.ERROR, name, {"error": str(e)})
            raise LifecycleError(f"Failed to initialize component '{name}': {e}")

    def _start_component(self, name: str) -> None:
        """
        启动单个组件

        Args:
            name (str): 组件名称

        Raises:
            LifecycleError: 启动失败时抛出异常
        """
        if name not in self._components:
            raise LifecycleError(f"Component '{name}' is not registered")

        component = self._components[name]
        current_status = self._component_status[name]

        if current_status == ComponentStatus.RUNNING:
            return  # 已经在运行

        if current_status not in [ComponentStatus.INITIALIZED, ComponentStatus.STOPPED]:
            raise LifecycleError(
                f"Component '{name}' is not in a valid state for starting: {current_status}"
            )

        try:
            self._component_status[name] = ComponentStatus.STARTING
            self._emit_event(LifecycleEvent.BEFORE_START, name)

            component.start()

            self._component_status[name] = ComponentStatus.RUNNING
            self._emit_event(LifecycleEvent.AFTER_START, name)

        except Exception as e:
            self._component_status[name] = ComponentStatus.ERROR
            self._emit_event(LifecycleEvent.ERROR, name, {"error": str(e)})
            raise LifecycleError(f"Failed to start component '{name}': {e}")

    def _stop_component(self, name: str) -> None:
        """
        停止单个组件

        Args:
            name (str): 组件名称

        Raises:
            LifecycleError: 停止失败时抛出异常
        """
        if name not in self._components:
            raise LifecycleError(f"Component '{name}' is not registered")

        component = self._components[name]
        current_status = self._component_status[name]

        if current_status == ComponentStatus.STOPPED:
            return  # 已经停止了

        if current_status not in [ComponentStatus.RUNNING, ComponentStatus.STARTING]:
            return  # 不在运行状态

        try:
            self._component_status[name] = ComponentStatus.STOPPING
            self._emit_event(LifecycleEvent.BEFORE_STOP, name)

            component.stop()

            self._component_status[name] = ComponentStatus.STOPPED
            self._emit_event(LifecycleEvent.AFTER_STOP, name)

        except Exception as e:
            self._component_status[name] = ComponentStatus.ERROR
            self._emit_event(LifecycleEvent.ERROR, name, {"error": str(e)})
            raise LifecycleError(f"Failed to stop component '{name}': {e}")

    def set_startup_timeout(self, timeout: float) -> None:
        """
        设置启动超时时间

        Args:
            timeout (float): 超时时间（秒）
        """
        self._startup_timeout = timeout

    def set_shutdown_timeout(self, timeout: float) -> None:
        """
        设置关闭超时时间

        Args:
            timeout (float): 超时时间（秒）
        """
        self._shutdown_timeout = timeout

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        检查所有组件的健康状态。

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "overall": "healthy",
            "components": {},
            "timestamp": time.time(),
        }

        unhealthy_count = 0

        for name, component in self._components.items():
            try:
                component_health = component.health_check()
                health_status["components"][name] = component_health

                if component_health.get("status") != "healthy":
                    unhealthy_count += 1

            except Exception as e:
                health_status["components"][name] = {
                    "status": "unhealthy",
                    "message": f"Health check failed: {e}",
                }
                unhealthy_count += 1

        if unhealthy_count > 0:
            health_status["overall"] = "unhealthy"
            health_status["unhealthy_count"] = unhealthy_count

        return health_status


class LifecycleError(Exception):
    """生命周期异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化生命周期异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)
