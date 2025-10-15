"""
应用集成测试

测试应用的完整启动流程和组件间交互。

测试内容：
- 应用完整启动流程
- 组件间依赖解析
- 配置管理集成
- 健康检查集成
- 错误处理集成

作者：开发团队
创建时间：2025-01-12
"""

import pytest
import time
from unittest.mock import Mock, patch
from framework.core.application import Application
from framework.core.config import Config
from components.auth.component import AuthComponent
from components.common.cache.component import CacheComponent
from components.common.database.component import DatabaseComponent
from components.common.logging.component import LoggingComponent


class TestAppIntegration:
    """应用集成测试"""
    
    def test_app_complete_startup_flow(self):
        """测试应用完整启动流程"""
        app = Application("integration-test", "1.0.0")
        
        # 配置应用
        config_data = {
            "debug": True,
            "log_level": "INFO",
            "components": {
                "logging": {
                    "level": "INFO",
                    "format": "detailed"
                },
                "cache": {
                    "type": "memory",
                    "max_size": 1000
                },
                "database": {
                    "type": "sqlite",
                    "database": ":memory:"
                },
                "auth": {
                    "secret_key": "test_secret"
                }
            }
        }
        
        app.configure(config_data)
        
        # 注册组件
        logging_component = LoggingComponent("logging", app.config)
        cache_component = CacheComponent("cache", app.config)
        database_component = DatabaseComponent("database", app.config)
        auth_component = AuthComponent("auth", app.config)
        
        app.register_component(logging_component)
        app.register_component(cache_component)
        app.register_component(database_component)
        app.register_component(auth_component)
        
        # 启动应用
        app.start()
        
        # 验证应用状态
        assert app.status.value == "running"
        
        # 验证组件状态
        assert logging_component._service is not None
        assert cache_component._cache is not None
        assert database_component._pool is not None
        assert auth_component._service is not None
        
        # 停止应用
        app.stop()
        
        # 验证应用已停止
        assert app.status.value == "stopped"
    
    def test_component_dependency_resolution(self):
        """测试组件依赖解析"""
        app = Application("dependency-test", "1.0.0")
        
        # 创建有依赖的组件
        class DependentComponent:
            def __init__(self, name: str, config: Config):
                self.name = name
                self.config = config
                self.dependencies = ["logging", "cache"]
                self.initialized = False
                self.started = False
            
            def initialize(self):
                self.initialized = True
            
            def start(self):
                self.started = True
            
            def stop(self):
                pass
            
            def get_health_status(self):
                return {"status": "healthy"}
        
        # 注册基础组件
        logging_component = LoggingComponent("logging", app.config)
        cache_component = CacheComponent("cache", app.config)
        dependent_component = DependentComponent("dependent", app.config)
        
        app.register_component(logging_component)
        app.register_component(cache_component)
        app.register_component(dependent_component)
        
        # 启动应用
        app.start()
        
        # 验证依赖组件已启动
        assert dependent_component.initialized is True
        assert dependent_component.started is True
        
        app.stop()
    
    def test_configuration_management_integration(self):
        """测试配置管理集成"""
        app = Application("config-test", "1.0.0")
        
        # 设置复杂配置
        config_data = {
            "app_name": "Test Application",
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db",
                "credentials": {
                    "username": "test_user",
                    "password": "test_password"
                }
            },
            "cache": {
                "type": "redis",
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "components": {
                "auth": {
                    "secret_key": "test_secret_key",
                    "token_expiry": 3600
                }
            }
        }
        
        app.configure(config_data)
        
        # 验证配置正确设置
        assert app.get("app_name") == "Test Application"
        assert app.get("debug") is True
        assert app.get("log_level") == "DEBUG"
        assert app.get("database.host") == "localhost"
        assert app.get("database.port") == 5432
        assert app.get("database.credentials.username") == "test_user"
        assert app.get("cache.type") == "redis"
        assert app.get("components.auth.secret_key") == "test_secret_key"
    
    def test_health_check_integration(self):
        """测试健康检查集成"""
        app = Application("health-test", "1.0.0")
        
        # 注册组件
        logging_component = LoggingComponent("logging", app.config)
        cache_component = CacheComponent("cache", app.config)
        
        app.register_component(logging_component)
        app.register_component(cache_component)
        
        app.start()
        
        # 获取健康状态
        health = app.get_health_status()
        
        # 验证健康状态结构
        assert health["status"] == "healthy"
        assert health["app_name"] == "health-test"
        assert health["app_version"] == "1.0.0"
        assert "components" in health
        assert "logging" in health["components"]
        assert "cache" in health["components"]
        
        # 验证组件健康状态
        assert health["components"]["logging"]["status"] == "healthy"
        assert health["components"]["cache"]["status"] == "healthy"
        
        app.stop()
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        app = Application("error-test", "1.0.0")
        
        # 创建会出错的组件
        class ErrorComponent:
            def __init__(self, name: str, config: Config):
                self.name = name
                self.config = config
                self.initialized = False
            
            def initialize(self):
                raise RuntimeError("Component initialization failed")
            
            def start(self):
                pass
            
            def stop(self):
                pass
            
            def get_health_status(self):
                return {"status": "error"}
        
        # 注册正常组件和错误组件
        logging_component = LoggingComponent("logging", app.config)
        error_component = ErrorComponent("error", app.config)
        
        app.register_component(logging_component)
        app.register_component(error_component)
        
        # 启动应用应该抛出异常
        with pytest.raises(RuntimeError, match="Component initialization failed"):
            app.start()
        
        # 应用状态应该是错误
        assert app.status.value == "error"
    
    def test_component_interaction(self):
        """测试组件间交互"""
        app = Application("interaction-test", "1.0.0")
        
        # 注册组件
        logging_component = LoggingComponent("logging", app.config)
        cache_component = CacheComponent("cache", app.config)
        auth_component = AuthComponent("auth", app.config)
        
        app.register_component(logging_component)
        app.register_component(cache_component)
        app.register_component(auth_component)
        
        app.start()
        
        # 测试组件间交互
        # 1. 使用认证组件注册用户
        auth_service = auth_component.get_service()
        user = auth_service.register_user("testuser", "test@example.com", "password123")
        
        # 2. 使用缓存组件缓存用户信息
        cache_service = cache_component.get_service()
        cache_service.set(f"user:{user.id}", user.to_dict(), ttl=3600)
        
        # 3. 从缓存中获取用户信息
        cached_user_data = cache_service.get(f"user:{user.id}")
        assert cached_user_data is not None
        assert cached_user_data["username"] == "testuser"
        
        # 4. 使用认证服务验证用户
        authenticated_user = auth_service.authenticate("testuser", "password123")
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        
        app.stop()
    
    def test_application_lifecycle_with_context_manager(self):
        """测试使用上下文管理器的应用生命周期"""
        app = Application("context-test", "1.0.0")
        
        # 注册组件
        logging_component = LoggingComponent("logging", app.config)
        cache_component = CacheComponent("cache", app.config)
        
        app.register_component(logging_component)
        app.register_component(cache_component)
        
        # 使用上下文管理器
        with app:
            # 验证应用已启动
            assert app.status.value == "running"
            assert logging_component._service is not None
            assert cache_component._cache is not None
            
            # 在应用运行期间执行一些操作
            cache_service = cache_component.get_service()
            cache_service.set("test_key", "test_value", ttl=60)
            assert cache_service.get("test_key") == "test_value"
        
        # 验证应用已停止
        assert app.status.value == "stopped"
    
    def test_application_restart(self):
        """测试应用重启"""
        app = Application("restart-test", "1.0.0")
        
        # 注册组件
        logging_component = LoggingComponent("logging", app.config)
        
        app.register_component(logging_component)
        
        # 第一次启动
        app.start()
        assert app.status.value == "running"
        
        # 停止
        app.stop()
        assert app.status.value == "stopped"
        
        # 重新启动
        app.start()
        assert app.status.value == "running"
        
        # 再次停止
        app.stop()
        assert app.status.value == "stopped"
    
    def test_application_info_and_uptime(self):
        """测试应用信息和运行时间"""
        app = Application("info-test", "1.0.0")
        
        # 获取初始信息
        info = app.get_info()
        assert info["name"] == "info-test"
        assert info["version"] == "1.0.0"
        assert info["status"] == "stopped"
        assert info["uptime"] == 0
        
        # 启动应用
        app.start()
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 获取运行中的信息
        info = app.get_info()
        assert info["status"] == "running"
        assert info["uptime"] > 0
        
        # 停止应用
        app.stop()
        
        # 获取停止后的信息
        info = app.get_info()
        assert info["status"] == "stopped"
        # 运行时间应该保持不变
        assert info["uptime"] > 0
    
    def test_multiple_components_health_check(self):
        """测试多个组件的健康检查"""
        app = Application("multi-health-test", "1.0.0")
        
        # 注册多个组件
        components = [
            LoggingComponent("logging", app.config),
            CacheComponent("cache", app.config),
            DatabaseComponent("database", app.config),
            AuthComponent("auth", app.config)
        ]
        
        for component in components:
            app.register_component(component)
        
        app.start()
        
        # 获取健康状态
        health = app.get_health_status()
        
        # 验证所有组件都在健康状态中
        assert len(health["components"]) == 4
        for component in components:
            assert component.name in health["components"]
            assert health["components"][component.name]["status"] == "healthy"
        
        app.stop()
    
    def test_configuration_validation(self):
        """测试配置验证"""
        app = Application("config-validation-test", "1.0.0")
        
        # 测试无效配置
        invalid_config = {
            "components": {
                "auth": {
                    # 缺少必需的secret_key
                }
            }
        }
        
        app.configure(invalid_config)
        
        # 注册认证组件
        auth_component = AuthComponent("auth", app.config)
        app.register_component(auth_component)
        
        # 启动应用（应该成功，因为配置验证是可选的）
        app.start()
        
        # 验证组件已启动
        assert auth_component._service is not None
        
        app.stop()


