基本使用示例
============

本页面提供Python模块化框架的基本使用示例，帮助您快速上手。

简单应用示例
------------

创建第一个应用
~~~~~~~~~~~~~~

.. code-block:: python

    """
    简单应用示例
    
    演示如何创建一个基本的框架应用。
    """

    from framework.core.application import Application

    def main():
        """主函数"""
        # 创建应用实例
        app = Application(name="my-first-app", version="1.0.0")
        
        # 配置应用
        app.configure({
            "debug": True,
            "log_level": "INFO"
        })
        
        try:
            # 启动应用
            app.start()
            print("应用启动成功！")
            
            # 应用运行中...
            import time
            time.sleep(5)
            
        except Exception as e:
            print(f"应用启动失败: {e}")
        finally:
            # 停止应用
            app.stop()
            print("应用已停止")

    if __name__ == "__main__":
        main()

运行示例::

    python examples/simple_app.py

组件使用示例
------------

创建自定义组件
~~~~~~~~~~~~~~

.. code-block:: python

    """
    自定义组件示例
    
    演示如何创建和使用自定义组件。
    """

    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any
    import logging

    class GreetingComponent(ComponentInterface):
        """问候组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.greeting_message = "Hello, World!"
        
        def initialize(self) -> None:
            """初始化组件"""
            self.logger.info(f"初始化组件: {self.name}")
            # 从配置获取问候消息
            self.greeting_message = self.config.get(
                f"components.{self.name}.message", 
                "Hello, World!"
            )
        
        def start(self) -> None:
            """启动组件"""
            self.logger.info(f"启动组件: {self.name}")
            print(self.greeting_message)
        
        def stop(self) -> None:
            """停止组件"""
            self.logger.info(f"停止组件: {self.name}")
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy",
                "message": self.greeting_message
            }
        
        def greet(self, name: str) -> str:
            """问候指定的人"""
            return f"{self.greeting_message} {name}!"

    # 使用组件
    def main():
        from framework.core.application import Application
        
        app = Application("greeting-app", "1.0.0")
        
        # 配置组件
        app.configure({
            "components": {
                "greeting": {
                    "message": "你好"
                }
            }
        })
        
        # 注册组件
        greeting_component = GreetingComponent("greeting", app.config)
        app.register_component(greeting_component)
        
        # 启动应用
        app.start()
        
        # 使用组件功能
        greeting = app.get_component("greeting")
        print(greeting.greet("张三"))
        
        app.stop()

    if __name__ == "__main__":
        main()

中间件使用示例
--------------

创建自定义中间件
~~~~~~~~~~~~~~~

.. code-block:: python

    """
    自定义中间件示例
    
    演示如何创建和使用自定义中间件。
    """

    from framework.core.middleware import MiddlewareInterface
    from typing import Dict, Any
    import time

    class TimingMiddleware(MiddlewareInterface):
        """计时中间件"""
        
        def __init__(self, name: str):
            super().__init__(name)
            self.request_count = 0
            self.total_time = 0.0
        
        def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理请求"""
            self.request_count += 1
            request["_start_time"] = time.time()
            request["_request_id"] = f"req_{self.request_count}"
            print(f"开始处理请求: {request['_request_id']}")
            return request
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """处理响应"""
            if "_start_time" in response:
                duration = time.time() - response["_start_time"]
                self.total_time += duration
                response["processing_time"] = duration
                response["avg_processing_time"] = self.total_time / self.request_count
                print(f"请求处理完成，耗时: {duration:.3f}秒")
            return response
        
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            print(f"处理请求时发生错误: {error}")
            return {
                "error": str(error),
                "status": 500,
                "processed_by": self.name
            }

    # 使用中间件
    def main():
        from framework.core.middleware import MiddlewareManager
        
        # 创建中间件管理器
        manager = MiddlewareManager()
        
        # 注册中间件
        timing_middleware = TimingMiddleware("timing")
        manager.register(timing_middleware)
        
        # 处理请求
        request = {
            "path": "/api/test",
            "method": "GET",
            "data": {"key": "value"}
        }
        
        try:
            response = manager.process_request(request)
            print(f"响应: {response}")
        except Exception as e:
            error_response = manager.process_error(e, request)
            print(f"错误响应: {error_response}")

    if __name__ == "__main__":
        main()

插件使用示例
------------

创建自定义插件
~~~~~~~~~~~~~~

