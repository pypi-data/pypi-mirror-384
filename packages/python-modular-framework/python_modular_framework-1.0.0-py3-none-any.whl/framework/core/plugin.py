"""
插件系统实现
- 提供插件接口和插件管理器
- 支持插件动态加载和生命周期管理
- 实现插件依赖解析和配置管理

主要功能：
- 插件接口定义
- 插件加载机制
- 插件生命周期管理
- 插件依赖解析
- 插件配置管理

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import os
import importlib
import importlib.util
import inspect
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum


class PluginStatus(Enum):
    """插件状态枚举"""

    UNLOADED = "unloaded"  # 未加载
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    INITIALIZING = "initializing"  # 初始化中
    INITIALIZED = "initialized"  # 已初始化
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态
    UNLOADING = "unloading"  # 卸载中


@dataclass
class PluginInfo:
    """
    插件信息

    包含插件的元数据和配置信息。
    """

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    entry_point: str = "main"
    config_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 插件信息字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "entry_point": self.entry_point,
            "config_schema": self.config_schema,
            "metadata": self.metadata,
        }


class PluginInterface(ABC):
    """
    插件接口

    定义插件的标准行为。
    """

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """
        获取插件信息

        Returns:
            PluginInfo: 插件信息
        """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化插件

        Args:
            config (Dict[str, Any]): 插件配置

        Raises:
            PluginError: 初始化失败时抛出异常
        """

    @abstractmethod
    def start(self) -> None:
        """
        启动插件

        Raises:
            PluginError: 启动失败时抛出异常
        """

    @abstractmethod
    def stop(self) -> None:
        """
        停止插件

        Raises:
            PluginError: 停止失败时抛出异常
        """

    @abstractmethod
    def get_status(self) -> PluginStatus:
        """
        获取插件状态

        Returns:
            PluginStatus: 插件当前状态
        """

    def get_config(self) -> Dict[str, Any]:
        """
        获取插件配置

        Returns:
            Dict[str, Any]: 插件配置
        """
        return {}

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新插件配置

        Args:
            config (Dict[str, Any]): 新配置
        """

    def health_check(self) -> Dict[str, Any]:
        """
        插件健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        return {
            "status": (
                "healthy" if self.get_status() == PluginStatus.RUNNING else "unhealthy"
            ),
            "plugin": self.info.name,
            "version": self.info.version,
        }


