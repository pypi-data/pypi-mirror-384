"""
应用管理模块测试

测试framework.core.application模块的功能。

测试内容：
- 应用创建和初始化
- 应用生命周期管理
- 组件注册和管理
- 配置管理
- 健康检查

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from framework.core.application import Application, ApplicationStatus
from framework.core.config import Config
from framework.interfaces.component import ComponentInterface


class MockComponent(ComponentInterface):
    """模拟组件用于测试"""
    
    def __init__(self, name: str, config: Config):
        super().__init__(name, config)
        self.initialized = False
        self.started = False
        self.stopped = False
    
    def initialize(self) -> None:
        """初始化组件"""
        self.initialized = True
    
    def start(self) -> None:
        """启动组件"""
        self.started = True
    
    def stop(self) -> None:
        """停止组件"""
        self.stopped = True
    
    def get_health_status(self) -> dict:
        """获取健康状态"""
        return {
            "status": "healthy",
            "initialized": self.initialized,
            "started": self.started
        }


class TestApplication:
    """应用类测试"""
    
    def test_application_creation(self):
        """测试应用创建"""
        app = Application("test-app", "1.0.0")
        
        assert app.name == "test-app"
        assert app.version == "1.0.0"
        assert app.status == ApplicationStatus.STOPPED
        assert app.config is not None
        assert isinstance(app.config, Config)
    
    def test_application_creation_with_config(self):
        """测试使用配置创建应用"""
        config_data = {"debug": True, "log_level": "INFO"}
        app = Application("test-app", "1.0.0", config_data)
        
        assert app.get("debug") is True
        assert app.get("log_level") == "INFO"
    
    def test_configure(self):
        """测试应用配置"""
        app = Application("test-app", "1.0.0")
        
        config_data = {
            "debug": True,
            "log_level": "DEBUG",
            "components": {
                "test": {
                    "enabled": True
                }
            }
        }
        
        app.configure(config_data)
        
        assert app.get("debug") is True
        assert app.get("log_level") == "DEBUG"
        assert app.get("components.test.enabled") is True
    
    def test_register_component(self):
        """测试注册组件"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        
        assert "test-component" in app._components
        assert app._components["test-component"] == component
    
    def test_register_component_duplicate(self):
        """测试注册重复组件"""
        app = Application("test-app", "1.0.0")
        component1 = MockComponent("test-component", app.config)
        component2 = MockComponent("test-component", app.config)
        
        app.register_component(component1)
        
        # 注册重复组件应该抛出异常
        with pytest.raises(ValueError, match="Component 'test-component' is already registered"):
            app.register_component(component2)
    
    def test_get_component(self):
        """测试获取组件"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        
        retrieved_component = app.get_component("test-component")
        assert retrieved_component == component
    
    def test_get_component_not_found(self):
        """测试获取不存在的组件"""
        app = Application("test-app", "1.0.0")
        
        with pytest.raises(ValueError, match="Component 'nonexistent' not found"):
            app.get_component("nonexistent")
    
    def test_get_component_names(self):
        """测试获取组件名称列表"""
        app = Application("test-app", "1.0.0")
        
        # 初始状态应该为空
        assert len(app.get_component_names()) == 0
        
        # 注册组件
        component1 = MockComponent("component1", app.config)
        component2 = MockComponent("component2", app.config)
        
        app.register_component(component1)
        app.register_component(component2)
        
        names = app.get_component_names()
        assert len(names) == 2
        assert "component1" in names
        assert "component2" in names
    
    def test_start_application(self):
        """测试启动应用"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        app.start()
        
        assert app.status == ApplicationStatus.RUNNING
        assert component.initialized is True
        assert component.started is True
    
    def test_start_application_without_components(self):
        """测试启动没有组件的应用"""
        app = Application("test-app", "1.0.0")
        
        # 启动没有组件的应用应该成功
        app.start()
        assert app.status == ApplicationStatus.RUNNING
    
    def test_stop_application(self):
        """测试停止应用"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        app.start()
        app.stop()
        
        assert app.status == ApplicationStatus.STOPPED
        assert component.stopped is True
    
    def test_stop_application_not_started(self):
        """测试停止未启动的应用"""
        app = Application("test-app", "1.0.0")
        
        # 停止未启动的应用应该不报错
        app.stop()
        assert app.status == ApplicationStatus.STOPPED
    
    def test_restart_application(self):
        """测试重启应用"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        
        # 启动应用
        app.start()
        assert app.status == ApplicationStatus.RUNNING
        assert component.started is True
        
        # 停止应用
        app.stop()
        assert app.status == ApplicationStatus.STOPPED
        assert component.stopped is True
        
        # 重新启动应用
        component.initialized = False
        component.started = False
        component.stopped = False
        
        app.start()
        assert app.status == ApplicationStatus.RUNNING
        assert component.initialized is True
        assert component.started is True
    
    def test_get_health_status(self):
        """测试获取应用健康状态"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        app.start()
        
        health = app.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["app_name"] == "test-app"
        assert health["app_version"] == "1.0.0"
        assert "components" in health
        assert "test-component" in health["components"]
    
    def test_get_health_status_with_unhealthy_component(self):
        """测试获取包含不健康组件的应用健康状态"""
        app = Application("test-app", "1.0.0")
        
        # 创建不健康的组件
        unhealthy_component = MockComponent("unhealthy-component", app.config)
        unhealthy_component.get_health_status = Mock(return_value={"status": "unhealthy"})
        
        app.register_component(unhealthy_component)
        app.start()
        
        health = app.get_health_status()
        
        assert health["status"] == "unhealthy"
        assert health["components"]["unhealthy-component"]["status"] == "unhealthy"
    
    def test_auto_discover_components(self):
        """测试自动发现组件"""
        app = Application("test-app", "1.0.0")
        
        # 模拟组件发现
        with patch.object(app, '_discover_components') as mock_discover:
            mock_discover.return_value = ["component1", "component2"]
            
            app.auto_discover_components()
            
            mock_discover.assert_called_once()
    
    def test_context_manager(self):
        """测试应用作为上下文管理器"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        
        with app:
            assert app.status == ApplicationStatus.RUNNING
            assert component.started is True
        
        assert app.status == ApplicationStatus.STOPPED
        assert component.stopped is True
    
    def test_context_manager_exception(self):
        """测试上下文管理器异常处理"""
        app = Application("test-app", "1.0.0")
        component = MockComponent("test-component", app.config)
        
        app.register_component(component)
        
        with pytest.raises(ValueError):
            with app:
                assert app.status == ApplicationStatus.RUNNING
                raise ValueError("Test exception")
        
        assert app.status == ApplicationStatus.STOPPED
        assert component.stopped is True
    
    def test_component_dependency_resolution(self):
        """测试组件依赖解析"""
        app = Application("test-app", "1.0.0")
        
        # 创建有依赖的组件
        component1 = MockComponent("component1", app.config)
        component1.dependencies = []
        
        component2 = MockComponent("component2", app.config)
        component2.dependencies = ["component1"]
        
        app.register_component(component1)
        app.register_component(component2)
        
        app.start()
        
        # 两个组件都应该被初始化
        assert component1.initialized is True
        assert component2.initialized is True
    
    def test_component_initialization_error(self):
        """测试组件初始化错误"""
        app = Application("test-app", "1.0.0")
        
        # 创建会抛出异常的组件
        error_component = MockComponent("error-component", app.config)
        error_component.initialize = Mock(side_effect=RuntimeError("Initialization failed"))
        
        app.register_component(error_component)
        
        # 启动应用应该抛出异常
        with pytest.raises(RuntimeError, match="Initialization failed"):
            app.start()
    
    def test_component_start_error(self):
        """测试组件启动错误"""
        app = Application("test-app", "1.0.0")
        
        # 创建会抛出异常的组件
        error_component = MockComponent("error-component", app.config)
        error_component.start = Mock(side_effect=RuntimeError("Start failed"))
        
        app.register_component(error_component)
        
        # 启动应用应该抛出异常
        with pytest.raises(RuntimeError, match="Start failed"):
            app.start()
    
    def test_application_info(self):
        """测试应用信息"""
        app = Application("test-app", "1.0.0")
        
        info = app.get_info()
        
        assert info["name"] == "test-app"
        assert info["version"] == "1.0.0"
        assert info["status"] == ApplicationStatus.STOPPED
        assert "start_time" in info
        assert "uptime" in info
    
    def test_application_uptime(self):
        """测试应用运行时间"""
        app = Application("test-app", "1.0.0")
        
        # 未启动的应用运行时间应该为0
        assert app.get_uptime() == 0
        
        app.start()
        
        # 启动后应该有运行时间
        uptime = app.get_uptime()
        assert uptime >= 0
        
        app.stop()
        
        # 停止后运行时间应该保持不变
        assert app.get_uptime() == uptime


