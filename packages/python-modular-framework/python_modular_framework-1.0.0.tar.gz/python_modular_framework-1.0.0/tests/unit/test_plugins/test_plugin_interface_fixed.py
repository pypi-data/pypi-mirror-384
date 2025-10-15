"""
插件接口测试（修复版）

测试framework.core.plugin模块中的插件接口和基础类。

测试内容：
- 插件状态枚举
- 插件信息类
- 插件接口定义
- 基础插件类

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock
from framework.core.plugin import (
    PluginStatus,
    PluginInfo,
    PluginInterface,
    BasePlugin,
    PluginError
)


class TestPluginStatus:
    """插件状态枚举测试"""
    
    def test_plugin_status_values(self):
        """测试插件状态值"""
        assert PluginStatus.UNLOADED.value == "unloaded"
        assert PluginStatus.LOADING.value == "loading"
        assert PluginStatus.LOADED.value == "loaded"
        assert PluginStatus.INITIALIZING.value == "initializing"
        assert PluginStatus.INITIALIZED.value == "initialized"
        assert PluginStatus.STARTING.value == "starting"
        assert PluginStatus.RUNNING.value == "running"
        assert PluginStatus.STOPPING.value == "stopping"
        assert PluginStatus.STOPPED.value == "stopped"
        assert PluginStatus.ERROR.value == "error"
        assert PluginStatus.UNLOADING.value == "unloading"


class TestPluginInfo:
    """插件信息测试"""
    
    def test_plugin_info_initialization(self):
        """测试插件信息初始化"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        assert info.description == "Test plugin"
        assert info.author == "Test Author"
        assert info.dependencies == []
        assert info.optional_dependencies == []
        assert info.entry_point == "main"
        assert info.config_schema is None
        assert info.metadata == {}
    
    def test_plugin_info_initialization_with_all_fields(self):
        """测试使用所有字段初始化插件信息"""
        dependencies = ["plugin1", "plugin2"]
        optional_dependencies = ["plugin3"]
        config_schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        metadata = {"category": "utility", "priority": 1}
        
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            dependencies=dependencies,
            optional_dependencies=optional_dependencies,
            entry_point="custom_entry",
            config_schema=config_schema,
            metadata=metadata
        )
        
        assert info.dependencies == dependencies
        assert info.optional_dependencies == optional_dependencies
        assert info.entry_point == "custom_entry"
        assert info.config_schema == config_schema
        assert info.metadata == metadata
    
    def test_plugin_info_to_dict(self):
        """测试插件信息转换为字典"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            dependencies=["plugin1"],
            optional_dependencies=["plugin2"],
            entry_point="main",
            config_schema={"type": "object"},
            metadata={"category": "utility"}
        )
        
        info_dict = info.to_dict()
        
        expected = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "dependencies": ["plugin1"],
            "optional_dependencies": ["plugin2"],
            "entry_point": "main",
            "config_schema": {"type": "object"},
            "metadata": {"category": "utility"}
        }
        
        assert info_dict == expected


class TestPluginInterface:
    """插件接口测试"""
    
    def test_interface_abstract_methods(self):
        """测试插件接口的抽象方法"""
        # 创建实现接口的类
        class TestPlugin(PluginInterface):
            def __init__(self):
                self._info = PluginInfo(
                    name="test_plugin",
                    version="1.0.0",
                    description="Test plugin",
                    author="Test Author"
                )
                self._status = PluginStatus.UNLOADED
                self._config = {}
            
            @property
            def info(self) -> PluginInfo:
                return self._info
            
            def initialize(self, config: dict) -> None:
                self._config = config
                self._status = PluginStatus.INITIALIZED
            
            def start(self) -> None:
                self._status = PluginStatus.RUNNING
            
            def stop(self) -> None:
                self._status = PluginStatus.STOPPED
            
            def get_status(self) -> PluginStatus:
                return self._status
            
            def get_config(self) -> dict:
                return self._config.copy()
        
        plugin = TestPlugin()
        
        # 测试基本信息
        assert plugin.info.name == "test_plugin"
        assert plugin.info.version == "1.0.0"
        
        # 测试生命周期方法
        plugin.initialize({"key": "value"})
        assert plugin.get_status() == PluginStatus.INITIALIZED
        assert plugin.get_config() == {"key": "value"}
        
        plugin.start()
        assert plugin.get_status() == PluginStatus.RUNNING
        
        plugin.stop()
        assert plugin.get_status() == PluginStatus.STOPPED
    
    def test_interface_cannot_instantiate(self):
        """测试不能直接实例化接口"""
        with pytest.raises(TypeError):
            PluginInterface()


class TestBasePlugin:
    """基础插件类测试"""
    
    def test_base_plugin_initialization(self):
        """测试基础插件初始化"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        
        assert plugin.info == info
        assert plugin.get_status() == PluginStatus.UNLOADED
        assert plugin.get_config() == {}
    
    def test_base_plugin_initialize(self):
        """测试基础插件初始化"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        # 先设置为LOADED状态
        plugin._status = PluginStatus.LOADED
        config = {"key": "value", "number": 42}
        
        plugin.initialize(config)
        
        assert plugin.get_status() == PluginStatus.INITIALIZED
        assert plugin.get_config() == config
    
    def test_base_plugin_initialize_wrong_status(self):
        """测试在错误状态下初始化插件"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({})  # 先初始化一次
        
        # 尝试再次初始化应该失败
        with pytest.raises(PluginError, match="Cannot initialize plugin"):
            plugin.initialize({"key": "value"})
    
    def test_base_plugin_start(self):
        """测试基础插件启动"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({})
        
        plugin.start()
        
        assert plugin.get_status() == PluginStatus.RUNNING
    
    def test_base_plugin_start_wrong_status(self):
        """测试在错误状态下启动插件"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        
        # 未初始化就启动应该失败
        with pytest.raises(PluginError, match="Cannot start plugin"):
            plugin.start()
    
    def test_base_plugin_stop(self):
        """测试基础插件停止"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({})
        plugin.start()
        
        plugin.stop()
        
        assert plugin.get_status() == PluginStatus.STOPPED
    
    def test_base_plugin_stop_not_running(self):
        """测试停止未运行的插件"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        
        # 停止未运行的插件应该不报错
        plugin.stop()
        assert plugin.get_status() == PluginStatus.UNLOADED
    
    def test_base_plugin_update_config(self):
        """测试基础插件配置更新"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        plugin = BasePlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({"key1": "value1"})
        
        plugin.update_config({"key2": "value2"})
        
        config = plugin.get_config()
        assert config["key1"] == "value1"
        assert config["key2"] == "value2"
    
    def test_base_plugin_custom_callbacks(self):
        """测试基础插件自定义回调"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        class CustomPlugin(BasePlugin):
            def __init__(self, info):
                super().__init__(info)
                self.initialize_called = False
                self.start_called = False
                self.stop_called = False
                self.config_update_called = False
            
            def _on_initialize(self, config):
                self.initialize_called = True
            
            def _on_start(self):
                self.start_called = True
            
            def _on_stop(self):
                self.stop_called = True
            
            def _on_config_update(self, config):
                self.config_update_called = True
        
        plugin = CustomPlugin(info)
        plugin._status = PluginStatus.LOADED
        
        # 测试初始化回调
        plugin.initialize({"key": "value"})
        assert plugin.initialize_called is True
        
        # 测试启动回调
        plugin.start()
        assert plugin.start_called is True
        
        # 测试停止回调
        plugin.stop()
        assert plugin.stop_called is True
        
        # 测试配置更新回调
        plugin.update_config({"new_key": "new_value"})
        assert plugin.config_update_called is True
    
    def test_base_plugin_initialize_error(self):
        """测试基础插件初始化错误处理"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        class ErrorPlugin(BasePlugin):
            def _on_initialize(self, config):
                raise ValueError("Initialization failed")
        
        plugin = ErrorPlugin(info)
        plugin._status = PluginStatus.LOADED
        
        with pytest.raises(PluginError, match="Failed to initialize plugin"):
            plugin.initialize({})
        
        assert plugin.get_status() == PluginStatus.ERROR
    
    def test_base_plugin_start_error(self):
        """测试基础插件启动错误处理"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        class ErrorPlugin(BasePlugin):
            def _on_start(self):
                raise RuntimeError("Start failed")
        
        plugin = ErrorPlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({})
        
        with pytest.raises(PluginError, match="Failed to start plugin"):
            plugin.start()
        
        assert plugin.get_status() == PluginStatus.ERROR
    
    def test_base_plugin_stop_error(self):
        """测试基础插件停止错误处理"""
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        
        class ErrorPlugin(BasePlugin):
            def _on_stop(self):
                raise RuntimeError("Stop failed")
        
        plugin = ErrorPlugin(info)
        plugin._status = PluginStatus.LOADED
        plugin.initialize({})
        plugin.start()
        
        with pytest.raises(PluginError, match="Failed to stop plugin"):
            plugin.stop()
        
        assert plugin.get_status() == PluginStatus.ERROR


