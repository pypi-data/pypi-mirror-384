中间件系统
==========

中间件系统提供了灵活的请求处理管道，支持链式调用和模块化处理。

中间件概述
----------

中间件是处理请求和响应的可插拔组件，按照注册顺序依次执行。每个中间件都可以修改请求、响应或处理错误。

中间件特性
----------

* **链式调用**: 按顺序执行多个中间件
* **请求处理**: 在请求到达业务逻辑前进行处理
* **响应处理**: 在响应返回前进行处理
* **错误处理**: 统一的错误处理机制
* **配置灵活**: 支持中间件级别的配置

内置中间件
----------

日志中间件 (LoggingMiddleware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

记录请求和响应信息::

    from framework.core.middleware import LoggingMiddleware

    middleware = LoggingMiddleware("logging")
    middleware.configure({
        "log_level": "INFO",
        "log_format": "%(asctime)s - %(message)s"
    })

认证中间件 (AuthMiddleware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

处理用户认证::

    from framework.core.middleware import AuthMiddleware

    middleware = AuthMiddleware("auth")
    middleware.configure({
        "token_header": "Authorization",
        "token_prefix": "Bearer"
    })

缓存中间件 (CacheMiddleware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

提供响应缓存::

    from framework.core.middleware import CacheMiddleware

    middleware = CacheMiddleware("cache")
    middleware.configure({
        "default_ttl": 3600,
        "cache_key_prefix": "api:"
    })

限流中间件 (RateLimitMiddleware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

限制请求频率::

    from framework.core.middleware import RateLimitMiddleware

    middleware = RateLimitMiddleware("rate_limit")
    middleware.configure({
        "requests_per_minute": 100,
        "burst_size": 10
    })

错误处理中间件 (ErrorHandlingMiddleware)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

统一错误处理::

    from framework.core.middleware import ErrorHandlingMiddleware

    middleware = ErrorHandlingMiddleware("error_handler")
    middleware.configure({
        "log_errors": True,
        "return_error_details": False
    })

创建自定义中间件
----------------

定义中间件类
~~~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareInterface
    from typing import Dict, Any

    class CustomMiddleware(MiddlewareInterface):
        """自定义中间件示例"""
        
        def __init__(self, name: str):
            super().__init__(name)
            self.request_count = 0
        
        def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理请求"""
            self.request_count += 1
            request["request_id"] = f"req_{self.request_count}"
            return request
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """处理响应"""
            response["processed_by"] = self.name
            return response
        
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            return {
                "error": str(error),
                "status": 500,
                "processed_by": self.name
            }

注册中间件
~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager

    manager = MiddlewareManager()
    manager.register(CustomMiddleware("custom"))

中间件配置
----------

中间件可以通过配置进行定制::

    middleware:
      logging:
        log_level: INFO
        log_format: "%(asctime)s - %(message)s"
      auth:
        token_header: Authorization
        token_prefix: Bearer
      cache:
        default_ttl: 3600
        cache_key_prefix: api:

在中间件中访问配置::

    class CustomMiddleware(MiddlewareInterface):
        def __init__(self, name: str):
            super().__init__(name)
            self.config = {}
        
        def configure(self, config: Dict[str, Any]) -> None:
            """配置中间件"""
            self.config = config.get("middleware", {}).get(self.name, {})

中间件执行顺序
--------------

中间件按照注册顺序执行::

    manager = MiddlewareManager()
    
    # 按顺序注册中间件
    manager.register(LoggingMiddleware("logging"))      # 1. 记录日志
    manager.register(AuthMiddleware("auth"))            # 2. 认证检查
    manager.register(CacheMiddleware("cache"))          # 3. 缓存处理
    manager.register(CustomMiddleware("custom"))        # 4. 自定义处理

执行流程::

    请求 -> 日志 -> 认证 -> 缓存 -> 自定义 -> 业务逻辑
    响应 <- 日志 <- 认证 <- 缓存 <- 自定义 <- 业务逻辑

错误处理
--------

中间件可以处理执行过程中的错误::

    class ErrorHandlingMiddleware(MiddlewareInterface):
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            if isinstance(error, ValueError):
                return {"error": "Invalid input", "status": 400}
            elif isinstance(error, PermissionError):
                return {"error": "Access denied", "status": 403}
            else:
                return {"error": "Internal server error", "status": 500}

性能考虑
--------

* 避免在中间件中执行耗时操作
* 使用异步处理提高并发性能
* 合理使用缓存减少重复计算
* 监控中间件执行时间

最佳实践
--------

* 保持中间件的单一职责
* 正确处理异常情况
* 使用配置而不是硬编码
* 提供有意义的日志信息
* 考虑中间件的执行顺序

更多信息
--------

* :doc:`../api/middleware` - 中间件API参考
* :doc:`../development/creating_middleware` - 创建中间件指南
* :doc:`../examples/middleware_usage` - 使用示例
