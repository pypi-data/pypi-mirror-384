"""
测试工具函数

提供测试中使用的工具函数和辅助类。

主要功能：
- 测试数据生成器
- 模拟对象创建
- 测试环境设置
- 断言辅助函数

作者：开发团队
创建时间：2025-01-12
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import json
import yaml

from framework.core.config import Config
from framework.core.application import Application


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_user_data(count: int = 1) -> List[Dict[str, Any]]:
        """生成用户测试数据"""
        users = []
        for i in range(count):
            users.append({
                "username": f"testuser{i}",
                "email": f"testuser{i}@example.com",
                "password": f"password{i}",
                "first_name": f"Test{i}",
                "last_name": f"User{i}",
                "is_active": True
            })
        return users
    
    @staticmethod
    def generate_config_data() -> Dict[str, Any]:
        """生成配置测试数据"""
        return {
            "app_name": "Test App",
            "version": "1.0.0",
            "debug": True,
            "log_level": "DEBUG",
            "database": {
                "type": "sqlite",
                "database": ":memory:",
                "host": "localhost",
                "port": 5432
            },
            "cache": {
                "type": "memory",
                "max_size": 1000,
                "default_ttl": 3600
            },
            "components": {
                "auth": {
                    "secret_key": "test_secret",
                    "token_expiry": 3600
                }
            }
        }
    
    @staticmethod
    def generate_middleware_data() -> List[Dict[str, Any]]:
        """生成中间件测试数据"""
        return [
            {
                "name": "logging",
                "enabled": True,
                "config": {
                    "level": "INFO",
                    "format": "detailed"
                }
            },
            {
                "name": "auth",
                "enabled": True,
                "config": {
                    "token_header": "Authorization",
                    "token_prefix": "Bearer"
                }
            },
            {
                "name": "cache",
                "enabled": True,
                "config": {
                    "default_ttl": 300,
                    "cache_key_prefix": "api:"
                }
            }
        ]
    
    @staticmethod
    def generate_plugin_data() -> List[Dict[str, Any]]:
        """生成插件测试数据"""
        return [
            {
                "name": "analytics",
                "version": "1.0.0",
                "description": "Analytics plugin",
                "dependencies": [],
                "config": {
                    "enabled": True,
                    "retention_days": 30
                }
            },
            {
                "name": "notification",
                "version": "1.0.0",
                "description": "Notification plugin",
                "dependencies": [],
                "config": {
                    "enabled": True,
                    "max_notifications": 100
                }
            }
        ]


class MockFactory:
    """模拟对象工厂"""
    
    @staticmethod
    def create_mock_component(name: str = "mock_component") -> Mock:
        """创建模拟组件"""
        component = Mock()
        component.name = name
        component.initialized = False
        component.started = False
        component.stopped = False
        component.dependencies = []
        
        def initialize():
            component.initialized = True
        
        def start():
            component.started = True
        
        def stop():
            component.stopped = True
        
        def get_health_status():
            return {
                "status": "healthy",
                "initialized": component.initialized,
                "started": component.started
            }
        
        component.initialize = initialize
        component.start = start
        component.stop = stop
        component.get_health_status = get_health_status
        
        return component
    
    @staticmethod
    def create_mock_middleware(name: str = "mock_middleware") -> Mock:
        """创建模拟中间件"""
        middleware = Mock()
        middleware.name = name
        middleware.enabled = True
        
        def process_request(request):
            return request
        
        def process_response(response):
            return response
        
        def process_error(error, request):
            return {"error": str(error), "status": 500}
        
        middleware.process_request = process_request
        middleware.process_response = process_response
        middleware.process_error = process_error
        
        return middleware
    
    @staticmethod
    def create_mock_plugin(name: str = "mock_plugin") -> Mock:
        """创建模拟插件"""
        plugin = Mock()
        plugin.name = name
        plugin.version = "1.0.0"
        plugin.description = f"Mock plugin {name}"
        plugin.dependencies = []
        plugin.optional_dependencies = []
        plugin.metadata = {}
        plugin.initialized = False
        plugin.started = False
        plugin.stopped = False
        
        def initialize(config):
            plugin.initialized = True
        
        def start():
            plugin.started = True
        
        def stop():
            plugin.stopped = True
        
        def get_health_status():
            return {
                "status": "healthy",
                "initialized": plugin.initialized,
                "started": plugin.started
            }
        
        plugin.initialize = initialize
        plugin.start = start
        plugin.stop = stop
        plugin.get_health_status = get_health_status
        
        return plugin


class TestEnvironment:
    """测试环境管理"""
    
    def __init__(self):
        self.temp_dir = None
        self.original_cwd = None
    
    def setup(self) -> Path:
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        return self.temp_dir
    
    def teardown(self):
        """清理测试环境"""
        if self.original_cwd:
            os.chdir(self.original_cwd)
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str) -> Path:
        """创建测试文件"""
        if not self.temp_dir:
            raise RuntimeError("Test environment not set up")
        
        file_path = self.temp_dir / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def create_test_config_file(self, filename: str, config_data: Dict[str, Any]) -> Path:
        """创建测试配置文件"""
        if filename.endswith('.json'):
            content = json.dumps(config_data, indent=2)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            content = yaml.dump(config_data, default_flow_style=False)
        else:
            raise ValueError("Unsupported config file format")
        
        return self.create_test_file(filename, content)


class TestApplicationBuilder:
    """测试应用构建器"""
    
    def __init__(self):
        self.app = None
        self.config_data = {}
        self.components = []
    
    def with_name(self, name: str) -> 'TestApplicationBuilder':
        """设置应用名称"""
        self.name = name
        return self
    
    def with_version(self, version: str) -> 'TestApplicationBuilder':
        """设置应用版本"""
        self.version = version
        return self
    
    def with_config(self, config_data: Dict[str, Any]) -> 'TestApplicationBuilder':
        """设置配置数据"""
        self.config_data.update(config_data)
        return self
    
    def with_component(self, component) -> 'TestApplicationBuilder':
        """添加组件"""
        self.components.append(component)
        return self
    
    def build(self) -> Application:
        """构建应用"""
        if not hasattr(self, 'name'):
            self.name = "test-app"
        if not hasattr(self, 'version'):
            self.version = "1.0.0"
        
        self.app = Application(self.name, self.version)
        
        if self.config_data:
            self.app.configure(self.config_data)
        
        for component in self.components:
            self.app.register_component(component)
        
        return self.app
    
    def build_and_start(self) -> Application:
        """构建并启动应用"""
        app = self.build()
        app.start()
        return app


class AssertionHelpers:
    """断言辅助函数"""
    
    @staticmethod
    def assert_component_healthy(component, name: str = None):
        """断言组件健康"""
        assert component is not None
        if hasattr(component, 'get_health_status'):
            health = component.get_health_status()
            assert health["status"] == "healthy"
        if name:
            assert component.name == name
    
    @staticmethod
    def assert_application_healthy(app: Application):
        """断言应用健康"""
        assert app.status.value == "running"
        health = app.get_health_status()
        assert health["status"] == "healthy"
    
    @staticmethod
    def assert_config_loaded(config: Config, expected_keys: List[str]):
        """断言配置已加载"""
        for key in expected_keys:
            assert config.has(key), f"Config key '{key}' not found"
    
    @staticmethod
    def assert_component_initialized(component):
        """断言组件已初始化"""
        if hasattr(component, 'initialized'):
            assert component.initialized is True
        if hasattr(component, '_service') and component._service:
            assert component._service is not None
    
    @staticmethod
    def assert_component_started(component):
        """断言组件已启动"""
        if hasattr(component, 'started'):
            assert component.started is True


class PerformanceTestHelper:
    """性能测试辅助函数"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """测量函数执行时间"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def measure_memory_usage(func, *args, **kwargs):
        """测量函数内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        final_memory = process.memory_info().rss
        memory_usage = final_memory - initial_memory
        
        return result, memory_usage
    
    @staticmethod
    def benchmark_function(func, iterations: int = 1000, *args, **kwargs):
        """基准测试函数"""
        import time
        import statistics
        
        times = []
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "iterations": iterations,
            "total_time": sum(times),
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0
        }


# 便捷函数
def create_test_app(name: str = "test-app", version: str = "1.0.0") -> Application:
    """创建测试应用"""
    return TestApplicationBuilder().with_name(name).with_version(version).build()


def create_test_config() -> Config:
    """创建测试配置"""
    config = Config()
    config_data = TestDataGenerator.generate_config_data()
    config.merge_dict(config_data)
    return config


def create_temp_file(content: str, suffix: str = ".txt") -> Path:
    """创建临时文件"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return Path(temp_file.name)


def cleanup_temp_file(file_path: Path):
    """清理临时文件"""
    if file_path.exists():
        file_path.unlink()