class BasePlugin(PluginInterface):
    """
    基础插件类

    提供插件的基础实现。
    """

    def __init__(self, info: PluginInfo):
        """
        初始化基础插件

        Args:
            info (PluginInfo): 插件信息
        """
        self._info = info
        self._status = PluginStatus.UNLOADED
        self._config: Dict[str, Any] = {}
        self._lock = threading.RLock()

    @property
    def info(self) -> PluginInfo:
        """获取插件信息"""
        return self._info

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化插件

        Args:
            config (Dict[str, Any]): 插件配置
        """
        with self._lock:
            if self._status != PluginStatus.LOADED:
                raise PluginError(
                    f"Cannot initialize plugin '{self._info.name}' in status {self._status}"
                )

            self._status = PluginStatus.INITIALIZING
            try:
                self._config = config.copy()
                self._on_initialize(config)
                self._status = PluginStatus.INITIALIZED
            except Exception as e:
                self._status = PluginStatus.ERROR
                raise PluginError(
                    f"Failed to initialize plugin '{self._info.name}': {e}"
                )

    def start(self) -> None:
        """启动插件"""
        with self._lock:
            if self._status != PluginStatus.INITIALIZED:
                raise PluginError(
                    f"Cannot start plugin '{self._info.name}' in status {self._status}"
                )

            self._status = PluginStatus.STARTING
            try:
                self._on_start()
                self._status = PluginStatus.RUNNING
            except Exception as e:
                self._status = PluginStatus.ERROR
                raise PluginError(f"Failed to start plugin '{self._info.name}': {e}")

    def stop(self) -> None:
        """停止插件"""
        with self._lock:
            if self._status not in [PluginStatus.RUNNING, PluginStatus.STARTING]:
                return

            self._status = PluginStatus.STOPPING
            try:
                self._on_stop()
                self._status = PluginStatus.STOPPED
            except Exception as e:
                self._status = PluginStatus.ERROR
                raise PluginError(f"Failed to stop plugin '{self._info.name}': {e}")

    def get_status(self) -> PluginStatus:
        """获取插件状态"""
        with self._lock:
            return self._status

    def get_config(self) -> Dict[str, Any]:
        """获取插件配置"""
        with self._lock:
            return self._config.copy()

    def update_config(self, config: Dict[str, Any]) -> None:
        """更新插件配置"""
        with self._lock:
            self._config.update(config)
            self._on_config_update(config)

    def _on_initialize(self, config: Dict[str, Any]) -> None:
        """
        插件初始化回调

        Args:
            config (Dict[str, Any]): 插件配置
        """

    def _on_start(self) -> None:
        """插件启动回调"""

    def _on_stop(self) -> None:
        """插件停止回调"""

    def _on_config_update(self, config: Dict[str, Any]) -> None:
        """
        配置更新回调

        Args:
            config (Dict[str, Any]): 新配置
        """


class PluginLoader:
    """
    插件加载器

    负责从文件系统加载插件。
    """

    def __init__(self, plugin_dirs: List[str] = None):
        """
        初始化插件加载器

        Args:
            plugin_dirs (List[str]): 插件目录列表
        """
        self.plugin_dirs = plugin_dirs or []
        self._loaded_modules: Dict[str, Any] = {}

    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """
        发现插件

        Returns:
            Dict[str, PluginInfo]: 发现的插件信息字典
        """
        plugins = {}

        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)

                if os.path.isdir(item_path):
                    # 目录形式的插件
                    plugin_instance = self._load_plugin_from_dir(item_path)
                    if plugin_instance and hasattr(plugin_instance, "info"):
                        plugins[plugin_instance.info.name] = plugin_instance.info
                elif item.endswith(".py") and not item.startswith("__"):
                    # 文件形式的插件
                    plugin_instance = self._load_plugin_from_file(item_path)
                    if plugin_instance and hasattr(plugin_instance, "info"):
                        plugins[plugin_instance.info.name] = plugin_instance.info

        return plugins

    def load_plugin(self, plugin_path: str) -> Optional[PluginInterface]:
        """
        加载插件

        Args:
            plugin_path (str): 插件路径

        Returns:
            Optional[PluginInterface]: 插件实例，如果加载失败则返回None
        """
        try:
            if os.path.isdir(plugin_path):
                return self._load_plugin_from_dir(plugin_path)
            else:
                return self._load_plugin_from_file(plugin_path)
        except Exception as e:
            print(f"Failed to load plugin from {plugin_path}: {e}")
            return None

    def _load_plugin_from_dir(self, plugin_dir: str) -> Optional[PluginInterface]:
        """
        从目录加载插件

        Args:
            plugin_dir (str): 插件目录路径

        Returns:
            Optional[PluginInterface]: 插件实例
        """
        # 查找插件入口文件
        entry_files = ["__init__.py", "main.py", "plugin.py"]
        entry_file = None

        for file_name in entry_files:
            file_path = os.path.join(plugin_dir, file_name)
            if os.path.exists(file_path):
                entry_file = file_path
                break

        if not entry_file:
            return None

        return self._load_plugin_from_file(entry_file)

    def _load_plugin_from_file(self, plugin_file: str) -> Optional[PluginInterface]:
        """
        从文件加载插件

        Args:
            plugin_file (str): 插件文件路径

        Returns:
            Optional[PluginInterface]: 插件实例
        """
        try:
            # 动态导入模块
            module_name = f"plugin_{int(time.time() * 1000000)}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return None

            # 创建插件实例
            plugin_instance = plugin_class()

            # 验证插件接口
            if not isinstance(plugin_instance, PluginInterface):
                return None

            return plugin_instance

        except Exception as e:
            print(f"Failed to load plugin from file {plugin_file}: {e}")
            return None

    def _find_plugin_class(self, module: Any) -> Optional[Type[PluginInterface]]:
        """
        查找插件类

        Args:
            module: 模块对象

        Returns:
            Optional[Type[PluginInterface]]: 插件类
        """
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, PluginInterface)
                and obj != PluginInterface
                and obj != BasePlugin
            ):
                return obj
        return None


class PluginManager:
    """
    插件管理器

    管理插件的加载、生命周期和依赖关系。
    """

    def __init__(self, plugin_dirs: List[str] = None):
        """
        初始化插件管理器

        Args:
            plugin_dirs (List[str]): 插件目录列表
        """
        self._loader = PluginLoader(plugin_dirs)
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_status: Dict[str, PluginStatus] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """
        发现插件

        Returns:
            Dict[str, PluginInfo]: 发现的插件信息字典
        """
        return self._loader.discover_plugins()

    def load_plugin(
        self, name: str, plugin_path: str = None, config: Dict[str, Any] = None
    ) -> bool:
        """
        加载插件

        Args:
            name (str): 插件名称
            plugin_path (str): 插件路径（可选）
            config (Dict[str, Any]): 插件配置（可选）

        Returns:
            bool: 是否加载成功
        """
        with self._lock:
            if name in self._plugins:
                return True  # 已经加载

            try:
                if plugin_path:
                    plugin = self._loader.load_plugin(plugin_path)
                else:
                    # 从发现的插件中查找
                    discovered = self.discover_plugins()
                    if name not in discovered:
                        return False

                    # 这里需要实现从发现的插件信息加载插件的逻辑
                    return False

                if not plugin:
                    return False

                # 验证插件名称
                if plugin.info.name != name:
                    return False

                # 注册插件
                self._plugins[name] = plugin
                self._plugin_status[name] = PluginStatus.LOADED
                self._plugin_configs[name] = config or {}

                # 设置插件状态为已加载
                plugin._status = PluginStatus.LOADED

                return True

            except Exception as e:
                print(f"Failed to load plugin '{name}': {e}")
                return False

    def unload_plugin(self, name: str) -> bool:
        """
        卸载插件

        Args:
            name (str): 插件名称

        Returns:
            bool: 是否卸载成功
        """
        with self._lock:
            if name not in self._plugins:
                return False

            try:
                plugin = self._plugins[name]

                # 如果插件正在运行，先停止
                if plugin.get_status() in [PluginStatus.RUNNING, PluginStatus.STARTING]:
                    plugin.stop()

                # 移除插件
                del self._plugins[name]
                del self._plugin_status[name]
                del self._plugin_configs[name]

                return True

            except Exception as e:
                print(f"Failed to unload plugin '{name}': {e}")
                return False

    def initialize_plugin(self, name: str, config: Dict[str, Any] = None) -> bool:
        """
        初始化插件

        Args:
            name (str): 插件名称
            config (Dict[str, Any]): 插件配置

        Returns:
            bool: 是否初始化成功
        """
        with self._lock:
            if name not in self._plugins:
                return False

            try:
                plugin = self._plugins[name]
                plugin_config = config or self._plugin_configs.get(name, {})

                plugin.initialize(plugin_config)
                self._plugin_status[name] = PluginStatus.INITIALIZED

                return True

            except Exception as e:
                print(f"Failed to initialize plugin '{name}': {e}")
                self._plugin_status[name] = PluginStatus.ERROR
                return False

    def start_plugin(self, name: str) -> bool:
        """
        启动插件

        Args:
            name (str): 插件名称

        Returns:
            bool: 是否启动成功
        """
        with self._lock:
            if name not in self._plugins:
                return False

            try:
                plugin = self._plugins[name]
                plugin.start()
                self._plugin_status[name] = PluginStatus.RUNNING

                return True

            except Exception as e:
                print(f"Failed to start plugin '{name}': {e}")
                self._plugin_status[name] = PluginStatus.ERROR
                return False

    def stop_plugin(self, name: str) -> bool:
        """
        停止插件

        Args:
            name (str): 插件名称

        Returns:
            bool: 是否停止成功
        """
        with self._lock:
            if name not in self._plugins:
                return False

            try:
                plugin = self._plugins[name]
                plugin.stop()
                self._plugin_status[name] = PluginStatus.STOPPED

                return True

            except Exception as e:
                print(f"Failed to stop plugin '{name}': {e}")
                self._plugin_status[name] = PluginStatus.ERROR
                return False

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """
        获取插件实例

        Args:
            name (str): 插件名称

        Returns:
            Optional[PluginInterface]: 插件实例
        """
        with self._lock:
            return self._plugins.get(name)

    def get_plugin_status(self, name: str) -> Optional[PluginStatus]:
        """
        获取插件状态

        Args:
            name (str): 插件名称

        Returns:
            Optional[PluginStatus]: 插件状态
        """
        with self._lock:
            return self._plugin_status.get(name)

    def list_plugins(self) -> List[str]:
        """
        获取所有插件名称列表

        Returns:
            List[str]: 插件名称列表
        """
        with self._lock:
            return list(self._plugins.keys())

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """
        获取插件信息

        Args:
            name (str): 插件名称

        Returns:
            Optional[PluginInfo]: 插件信息
        """
        with self._lock:
            plugin = self._plugins.get(name)
            return plugin.info if plugin else None

    def health_check(self) -> Dict[str, Any]:
        """
        插件健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        with self._lock:
            health_status = {"overall": "healthy", "plugins": {}}

            for name, plugin in self._plugins.items():
                try:
                    plugin_health = plugin.health_check()
                    health_status["plugins"][name] = plugin_health

                    if plugin_health.get("status") != "healthy":
                        health_status["overall"] = "unhealthy"

                except Exception as e:
                    health_status["plugins"][name] = {
                        "status": "error",
                        "error": str(e),
                    }
                    health_status["overall"] = "unhealthy"

            return health_status

    def clear(self) -> None:
        """清空所有插件"""
        with self._lock:
            # 停止所有插件
            for name in list(self._plugins.keys()):
                self.stop_plugin(name)
                self.unload_plugin(name)

            self._plugins.clear()
            self._plugin_status.clear()
            self._plugin_configs.clear()


# 异常类定义
class PluginError(Exception):
    """插件异常基类"""



class PluginLoadError(PluginError):
    """插件加载异常"""



class PluginInitializationError(PluginError):
    """插件初始化异常"""



class PluginStartError(PluginError):
    """插件启动异常"""



class PluginStopError(PluginError):
    """插件停止异常"""