class TestApplicationStatus:
    """应用状态枚举测试"""
    
    def test_application_status_values(self):
        """测试应用状态值"""
        assert ApplicationStatus.STOPPED == "stopped"
        assert ApplicationStatus.STARTING == "starting"
        assert ApplicationStatus.RUNNING == "running"
        assert ApplicationStatus.STOPPING == "stopping"
        assert ApplicationStatus.ERROR == "error"


@pytest.mark.parametrize("name,version", [
    ("app1", "1.0.0"),
    ("app2", "2.1.3"),
    ("test-app", "0.1.0"),
])
def test_application_creation_with_different_names(name, version):
    """测试使用不同名称和版本创建应用"""
    app = Application(name, version)
    
    assert app.name == name
    assert app.version == version
    assert app.status == ApplicationStatus.STOPPED


@pytest.mark.parametrize("config_data", [
    {"debug": True},
    {"log_level": "INFO", "debug": False},
    {"components": {"test": {"enabled": True}}},
    {"database": {"host": "localhost", "port": 5432}},
])
def test_application_configure_with_different_data(config_data):
    """测试使用不同配置数据配置应用"""
    app = Application("test-app", "1.0.0")
    app.configure(config_data)
    
    for key, value in config_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                assert app.get(f"{key}.{sub_key}") == sub_value
        else:
            assert app.get(key) == value