@pytest.mark.integration
class TestIntegrationScenarios:
    """集成测试场景"""
    
    def test_web_application_scenario(self):
        """测试Web应用场景"""
        app = Application("web-app", "1.0.0")
        
        # 配置Web应用
        config_data = {
            "app_name": "Web Application",
            "debug": False,
            "log_level": "INFO",
            "database": {
                "type": "sqlite",
                "database": ":memory:"
            },
            "cache": {
                "type": "memory",
                "max_size": 10000
            },
            "auth": {
                "secret_key": "web_app_secret",
                "token_expiry": 7200
            }
        }
        
        app.configure(config_data)
        
        # 注册Web应用组件
        logging_component = LoggingComponent("logging", app.config)
        database_component = DatabaseComponent("database", app.config)
        cache_component = CacheComponent("cache", app.config)
        auth_component = AuthComponent("auth", app.config)
        
        app.register_component(logging_component)
        app.register_component(database_component)
        app.register_component(cache_component)
        app.register_component(auth_component)
        
        # 启动应用
        app.start()
        
        # 模拟Web应用操作
        # 1. 用户注册
        auth_service = auth_component.get_service()
        user = auth_service.register_user("webuser", "webuser@example.com", "webpassword")
        
        # 2. 缓存用户会话
        cache_service = cache_component.get_service()
        session_data = {
            "user_id": user.id,
            "username": user.username,
            "login_time": time.time()
        }
        cache_service.set(f"session:{user.id}", session_data, ttl=7200)
        
        # 3. 验证会话
        cached_session = cache_service.get(f"session:{user.id}")
        assert cached_session is not None
        assert cached_session["user_id"] == user.id
        
        # 4. 用户认证
        authenticated_user = auth_service.authenticate("webuser", "webpassword")
        assert authenticated_user is not None
        
        app.stop()
    
    def test_microservice_scenario(self):
        """测试微服务场景"""
        app = Application("microservice", "1.0.0")
        
        # 配置微服务
        config_data = {
            "service_name": "user-service",
            "service_version": "1.0.0",
            "debug": False,
            "log_level": "WARNING",
            "database": {
                "type": "sqlite",
                "database": ":memory:"
            },
            "cache": {
                "type": "memory",
                "max_size": 1000
            }
        }
        
        app.configure(config_data)
        
        # 注册微服务组件
        logging_component = LoggingComponent("logging", app.config)
        database_component = DatabaseComponent("database", app.config)
        cache_component = CacheComponent("cache", app.config)
        
        app.register_component(logging_component)
        app.register_component(database_component)
        app.register_component(cache_component)
        
        # 启动微服务
        app.start()
        
        # 模拟微服务操作
        # 1. 健康检查
        health = app.get_health_status()
        assert health["status"] == "healthy"
        
        # 2. 服务信息
        info = app.get_info()
        assert info["name"] == "microservice"
        assert info["version"] == "1.0.0"
        
        # 3. 缓存操作
        cache_service = cache_component.get_service()
        cache_service.set("service:status", "running", ttl=60)
        assert cache_service.get("service:status") == "running"
        
        app.stop()
