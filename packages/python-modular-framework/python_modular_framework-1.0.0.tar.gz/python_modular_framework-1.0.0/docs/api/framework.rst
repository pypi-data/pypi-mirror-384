框架核心API
===========

本页面介绍框架核心模块的API文档。

应用类 (Application)
--------------------

.. autoclass:: framework.core.application.Application
   :members:
   :undoc-members:
   :show-inheritance:

应用状态枚举
------------

.. autoclass:: framework.core.application.ApplicationStatus
   :members:
   :undoc-members:

配置管理 (Config)
-----------------

.. autoclass:: framework.core.config.Config
   :members:
   :undoc-members:
   :show-inheritance:

配置构建器
----------

.. autoclass:: framework.core.config.ConfigBuilder
   :members:
   :undoc-members:
   :show-inheritance:

依赖注入容器 (Container)
------------------------

.. autoclass:: framework.core.container.Container
   :members:
   :undoc-members:
   :show-inheritance:

生命周期管理器
--------------

.. autoclass:: framework.core.lifecycle.LifecycleManager
   :members:
   :undoc-members:
   :show-inheritance:

中间件管理器
------------

.. autoclass:: framework.core.middleware.MiddlewareManager
   :members:
   :undoc-members:
   :show-inheritance:

插件管理器
----------

.. autoclass:: framework.core.plugin.PluginManager
   :members:
   :undoc-members:
   :show-inheritance:

依赖解析器
----------

.. autoclass:: framework.core.dependency_resolver.DependencyResolver
   :members:
   :undoc-members:
   :show-inheritance:

组件发现器
----------

.. autoclass:: framework.core.dependency_resolver.ComponentDiscovery
   :members:
   :undoc-members:
   :show-inheritance:

异常类
------

.. autoexception:: framework.core.exceptions.FrameworkError
   :show-inheritance:

.. autoexception:: framework.core.exceptions.ComponentError
   :show-inheritance:

.. autoexception:: framework.core.exceptions.ConfigurationError
   :show-inheritance:

.. autoexception:: framework.core.exceptions.DependencyError
   :show-inheritance:

.. autoexception:: framework.core.exceptions.MiddlewareError
   :show-inheritance:

.. autoexception:: framework.core.exceptions.PluginError
   :show-inheritance:

使用示例
--------

创建应用
~~~~~~~~

.. code-block:: python

    from framework.core.application import Application

    app = Application(name="my-app", version="1.0.0")
    app.configure({"debug": True})
    app.start()

配置管理
~~~~~~~~

.. code-block:: python

    from framework.core.config import Config

    config = Config()
    config.set("database.host", "localhost")
    config.set("database.port", 5432)
    
    host = config.get("database.host")
    port = config.get("database.port", 3306)

依赖注入
~~~~~~~~

.. code-block:: python

    from framework.core.container import Container

    container = Container()
    
    # 注册服务
    container.register_singleton("database", DatabaseService)
    container.register_transient("user_service", UserService)
    
    # 获取服务
    db = container.get("database")
    user_service = container.get("user_service")

中间件管理
~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager, LoggingMiddleware

    manager = MiddlewareManager()
    manager.register(LoggingMiddleware("logging"))
    
    # 处理请求
    request = {"path": "/api/test"}
    response = manager.process_request(request)

插件管理
~~~~~~~~

.. code-block:: python

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins"])
    plugins = manager.discover_plugins()
    
    for plugin in plugins:
        manager.load_plugin(plugin)
        manager.start_plugin(plugin)
