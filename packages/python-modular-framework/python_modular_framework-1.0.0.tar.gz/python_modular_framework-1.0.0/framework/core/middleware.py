"""
中间件系统实现
- 提供中间件接口和基础中间件类
- 支持请求处理中间件和错误处理中间件
- 实现中间件链式调用机制

主要功能：
- 中间件接口定义
- 请求处理中间件
- 错误处理中间件
- 中间件管理器
- 中间件链式调用

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

class MiddlewareType(Enum):
    """中间件类型枚举"""

    REQUEST = "request"  # 请求处理中间件
    RESPONSE = "response"  # 响应处理中间件
    ERROR = "error"  # 错误处理中间件
    AUTH = "auth"  # 认证中间件
    LOGGING = "logging"  # 日志中间件
    CACHE = "cache"  # 缓存中间件


@dataclass
class Request:
    """
    请求对象

    封装HTTP请求的相关信息。
    """

    method: str = "GET"
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    body: Any = None
    user: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def get_header(self, name: str, default: str = None) -> Optional[str]:
        """
        获取请求头

        Args:
            name (str): 头名称
            default (str): 默认值

        Returns:
            Optional[str]: 头值
        """
        return self.headers.get(name.lower(), default)

    def get_query_param(self, name: str, default: Any = None) -> Any:
        """
        获取查询参数

        Args:
            name (str): 参数名称
            default (Any): 默认值

        Returns:
            Any: 参数值
        """
        return self.query_params.get(name, default)


@dataclass
class Response:
    """
    响应对象

    封装HTTP响应的相关信息。
    """

    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    content_type: str = "application/json"
    timestamp: float = field(default_factory=time.time)

    def set_header(self, name: str, value: str) -> None:
        """
        设置响应头

        Args:
            name (str): 头名称
            value (str): 头值
        """
        self.headers[name.lower()] = value

    def get_header(self, name: str, default: str = None) -> Optional[str]:
        """
        获取响应头

        Args:
            name (str): 头名称
            default (str): 默认值

        Returns:
            Optional[str]: 头值
        """
        return self.headers.get(name.lower(), default)


@dataclass
class MiddlewareContext:
    """
    中间件上下文

    在中间件链中传递的上下文信息。
    """

    request: Request
    response: Optional[Response] = None
    error: Optional[Exception] = None
    data: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据

        Args:
            key (str): 数据键
            default (Any): 默认值

        Returns:
            Any: 数据值
        """
        return self.data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """
        设置上下文数据

        Args:
            key (str): 数据键
            value (Any): 数据值
        """
        self.data[key] = value

    def get_elapsed_time(self) -> float:
        """
        获取经过的时间

        Returns:
            float: 经过的时间（秒）
        """
        return time.time() - self.start_time


class MiddlewareInterface(ABC):
    """
    中间件接口

    定义中间件的标准行为。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        获取中间件名称

        Returns:
            str: 中间件名称
        """

    @property
    @abstractmethod
    def middleware_type(self) -> MiddlewareType:
        """
        获取中间件类型

        Returns:
            MiddlewareType: 中间件类型
        """

    @abstractmethod
    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        """
        处理中间件逻辑

        Args:
            context (MiddlewareContext): 中间件上下文
            next_handler (Callable): 下一个处理器

        Returns:
            Any: 处理结果
        """


class BaseMiddleware(MiddlewareInterface):
    """
    基础中间件类

    提供中间件的基础实现。
    """

    def __init__(self, name: str, middleware_type: MiddlewareType):
        """
        初始化基础中间件

        Args:
            name (str): 中间件名称
            middleware_type (MiddlewareType): 中间件类型
        """
        self._name = name
        self._middleware_type = middleware_type

    @property
    def name(self) -> str:
        """获取中间件名称"""
        return self._name

    @property
    def middleware_type(self) -> MiddlewareType:
        """获取中间件类型"""
        return self._middleware_type

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        """
        处理中间件逻辑

        Args:
            context (MiddlewareContext): 中间件上下文
            next_handler (Callable): 下一个处理器

        Returns:
            Any: 处理结果
        """
        # 默认实现：直接调用下一个处理器
        return next_handler(context)


class RequestMiddleware(BaseMiddleware):
    """
    请求处理中间件

    处理HTTP请求的中间件基类。
    """

    def __init__(self, name: str):
        """
        初始化请求处理中间件

        Args:
            name (str): 中间件名称
        """
        super().__init__(name, MiddlewareType.REQUEST)

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        """
        处理请求

        Args:
            context (MiddlewareContext): 中间件上下文
            next_handler (Callable): 下一个处理器

        Returns:
            Any: 处理结果
        """
        # 请求前处理
        self.before_request(context)

        try:
            # 调用下一个处理器
            result = next_handler(context)

            # 请求后处理
            self.after_request(context, result)

            return result

        except Exception as e:
            # 请求异常处理
            self.on_request_error(context, e)
            raise

    def before_request(self, context: MiddlewareContext) -> None:
        """
        请求前处理

        Args:
            context (MiddlewareContext): 中间件上下文
        """

    def after_request(self, context: MiddlewareContext, result: Any) -> None:
        """
        请求后处理

        Args:
            context (MiddlewareContext): 中间件上下文
            result (Any): 处理结果
        """

    def on_request_error(self, context: MiddlewareContext, error: Exception) -> None:
        """
        请求错误处理

        Args:
            context (MiddlewareContext): 中间件上下文
            error (Exception): 错误对象
        """


