"""
内置中间件测试

测试framework.core.middleware模块中的内置中间件实现。

测试内容：
- 日志中间件
- 认证中间件
- 缓存中间件
- 错误处理中间件

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from framework.core.middleware import (
    LoggingMiddleware,
    AuthMiddleware,
    CacheMiddleware,
    ErrorMiddleware,
    RequestMiddleware,
    MiddlewareType,
    Request,
    Response,
    MiddlewareContext,
    UnauthorizedError,
    MiddlewareError
)


class TestLoggingMiddleware:
    """日志中间件测试"""
    
    def test_logging_middleware_initialization(self):
        """测试日志中间件初始化"""
        middleware = LoggingMiddleware("test_logging")
        
        assert middleware.name == "test_logging"
        assert middleware.middleware_type == MiddlewareType.REQUEST
        assert middleware.log_requests is True
        assert middleware.log_responses is True
        assert middleware.log_errors is True
    
    def test_logging_middleware_initialization_with_options(self):
        """测试使用选项初始化日志中间件"""
        middleware = LoggingMiddleware(
            "test_logging",
            log_requests=False,
            log_responses=False,
            log_errors=False
        )
        
        assert middleware.log_requests is False
        assert middleware.log_responses is False
        assert middleware.log_errors is False
    
    def test_before_request_logging(self):
        """测试请求前日志记录"""
        middleware = LoggingMiddleware("test_logging")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        
        with patch('builtins.print') as mock_print:
            middleware.before_request(context)
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[test_logging] Request: GET /test" in call_args
    
    def test_before_request_logging_disabled(self):
        """测试禁用请求日志记录"""
        middleware = LoggingMiddleware("test_logging", log_requests=False)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        
        with patch('builtins.print') as mock_print:
            middleware.before_request(context)
            mock_print.assert_not_called()
    
    def test_after_request_logging(self):
        """测试请求后日志记录"""
        middleware = LoggingMiddleware("test_logging")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        context.response = Response(status_code=200)
        
        with patch('builtins.print') as mock_print:
            middleware.after_request(context, "result")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[test_logging] Response: 200" in call_args
            assert "s)" in call_args  # 应该包含执行时间
    
    def test_after_request_logging_disabled(self):
        """测试禁用响应日志记录"""
        middleware = LoggingMiddleware("test_logging", log_responses=False)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        context.response = Response(status_code=200)
        
        with patch('builtins.print') as mock_print:
            middleware.after_request(context, "result")
            mock_print.assert_not_called()
    
    def test_on_request_error_logging(self):
        """测试请求错误日志记录"""
        middleware = LoggingMiddleware("test_logging")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        error = ValueError("Test error")
        
        with patch('builtins.print') as mock_print:
            middleware.on_request_error(context, error)
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[test_logging] Error: ValueError: Test error" in call_args
    
    def test_on_request_error_logging_disabled(self):
        """测试禁用错误日志记录"""
        middleware = LoggingMiddleware("test_logging", log_errors=False)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        error = ValueError("Test error")
        
        with patch('builtins.print') as mock_print:
            middleware.on_request_error(context, error)
            mock_print.assert_not_called()


class TestAuthMiddleware:
    """认证中间件测试"""
    
    def test_auth_middleware_initialization(self):
        """测试认证中间件初始化"""
        middleware = AuthMiddleware("test_auth")
        
        assert middleware.name == "test_auth"
        assert middleware.middleware_type == MiddlewareType.REQUEST
        assert middleware.required is True
    
    def test_auth_middleware_initialization_optional(self):
        """测试可选认证中间件初始化"""
        middleware = AuthMiddleware("test_auth", required=False)
        
        assert middleware.required is False
    
    def test_before_request_with_valid_token(self):
        """测试使用有效令牌的请求前处理"""
        middleware = AuthMiddleware("test_auth")
        context = MiddlewareContext(
            request=Request(
                method="GET",
                path="/test",
                headers={"authorization": "Bearer valid_token"}
            )
        )
        
        middleware.before_request(context)
        
        # 验证用户信息被设置
        assert context.request.user is not None
        assert context.request.user["id"] == "user123"
        assert context.request.user["username"] == "testuser"
        assert context.get_data("authenticated") is True
    
    def test_before_request_without_token_required(self):
        """测试没有令牌的必需认证请求"""
        middleware = AuthMiddleware("test_auth", required=True)
        context = MiddlewareContext(
            request=Request(method="GET", path="/test")
        )
        
        with pytest.raises(UnauthorizedError, match="Authentication required"):
            middleware.before_request(context)
    
    def test_before_request_without_token_optional(self):
        """测试没有令牌的可选认证请求"""
        middleware = AuthMiddleware("test_auth", required=False)
        context = MiddlewareContext(
            request=Request(method="GET", path="/test")
        )
        
        # 应该不抛出异常
        middleware.before_request(context)
        
        # 验证用户信息没有被设置
        assert context.request.user is None
        assert context.get_data("authenticated") is None
    
    def test_before_request_with_invalid_token_format(self):
        """测试无效令牌格式"""
        middleware = AuthMiddleware("test_auth", required=True)
        context = MiddlewareContext(
            request=Request(
                method="GET",
                path="/test",
                headers={"authorization": "InvalidToken"}
            )
        )
        
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            middleware.before_request(context)
    
    def test_validate_token_valid_format(self):
        """测试验证有效格式的令牌"""
        middleware = AuthMiddleware("test_auth")
        
        user = middleware.validate_token("Bearer valid_token")
        
        assert user is not None
        assert user["id"] == "user123"
        assert user["username"] == "testuser"
        assert user["roles"] == ["user"]
    
    def test_validate_token_invalid_format(self):
        """测试验证无效格式的令牌"""
        middleware = AuthMiddleware("test_auth")
        
        with pytest.raises(ValueError, match="Invalid token format"):
            middleware.validate_token("InvalidToken")
    
    def test_validate_token_empty_token(self):
        """测试验证空令牌"""
        middleware = AuthMiddleware("test_auth")
        
        with pytest.raises(ValueError, match="Invalid token format"):
            middleware.validate_token("")


class TestCacheMiddleware:
    """缓存中间件测试"""
    
    def test_cache_middleware_initialization(self):
        """测试缓存中间件初始化"""
        middleware = CacheMiddleware("test_cache")
        
        assert middleware.name == "test_cache"
        assert middleware.middleware_type == MiddlewareType.REQUEST
        assert middleware.cache_requests is True
        assert middleware.cache_responses is True
        assert middleware.default_ttl == 300
    
    def test_cache_middleware_initialization_with_options(self):
        """测试使用选项初始化缓存中间件"""
        cache_service = Mock()
        middleware = CacheMiddleware(
            "test_cache",
            cache_service=cache_service,
            cache_requests=False,
            cache_responses=False,
            default_ttl=600
        )
        
        assert middleware.cache_service == cache_service
        assert middleware.cache_requests is False
        assert middleware.cache_responses is False
        assert middleware.default_ttl == 600
    
    def test_generate_cache_key(self):
        """测试生成缓存键"""
        middleware = CacheMiddleware("test_cache")
        request = Request(method="GET", path="/api/users")
        
        cache_key = middleware._generate_cache_key(request)
        
        assert cache_key == "GET:/api/users"
    
    def test_before_request_cache_hit(self):
        """测试请求前缓存命中"""
        cache_service = Mock()
        cache_service.get.return_value = {"cached": "data"}
        
        middleware = CacheMiddleware("test_cache", cache_service=cache_service)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        
        # 模拟缓存命中
        with patch.object(middleware, '_generate_cache_key', return_value="GET:/test"):
            middleware.before_request(context)
        
        # 验证缓存服务被调用
        cache_service.get.assert_called_once_with("GET:/test")
        
        # 验证缓存数据被设置到上下文
        assert context.get_data("cache_hit") is True
        assert context.get_data("cached_response") == {"cached": "data"}
    
    def test_before_request_cache_miss(self):
        """测试请求前缓存未命中"""
        cache_service = Mock()
        cache_service.get.return_value = None
        
        middleware = CacheMiddleware("test_cache", cache_service=cache_service)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        
        # 模拟缓存未命中
        with patch.object(middleware, '_generate_cache_key', return_value="GET:/test"):
            middleware.before_request(context)
        
        # 验证缓存服务被调用
        cache_service.get.assert_called_once_with("GET:/test")
        
        # 验证缓存未命中
        assert context.get_data("cache_hit") is None
    
    def test_after_request_cache_response(self):
        """测试请求后缓存响应"""
        cache_service = Mock()
        
        middleware = CacheMiddleware("test_cache", cache_service=cache_service)
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        context.response = Response(status_code=200, body={"data": "test"})
        
        # 模拟缓存响应
        with patch.object(middleware, '_generate_cache_key', return_value="GET:/test"):
            middleware.after_request(context, "result")
        
        # 验证缓存服务被调用
        cache_service.set.assert_called_once()
        call_args = cache_service.set.call_args
        assert call_args[0][0] == "GET:/test"  # 缓存键
        assert call_args[0][1].body == {"data": "test"}  # 响应体
        assert call_args[1]["ttl"] == 300  # TTL
    
    def test_after_request_cache_disabled(self):
        """测试禁用响应缓存"""
        cache_service = Mock()
        
        middleware = CacheMiddleware(
            "test_cache",
            cache_service=cache_service,
            cache_responses=False
        )
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        context.response = Response(status_code=200, body={"data": "test"})
        
        middleware.after_request(context, "result")
        
        # 验证缓存服务没有被调用
        cache_service.set.assert_not_called()


class TestErrorMiddleware:
    """错误处理中间件测试"""
    
    def test_error_middleware_initialization(self):
        """测试错误处理中间件初始化"""
        middleware = ErrorMiddleware("test_error")
        
        assert middleware.name == "test_error"
        assert middleware.middleware_type == MiddlewareType.ERROR
    
    def test_handle_error_generic_exception(self):
        """测试处理通用异常"""
        middleware = ErrorMiddleware("test_error")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        error = ValueError("Test error")
        
        # 默认实现会重新抛出异常
        with pytest.raises(ValueError, match="Test error"):
            middleware.handle_error(context, error)
    
    def test_handle_error_unauthorized_error(self):
        """测试处理未授权异常"""
        middleware = ErrorMiddleware("test_error")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        error = UnauthorizedError("Authentication required")
        
        # 默认实现会重新抛出异常
        with pytest.raises(UnauthorizedError, match="Authentication required"):
            middleware.handle_error(context, error)
    
    def test_handle_error_middleware_error(self):
        """测试处理中间件异常"""
        middleware = ErrorMiddleware("test_error")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        error = MiddlewareError("Middleware error")
        
        # 默认实现会重新抛出异常
        with pytest.raises(MiddlewareError, match="Middleware error"):
            middleware.handle_error(context, error)


class TestRequestMiddleware:
    """请求中间件基类测试"""
    
    def test_request_middleware_initialization(self):
        """测试请求中间件初始化"""
        middleware = RequestMiddleware("test_request")
        
        assert middleware.name == "test_request"
        assert middleware.middleware_type == MiddlewareType.REQUEST
    
    def test_process_successful_request(self):
        """测试成功处理请求"""
        middleware = RequestMiddleware("test_request")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        next_handler = Mock(return_value="success")
        
        result = middleware.process(context, next_handler)
        
        assert result == "success"
        next_handler.assert_called_once_with(context)
    
    def test_process_request_with_exception(self):
        """测试处理请求时发生异常"""
        middleware = RequestMiddleware("test_request")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        next_handler = Mock(side_effect=ValueError("Test error"))
        
        with pytest.raises(ValueError, match="Test error"):
            middleware.process(context, next_handler)
    
    def test_before_request_override(self):
        """测试重写before_request方法"""
        class CustomRequestMiddleware(RequestMiddleware):
            def before_request(self, context):
                context.set_data("custom_data", "test_value")
        
        middleware = CustomRequestMiddleware("test_request")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        next_handler = Mock(return_value="success")
        
        middleware.process(context, next_handler)
        
        assert context.get_data("custom_data") == "test_value"
    
    def test_after_request_override(self):
        """测试重写after_request方法"""
        class CustomRequestMiddleware(RequestMiddleware):
            def after_request(self, context, result):
                context.set_data("result_processed", True)
        
        middleware = CustomRequestMiddleware("test_request")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        next_handler = Mock(return_value="success")
        
        middleware.process(context, next_handler)
        
        assert context.get_data("result_processed") is True
    
    def test_on_request_error_override(self):
        """测试重写on_request_error方法"""
        class CustomRequestMiddleware(RequestMiddleware):
            def on_request_error(self, context, error):
                context.set_data("error_handled", True)
        
        middleware = CustomRequestMiddleware("test_request")
        context = MiddlewareContext(request=Request(method="GET", path="/test"))
        next_handler = Mock(side_effect=ValueError("Test error"))
        
        with pytest.raises(ValueError):
            middleware.process(context, next_handler)
        
        assert context.get_data("error_handled") is True


@pytest.mark.parametrize("method,path,expected_key", [
    ("GET", "/", "GET:/"),
    ("POST", "/api/users", "POST:/api/users"),
    ("PUT", "/api/users/123", "PUT:/api/users/123"),
    ("DELETE", "/api/users/123", "DELETE:/api/users/123"),
])
def test_cache_middleware_generate_cache_key(method, path, expected_key):
    """测试缓存中间件生成不同请求的缓存键"""
    middleware = CacheMiddleware("test_cache")
    request = Request(method=method, path=path)
    
    cache_key = middleware._generate_cache_key(request)
    
    assert cache_key == expected_key


@pytest.mark.parametrize("error_type", [
    ValueError("Test error"),
    UnauthorizedError("Auth error"),
    MiddlewareError("Middleware error"),
    RuntimeError("Runtime error"),
])
def test_error_middleware_handle_different_errors(error_type):
    """测试错误处理中间件处理不同类型的错误"""
    middleware = ErrorMiddleware("test_error")
    context = MiddlewareContext(request=Request(method="GET", path="/test"))
    
    # 默认实现会重新抛出异常
    with pytest.raises(type(error_type)):
        middleware.handle_error(context, error_type)
