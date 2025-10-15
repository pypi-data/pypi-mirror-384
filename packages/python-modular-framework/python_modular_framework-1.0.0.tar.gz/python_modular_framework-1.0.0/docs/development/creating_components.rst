创建组件指南
============

本指南详细介绍如何创建自定义组件，包括最佳实践和常见模式。

组件设计原则
------------

单一职责原则
~~~~~~~~~~~~

每个组件应该只负责一个特定的功能::

    class UserComponent(ComponentInterface):
        """用户管理组件 - 只负责用户相关操作"""
        pass
    
    class EmailComponent(ComponentInterface):
        """邮件组件 - 只负责邮件发送"""
        pass

接口隔离原则
~~~~~~~~~~~~

组件应该只依赖它需要的接口::

    class UserComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            # 只声明实际需要的依赖
            self.dependencies = ["database"]

开闭原则
~~~~~~~~

组件应该对扩展开放，对修改关闭::

    class BaseComponent(ComponentInterface):
        """基础组件，提供通用功能"""
        def get_health_status(self) -> Dict[str, Any]:
            return {"status": "healthy"}
    
    class ExtendedComponent(BaseComponent):
        """扩展组件，添加特定功能"""
        def get_health_status(self) -> Dict[str, Any]:
            base_status = super().get_health_status()
            base_status["extended"] = True
            return base_status

组件模板
--------

基础组件模板
~~~~~~~~~~~~

.. code-block:: python

    """
    组件名称组件

    该组件提供[功能描述]功能。
    
    作者：[作者名]
    创建时间：[日期]
    最后修改：[日期]
    """

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, Optional
    import logging

    class MyComponent(ComponentInterface):
        """
        我的组件
        
        该组件提供[具体功能描述]。
        
        Args:
            name: 组件名称
            config: 配置对象
        """
        
        def __init__(self, name: str, config: Config):
            """
            初始化组件
            
            Args:
                name: 组件名称
                config: 配置对象
            """
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self._initialized = False
            self._started = False
        
        def initialize(self) -> None:
            """
            初始化组件
            
            在组件启动前调用，用于设置初始状态。
            """
            if self._initialized:
                self.logger.warning("组件已经初始化")
                return
            
            try:
                # 初始化逻辑
                self.logger.info(f"初始化组件: {self.name}")
                self._initialized = True
            except Exception as e:
                self.logger.error(f"组件初始化失败: {e}")
                raise
        
        def start(self) -> None:
            """
            启动组件
            
            在组件初始化后调用，用于启动服务。
            """
            if not self._initialized:
                raise RuntimeError("组件未初始化")
            
            if self._started:
                self.logger.warning("组件已经启动")
                return
            
            try:
                # 启动逻辑
                self.logger.info(f"启动组件: {self.name}")
                self._started = True
            except Exception as e:
                self.logger.error(f"组件启动失败: {e}")
                raise
        
        def stop(self) -> None:
            """
            停止组件
            
            在应用关闭时调用，用于清理资源。
            """
            if not self._started:
                self.logger.warning("组件未启动")
                return
            
            try:
                # 停止逻辑
                self.logger.info(f"停止组件: {self.name}")
                self._started = False
            except Exception as e:
                self.logger.error(f"组件停止失败: {e}")
                raise
        
        def get_health_status(self) -> Dict[str, Any]:
            """
            获取组件健康状态
            
            Returns:
                包含健康状态信息的字典
            """
            return {
                "status": "healthy" if self._started else "stopped",
                "initialized": self._initialized,
                "started": self._started,
                "component_name": self.name
            }

服务组件模板
~~~~~~~~~~~~

.. code-block:: python

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any, Optional, List
    import logging

    class ServiceComponent(ComponentInterface):
        """
        服务组件
        
        提供[服务描述]的组件。
        """
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.service = None
        
        def initialize(self) -> None:
            """初始化服务"""
            self.logger.info(f"初始化服务组件: {self.name}")
            # 初始化服务
            self.service = self._create_service()
        
        def start(self) -> None:
            """启动服务"""
            if self.service:
                self.service.start()
                self.logger.info(f"服务组件已启动: {self.name}")
        
        def stop(self) -> None:
            """停止服务"""
            if self.service:
                self.service.stop()
                self.logger.info(f"服务组件已停止: {self.name}")
        
        def _create_service(self):
            """创建服务实例"""
            # 服务创建逻辑
            pass
        
        def get_service(self):
            """获取服务实例"""
            return self.service