class ErrorMiddleware(BaseMiddleware):
    """
    错误处理中间件

    处理异常的中间件基类。
    """

    def __init__(self, name: str):
        """
        初始化错误处理中间件

        Args:
            name (str): 中间件名称
        """
        super().__init__(name, MiddlewareType.ERROR)

    def process(self, context: MiddlewareContext, next_handler: Callable) -> Any:
        """
        处理错误

        Args:
            context (MiddlewareContext): 中间件上下文
            next_handler (Callable): 下一个处理器

        Returns:
            Any: 处理结果
        """
        try:
            return next_handler(context)
        except Exception as e:
            context.error = e
            # 直接返回错误响应，不重新抛出异常
            return self.handle_error(context, e)

    def handle_error(self, context: MiddlewareContext, error: Exception) -> Any:
        """
        处理错误

        Args:
            context (MiddlewarewareContext): 中间件上下文
            error (Exception): 错误对象

        Returns:
            Any: 错误处理结果
        """
        # 默认实现：重新抛出异常
        raise error


class LoggingMiddleware(RequestMiddleware):
    """
    日志中间件

    记录请求和响应的日志信息。
    """

    def __init__(
        self,
        name: str = "logging",
        log_requests: bool = True,
        log_responses: bool = True,
        log_errors: bool = True,
    ):
        """
        初始化日志中间件

        Args:
            name (str): 中间件名称
            log_requests (bool): 是否记录请求日志
            log_responses (bool): 是否记录响应日志
            log_errors (bool): 是否记录错误日志
        """
        super().__init__(name)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_errors = log_errors

    def before_request(self, context: MiddlewareContext) -> None:
        """记录请求日志"""
        if self.log_requests:
            print(
                f"[{self.name}] Request: {context.request.method} {context.request.path}"
            )

    def after_request(self, context: MiddlewareContext, result: Any) -> None:
        """记录响应日志"""
        if self.log_responses and context.response:
            elapsed = context.get_elapsed_time()
            print(
                f"[{self.name}] Response: {context.response.status_code} ({elapsed:.3f}s)"
            )

    def on_request_error(self, context: MiddlewareContext, error: Exception) -> None:
        """记录错误日志"""
        if self.log_errors:
            print(f"[{self.name}] Error: {type(error).__name__}: {error}")


