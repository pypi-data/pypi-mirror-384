#!/usr/bin/env python3
"""
中间件集成示例

演示如何将中间件系统与框架应用集成，包括：
- 在应用中集成中间件管理器
- 中间件与组件的协作
- 请求路由和中间件链
- 完整的Web应用模拟

作者：开发团队
创建时间：2024-01-XX
"""

import sys
import os
import time
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.core.application import Application
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


class WebApplication:
    """Web应用类，集成中间件系统"""

    def __init__(self, name: str = "web-app", version: str = "1.0.0"):
        """初始化Web应用"""
        self.app = Application(name=name, version=version)
        self.middleware_manager = MiddlewareManager()
        self.routes = {}
        self.setup_middlewares()

    def setup_middlewares(self):
        """设置中间件"""
        print("=== 设置Web应用中间件 ===")

        # 1. 错误处理中间件
        error_middleware = ErrorMiddleware("error_handler")
        self.middleware_manager.register(error_middleware)
        print("✅ 注册错误处理中间件")

        # 2. 日志中间件
        logging_middleware = LoggingMiddleware(
            name="access_log", log_requests=True, log_responses=True, log_errors=True
        )
        self.middleware_manager.register(logging_middleware)
        print("✅ 注册访问日志中间件")

        # 3. 认证中间件
        auth_middleware = AuthMiddleware(name="authentication", required=False)
        self.middleware_manager.register(auth_middleware)
        print("✅ 注册认证中间件")

        # 4. 缓存中间件
        cache_middleware = CacheMiddleware(
            name="response_cache",
            cache_service=None,  # 暂时不使用缓存服务
            cache_requests=False,
            cache_responses=False,
        )
        self.middleware_manager.register(cache_middleware)
        print("✅ 注册缓存中间件")

    def route(self, path: str, methods: list = None):
        """路由装饰器"""
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            if path not in self.routes:
                self.routes[path] = {}
            for method in methods:
                self.routes[path][method.upper()] = handler
            return handler

        return decorator

    def handle_request(self, request: Request) -> Response:
        """处理请求"""
        # 查找路由处理器
        handler = self._find_handler(request)

        if not handler:
            # 临时修改处理器来处理404
            original_handler = self.middleware_manager._execute_handler

            def not_found_handler(context):
                return Response(
                    status_code=404,
                    body={
                        "error": "Not Found",
                        "message": f"Route {context.request.path} not found",
                    },
                    content_type="application/json",
                )

            self.middleware_manager._execute_handler = not_found_handler
            response = self.middleware_manager.process_request(request)
            self.middleware_manager._execute_handler = original_handler
            return response

        # 临时修改处理器来调用实际的路由处理器
        original_handler = self.middleware_manager._execute_handler

        def route_handler(context):
            return handler(context.request)

        self.middleware_manager._execute_handler = route_handler

        # 通过中间件链处理请求
        response = self.middleware_manager.process_request(request)

        # 恢复原始处理器
        self.middleware_manager._execute_handler = original_handler

        return response

    def _find_handler(self, request: Request):
        """查找路由处理器"""
        path = request.path
        method = request.method.upper()

        if path in self.routes and method in self.routes[path]:
            return self.routes[path][method]

        return None

    def start(self):
        """启动应用"""
        print("\n=== 启动Web应用 ===")

        # 配置应用
        config = {
            "app_name": "Web Application with Middleware",
            "debug": True,
            "log_level": "INFO",
        }

        self.app.configure(config)
        print("✅ 应用配置完成")

        # 启动应用
        self.app.start()
        print("✅ 应用启动成功")

    def stop(self):
        """停止应用"""
        print("\n=== 停止Web应用 ===")
        self.app.stop()
        print("✅ 应用停止成功")


