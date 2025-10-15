#!/usr/bin/env python3
"""
中间件系统示例

演示框架的中间件系统功能，包括：
- 中间件注册和管理
- 请求处理中间件
- 错误处理中间件
- 认证中间件
- 缓存中间件
- 日志中间件

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.middleware import (
    MiddlewareManager,
    Request,
    Response,
    MiddlewareContext,
    LoggingMiddleware,
    AuthMiddleware,
    CacheMiddleware,
    ErrorMiddleware,
    MiddlewareType,
    UnauthorizedError,
)


class CustomErrorMiddleware(ErrorMiddleware):
    """自定义错误处理中间件"""

    def __init__(self, name: str = "custom_error"):
        super().__init__(name)

    def handle_error(self, context: MiddlewareContext, error: Exception) -> Response:
        """处理错误"""
        if isinstance(error, UnauthorizedError):
            return Response(
                status_code=401,
                body={"error": "Unauthorized", "message": str(error)},
                content_type="application/json",
            )
        elif isinstance(error, ValueError):
            return Response(
                status_code=400,
                body={"error": "Bad Request", "message": str(error)},
                content_type="application/json",
            )
        else:
            return Response(
                status_code=500,
                body={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                },
                content_type="application/json",
            )


class RateLimitMiddleware(LoggingMiddleware):
    """限流中间件"""

    def __init__(
        self,
        name: str = "rate_limit",
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        super().__init__(name)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # 简化的内存存储

    def before_request(self, context: MiddlewareContext) -> None:
        """检查限流"""
        client_ip = context.request.get_header("x-forwarded-for", "127.0.0.1")
        current_time = time.time()

        # 清理过期记录
        self.request_counts = {
            ip: count
            for ip, count in self.request_counts.items()
            if current_time - count["last_reset"] < self.window_seconds
        }

        # 检查当前客户端请求数
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {"count": 0, "last_reset": current_time}

        if self.request_counts[client_ip]["count"] >= self.max_requests:
            raise ValueError(
                f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds} seconds"
            )

        # 增加请求计数
        self.request_counts[client_ip]["count"] += 1

        # 调用父类方法记录日志
        super().before_request(context)


class MockCacheService:
    """模拟缓存服务"""

    def __init__(self):
        self.cache = {}

    def get(self, key: str):
        """获取缓存"""
        return self.cache.get(key)

    def set(self, key: str, value: any, ttl: int = 300):
        """设置缓存"""
        self.cache[key] = value
        print(f"[Cache] Set cache for key: {key}, TTL: {ttl}s")

    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            print(f"[Cache] Deleted cache for key: {key}")


class MiddlewareDemo:
    """中间件演示类"""

    def __init__(self):
        self.manager = MiddlewareManager()
        self.cache_service = MockCacheService()
        self.setup_middlewares()

    def setup_middlewares(self):
        """设置中间件"""
        print("=== 设置中间件 ===")

        # 1. 错误处理中间件（最先注册，最后执行）
        error_middleware = CustomErrorMiddleware()
        self.manager.register(error_middleware)
        print(f"✅ 注册错误处理中间件: {error_middleware.name}")

        # 2. 日志中间件
        logging_middleware = LoggingMiddleware(
            name="request_logging",
            log_requests=True,
            log_responses=True,
            log_errors=True,
        )
        self.manager.register(logging_middleware)
        print(f"✅ 注册日志中间件: {logging_middleware.name}")

        # 3. 限流中间件
        rate_limit_middleware = RateLimitMiddleware(
            name="rate_limit", max_requests=5, window_seconds=60
        )
        self.manager.register(rate_limit_middleware)
        print(f"✅ 注册限流中间件: {rate_limit_middleware.name}")

        # 4. 缓存中间件
        cache_middleware = CacheMiddleware(
            name="response_cache",
            cache_service=self.cache_service,
            cache_requests=True,
            cache_responses=True,
            default_ttl=300,
        )
        self.manager.register(cache_middleware)
        print(f"✅ 注册缓存中间件: {cache_middleware.name}")

        # 5. 认证中间件
        auth_middleware = AuthMiddleware(
            name="user_auth", required=False  # 设置为非必需，便于演示
        )
        self.manager.register(auth_middleware)
        print(f"✅ 注册认证中间件: {auth_middleware.name}")

        print(f"\n📋 已注册的中间件: {self.manager.list_middlewares()}")

    def create_test_request(
        self,
        method: str = "GET",
        path: str = "/",
        headers: dict = None,
        body: any = None,
    ) -> Request:
        """创建测试请求"""
        return Request(method=method, path=path, headers=headers or {}, body=body)

    def test_normal_request(self):
        """测试正常请求"""
        print("\n=== 测试正常请求 ===")

        request = self.create_test_request(
            method="GET",
            path="/api/users",
            headers={"content-type": "application/json"},
        )

        try:
            response = self.manager.process_request(request)
            print(f"✅ 请求处理成功")
            print(f"   状态码: {response.status_code}")
            print(f"   响应体: {response.body}")
        except Exception as e:
            print(f"❌ 请求处理失败: {e}")

    def test_authenticated_request(self):
        """测试认证请求"""
        print("\n=== 测试认证请求 ===")

        request = self.create_test_request(
            method="GET",
            path="/api/profile",
            headers={
                "authorization": "Bearer valid_token_123",
                "content-type": "application/json",
            },
        )

        try:
            response = self.manager.process_request(request)
            print(f"✅ 认证请求处理成功")
            print(f"   状态码: {response.status_code}")
            print(f"   响应体: {response.body}")
        except Exception as e:
            print(f"❌ 认证请求处理失败: {e}")

    def test_unauthorized_request(self):
        """测试未授权请求"""
        print("\n=== 测试未授权请求 ===")

        # 临时设置认证中间件为必需
        auth_middleware = self.manager.get_middleware("user_auth")
        if auth_middleware:
            auth_middleware.required = True

        request = self.create_test_request(
            method="GET",
            path="/api/protected",
            headers={"content-type": "application/json"},
        )

        try:
            response = self.manager.process_request(request)
            print(f"✅ 未授权请求处理成功（应该返回401）")
            print(f"   状态码: {response.status_code}")
            print(f"   响应体: {response.body}")
        except Exception as e:
            print(f"❌ 未授权请求处理失败: {e}")

        # 恢复认证中间件设置
        if auth_middleware:
            auth_middleware.required = False

    def test_rate_limit(self):
        """测试限流功能"""
        print("\n=== 测试限流功能 ===")

        # 发送多个请求来触发限流
        for i in range(7):  # 超过限流阈值（5个请求）
            request = self.create_test_request(
                method="GET",
                path=f"/api/test/{i}",
                headers={"x-forwarded-for": "192.168.1.100"},
            )

            try:
                response = self.manager.process_request(request)
                print(f"   请求 {i+1}: 状态码 {response.status_code}")
            except Exception as e:
                print(f"   请求 {i+1}: 被限流 - {e}")
                break

    def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n=== 测试缓存功能 ===")

        # 第一次请求（应该缓存）
        request1 = self.create_test_request(method="GET", path="/api/cached-data")

        print("第一次请求（应该缓存）:")
        response1 = self.manager.process_request(request1)
        print(f"   状态码: {response1.status_code}")
        print(f"   响应体: {response1.body}")

        # 第二次请求（应该从缓存获取）
        request2 = self.create_test_request(method="GET", path="/api/cached-data")

        print("\n第二次请求（应该从缓存获取）:")
        response2 = self.manager.process_request(request2)
        print(f"   状态码: {response2.status_code}")
        print(f"   响应体: {response2.body}")

    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")

        # 测试不同类型的错误
        test_cases = [
            ("ValueError", ValueError("Invalid input data")),
            ("UnauthorizedError", UnauthorizedError("Token expired")),
            ("GenericError", RuntimeError("Something went wrong")),
        ]

        for error_name, error in test_cases:
            print(f"\n测试 {error_name}:")
            try:
                # 模拟在中间件中抛出错误
                request = self.create_test_request(path=f"/api/error/{error_name}")

                # 临时修改处理器来抛出错误
                original_handler = self.manager._execute_handler

                def error_handler(context):
                    raise error

                self.manager._execute_handler = error_handler

                response = self.manager.process_request(request)
                print(f"   状态码: {response.status_code}")
                print(f"   响应体: {response.body}")

                # 恢复原始处理器
                self.manager._execute_handler = original_handler

            except Exception as e:
                print(f"   未处理的错误: {e}")

        # 重置限流计数器，避免影响后续测试
        rate_limit_middleware = self.manager.get_middleware("rate_limit")
        if rate_limit_middleware:
            rate_limit_middleware.request_counts.clear()

    def show_middleware_info(self):
        """显示中间件信息"""
        print("\n=== 中间件信息 ===")

        middlewares = self.manager.list_middlewares()
        print(f"已注册中间件数量: {len(middlewares)}")

        for name in middlewares:
            middleware = self.manager.get_middleware(name)
            if middleware:
                print(f"📦 {name}:")
                print(f"   类型: {middleware.middleware_type.value}")
                print(f"   类名: {middleware.__class__.__name__}")

    def run_demo(self):
        """运行完整演示"""
        print("=== Python模块化框架 - 中间件系统演示 ===\n")

        try:
            # 显示中间件信息
            self.show_middleware_info()

            # 测试各种场景
            self.test_normal_request()
            self.test_authenticated_request()
            self.test_unauthorized_request()
            self.test_rate_limit()
            self.test_cache_functionality()
            self.test_error_handling()

            print("\n=== 演示完成 ===")
            return 0

        except Exception as e:
            print(f"\n❌ 演示过程中发生错误: {e}")
            return 1


def main():
    """主函数"""
    demo = MiddlewareDemo()
    return demo.run_demo()


if __name__ == "__main__":
    exit(main())
