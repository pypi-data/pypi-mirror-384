"""
中间件接口测试

测试framework.core.middleware模块中的接口和基础类。

测试内容：
- 中间件接口定义
- 基础中间件类
- 请求和响应对象
- 中间件上下文

作者：开发团队
创建时间：2025-01-12
"""

import pytest
import time
from unittest.mock import Mock, MagicMock
from framework.core.middleware import (
    MiddlewareInterface,
    BaseMiddleware,
    MiddlewareType,
    Request,
    Response,
    MiddlewareContext,
    MiddlewareError
)


class TestMiddlewareType:
    """中间件类型枚举测试"""
    
    def test_middleware_type_values(self):
        """测试中间件类型值"""
        assert MiddlewareType.REQUEST.value == "request"
        assert MiddlewareType.RESPONSE.value == "response"
        assert MiddlewareType.ERROR.value == "error"
        assert MiddlewareType.AUTH.value == "auth"
        assert MiddlewareType.LOGGING.value == "logging"
        assert MiddlewareType.CACHE.value == "cache"


class TestRequest:
    """请求对象测试"""
    
    def test_request_initialization(self):
        """测试请求对象初始化"""
        request = Request()
        
        assert request.method == "GET"
        assert request.path == "/"
        assert request.headers == {}
        assert request.query_params == {}
        assert request.body is None
        assert request.user is None
        assert request.context == {}
        assert isinstance(request.timestamp, float)
    
    def test_request_initialization_with_data(self):
        """测试使用数据初始化请求对象"""
        headers = {"Content-Type": "application/json"}
        query_params = {"page": 1, "limit": 10}
        context = {"request_id": "123"}
        
        request = Request(
            method="POST",
            path="/api/users",
            headers=headers,
            query_params=query_params,
            body={"name": "test"},
            user={"id": "user123"},
            context=context
        )
        
        assert request.method == "POST"
        assert request.path == "/api/users"
        assert request.headers == headers
        assert request.query_params == query_params
        assert request.body == {"name": "test"}
        assert request.user == {"id": "user123"}
        assert request.context == context
    
    def test_get_header(self):
        """测试获取请求头"""
        request = Request()
        request.headers = {"content-type": "application/json", "authorization": "Bearer token"}
        
        # 测试获取存在的头
        assert request.get_header("Content-Type") == "application/json"
        assert request.get_header("content-type") == "application/json"  # 大小写不敏感
        assert request.get_header("Authorization") == "Bearer token"
        
        # 测试获取不存在的头
        assert request.get_header("Non-Existent") is None
        assert request.get_header("Non-Existent", "default") == "default"
    
    def test_get_query_param(self):
        """测试获取查询参数"""
        request = Request()
        request.query_params = {"page": 1, "limit": 10, "search": "test"}
        
        # 测试获取存在的参数
        assert request.get_query_param("page") == 1
        assert request.get_query_param("limit") == 10
        assert request.get_query_param("search") == "test"
        
        # 测试获取不存在的参数
        assert request.get_query_param("non_existent") is None
        assert request.get_query_param("non_existent", "default") == "default"


class TestResponse:
    """响应对象测试"""
    
    def test_response_initialization(self):
        """测试响应对象初始化"""
        response = Response()
        
        assert response.status_code == 200
        assert response.headers == {}
        assert response.body is None
        assert response.content_type == "application/json"
        assert isinstance(response.timestamp, float)
    
    def test_response_initialization_with_data(self):
        """测试使用数据初始化响应对象"""
        headers = {"Content-Type": "application/json"}
        
        response = Response(
            status_code=201,
            headers=headers,
            body={"id": "123", "name": "test"},
            content_type="application/json"
        )
        
        assert response.status_code == 201
        assert response.headers == headers
        assert response.body == {"id": "123", "name": "test"}
        assert response.content_type == "application/json"
    
    def test_set_header(self):
        """测试设置响应头"""
        response = Response()
        
        response.set_header("Content-Type", "application/json")
        response.set_header("Cache-Control", "no-cache")
        
        assert response.headers["content-type"] == "application/json"
        assert response.headers["cache-control"] == "no-cache"
    
    def test_get_header(self):
        """测试获取响应头"""
        response = Response()
        response.headers = {"content-type": "application/json", "cache-control": "no-cache"}
        
        # 测试获取存在的头
        assert response.get_header("Content-Type") == "application/json"
        assert response.get_header("content-type") == "application/json"
        assert response.get_header("Cache-Control") == "no-cache"
        
        # 测试获取不存在的头
        assert response.get_header("Non-Existent") is None
        assert response.get_header("Non-Existent", "default") == "default"


