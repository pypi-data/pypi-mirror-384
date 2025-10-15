插件系统
========

插件系统提供了动态扩展框架功能的能力，支持热插拔和生命周期管理。

插件概述
--------

插件是框架的扩展模块，可以在运行时动态加载、配置和管理。插件系统支持依赖管理、配置管理和生命周期控制。

插件特性
--------

* **动态加载**: 运行时发现和加载插件
* **生命周期管理**: 初始化、启动、停止、卸载
* **依赖管理**: 自动解析插件依赖关系
* **配置管理**: 插件级别的配置系统
* **热插拔**: 支持运行时加载和卸载插件

插件结构
--------

插件元数据
~~~~~~~~~~

每个插件都需要定义元数据::

    class MyPlugin(PluginInterface):
        def __init__(self):
            super().__init__()
            self.name = "my-plugin"
            self.version = "1.0.0"
            self.description = "示例插件"
            self.dependencies = ["database-plugin"]
            self.optional_dependencies = ["cache-plugin"]
            self.metadata = {
                "category": "utility",
                "tags": ["example", "demo"]
            }

插件接口
~~~~~~~~

所有插件都必须实现 ``PluginInterface``::

    from framework.interfaces.plugin import PluginInterface
    from typing import Dict, Any

    class MyPlugin(PluginInterface):
        def initialize(self, config: Dict[str, Any]) -> None:
            """初始化插件"""
            pass
        
        def start(self) -> None:
            """启动插件"""
            pass
        
        def stop(self) -> None:
            """停止插件"""
            pass
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {"status": "healthy"}

内置插件
--------

通知插件 (NotificationPlugin)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供通知功能::

    from example_plugins.notification_plugin import NotificationPlugin

    plugin = NotificationPlugin()
    plugin.initialize({"max_notifications": 100})
    plugin.start()
    plugin.send_notification("user@example.com", "Hello World!")

分析插件 (AnalyticsPlugin)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供数据分析功能::

    from example_plugins.analytics_plugin import AnalyticsPlugin

    plugin = AnalyticsPlugin()
    plugin.initialize({"retention_days": 30})
    plugin.start()
    plugin.track_event("user_login", {"user_id": 123})

创建自定义插件
--------------

定义插件类
~~~~~~~~~~

.. code-block:: python

    from framework.interfaces.plugin import PluginInterface
    from typing import Dict, Any

    class CustomPlugin(PluginInterface):
        """自定义插件示例"""
        
        def __init__(self):
            super().__init__()
            self.name = "custom-plugin"
            self.version = "1.0.0"
            self.description = "自定义插件示例"
            self.dependencies = []
            self.optional_dependencies = []
            self.metadata = {
                "category": "utility",
                "tags": ["custom", "example"]
            }
            self.running = False
        
        def initialize(self, config: Dict[str, Any]) -> None:
            """初始化插件"""
            print(f"初始化插件: {self.name}")
            self.config = config
        
        def start(self) -> None:
            """启动插件"""
            print(f"启动插件: {self.name}")
            self.running = True
        
        def stop(self) -> None:
            """停止插件"""
            print(f"停止插件: {self.name}")
            self.running = False
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy" if self.running else "stopped",
                "plugin_name": self.name,
                "version": self.version
            }

插件管理
--------

插件发现
~~~~~~~~

插件管理器可以自动发现插件::

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins", "example_plugins"])
    plugins = manager.discover_plugins()
    print(f"发现 {len(plugins)} 个插件")

插件加载
~~~~~~~~

加载发现的插件::

    for plugin_info in plugins:
        try:
            manager.load_plugin(plugin_info)
            print(f"插件 {plugin_info.name} 加载成功")
        except Exception as e:
            print(f"插件 {plugin_info.name} 加载失败: {e}")

插件启动
~~~~~~~~

启动已加载的插件::

    for plugin_name in manager.get_loaded_plugins():
        try:
            manager.start_plugin(plugin_name)
            print(f"插件 {plugin_name} 启动成功")
        except Exception as e:
            print(f"插件 {plugin_name} 启动失败: {e}")

插件配置
--------

插件可以通过配置文件进行配置::

    plugins:
      notification:
        max_notifications: 100
        supported_types: ["email", "sms", "push"]
      analytics:
        retention_days: 30
        collection_interval: 60

在插件中访问配置::

    class MyPlugin(PluginInterface):
        def initialize(self, config: Dict[str, Any]) -> None:
            plugin_config = config.get("plugins", {}).get(self.name, {})
            self.max_items = plugin_config.get("max_items", 1000)

依赖管理
--------

声明依赖
~~~~~~~~

插件可以声明对其他插件的依赖::

    class MyPlugin(PluginInterface):
        def __init__(self):
            super().__init__()
            self.dependencies = ["database-plugin", "cache-plugin"]
            self.optional_dependencies = ["logging-plugin"]

依赖解析
~~~~~~~~

插件管理器会自动解析依赖关系::

    manager = PluginManager(plugin_dirs=["plugins"])
    plugins = manager.discover_plugins()
    dependency_graph = manager.resolve_dependencies(plugins)

按依赖顺序加载插件::

    for plugin_name in dependency_graph:
        plugin_info = next(p for p in plugins if p.name == plugin_name)
        if manager.check_dependencies(plugin_info):
            manager.load_plugin(plugin_info)
            manager.start_plugin(plugin_name)

生命周期管理
------------

完整的生命周期管理::

    manager = PluginManager(plugin_dirs=["plugins"])
    plugins = manager.discover_plugins()
    
    for plugin_info in plugins:
        try:
            # 1. 加载插件
            manager.load_plugin(plugin_info)
            
            # 2. 配置插件
            config = {"debug": True}
            manager.configure_plugin(plugin_info.name, config)
            
            # 3. 启动插件
            manager.start_plugin(plugin_info.name)
            
            # 4. 检查健康状态
            health = manager.get_plugin_health(plugin_info.name)
            
        except Exception as e:
            print(f"插件 {plugin_info.name} 处理失败: {e}")

停止和卸载::

    # 停止所有插件
    for plugin_name in manager.get_loaded_plugins():
        manager.stop_plugin(plugin_name)
    
    # 卸载所有插件
    for plugin_name in manager.get_loaded_plugins():
        manager.unload_plugin(plugin_name)

热插拔
------

插件支持运行时热插拔::

    # 热重载插件
    for plugin_name in manager.get_loaded_plugins():
        # 停止插件
        manager.stop_plugin(plugin_name)
        
        # 卸载插件
        manager.unload_plugin(plugin_name)
        
        # 重新发现和加载
        new_plugins = manager.discover_plugins()
        plugin_info = next(p for p in new_plugins if p.name == plugin_name)
        
        manager.load_plugin(plugin_info)
        manager.start_plugin(plugin_name)

最佳实践
--------

* 保持插件的单一职责
* 正确处理插件生命周期
* 使用配置而不是硬编码
* 提供有意义的健康状态信息
* 正确处理依赖关系
* 实现优雅的错误处理

更多信息
--------

* :doc:`../api/plugins` - 插件API参考
* :doc:`../development/creating_plugins` - 创建插件指南
* :doc:`../examples/plugin_usage` - 使用示例
