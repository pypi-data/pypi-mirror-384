"""
中间件管理器测试

测试framework.core.middleware模块中的中间件管理器。

测试内容：
- 中间件管理器功能
- 中间件注册和注销
- 中间件链式调用
- 请求处理流程
- 错误处理

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from framework.core.middleware import (
    MiddlewareManager,
    MiddlewareInterface,
    MiddlewareType,
    Request,
    Response,
    MiddlewareContext,
    MiddlewareError,
    MiddlewareRegistrationError,
    UnauthorizedError
)


class MockMiddleware(MiddlewareInterface):
    """模拟中间件用于测试"""
    
    def __init__(self, name: str, middleware_type: MiddlewareType = MiddlewareType.REQUEST):
        self._name = name
        self._middleware_type = middleware_type
        self.process_called = False
        self.process_context = None
        self.process_result = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def middleware_type(self) -> MiddlewareType:
        return self._middleware_type
    
    def process(self, context: MiddlewareContext, next_handler) -> any:
        self.process_called = True
        self.process_context = context
        result = next_handler(context)
        self.process_result = result
        return result


class TestMiddlewareManager:
    """中间件管理器测试"""
    
    def test_middleware_manager_initialization(self):
        """测试中间件管理器初始化"""
        manager = MiddlewareManager()
        
        assert manager._middlewares == []
        assert manager._middleware_map == {}
    
    def test_register_middleware(self):
        """测试注册中间件"""
        manager = MiddlewareManager()
        middleware = MockMiddleware("test_middleware")
        
        manager.register(middleware)
        
        assert len(manager._middlewares) == 1
        assert manager._middlewares[0] == middleware
        assert "test_middleware" in manager._middleware_map
        assert manager._middleware_map["test_middleware"] == middleware
    
    def test_register_middleware_with_position(self):
        """测试在指定位置注册中间件"""
        manager = MiddlewareManager()
        
        middleware1 = MockMiddleware("middleware1")
        middleware2 = MockMiddleware("middleware2")
        middleware3 = MockMiddleware("middleware3")
        
        # 注册第一个中间件
        manager.register(middleware1)
        
        # 在位置0插入第二个中间件
        manager.register(middleware2, position=0)
        
        # 在位置1插入第三个中间件
        manager.register(middleware3, position=1)
        
        # 验证顺序
        assert manager._middlewares[0] == middleware2
        assert manager._middlewares[1] == middleware3
        assert manager._middlewares[2] == middleware1
    
    def test_register_duplicate_middleware(self):
        """测试注册重复中间件"""
        manager = MiddlewareManager()
        middleware1 = MockMiddleware("test_middleware")
        middleware2 = MockMiddleware("test_middleware")
        
        manager.register(middleware1)
        
        # 尝试注册同名中间件应该抛出异常
        with pytest.raises(ValueError, match="Middleware 'test_middleware' is already registered"):
            manager.register(middleware2)
    
    def test_unregister_middleware(self):
        """测试注销中间件"""
        manager = MiddlewareManager()
        middleware = MockMiddleware("test_middleware")
        
        manager.register(middleware)
        assert len(manager._middlewares) == 1
        
        manager.unregister("test_middleware")
        
        assert len(manager._middlewares) == 0
        assert "test_middleware" not in manager._middleware_map
    
    def test_unregister_nonexistent_middleware(self):
        """测试注销不存在的中间件"""
        manager = MiddlewareManager()
        
        with pytest.raises(ValueError, match="Middleware 'nonexistent' is not registered"):
            manager.unregister("nonexistent")
    
    def test_get_middleware(self):
        """测试获取中间件"""
        manager = MiddlewareManager()
        middleware = MockMiddleware("test_middleware")
        
        manager.register(middleware)
        
        retrieved_middleware = manager.get_middleware("test_middleware")
        assert retrieved_middleware == middleware
        
        # 获取不存在的中间件
        nonexistent = manager.get_middleware("nonexistent")
        assert nonexistent is None
    
    def test_list_middlewares(self):
        """测试列出中间件"""
        manager = MiddlewareManager()
        
        # 初始状态应该为空
        assert manager.list_middlewares() == []
        
        # 注册一些中间件
        middleware1 = MockMiddleware("middleware1")
        middleware2 = MockMiddleware("middleware2")
        middleware3 = MockMiddleware("middleware3")
        
        manager.register(middleware1)
        manager.register(middleware2)
        manager.register(middleware3)
        
        middlewares = manager.list_middlewares()
        
        assert len(middlewares) == 3
        assert "middleware1" in middlewares
        assert "middleware2" in middlewares
        assert "middleware3" in middlewares
    
    def test_process_request_without_middleware(self):
        """测试没有中间件时处理请求"""
        manager = MiddlewareManager()
        request = Request(method="GET", path="/test")
        
        response = manager.process_request(request)
        
        assert isinstance(response, Response)
        assert response.status_code == 200
        assert response.body == {"message": "Hello, World!", "path": "/test"}
    
    def test_process_request_with_single_middleware(self):
        """测试单个中间件处理请求"""
        manager = MiddlewareManager()
        middleware = MockMiddleware("test_middleware")
        manager.register(middleware)
        
        request = Request(method="GET", path="/test")
        response = manager.process_request(request)
        
        # 验证中间件被调用
        assert middleware.process_called is True
        assert middleware.process_context is not None
        assert middleware.process_context.request == request
        
        # 验证响应
        assert isinstance(response, Response)
        assert response.status_code == 200
    
    def test_process_request_with_multiple_middlewares(self):
        """测试多个中间件处理请求"""
        manager = MiddlewareManager()
        
        middleware1 = MockMiddleware("middleware1")
        middleware2 = MockMiddleware("middleware2")
        middleware3 = MockMiddleware("middleware3")
        
        manager.register(middleware1)
        manager.register(middleware2)
        manager.register(middleware3)
        
        request = Request(method="GET", path="/test")
        response = manager.process_request(request)
        
        # 验证所有中间件都被调用
        assert middleware1.process_called is True
        assert middleware2.process_called is True
        assert middleware3.process_called is True
        
        # 验证响应
        assert isinstance(response, Response)
        assert response.status_code == 200
    
    def test_process_request_middleware_order(self):
        """测试中间件执行顺序"""
        manager = MiddlewareManager()
        
        # 创建会记录执行顺序的中间件
        execution_order = []
        
        class OrderMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                execution_order.append(self.name)
                return super().process(context, next_handler)
        
        middleware1 = OrderMiddleware("middleware1")
        middleware2 = OrderMiddleware("middleware2")
        middleware3 = OrderMiddleware("middleware3")
        
        manager.register(middleware1)
        manager.register(middleware2)
        manager.register(middleware3)
        
        request = Request(method="GET", path="/test")
        manager.process_request(request)
        
        # 验证执行顺序
        assert execution_order == ["middleware1", "middleware2", "middleware3"]
    
    def test_process_request_with_exception(self):
        """测试中间件处理请求时发生异常"""
        manager = MiddlewareManager()
        
        class ExceptionMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                raise ValueError("Test exception")
        
        middleware = ExceptionMiddleware("exception_middleware")
        manager.register(middleware)
        
        request = Request(method="GET", path="/test")
        response = manager.process_request(request)
        
        # 验证返回错误响应
        assert isinstance(response, Response)
        assert response.status_code == 500
        assert "error" in response.body
        assert "Test exception" in response.body["message"]
    
    def test_process_request_with_response_object(self):
        """测试中间件返回Response对象"""
        manager = MiddlewareManager()
        
        class ResponseMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                return Response(status_code=201, body={"created": True})
        
        middleware = ResponseMiddleware("response_middleware")
        manager.register(middleware)
        
        request = Request(method="POST", path="/test")
        response = manager.process_request(request)
        
        # 验证返回的Response对象
        assert isinstance(response, Response)
        assert response.status_code == 201
        assert response.body == {"created": True}
    
    def test_clear_middlewares(self):
        """测试清空所有中间件"""
        manager = MiddlewareManager()
        
        middleware1 = MockMiddleware("middleware1")
        middleware2 = MockMiddleware("middleware2")
        
        manager.register(middleware1)
        manager.register(middleware2)
        
        assert len(manager._middlewares) == 2
        assert len(manager._middleware_map) == 2
        
        manager.clear()
        
        assert len(manager._middlewares) == 0
        assert len(manager._middleware_map) == 0
    
    def test_middleware_context_preservation(self):
        """测试中间件上下文保持"""
        manager = MiddlewareManager()
        
        class ContextMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                context.set_data("middleware_data", "test_value")
                return super().process(context, next_handler)
        
        middleware = ContextMiddleware("context_middleware")
        manager.register(middleware)
        
        request = Request(method="GET", path="/test")
        response = manager.process_request(request)
        
        # 验证上下文数据被保持
        assert middleware.process_context is not None
        assert middleware.process_context.get_data("middleware_data") == "test_value"
    
    def test_middleware_chain_interruption(self):
        """测试中间件链中断"""
        manager = MiddlewareManager()
        
        class InterruptMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                # 标记为已调用
                self.process_called = True
                self.process_context = context
                # 不调用next_handler，中断链
                result = Response(status_code=403, body={"error": "Access denied"})
                self.process_result = result
                return result
        
        class NeverCalledMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                # 这个中间件不应该被调用
                assert False, "This middleware should not be called"
        
        interrupt_middleware = InterruptMiddleware("interrupt_middleware")
        never_called_middleware = NeverCalledMiddleware("never_called_middleware")
        
        manager.register(interrupt_middleware)
        manager.register(never_called_middleware)
        
        request = Request(method="GET", path="/test")
        response = manager.process_request(request)
        
        # 验证链被中断
        assert interrupt_middleware.process_called is True
        assert response.status_code == 403
        assert response.body == {"error": "Access denied"}


class TestMiddlewareManagerIntegration:
    """中间件管理器集成测试"""
    
    def test_complex_middleware_chain(self):
        """测试复杂的中间件链"""
        manager = MiddlewareManager()
        
        # 创建多个不同类型的中间件
        class LoggingMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                context.set_data("start_time", context.start_time)
                return super().process(context, next_handler)
        
        class AuthMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                context.set_data("authenticated", True)
                return super().process(context, next_handler)
        
        class CacheMiddleware(MockMiddleware):
            def process(self, context, next_handler):
                context.set_data("cached", False)
                return super().process(context, next_handler)
        
        # 注册中间件
        logging_middleware = LoggingMiddleware("logging")
        auth_middleware = AuthMiddleware("auth")
        cache_middleware = CacheMiddleware("cache")
        
        manager.register(logging_middleware)
        manager.register(auth_middleware)
        manager.register(cache_middleware)
        
        request = Request(method="GET", path="/api/users")
        response = manager.process_request(request)
        
        # 验证所有中间件都被调用
        assert logging_middleware.process_called is True
        assert auth_middleware.process_called is True
        assert cache_middleware.process_called is True
        
        # 验证上下文数据
        assert logging_middleware.process_context.get_data("start_time") is not None
        assert auth_middleware.process_context.get_data("authenticated") is True
        assert cache_middleware.process_context.get_data("cached") is False
        
        # 验证响应
        assert isinstance(response, Response)
        assert response.status_code == 200
    
    def test_middleware_with_different_request_types(self):
        """测试不同请求类型的中间件处理"""
        manager = MiddlewareManager()
        middleware = MockMiddleware("test_middleware")
        manager.register(middleware)
        
        # 测试不同的请求类型
        requests = [
            Request(method="GET", path="/"),
            Request(method="POST", path="/api/users"),
            Request(method="PUT", path="/api/users/123"),
            Request(method="DELETE", path="/api/users/123"),
        ]
        
        for request in requests:
            response = manager.process_request(request)
            
            assert isinstance(response, Response)
            assert response.status_code == 200
            assert middleware.process_called is True
            assert middleware.process_context.request == request
            
            # 重置中间件状态
            middleware.process_called = False
            middleware.process_context = None


@pytest.mark.parametrize("middleware_count", [1, 3, 5, 10])
def test_middleware_manager_with_different_counts(middleware_count):
    """测试不同数量中间件的管理器"""
    manager = MiddlewareManager()
    
    # 注册指定数量的中间件
    for i in range(middleware_count):
        middleware = MockMiddleware(f"middleware_{i}")
        manager.register(middleware)
    
    assert len(manager._middlewares) == middleware_count
    assert len(manager._middleware_map) == middleware_count
    
    # 测试处理请求
    request = Request(method="GET", path="/test")
    response = manager.process_request(request)
    
    assert isinstance(response, Response)
    assert response.status_code == 200
    
    # 验证所有中间件都被调用
    for i in range(middleware_count):
        middleware = manager.get_middleware(f"middleware_{i}")
        assert middleware.process_called is True


@pytest.mark.parametrize("position", [0, 1, 2, 5])
def test_middleware_registration_at_different_positions(position):
    """测试在不同位置注册中间件"""
    manager = MiddlewareManager()
    
    # 先注册一些中间件
    for i in range(3):
        middleware = MockMiddleware(f"middleware_{i}")
        manager.register(middleware)
    
    # 在指定位置插入新中间件
    new_middleware = MockMiddleware("new_middleware")
    manager.register(new_middleware, position=position)
    
    # 验证位置
    if position >= len(manager._middlewares) - 1:
        # 如果位置超出范围，应该添加到末尾
        assert manager._middlewares[-1] == new_middleware
    else:
        # 否则应该在指定位置
        assert manager._middlewares[position] == new_middleware