配置管理
--------

组件配置
~~~~~~~~

组件可以通过配置进行定制::

    # config.yaml
    components:
      my-component:
        setting1: value1
        setting2: 42
        nested:
          option: true
          list: [1, 2, 3]

访问配置::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            # 获取组件配置
            self.setting1 = config.get(f"components.{name}.setting1", "default")
            self.setting2 = config.get(f"components.{name}.setting2", 0)
            self.nested_option = config.get(f"components.{name}.nested.option", False)

配置验证
~~~~~~~~

验证配置的有效性::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self._validate_config(config)
        
        def _validate_config(self, config: Config) -> None:
            """验证配置"""
            required_settings = [
                f"components.{self.name}.setting1",
                f"components.{self.name}.setting2"
            ]
            
            for setting in required_settings:
                if not config.has(setting):
                    raise ValueError(f"缺少必需配置: {setting}")

依赖管理
--------

声明依赖
~~~~~~~~

组件可以声明对其他组件的依赖::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.dependencies = ["database", "cache"]
            self.optional_dependencies = ["logging"]

依赖注入
~~~~~~~~

框架会自动注入依赖::

    class MyComponent(ComponentInterface):
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.database = None
            self.cache = None
        
        def initialize(self) -> None:
            # 获取依赖
            self.database = self.get_dependency("database")
            self.cache = self.get_dependency("cache")
            
            # 检查可选依赖
            if self.has_dependency("logging"):
                self.logger = self.get_dependency("logging")

错误处理
--------

异常处理
~~~~~~~~

组件应该正确处理异常::

    class MyComponent(ComponentInterface):
        def start(self) -> None:
            try:
                # 启动逻辑
                self._start_service()
            except ConnectionError as e:
                self.logger.error(f"连接失败: {e}")
                raise
            except Exception as e:
                self.logger.error(f"启动失败: {e}")
                raise
        
        def _start_service(self) -> None:
            """启动服务"""
            # 服务启动逻辑
            pass

健康检查
~~~~~~~~

提供详细的健康状态信息::

    class MyComponent(ComponentInterface):
        def get_health_status(self) -> Dict[str, Any]:
            status = {
                "status": "healthy",
                "component_name": self.name,
                "uptime": self._get_uptime(),
                "metrics": self._get_metrics()
            }
            
            # 检查关键依赖
            if self.database:
                db_status = self.database.get_health_status()
                status["database"] = db_status
            
            return status

测试
----

单元测试
~~~~~~~~

为组件编写单元测试::

    import unittest
    from unittest.mock import Mock, patch
    from framework.core.config import Config
    from my_component import MyComponent

    class TestMyComponent(unittest.TestCase):
        def setUp(self):
            self.config = Config()
            self.component = MyComponent("test", self.config)
        
        def test_initialization(self):
            """测试组件初始化"""
            self.component.initialize()
            self.assertTrue(self.component._initialized)
        
        def test_start_stop(self):
            """测试组件启动和停止"""
            self.component.initialize()
            self.component.start()
            self.assertTrue(self.component._started)
            
            self.component.stop()
            self.assertFalse(self.component._started)

集成测试
~~~~~~~~

测试组件与其他组件的集成::

    class TestComponentIntegration(unittest.TestCase):
        def test_component_dependencies(self):
            """测试组件依赖"""
            # 创建依赖组件
            db_component = DatabaseComponent("database", config)
            cache_component = CacheComponent("cache", config)
            
            # 创建测试组件
            test_component = MyComponent("test", config)
            
            # 测试依赖注入
            test_component.initialize()
            self.assertIsNotNone(test_component.database)
            self.assertIsNotNone(test_component.cache)

最佳实践
--------

* 使用类型注解提高代码可读性
* 提供详细的文档字符串
* 实现完整的生命周期方法
* 正确处理异常和错误情况
* 使用配置而不是硬编码
* 提供有意义的健康状态信息
* 编写完整的测试用例
* 遵循单一职责原则

更多信息
--------

* :doc:`../concepts/components` - 组件概念
* :doc:`../api/components` - 组件API参考
* :doc:`../examples/component_usage` - 使用示例
