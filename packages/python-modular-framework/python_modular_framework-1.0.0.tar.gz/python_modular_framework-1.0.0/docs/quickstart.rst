快速开始
========

本指南将帮助您快速上手Python模块化框架，创建一个简单的应用程序。

安装
----

使用pip安装框架::

    pip install python-modular-framework

或者从源码安装::

    git clone https://github.com/your-org/python-modular-framework.git
    cd python-modular-framework
    pip install -e .

创建第一个应用
--------------

创建一个简单的应用程序只需要几行代码::

    from framework.core.application import Application

    # 创建应用实例
    app = Application(name="my-first-app", version="1.0.0")
    
    # 配置应用
    app.configure({
        "debug": True,
        "log_level": "INFO"
    })
    
    # 启动应用
    app.start()
    
    # 应用运行中...
    
    # 停止应用
    app.stop()

运行这个脚本，您将看到应用启动、运行和停止的日志输出。

添加组件
--------

框架的核心是组件系统。让我们创建一个简单的组件::

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any

    class MyComponent(ComponentInterface):
        """我的第一个组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.message = "Hello from MyComponent!"
        
        def initialize(self) -> None:
            """初始化组件"""
            print(f"初始化组件: {self.name}")
        
        def start(self) -> None:
            """启动组件"""
            print(f"启动组件: {self.name}")
            print(self.message)
        
        def stop(self) -> None:
            """停止组件"""
            print(f"停止组件: {self.name}")
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy",
                "message": "组件运行正常"
            }

现在将组件添加到应用中::

    from framework.core.application import Application
    from my_component import MyComponent

    app = Application(name="my-app", version="1.0.0")
    
    # 注册组件
    app.register_component(MyComponent("my-component", app.config))
    
    # 配置并启动
    app.configure({"debug": True})
    app.start()

使用配置
--------

框架支持灵活的配置管理::

    app.configure({
        "debug": True,
        "log_level": "DEBUG",
        "components": {
            "my-component": {
                "setting1": "value1",
                "setting2": 42
            }
        }
    })

组件可以通过配置获取设置::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            # 获取组件特定配置
            self.setting1 = config.get(f"components.{name}.setting1", "default")
            self.setting2 = config.get(f"components.{name}.setting2", 0)

中间件系统
----------

框架支持中间件系统来处理请求::

    from framework.core.middleware import MiddlewareInterface
    from typing import Dict, Any

    class LoggingMiddleware(MiddlewareInterface):
        """日志中间件"""
        
        def __init__(self, name: str):
            super().__init__(name)
        
        def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理请求"""
            print(f"处理请求: {request.get('path', 'unknown')}")
            return request
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """处理响应"""
            print(f"响应状态: {response.get('status', 'unknown')}")
            return response

注册中间件::

    from framework.core.middleware import MiddlewareManager

    manager = MiddlewareManager()
    manager.register(LoggingMiddleware("logging"))
    
    # 处理请求
    request = {"path": "/api/test", "method": "GET"}
    response = manager.process_request(request)

插件系统
--------

框架支持动态插件加载::

    from framework.interfaces.plugin import PluginInterface
    from typing import Dict, Any

    class MyPlugin(PluginInterface):
        """我的插件"""
        
        def __init__(self):
            super().__init__()
            self.name = "my-plugin"
            self.version = "1.0.0"
            self.description = "示例插件"
        
        def initialize(self, config: Dict[str, Any]) -> None:
            """初始化插件"""
            print("插件初始化")
        
        def start(self) -> None:
            """启动插件"""
            print("插件启动")
        
        def stop(self) -> None:
            """停止插件"""
            print("插件停止")

加载插件::

    from framework.core.plugin import PluginManager

    manager = PluginManager(plugin_dirs=["plugins"])
    plugins = manager.discover_plugins()
    
    for plugin in plugins:
        manager.load_plugin(plugin)
        manager.start_plugin(plugin)

下一步
------

现在您已经了解了框架的基本用法，可以继续学习:

* :doc:`concepts/overview` - 了解框架的核心概念
* :doc:`development/creating_components` - 学习如何创建组件
* :doc:`examples/basic_usage` - 查看更多示例

如果您遇到问题，请查看 :doc:`troubleshooting/common_issues` 页面。
