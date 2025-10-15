插件API
=======

本页面介绍框架插件系统的API文档。

插件接口
--------

.. autoclass:: framework.interfaces.plugin.PluginInterface
   :members:
   :undoc-members:
   :show-inheritance:

插件管理器
----------

.. autoclass:: framework.core.plugin.PluginManager
   :members:
   :undoc-members:
   :show-inheritance:

插件元数据
----------

.. autoclass:: framework.core.plugin.PluginMetadata
   :members:
   :undoc-members:

插件状态枚举
------------

.. autoclass:: framework.core.plugin.PluginStatus
   :members:
   :undoc-members:

插件异常
--------

.. autoexception:: framework.core.plugin.PluginError
   :show-inheritance:

.. autoexception:: framework.core.plugin.PluginLoadError
   :show-inheritance:

.. autoexception:: framework.core.plugin.PluginDependencyError
   :show-inheritance:

.. autoexception:: framework.core.plugin.PluginConfigurationError
   :show-inheritance:

示例插件
--------

通知插件
~~~~~~~~

.. autoclass:: example_plugins.notification_plugin.NotificationPlugin
   :members:
   :undoc-members:
   :show-inheritance:

分析插件
~~~~~~~~

.. autoclass:: example_plugins.analytics_plugin.AnalyticsPlugin
   :members:
   :undoc-members:
   :show-inheritance:

使用示例
--------

创建自定义插件
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.interfaces.plugin import PluginInterface
    from typing import Dict, Any

    class MyCustomPlugin(PluginInterface):
        """自定义插件示例"""
        
        def __init__(self):
            super().__init__()
            self.name = "my-custom-plugin"
            self.version = "1.0.0"
            self.description = "自定义插件示例"
            self.dependencies = []
            self.optional_dependencies = []
            self.metadata = {
                "category": "utility",
                "tags": ["custom", "example"]
            }
        
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

使用插件管理器
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager

    # 创建插件管理器
    manager = PluginManager(plugin_dirs=["plugins", "example_plugins"])
    
    # 发现插件
    plugins = manager.discover_plugins()
    print(f"发现 {len(plugins)} 个插件")
    
    # 加载插件
    for plugin_info in plugins:
        try:
            manager.load_plugin(plugin_info)
            print(f"插件 {plugin_info.name} 加载成功")
        except Exception as e:
            print(f"插件 {plugin_info.name} 加载失败: {e}")
    
    # 启动插件
    for plugin_name in manager.get_loaded_plugins():
        try:
            manager.start_plugin(plugin_name)
            print(f"插件 {plugin_name} 启动成功")
        except Exception as e:
            print(f"插件 {plugin_name} 启动失败: {e}")

插件配置管理
~~~~~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins"])
    
    # 插件配置
    plugin_config = {
        "notification": {
            "max_notifications": 100,
            "supported_types": ["email", "sms", "push"]
        },
        "analytics": {
            "retention_days": 30,
            "collection_interval": 60
        }
    }
    
    # 加载并配置插件
    plugins = manager.discover_plugins()
    for plugin_info in plugins:
        manager.load_plugin(plugin_info)
        
        # 获取插件配置
        config = plugin_config.get(plugin_info.name, {})
        manager.configure_plugin(plugin_info.name, config)
        
        # 启动插件
        manager.start_plugin(plugin_info.name)

插件依赖管理
~~~~~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins"])
    
    # 发现插件
    plugins = manager.discover_plugins()
    
    # 解析依赖关系
    dependency_graph = manager.resolve_dependencies(plugins)
    
    # 按依赖顺序加载插件
    for plugin_name in dependency_graph:
        plugin_info = next(p for p in plugins if p.name == plugin_name)
        
        # 检查依赖是否满足
        if manager.check_dependencies(plugin_info):
            manager.load_plugin(plugin_info)
            manager.start_plugin(plugin_name)
        else:
            print(f"插件 {plugin_name} 的依赖不满足")

插件生命周期管理
~~~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins"])
    
    # 完整的插件生命周期管理
    plugins = manager.discover_plugins()
    
    for plugin_info in plugins:
        try:
            # 1. 加载插件
            manager.load_plugin(plugin_info)
            print(f"插件 {plugin_info.name} 已加载")
            
            # 2. 配置插件
            config = {"debug": True}
            manager.configure_plugin(plugin_info.name, config)
            print(f"插件 {plugin_info.name} 已配置")
            
            # 3. 启动插件
            manager.start_plugin(plugin_info.name)
            print(f"插件 {plugin_info.name} 已启动")
            
            # 4. 检查健康状态
            health = manager.get_plugin_health(plugin_info.name)
            print(f"插件 {plugin_info.name} 健康状态: {health}")
            
        except Exception as e:
            print(f"插件 {plugin_info.name} 处理失败: {e}")
    
    # 停止所有插件
    for plugin_name in manager.get_loaded_plugins():
        try:
            manager.stop_plugin(plugin_name)
            print(f"插件 {plugin_name} 已停止")
        except Exception as e:
            print(f"停止插件 {plugin_name} 失败: {e}")
    
    # 卸载所有插件
    for plugin_name in manager.get_loaded_plugins():
        try:
            manager.unload_plugin(plugin_name)
            print(f"插件 {plugin_name} 已卸载")
        except Exception as e:
            print(f"卸载插件 {plugin_name} 失败: {e}")

插件热插拔
~~~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager
    import time

    manager = PluginManager(plugin_dirs=["plugins"])
    
    # 初始加载
    plugins = manager.discover_plugins()
    for plugin_info in plugins:
        manager.load_plugin(plugin_info)
        manager.start_plugin(plugin_info.name)
    
    print("所有插件已启动")
    
    # 运行一段时间
    time.sleep(10)
    
    # 热重载插件
    print("开始热重载插件...")
    for plugin_name in manager.get_loaded_plugins():
        try:
            # 停止插件
            manager.stop_plugin(plugin_name)
            
            # 卸载插件
            manager.unload_plugin(plugin_name)
            
            # 重新发现和加载
            new_plugins = manager.discover_plugins()
            plugin_info = next(p for p in new_plugins if p.name == plugin_name)
            
            manager.load_plugin(plugin_info)
            manager.start_plugin(plugin_name)
            
            print(f"插件 {plugin_name} 热重载成功")
            
        except Exception as e:
            print(f"插件 {plugin_name} 热重载失败: {e}")
