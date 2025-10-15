组件系统
========

组件是框架的核心概念，提供了模块化和可复用的功能单元。

组件概述
--------

组件是框架中可独立开发、测试和部署的功能模块。每个组件都实现了 ``ComponentInterface`` 接口，具有完整的生命周期管理。

组件特性
--------

* **生命周期管理**: 初始化、启动、停止等完整生命周期
* **依赖注入**: 自动依赖解析和注入
* **配置管理**: 灵活的配置系统
* **健康检查**: 实时健康状态监控
* **类型安全**: 完整的类型注解支持

内置组件
--------

框架提供了以下内置组件:

认证组件 (AuthComponent)
~~~~~~~~~~~~~~~~~~~~~~~~

提供用户认证和授权功能::

    from components.auth.component import AuthComponent

    auth = AuthComponent("auth", config)
    auth.initialize()
    auth.start()

缓存组件 (CacheComponent)
~~~~~~~~~~~~~~~~~~~~~~~~~~

提供多种缓存策略::

    from components.common.cache.component import CacheComponent

    cache = CacheComponent("cache", config)
    cache.set("key", "value", ttl=3600)
    value = cache.get("key")

数据库组件 (DatabaseComponent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供数据库连接和操作::

    from components.common.database.component import DatabaseComponent

    db = DatabaseComponent("database", config)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")

日志组件 (LoggingComponent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供结构化日志功能::

    from components.common.logging.component import LoggingComponent

    logger = LoggingComponent("logging", config)
    logger.info("应用启动")

用户组件 (UserComponent)
~~~~~~~~~~~~~~~~~~~~~~~~

提供用户管理功能::

    from components.user.component import UserComponent

    user_mgr = UserComponent("user", config)
    user = user_mgr.create_user("username", "email@example.com")

支付组件 (PaymentComponent)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供支付处理功能::

    from components.payment.component import PaymentComponent

    payment = PaymentComponent("payment", config)
    result = payment.process_payment(amount=100, method="credit_card")

创建自定义组件
--------------

定义组件类
~~~~~~~~~~

.. code-block:: python

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any

    class MyComponent(ComponentInterface):
        """自定义组件示例"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.data = {}
        
        def initialize(self) -> None:
            """初始化组件"""
            print(f"初始化组件: {self.name}")
        
        def start(self) -> None:
            """启动组件"""
            print(f"启动组件: {self.name}")
        
        def stop(self) -> None:
            """停止组件"""
            print(f"停止组件: {self.name}")
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy",
                "data_count": len(self.data)
            }

注册组件
~~~~~~~~

.. code-block:: python

    from framework.core.application import Application

    app = Application("my-app", "1.0.0")
    app.register_component(MyComponent("my-component", app.config))

组件配置
--------

组件可以通过配置文件进行配置::

    components:
      my-component:
        setting1: value1
        setting2: 42
        nested:
          option: true

在组件中访问配置::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.setting1 = config.get(f"components.{name}.setting1")
            self.setting2 = config.get(f"components.{name}.setting2", 0)

组件依赖
--------

声明依赖
~~~~~~~~

组件可以声明对其他组件的依赖::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.dependencies = ["database", "cache"]

依赖注入
~~~~~~~~

框架会自动解析和注入依赖::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.database = None
            self.cache = None
        
        def initialize(self) -> None:
            # 框架会自动注入依赖
            self.database = self.get_dependency("database")
            self.cache = self.get_dependency("cache")

最佳实践
--------

* 保持组件的单一职责
* 使用类型注解提高代码可读性
* 实现完整的生命周期方法
* 提供有意义的健康状态信息
* 使用配置而不是硬编码
* 正确处理异常和错误情况

更多信息
--------

* :doc:`../api/components` - 组件API参考
* :doc:`../development/creating_components` - 创建组件指南
* :doc:`../examples/basic_usage` - 使用示例