class TestPluginError:
    """插件异常测试"""
    
    def test_plugin_error_initialization(self):
        """测试插件异常初始化"""
        error = PluginError("Test error")
        
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_plugin_error_inheritance(self):
        """测试插件异常继承"""
        error = PluginError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, PluginError)


@pytest.mark.parametrize("status", [
    PluginStatus.UNLOADED,
    PluginStatus.LOADING,
    PluginStatus.LOADED,
    PluginStatus.INITIALIZING,
    PluginStatus.INITIALIZED,
    PluginStatus.STARTING,
    PluginStatus.RUNNING,
    PluginStatus.STOPPING,
    PluginStatus.STOPPED,
    PluginStatus.ERROR,
    PluginStatus.UNLOADING,
])
def test_plugin_status_enum_values(status):
    """测试所有插件状态枚举值"""
    assert isinstance(status.value, str)
    assert len(status.value) > 0


@pytest.mark.parametrize("name,version,description,author", [
    ("plugin1", "1.0.0", "Description 1", "Author 1"),
    ("plugin2", "2.1.0", "Description 2", "Author 2"),
    ("my-plugin", "0.1.0", "My Plugin Description", "My Name"),
])
def test_plugin_info_creation(name, version, description, author):
    """测试创建不同参数的插件信息"""
    info = PluginInfo(
        name=name,
        version=version,
        description=description,
        author=author
    )
    
    assert info.name == name
    assert info.version == version
    assert info.description == description
    assert info.author == author
