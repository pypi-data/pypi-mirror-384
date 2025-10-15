中间件API
=========

本页面介绍框架中间件系统的API文档。

中间件接口
----------

.. autoclass:: framework.core.middleware.MiddlewareInterface
   :members:
   :undoc-members:
   :show-inheritance:

中间件管理器
------------

.. autoclass:: framework.core.middleware.MiddlewareManager
   :members:
   :undoc-members:
   :show-inheritance:

内置中间件
----------

日志中间件
~~~~~~~~~~

.. autoclass:: framework.core.middleware.LoggingMiddleware
   :members:
   :undoc-members:
   :show-inheritance:

认证中间件
~~~~~~~~~~

.. autoclass:: framework.core.middleware.AuthMiddleware
   :members:
   :undoc-members:
   :show-inheritance:

缓存中间件
~~~~~~~~~~

.. autoclass:: framework.core.middleware.CacheMiddleware
   :members:
   :undoc-members:
   :show-inheritance:

限流中间件
~~~~~~~~~~

.. autoclass:: framework.core.middleware.RateLimitMiddleware
   :members:
   :undoc-members:
   :show-inheritance:

错误处理中间件
~~~~~~~~~~~~~~

.. autoclass:: framework.core.middleware.ErrorHandlingMiddleware
   :members:
   :undoc-members:
   :show-inheritance:

中间件异常
----------

.. autoexception:: framework.core.middleware.MiddlewareError
   :show-inheritance:

.. autoexception:: framework.core.middleware.MiddlewareExecutionError
   :show-inheritance:

.. autoexception:: framework.core.middleware.MiddlewareRegistrationError
   :show-inheritance:

使用示例
--------

创建自定义中间件
~~~~~~~~~~~~~~~~

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
            print(f"处理请求: {request['request_id']}")
            return request
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """处理响应"""
            response["processed_by"] = self.name
            print(f"处理响应: {response.get('status', 'unknown')}")
            return response
        
        def process_error(self, error: Exception, request: Dict[str, Any]) -> Dict[str, Any]:
            """处理错误"""
            print(f"处理错误: {error}")
            return {
                "error": str(error),
                "status": 500,
                "processed_by": self.name
            }

使用中间件管理器
~~~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager, LoggingMiddleware, AuthMiddleware

    # 创建中间件管理器
    manager = MiddlewareManager()
    
    # 注册中间件
    manager.register(LoggingMiddleware("logging"))
    manager.register(AuthMiddleware("auth"))
    manager.register(CustomMiddleware("custom"))
    
    # 处理请求
    request = {
        "path": "/api/users",
        "method": "GET",
        "headers": {"Authorization": "Bearer token123"}
    }
    
    try:
        response = manager.process_request(request)
        print(f"响应: {response}")
    except Exception as e:
        error_response = manager.process_error(e, request)
        print(f"错误响应: {error_response}")

中间件链式调用
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager
    from framework.core.middleware import LoggingMiddleware, AuthMiddleware, CacheMiddleware

    manager = MiddlewareManager()
    
    # 按顺序注册中间件
    manager.register(LoggingMiddleware("logging"))      # 1. 记录日志
    manager.register(AuthMiddleware("auth"))            # 2. 认证检查
    manager.register(CacheMiddleware("cache"))          # 3. 缓存处理
    
    # 处理请求
    request = {"path": "/api/data", "method": "GET"}
    response = manager.process_request(request)

中间件配置
~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager, LoggingMiddleware

    manager = MiddlewareManager()
    
    # 配置日志中间件
    logging_middleware = LoggingMiddleware("logging")
    logging_middleware.configure({
        "log_level": "INFO",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_file": "app.log"
    })
    
    manager.register(logging_middleware)

中间件错误处理
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareManager, ErrorHandlingMiddleware

    manager = MiddlewareManager()
    
    # 注册错误处理中间件
    error_middleware = ErrorHandlingMiddleware("error_handler")
    manager.register(error_middleware)
    
    # 处理可能出错的请求
    try:
        response = manager.process_request(request)
    except Exception as e:
        # 错误处理中间件会自动处理异常
        error_response = manager.process_error(e, request)
        print(f"错误已处理: {error_response}")

中间件性能监控
~~~~~~~~~~~~~~

.. code-block:: python

    from framework.core.middleware import MiddlewareInterface
    import time
    from typing import Dict, Any

    class PerformanceMiddleware(MiddlewareInterface):
        """性能监控中间件"""
        
        def __init__(self, name: str):
            super().__init__(name)
            self.total_time = 0
            self.request_count = 0
        
        def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
            """记录请求开始时间"""
            request["_start_time"] = time.time()
            return request
        
        def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
            """计算处理时间"""
            if "_start_time" in response:
                duration = time.time() - response["_start_time"]
                self.total_time += duration
                self.request_count += 1
                response["processing_time"] = duration
                response["avg_processing_time"] = self.total_time / self.request_count
            return response