class AuthMiddleware(RequestMiddleware):
    """
    认证中间件

    处理用户认证和授权。
    """

    def __init__(self, name: str = "auth", required: bool = True):
        """
        初始化认证中间件

        Args:
            name (str): 中间件名称
            required (bool): 是否必需认证
        """
        super().__init__(name)
        self.required = required

    def before_request(self, context: MiddlewareContext) -> None:
        """验证用户认证"""
        # 检查认证头
        auth_header = context.request.get_header("authorization")

        if not auth_header:
            if self.required:
                raise UnauthorizedError("Authentication required")
            return

        # 验证令牌
        try:
            user = self.validate_token(auth_header)
            context.request.user = user
            context.set_data("authenticated", True)
        except Exception as e:
            if self.required:
                raise UnauthorizedError(f"Invalid token: {e}")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        验证令牌

        Args:
            token (str): 认证令牌

        Returns:
            Dict[str, Any]: 用户信息

        Raises:
            UnauthorizedError: 令牌无效时抛出异常
        """
        # 这里应该实现实际的令牌验证逻辑
        # 简化实现：假设令牌格式为 "Bearer <token>"
        if not token.startswith("Bearer "):
            raise ValueError("Invalid token format")

        # 模拟用户信息
        return {"id": "user123", "username": "testuser", "roles": ["user"]}


class CacheMiddleware(RequestMiddleware):
    """
    缓存中间件

    提供请求和响应的缓存功能。
    """

    def __init__(
        self,
        name: str = "cache",
        cache_service=None,
        cache_requests: bool = True,
        cache_responses: bool = True,
        default_ttl: int = 300,
    ):
        """
        初始化缓存中间件

        Args:
            name (str): 中间件名称
            cache_service: 缓存服务实例
            cache_requests (bool): 是否缓存请求
            cache_responses (bool): 是否缓存响应
            default_ttl (int): 默认缓存时间（秒）
        """
        super().__init__(name)
        self.cache_service = cache_service
        self.cache_requests = cache_requests
        self.cache_responses = cache_responses
        self.default_ttl = default_ttl

    def before_request(self, context: MiddlewareContext) -> None:
        """检查缓存"""
        if not self.cache_requests or not self.cache_service:
            return

        # 生成缓存键
        cache_key = self._generate_cache_key(context.request)

        # 检查缓存
        cached_response = self.cache_service.get(cache_key)
        if cached_response:
            context.set_data("cached_response", cached_response)
            context.set_data("cache_hit", True)

    def after_request(self, context: MiddlewareContext, result: Any) -> None:
        """缓存响应"""
        if not self.cache_responses or not self.cache_service:
            return

        # 如果是从缓存获取的响应，不重复缓存
        if context.get_data("cache_hit"):
            return

        # 生成缓存键
        cache_key = self._generate_cache_key(context.request)

        # 缓存响应
        if context.response and context.response.status_code == 200:
            self.cache_service.set(cache_key, context.response, ttl=self.default_ttl)

    def _generate_cache_key(self, request: Request) -> str:
        """
        生成缓存键

        Args:
            request (Request): 请求对象

        Returns:
            str: 缓存键
        """
        # 基于请求方法和路径生成缓存键
        return f"{request.method}:{request.path}"


class MiddlewareManager:
    """
    中间件管理器

    管理中间件链的注册、排序和执行。
    """

    def __init__(self):
        """
        初始化中间件管理器

        创建中间件存储和排序机制。
        """
        self._middlewares: List[MiddlewareInterface] = []
        self._middleware_map: Dict[str, MiddlewareInterface] = {}

    def register(
        self, middleware: MiddlewareInterface, position: Optional[int] = None
    ) -> None:
        """
        注册中间件

        Args:
            middleware (MiddlewareInterface): 中间件实例
            position (Optional[int]): 插入位置，None表示添加到末尾
        """
        if middleware.name in self._middleware_map:
            raise ValueError(f"Middleware '{middleware.name}' is already registered")

        if position is None:
            self._middlewares.append(middleware)
        else:
            self._middlewares.insert(position, middleware)

        self._middleware_map[middleware.name] = middleware

    def unregister(self, name: str) -> None:
        """
        注销中间件

        Args:
            name (str): 中间件名称
        """
        if name not in self._middleware_map:
            raise ValueError(f"Middleware '{name}' is not registered")

        middleware = self._middleware_map[name]
        self._middlewares.remove(middleware)
        del self._middleware_map[name]

    def get_middleware(self, name: str) -> Optional[MiddlewareInterface]:
        """
        获取中间件

        Args:
            name (str): 中间件名称

        Returns:
            Optional[MiddlewareInterface]: 中间件实例
        """
        return self._middleware_map.get(name)

    def list_middlewares(self) -> List[str]:
        """
        获取所有中间件名称列表

        Returns:
            List[str]: 中间件名称列表
        """
        return list(self._middleware_map.keys())

    def process_request(self, request: Request) -> Response:
        """
        处理请求

        按顺序执行所有中间件。

        Args:
            request (Request): 请求对象

        Returns:
            Response: 响应对象
        """
        context = MiddlewareContext(request=request)

        # 创建中间件链
        def create_handler(index: int) -> Callable:
            if index >= len(self._middlewares):
                # 最后一个处理器：执行实际业务逻辑
                return self._execute_handler

            middleware = self._middlewares[index]

            def handler(ctx: MiddlewareContext) -> Any:
                return middleware.process(ctx, create_handler(index + 1))

            return handler

        # 执行中间件链
        try:
            result = create_handler(0)(context)

            # 如果结果是Response对象，直接返回
            if isinstance(result, Response):
                return result

            # 如果没有响应，创建默认响应
            if not context.response:
                context.response = Response(body=result)

            return context.response

        except Exception as e:
            # 处理异常
            return self._handle_exception(context, e)

    def _execute_handler(self, context: MiddlewareContext) -> Any:
        """
        执行实际的处理逻辑

        Args:
            context (MiddlewareContext): 中间件上下文

        Returns:
            Any: 处理结果
        """
        # 这里应该调用实际的路由处理器
        # 简化实现：返回默认响应
        return {"message": "Hello, World!", "path": context.request.path}

    def _handle_exception(
        self, context: MiddlewareContext, error: Exception
    ) -> Response:
        """
        处理异常

        Args:
            context (MiddlewareContext): 中间件上下文
            error (Exception): 异常对象

        Returns:
            Response: 错误响应
        """
        # 查找错误处理中间件
        error_middlewares = [
            m for m in self._middlewares if isinstance(m, ErrorMiddleware)
        ]

        if error_middlewares:
            # 使用错误处理中间件
            for middleware in error_middlewares:
                try:
                    context.error = error
                    result = middleware.handle_error(context, error)
                    if isinstance(result, Response):
                        return result
                except Exception:
                    continue

        # 默认错误处理
        return Response(
            status_code=500,
            body={"error": "Internal Server Error", "message": str(error)},
            content_type="application/json",
        )

    def clear(self) -> None:
        """清空所有中间件"""
        self._middlewares.clear()
        self._middleware_map.clear()


# 异常类定义
class MiddlewareError(Exception):
    """中间件异常基类"""



class UnauthorizedError(MiddlewareError):
    """未授权异常"""



class MiddlewareRegistrationError(MiddlewareError):
    """中间件注册异常"""