def create_web_app():
    """创建Web应用实例"""
    app = WebApplication("middleware-web-app", "1.0.0")

    # 定义路由
    @app.route("/")
    def home_handler(request):
        """首页处理器"""
        return {
            "message": "Welcome to the Web Application",
            "version": "1.0.0",
            "timestamp": time.time(),
        }

    @app.route("/api/users")
    def users_handler(request):
        """用户列表处理器"""
        # 获取用户组件
        user_component = app.app.get_component("user")
        if user_component:
            # 搜索用户
            from components.user.models import UserSearch

            search_params = UserSearch(page=1, page_size=10)
            result = user_component.search_users(search_params)

            return {
                "users": [
                    {"id": user.id, "username": user.username, "email": user.email}
                    for user in result.users
                ],
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
            }
        else:
            return {"error": "User component not available"}

    @app.route("/api/users", methods=["POST"])
    def create_user_handler(request):
        """创建用户处理器"""
        try:
            # 解析请求体
            if isinstance(request.body, dict):
                user_data = request.body
            else:
                user_data = json.loads(request.body) if request.body else {}

            # 获取用户组件
            user_component = app.app.get_component("user")
            if user_component:
                from components.user.models import UserCreate

                create_data = UserCreate(
                    username=user_data.get("username", "newuser"),
                    email=user_data.get("email", "newuser@example.com"),
                    full_name=user_data.get("full_name", "New User"),
                )

                user = user_component.create_user(create_data)
                return {
                    "message": "User created successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                    },
                }
            else:
                return {"error": "User component not available"}

        except Exception as e:
            raise ValueError(f"Failed to create user: {e}")

    @app.route("/api/profile")
    def profile_handler(request):
        """用户资料处理器（需要认证）"""
        # 检查用户认证
        if not request.user:
            raise UnauthorizedError("Authentication required")

        return {
            "user": request.user,
            "message": "Profile information",
            "timestamp": time.time(),
        }

    @app.route("/api/health")
    def health_handler(request):
        """健康检查处理器"""
        health = app.app.health_check()
        return {
            "status": health["overall"],
            "components": health["components"],
            "timestamp": time.time(),
        }

    @app.route("/api/metrics")
    def metrics_handler(request):
        """指标处理器"""
        metrics = app.app.get_metrics()
        return {
            "application": metrics["application"],
            "components": metrics["components"],
            "timestamp": time.time(),
        }

    return app


def test_web_app():
    """测试Web应用"""
    print("=== Python模块化框架 - 中间件集成示例 ===\n")

    # 创建Web应用
    app = create_web_app()

    try:
        # 启动应用
        app.start()

        # 测试各种请求
        test_requests = [
            {
                "name": "首页请求",
                "request": Request(method="GET", path="/"),
                "expected_status": 200,
            },
            {
                "name": "用户列表请求",
                "request": Request(method="GET", path="/api/users"),
                "expected_status": 200,
            },
            {
                "name": "创建用户请求",
                "request": Request(
                    method="POST",
                    path="/api/users",
                    headers={"content-type": "application/json"},
                    body={
                        "username": "testuser",
                        "email": "test@example.com",
                        "full_name": "Test User",
                    },
                ),
                "expected_status": 200,
            },
            {
                "name": "用户资料请求（无认证）",
                "request": Request(method="GET", path="/api/profile"),
                "expected_status": 401,
            },
            {
                "name": "用户资料请求（有认证）",
                "request": Request(
                    method="GET",
                    path="/api/profile",
                    headers={"authorization": "Bearer valid_token_123"},
                ),
                "expected_status": 200,
            },
            {
                "name": "健康检查请求",
                "request": Request(method="GET", path="/api/health"),
                "expected_status": 200,
            },
            {
                "name": "指标请求",
                "request": Request(method="GET", path="/api/metrics"),
                "expected_status": 200,
            },
            {
                "name": "不存在的路由",
                "request": Request(method="GET", path="/api/nonexistent"),
                "expected_status": 404,
            },
        ]

        print("\n=== 测试Web应用请求 ===")

        for test_case in test_requests:
            print(f"\n测试: {test_case['name']}")
            try:
                response = app.handle_request(test_case["request"])
                print(f"   状态码: {response.status_code}")
                print(
                    f"   响应体: {json.dumps(response.body, indent=6) if isinstance(response.body, dict) else response.body}"
                )

                if response.status_code == test_case["expected_status"]:
                    print("   ✅ 测试通过")
                else:
                    print(f"   ❌ 测试失败，期望状态码: {test_case['expected_status']}")

            except Exception as e:
                print(f"   ❌ 请求处理异常: {e}")

        # 显示应用状态
        print(f"\n=== 应用状态 ===")
        health = app.app.health_check()
        print(f"整体健康状态: {health['overall']}")
        print(f"组件数量: {len(health['components'])}")

        # 停止应用
        app.stop()

        print("\n=== 测试完成 ===")
        return 0

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return 1


def main():
    """主函数"""
    return test_web_app()


if __name__ == "__main__":
    exit(main())