class TestMiddlewareContext:
    """中间件上下文测试"""
    
    def test_context_initialization(self):
        """测试中间件上下文初始化"""
        request = Request()
        context = MiddlewareContext(request=request)
        
        assert context.request == request
        assert context.response is None
        assert context.error is None
        assert context.data == {}
        assert isinstance(context.start_time, float)
    
    def test_context_initialization_with_data(self):
        """测试使用数据初始化中间件上下文"""
        request = Request()
        response = Response()
        error = Exception("Test error")
        data = {"key1": "value1", "key2": 42}
        
        context = MiddlewareContext(
            request=request,
            response=response,
            error=error,
            data=data
        )
        
        assert context.request == request
        assert context.response == response
        assert context.error == error
        assert context.data == data
    
    def test_get_data(self):
        """测试获取上下文数据"""
        context = MiddlewareContext(request=Request())
        context.data = {"key1": "value1", "key2": 42}
        
        # 测试获取存在的数据
        assert context.get_data("key1") == "value1"
        assert context.get_data("key2") == 42
        
        # 测试获取不存在的数据
        assert context.get_data("non_existent") is None
        assert context.get_data("non_existent", "default") == "default"
    
    def test_set_data(self):
        """测试设置上下文数据"""
        context = MiddlewareContext(request=Request())
        
        context.set_data("key1", "value1")
        context.set_data("key2", 42)
        
        assert context.data["key1"] == "value1"
        assert context.data["key2"] == 42
    
    def test_get_elapsed_time(self):
        """测试获取经过的时间"""
        context = MiddlewareContext(request=Request())
        
        # 等待一小段时间
        time.sleep(0.01)
        
        elapsed = context.get_elapsed_time()
        assert elapsed >= 0.01
        assert elapsed < 1.0  # 应该小于1秒


class TestMiddlewareInterface:
    """中间件接口测试"""
    
    def test_interface_abstract_methods(self):
        """测试中间件接口的抽象方法"""
        # 创建实现接口的类
        class TestMiddleware(MiddlewareInterface):
            @property
            def name(self) -> str:
                return "test"
            
            @property
            def middleware_type(self) -> MiddlewareType:
                return MiddlewareType.REQUEST
            
            def process(self, context, next_handler):
                return next_handler(context)
        
        middleware = TestMiddleware()
        
        assert middleware.name == "test"
        assert middleware.middleware_type == MiddlewareType.REQUEST
        
        # 测试process方法
        context = MiddlewareContext(request=Request())
        next_handler = Mock(return_value="result")
        
        result = middleware.process(context, next_handler)
        
        assert result == "result"
        next_handler.assert_called_once_with(context)
    
    def test_interface_cannot_instantiate(self):
        """测试不能直接实例化接口"""
        with pytest.raises(TypeError):
            MiddlewareInterface()


class TestBaseMiddleware:
    """基础中间件类测试"""
    
    def test_base_middleware_initialization(self):
        """测试基础中间件初始化"""
        middleware = BaseMiddleware("test", MiddlewareType.REQUEST)
        
        assert middleware.name == "test"
        assert middleware.middleware_type == MiddlewareType.REQUEST
    
    def test_base_middleware_process(self):
        """测试基础中间件处理"""
        middleware = BaseMiddleware("test", MiddlewareType.REQUEST)
        
        context = MiddlewareContext(request=Request())
        next_handler = Mock(return_value="result")
        
        result = middleware.process(context, next_handler)
        
        assert result == "result"
        next_handler.assert_called_once_with(context)
    
    def test_base_middleware_with_different_types(self):
        """测试不同类型的基础中间件"""
        request_middleware = BaseMiddleware("request", MiddlewareType.REQUEST)
        response_middleware = BaseMiddleware("response", MiddlewareType.RESPONSE)
        error_middleware = BaseMiddleware("error", MiddlewareType.ERROR)
        
        assert request_middleware.middleware_type == MiddlewareType.REQUEST
        assert response_middleware.middleware_type == MiddlewareType.RESPONSE
        assert error_middleware.middleware_type == MiddlewareType.ERROR


class TestMiddlewareError:
    """中间件异常测试"""
    
    def test_middleware_error_initialization(self):
        """测试中间件异常初始化"""
        error = MiddlewareError("Test error")
        
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_middleware_error_inheritance(self):
        """测试中间件异常继承"""
        error = MiddlewareError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, MiddlewareError)


@pytest.mark.parametrize("method,path,expected", [
    ("GET", "/", "GET:/"),
    ("POST", "/api/users", "POST:/api/users"),
    ("PUT", "/api/users/123", "PUT:/api/users/123"),
    ("DELETE", "/api/users/123", "DELETE:/api/users/123"),
])
def test_request_method_path_combinations(method, path, expected):
    """测试请求方法和路径的组合"""
    request = Request(method=method, path=path)
    
    assert request.method == method
    assert request.path == path


@pytest.mark.parametrize("status_code,content_type,expected", [
    (200, "application/json", 200),
    (201, "application/json", 201),
    (400, "application/json", 400),
    (500, "text/html", 500),
])
def test_response_status_code_combinations(status_code, content_type, expected):
    """测试响应状态码和内容类型的组合"""
    response = Response(status_code=status_code, content_type=content_type)
    
    assert response.status_code == expected
    assert response.content_type == content_type


@pytest.mark.parametrize("middleware_type", [
    MiddlewareType.REQUEST,
    MiddlewareType.RESPONSE,
    MiddlewareType.ERROR,
    MiddlewareType.AUTH,
    MiddlewareType.LOGGING,
    MiddlewareType.CACHE,
])
def test_base_middleware_with_all_types(middleware_type):
    """测试所有类型的基础中间件"""
    middleware = BaseMiddleware(f"test_{middleware_type.value}", middleware_type)
    
    assert middleware.name == f"test_{middleware_type.value}"
    assert middleware.middleware_type == middleware_type