.. code-block:: python

    """
    自定义插件示例
    
    演示如何创建和使用自定义插件。
    """

    from framework.interfaces.plugin import PluginInterface
    from typing import Dict, Any
    import logging

    class CalculatorPlugin(PluginInterface):
        """计算器插件"""
        
        def __init__(self):
            super().__init__()
            self.name = "calculator"
            self.version = "1.0.0"
            self.description = "简单的计算器插件"
            self.dependencies = []
            self.optional_dependencies = []
            self.metadata = {
                "category": "utility",
                "tags": ["calculator", "math"]
            }
            self.logger = logging.getLogger(f"plugin.{self.name}")
            self.running = False
        
        def initialize(self, config: Dict[str, Any]) -> None:
            """初始化插件"""
            self.logger.info(f"初始化插件: {self.name}")
            self.config = config
        
        def start(self) -> None:
            """启动插件"""
            self.logger.info(f"启动插件: {self.name}")
            self.running = True
        
        def stop(self) -> None:
            """停止插件"""
            self.logger.info(f"停止插件: {self.name}")
            self.running = False
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy" if self.running else "stopped",
                "plugin_name": self.name,
                "version": self.version
            }
        
        def add(self, a: float, b: float) -> float:
            """加法运算"""
            return a + b
        
        def subtract(self, a: float, b: float) -> float:
            """减法运算"""
            return a - b
        
        def multiply(self, a: float, b: float) -> float:
            """乘法运算"""
            return a * b
        
        def divide(self, a: float, b: float) -> float:
            """除法运算"""
            if b == 0:
                raise ValueError("除数不能为零")
            return a / b

    # 使用插件
    def main():
        from framework.core.plugin import PluginManager
        
        # 创建插件管理器
        manager = PluginManager(plugin_dirs=["."])
        
        # 创建插件实例
        calculator = CalculatorPlugin()
        
        # 初始化插件
        calculator.initialize({"debug": True})
        
        # 启动插件
        calculator.start()
        
        # 使用插件功能
        print(f"5 + 3 = {calculator.add(5, 3)}")
        print(f"10 - 4 = {calculator.subtract(10, 4)}")
        print(f"6 * 7 = {calculator.multiply(6, 7)}")
        print(f"15 / 3 = {calculator.divide(15, 3)}")
        
        # 停止插件
        calculator.stop()

    if __name__ == "__main__":
        main()

配置管理示例
------------

使用配置文件
~~~~~~~~~~~~

创建配置文件 ``config.yaml``::

    debug: true
    log_level: INFO
    
    components:
      database:
        host: localhost
        port: 5432
        name: myapp
        user: admin
        password: secret
      
      cache:
        type: redis
        host: localhost
        port: 6379
        db: 0
      
      logging:
        level: INFO
        format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file: app.log
    
    middleware:
      auth:
        token_header: Authorization
        token_prefix: Bearer
      
      cache:
        default_ttl: 3600
        cache_key_prefix: api:
    
    plugins:
      calculator:
        precision: 2
        enable_history: true

使用配置::

    from framework.core.config import Config
    from framework.core.application import Application

    def main():
        # 创建配置对象
        config = Config()
        
        # 从文件加载配置
        config.load_from_file("config.yaml")
        
        # 创建应用
        app = Application("config-app", "1.0.0")
        app.configure(config.to_dict())
        
        # 使用配置
        print(f"调试模式: {app.config.get('debug')}")
        print(f"日志级别: {app.config.get('log_level')}")
        
        # 获取组件配置
        db_config = app.config.get("components.database")
        print(f"数据库主机: {db_config.get('host')}")

    if __name__ == "__main__":
        main()

错误处理示例
------------

异常处理
~~~~~~~~

.. code-block:: python

    """
    错误处理示例
    
    演示如何在框架中处理各种错误情况。
    """

    from framework.core.application import Application
    from framework.interfaces.component import ComponentInterface
    from framework.core.config import Config
    from typing import Dict, Any
    import logging

    class ErrorProneComponent(ComponentInterface):
        """容易出错的组件"""
        
        def __init__(self, name: str, config: Config):
            super().__init__(name, config)
            self.logger = logging.getLogger(f"component.{name}")
            self.error_rate = config.get(f"components.{name}.error_rate", 0.1)
        
        def initialize(self) -> None:
            """初始化组件"""
            self.logger.info(f"初始化组件: {self.name}")
            if self.error_rate > 0.5:
                raise ValueError("错误率设置过高")
        
        def start(self) -> None:
            """启动组件"""
            self.logger.info(f"启动组件: {self.name}")
        
        def stop(self) -> None:
            """停止组件"""
            self.logger.info(f"停止组件: {self.name}")
        
        def get_health_status(self) -> Dict[str, Any]:
            """获取健康状态"""
            return {
                "status": "healthy",
                "error_rate": self.error_rate
            }
        
        def risky_operation(self) -> str:
            """有风险的操作"""
            import random
            if random.random() < self.error_rate:
                raise RuntimeError("随机错误发生")
            return "操作成功"

    def main():
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        
        app = Application("error-handling-app", "1.0.0")
        
        # 配置组件
        app.configure({
            "components": {
                "error-prone": {
                    "error_rate": 0.3
                }
            }
        })
        
        try:
            # 注册组件
            error_component = ErrorProneComponent("error-prone", app.config)
            app.register_component(error_component)
            
            # 启动应用
            app.start()
            
            # 执行有风险的操作
            component = app.get_component("error-prone")
            for i in range(5):
                try:
                    result = component.risky_operation()
                    print(f"操作 {i+1}: {result}")
                except RuntimeError as e:
                    print(f"操作 {i+1} 失败: {e}")
            
        except Exception as e:
            print(f"应用启动失败: {e}")
        finally:
            app.stop()

    if __name__ == "__main__":
        main()

更多示例
--------

* :doc:`advanced_usage` - 高级使用示例
* :doc:`real_world_applications` - 实际应用示例
* :doc:`../api/framework` - API参考
* :doc:`../concepts/overview` - 核心概念
