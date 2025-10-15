组件API
=======

本页面介绍框架组件系统的API文档。

组件接口
--------

.. autoclass:: framework.interfaces.component.ComponentInterface
   :members:
   :undoc-members:
   :show-inheritance:

认证组件
--------

.. autoclass:: components.auth.component.AuthComponent
   :members:
   :undoc-members:
   :show-inheritance:

认证服务接口
~~~~~~~~~~~~

.. autoclass:: components.auth.interfaces.AuthServiceInterface
   :members:
   :undoc-members:
   :show-inheritance:

认证服务实现
~~~~~~~~~~~~

.. autoclass:: components.auth.service.AuthService
   :members:
   :undoc-members:
   :show-inheritance:

认证模型
~~~~~~~~

.. autoclass:: components.auth.models.User
   :members:
   :undoc-members:

.. autoclass:: components.auth.models.Permission
   :members:
   :undoc-members:

.. autoclass:: components.auth.models.Role
   :members:
   :undoc-members:

缓存组件
--------

.. autoclass:: components.common.cache.component.CacheComponent
   :members:
   :undoc-members:
   :show-inheritance:

缓存策略
~~~~~~~~

.. autoclass:: components.common.cache.strategy.CacheStrategy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: components.common.cache.strategy.LRUStrategy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: components.common.cache.strategy.LFUStrategy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: components.common.cache.strategy.FIFOStrategy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: components.common.cache.strategy.TTLStrategy
   :members:
   :undoc-members:
   :show-inheritance:

缓存配置
~~~~~~~~

.. autoclass:: components.common.cache.config.CacheConfig
   :members:
   :undoc-members:

数据库组件
----------

.. autoclass:: components.common.database.component.DatabaseComponent
   :members:
   :undoc-members:
   :show-inheritance:

连接池
~~~~~~

.. autoclass:: components.common.database.pool.ConnectionPool
   :members:
   :undoc-members:
   :show-inheritance:

数据库配置
~~~~~~~~~~

.. autoclass:: components.common.database.config.DatabaseConfig
   :members:
   :undoc-members:

日志组件
--------

.. autoclass:: components.common.logging.component.LoggingComponent
   :members:
   :undoc-members:
   :show-inheritance:

日志格式化器
~~~~~~~~~~~~

.. autoclass:: components.common.logging.formatter.LogFormatter
   :members:
   :undoc-members:
   :show-inheritance:

日志配置
~~~~~~~~

.. autoclass:: components.common.logging.config.LoggingConfig
   :members:
   :undoc-members:

支付组件
--------

.. autoclass:: components.payment.component.PaymentComponent
   :members:
   :undoc-members:
   :show-inheritance:

支付服务接口
~~~~~~~~~~~~

.. autoclass:: components.payment.interfaces.PaymentServiceInterface
   :members:
   :undoc-members:
   :show-inheritance:

支付服务实现
~~~~~~~~~~~~

.. autoclass:: components.payment.service.PaymentService
   :members:
   :undoc-members:
   :show-inheritance:

支付模型
~~~~~~~~

.. autoclass:: components.payment.models.Payment
   :members:
   :undoc-members:

.. autoclass:: components.payment.models.PaymentMethod
   :members:
   :undoc-members:

.. autoclass:: components.payment.models.Refund
   :members:
   :undoc-members:

用户组件
--------

.. autoclass:: components.user.component.UserComponent
   :members:
   :undoc-members:
   :show-inheritance:

用户服务接口
~~~~~~~~~~~~

.. autoclass:: components.user.interfaces.UserServiceInterface
   :members:
   :undoc-members:
   :show-inheritance:

用户服务实现
~~~~~~~~~~~~

.. autoclass:: components.user.service.UserService
   :members:
   :undoc-members:
   :show-inheritance:

用户模型
~~~~~~~~

.. autoclass:: components.user.models.User
   :members:
   :undoc-members:

.. autoclass:: components.user.models.UserCreate
   :members:
   :undoc-members:

.. autoclass:: components.user.models.UserUpdate
   :members:
   :undoc-members:

.. autoclass:: components.user.models.UserSearch
   :members:
   :undoc-members:

使用示例
--------

创建自定义组件
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any

    class MyCustomComponent(ComponentInterface):
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

使用认证组件
~~~~~~~~~~~~

.. code-block:: python

    from components.auth.component import AuthComponent
    from framework.core.config import Config

    config = Config()
    auth_component = AuthComponent("auth", config)
    
    # 初始化并启动
    auth_component.initialize()
    auth_component.start()
    
    # 使用认证服务
    auth_service = auth_component.get_service()
    user = auth_service.authenticate("username", "password")

使用缓存组件
~~~~~~~~~~~~

.. code-block:: python

    from components.common.cache.component import CacheComponent
    from framework.core.config import Config

    config = Config()
    cache_component = CacheComponent("cache", config)
    
    # 初始化并启动
    cache_component.initialize()
    cache_component.start()
    
    # 使用缓存
    cache_component.set("key", "value", ttl=3600)
    value = cache_component.get("key")

使用数据库组件
~~~~~~~~~~~~~~

.. code-block:: python

    from components.common.database.component import DatabaseComponent
    from framework.core.config import Config

    config = Config()
    db_component = DatabaseComponent("database", config)
    
    # 初始化并启动
    db_component.initialize()
    db_component.start()
    
    # 执行查询
    with db_component.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
