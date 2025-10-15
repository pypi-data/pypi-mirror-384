"""
依赖注入容器模块测试

测试framework.core.container模块的功能。

测试内容：
- 服务注册
- 服务获取
- 生命周期管理
- 依赖解析
- 接口绑定

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock
from framework.core.container import Container, ServiceLifetime, ServiceRegistration


class MockService:
    """模拟服务类"""
    
    def __init__(self, name: str = "mock_service"):
        self.name = name
        self.initialized = False
    
    def initialize(self):
        """初始化服务"""
        self.initialized = True


class MockDependencyService:
    """模拟有依赖的服务类"""
    
    def __init__(self, dependency_service: MockService):
        self.dependency_service = dependency_service


class TestContainer:
    """容器类测试"""
    
    def test_container_initialization(self):
        """测试容器初始化"""
        container = Container()
        
        assert container is not None
        assert isinstance(container._services, dict)
        assert len(container._services) == 0
    
    def test_register_singleton(self):
        """测试注册单例服务"""
        container = Container()
        
        container.register_singleton("test_service", MockService)
        
        assert "test_service" in container._services
        registration = container._services["test_service"]
        assert registration.service_type == MockService
        assert registration.lifetime == ServiceLifetime.SINGLETON
    
    def test_register_transient(self):
        """测试注册瞬态服务"""
        container = Container()
        
        container.register_transient("test_service", MockService)
        
        assert "test_service" in container._services
        registration = container._services["test_service"]
        assert registration.service_type == MockService
        assert registration.lifetime == ServiceLifetime.TRANSIENT
    
    def test_register_scoped(self):
        """测试注册作用域服务"""
        container = Container()
        
        container.register_scoped("test_service", MockService)
        
        assert "test_service" in container._services
        registration = container._services["test_service"]
        assert registration.service_type == MockService
        assert registration.lifetime == ServiceLifetime.SCOPED
    
    def test_register_instance(self):
        """测试注册实例"""
        container = Container()
        instance = MockService("test_instance")
        
        container.register_instance("test_service", instance)
        
        assert "test_service" in container._services
        registration = container._services["test_service"]
        assert registration.instance == instance
        assert registration.lifetime == ServiceLifetime.SINGLETON
    
    def test_register_factory(self):
        """测试注册工厂函数"""
        container = Container()
        
        def factory():
            return MockService("factory_created")
        
        container.register_factory("test_service", factory)
        
        assert "test_service" in container._services
        registration = container._services["test_service"]
        assert registration.factory == factory
        assert registration.lifetime == ServiceLifetime.TRANSIENT
    
    def test_get_singleton_service(self):
        """测试获取单例服务"""
        container = Container()
        container.register_singleton("test_service", MockService)
        
        # 第一次获取
        service1 = container.get("test_service")
        
        # 第二次获取
        service2 = container.get("test_service")
        
        assert isinstance(service1, MockService)
        assert isinstance(service2, MockService)
        assert service1 is service2  # 应该是同一个实例
    
    def test_get_transient_service(self):
        """测试获取瞬态服务"""
        container = Container()
        container.register_transient("test_service", MockService)
        
        # 第一次获取
        service1 = container.get("test_service")
        
        # 第二次获取
        service2 = container.get("test_service")
        
        assert isinstance(service1, MockService)
        assert isinstance(service2, MockService)
        assert service1 is not service2  # 应该是不同的实例
    
    def test_get_scoped_service(self):
        """测试获取作用域服务"""
        container = Container()
        container.register_scoped("test_service", MockService)
        
        # 在同一个作用域内
        with container.scope():
            service1 = container.get("test_service")
            service2 = container.get("test_service")
            
            assert isinstance(service1, MockService)
            assert isinstance(service2, MockService)
            assert service1 is service2  # 同一个作用域内应该是同一个实例
        
        # 在不同作用域内
        with container.scope():
            service3 = container.get("test_service")
            
            assert isinstance(service3, MockService)
            assert service3 is not service1  # 不同作用域应该是不同实例
    
    def test_get_instance_service(self):
        """测试获取实例服务"""
        container = Container()
        instance = MockService("test_instance")
        container.register_instance("test_service", instance)
        
        service = container.get("test_service")
        
        assert service is instance
    
    def test_get_factory_service(self):
        """测试获取工厂服务"""
        container = Container()
        
        def factory():
            return MockService("factory_created")
        
        container.register_factory("test_service", factory)
        
        service = container.get("test_service")
        
        assert isinstance(service, MockService)
        assert service.name == "factory_created"
    
    def test_get_nonexistent_service(self):
        """测试获取不存在的服务"""
        container = Container()
        
        with pytest.raises(ValueError, match="Service 'nonexistent' not registered"):
            container.get("nonexistent")
    
    def test_resolve_dependencies(self):
        """测试解析依赖"""
        container = Container()
        
        # 注册依赖服务
        container.register_singleton("dependency_service", MockService)
        container.register_singleton("dependent_service", MockDependencyService)
        
        # 获取有依赖的服务
        service = container.get("dependent_service")
        
        assert isinstance(service, MockDependencyService)
        assert isinstance(service.dependency_service, MockService)
    
    def test_resolve_dependencies_with_parameters(self):
        """测试使用参数解析依赖"""
        container = Container()
        
        class ServiceWithParams:
            def __init__(self, param1: str, param2: int):
                self.param1 = param1
                self.param2 = param2
        
        container.register_singleton("service_with_params", ServiceWithParams)
        
        # 使用参数获取服务
        service = container.get("service_with_params", param1="test", param2=42)
        
        assert isinstance(service, ServiceWithParams)
        assert service.param1 == "test"
        assert service.param2 == 42
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        container = Container()
        
        class ServiceA:
            def __init__(self, service_b):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):
                self.service_a = service_a
        
        container.register_singleton("service_a", ServiceA)
        container.register_singleton("service_b", ServiceB)
        
        # 应该检测到循环依赖
        with pytest.raises(ValueError, match="Circular dependency detected"):
            container.get("service_a")
    
    def test_register_interface_binding(self):
        """测试注册接口绑定"""
        container = Container()
        
        class IInterface:
            pass
        
        class Implementation(IInterface):
            pass
        
        container.register_interface(IInterface, Implementation)
        
        service = container.get(IInterface)
        
        assert isinstance(service, Implementation)
    
    def test_register_interface_binding_with_lifetime(self):
        """测试使用生命周期注册接口绑定"""
        container = Container()
        
        class IInterface:
            pass
        
        class Implementation(IInterface):
            pass
        
        container.register_interface(IInterface, Implementation, ServiceLifetime.SINGLETON)
        
        service1 = container.get(IInterface)
        service2 = container.get(IInterface)
        
        assert isinstance(service1, Implementation)
        assert service1 is service2  # 单例应该是同一个实例
    
    def test_scope_management(self):
        """测试作用域管理"""
        container = Container()
        
        # 注册作用域服务
        container.register_scoped("scoped_service", MockService)
        
        # 创建作用域
        with container.scope() as scope:
            service1 = container.get("scoped_service")
            service2 = container.get("scoped_service")
            
            assert service1 is service2
            
            # 作用域结束时应该清理
            scope.__exit__(None, None, None)
    
    def test_clear_services(self):
        """测试清空服务"""
        container = Container()
        
        # 注册一些服务
        container.register_singleton("service1", MockService)
        container.register_transient("service2", MockService)
        
        assert len(container._services) == 2
        
        # 清空服务
        container.clear()
        
        assert len(container._services) == 0
    
    def test_is_registered(self):
        """测试检查服务是否已注册"""
        container = Container()
        
        # 未注册的服务
        assert not container.is_registered("nonexistent")
        
        # 注册服务
        container.register_singleton("test_service", MockService)
        
        assert container.is_registered("test_service")
    
    def test_get_registered_services(self):
        """测试获取已注册的服务列表"""
        container = Container()
        
        # 初始状态应该为空
        assert len(container.get_registered_services()) == 0
        
        # 注册一些服务
        container.register_singleton("service1", MockService)
        container.register_transient("service2", MockService)
        
        services = container.get_registered_services()
        
        assert len(services) == 2
        assert "service1" in services
        assert "service2" in services
    
    def test_service_with_initialization(self):
        """测试服务的初始化"""
        container = Container()
        
        class InitializableService:
            def __init__(self):
                self.initialized = False
            
            def initialize(self):
                self.initialized = True
        
        container.register_singleton("initializable_service", InitializableService)
        
        service = container.get("initializable_service")
        
        assert service.initialized is True
    
    def test_factory_with_dependencies(self):
        """测试工厂函数中的依赖注入"""
        container = Container()
        
        def factory(dependency_service: MockService):
            return MockDependencyService(dependency_service)
        
        container.register_singleton("dependency_service", MockService)
        container.register_factory("dependent_service", factory)
        
        service = container.get("dependent_service")
        
        assert isinstance(service, MockDependencyService)
        assert isinstance(service.dependency_service, MockService)


class TestServiceLifetime:
    """服务生命周期枚举测试"""
    
    def test_service_lifetime_values(self):
        """测试服务生命周期值"""
        assert ServiceLifetime.SINGLETON == "singleton"
        assert ServiceLifetime.TRANSIENT == "transient"
        assert ServiceLifetime.SCOPED == "scoped"


class TestServiceRegistration:
    """服务注册类测试"""
    
    def test_service_registration_creation(self):
        """测试服务注册创建"""
        registration = ServiceRegistration(
            service_type=MockService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert registration.service_type == MockService
        assert registration.lifetime == ServiceLifetime.SINGLETON
        assert registration.factory is None
        assert registration.instance is None
    
    def test_service_registration_with_factory(self):
        """测试使用工厂函数创建服务注册"""
        def factory():
            return MockService()
        
        registration = ServiceRegistration(
            service_type=MockService,
            lifetime=ServiceLifetime.TRANSIENT,
            factory=factory
        )
        
        assert registration.factory == factory
    
    def test_service_registration_with_instance(self):
        """测试使用实例创建服务注册"""
        instance = MockService("test_instance")
        
        registration = ServiceRegistration(
            service_type=MockService,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance
        )
        
        assert registration.instance == instance


@pytest.mark.parametrize("lifetime", [
    ServiceLifetime.SINGLETON,
    ServiceLifetime.TRANSIENT,
    ServiceLifetime.SCOPED,
])
def test_register_with_different_lifetimes(lifetime):
    """测试使用不同生命周期注册服务"""
    container = Container()
    
    if lifetime == ServiceLifetime.SINGLETON:
        container.register_singleton("test_service", MockService)
    elif lifetime == ServiceLifetime.TRANSIENT:
        container.register_transient("test_service", MockService)
    elif lifetime == ServiceLifetime.SCOPED:
        container.register_scoped("test_service", MockService)
    
    registration = container._services["test_service"]
    assert registration.lifetime == lifetime


@pytest.mark.parametrize("service_name", [
    "service1",
    "service_2",
    "service-with-dash",
    "service_with_underscore",
])
def test_register_with_different_names(service_name):
    """测试使用不同名称注册服务"""
    container = Container()
    container.register_singleton(service_name, MockService)
    
    assert container.is_registered(service_name)
    
    service = container.get(service_name)
    assert isinstance(service, MockService)
