"""
插件管理器测试（简化版）

测试framework.core.plugin模块中的插件管理器。

测试内容：
- 插件管理器基本功能
- 插件加载和卸载
- 插件生命周期管理

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from framework.core.plugin import (
    PluginManager,
    PluginInfo,
    PluginStatus,
    PluginInterface,
    BasePlugin,
    PluginError
)


class MockPlugin(BasePlugin):
    """模拟插件用于测试"""
    
    def __init__(self, name: str, version: str = "1.0.0", dependencies: list = None):
        info = PluginInfo(
            name=name,
            version=version,
            description=f"Mock plugin {name}",
            author="Test Author",
            dependencies=dependencies or []
        )
        super().__init__(info)
        self.initialize_called = False
        self.start_called = False
        self.stop_called = False
    
    def _on_initialize(self, config):
        self.initialize_called = True
    
    def _on_start(self):
        self.start_called = True
    
    def _on_stop(self):
        self.stop_called = True


class TestPluginManager:
    """插件管理器测试"""
    
    def test_plugin_manager_initialization(self):
        """测试插件管理器初始化"""
        manager = PluginManager()
        
        assert manager._plugins == {}
        assert manager._plugin_status == {}
        assert manager._plugin_configs == {}
    
    def test_load_plugin(self):
        """测试加载插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 模拟加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            result = manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        assert result is True
        assert "test_plugin" in manager._plugins
        assert manager._plugins["test_plugin"] == plugin
        assert manager._plugin_status["test_plugin"] == PluginStatus.LOADED
    
    def test_load_duplicate_plugin(self):
        """测试加载重复插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载一次
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            result1 = manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 再次加载应该返回True（已经加载）
        result2 = manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        assert result1 is True
        assert result2 is True
    
    def test_load_plugin_failure(self):
        """测试加载插件失败"""
        manager = PluginManager()
        
        # 模拟加载失败
        with patch.object(manager._loader, 'load_plugin', return_value=None):
            result = manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        assert result is False
        assert "test_plugin" not in manager._plugins
    
    def test_unload_plugin(self):
        """测试卸载插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 卸载插件
        result = manager.unload_plugin("test_plugin")
        
        assert result is True
        assert "test_plugin" not in manager._plugins
        assert "test_plugin" not in manager._plugin_status
    
    def test_unload_nonexistent_plugin(self):
        """测试卸载不存在的插件"""
        manager = PluginManager()
        
        result = manager.unload_plugin("nonexistent")
        
        assert result is False
    
    def test_initialize_plugin(self):
        """测试初始化插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 初始化插件
        config = {"key": "value"}
        result = manager.initialize_plugin("test_plugin", config)
        
        assert result is True
        assert plugin.get_status() == PluginStatus.INITIALIZED
        assert plugin.initialize_called is True
        assert plugin.get_config() == config
    
    def test_initialize_nonexistent_plugin(self):
        """测试初始化不存在的插件"""
        manager = PluginManager()
        
        result = manager.initialize_plugin("nonexistent", {})
        
        assert result is False
    
    def test_start_plugin(self):
        """测试启动插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载和初始化插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        manager.initialize_plugin("test_plugin", {})
        
        # 启动插件
        result = manager.start_plugin("test_plugin")
        
        assert result is True
        assert plugin.get_status() == PluginStatus.RUNNING
        assert plugin.start_called is True
    
    def test_start_nonexistent_plugin(self):
        """测试启动不存在的插件"""
        manager = PluginManager()
        
        result = manager.start_plugin("nonexistent")
        
        assert result is False
    
    def test_stop_plugin(self):
        """测试停止插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载、初始化和启动插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        manager.initialize_plugin("test_plugin", {})
        manager.start_plugin("test_plugin")
        
        # 停止插件
        result = manager.stop_plugin("test_plugin")
        
        assert result is True
        assert plugin.get_status() == PluginStatus.STOPPED
        assert plugin.stop_called is True
    
    def test_stop_nonexistent_plugin(self):
        """测试停止不存在的插件"""
        manager = PluginManager()
        
        result = manager.stop_plugin("nonexistent")
        
        assert result is False
    
    def test_get_plugin(self):
        """测试获取插件"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 获取插件
        retrieved_plugin = manager.get_plugin("test_plugin")
        assert retrieved_plugin == plugin
        
        # 获取不存在的插件
        nonexistent = manager.get_plugin("nonexistent")
        assert nonexistent is None
    
    def test_list_plugins(self):
        """测试列出插件"""
        manager = PluginManager()
        
        # 初始状态应该为空
        assert manager.list_plugins() == []
        
        # 加载一些插件
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")
        
        with patch.object(manager._loader, 'load_plugin', return_value=plugin1):
            manager.load_plugin("plugin1", "/path/to/plugin1.py")
        
        with patch.object(manager._loader, 'load_plugin', return_value=plugin2):
            manager.load_plugin("plugin2", "/path/to/plugin2.py")
        
        plugins = manager.list_plugins()
        
        assert len(plugins) == 2
        assert "plugin1" in plugins
        assert "plugin2" in plugins
    
    def test_get_plugin_status(self):
        """测试获取插件状态"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 获取状态
        status = manager.get_plugin_status("test_plugin")
        assert status == PluginStatus.LOADED
        
        # 获取不存在插件的状态
        status = manager.get_plugin_status("nonexistent")
        assert status is None
    
    def test_get_plugin_info(self):
        """测试获取插件信息"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 先加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        # 获取插件信息
        info = manager.get_plugin_info("test_plugin")
        assert info is not None
        assert info.name == "test_plugin"
        assert info.version == "1.0.0"
        
        # 获取不存在插件的信息
        info = manager.get_plugin_info("nonexistent")
        assert info is None
    
    def test_discover_plugins(self):
        """测试发现插件"""
        manager = PluginManager()
        
        # 模拟发现的插件
        plugin_info = PluginInfo(
            name="discovered_plugin",
            version="1.0.0",
            description="Discovered plugin",
            author="Test Author"
        )
        
        with patch.object(manager._loader, 'discover_plugins', return_value={"discovered_plugin": plugin_info}):
            plugins = manager.discover_plugins()
        
        assert "discovered_plugin" in plugins
        assert plugins["discovered_plugin"].name == "discovered_plugin"


class TestPluginManagerIntegration:
    """插件管理器集成测试"""
    
    def test_complete_plugin_lifecycle(self):
        """测试完整的插件生命周期"""
        manager = PluginManager()
        plugin = MockPlugin("test_plugin")
        
        # 加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            load_result = manager.load_plugin("test_plugin", "/path/to/plugin.py")
        
        assert load_result is True
        assert manager.get_plugin_status("test_plugin") == PluginStatus.LOADED
        
        # 初始化插件
        config = {"setting": "value"}
        init_result = manager.initialize_plugin("test_plugin", config)
        
        assert init_result is True
        assert manager.get_plugin_status("test_plugin") == PluginStatus.INITIALIZED
        assert plugin.initialize_called is True
        
        # 启动插件
        start_result = manager.start_plugin("test_plugin")
        
        assert start_result is True
        assert manager.get_plugin_status("test_plugin") == PluginStatus.RUNNING
        assert plugin.start_called is True
        
        # 停止插件
        stop_result = manager.stop_plugin("test_plugin")
        
        assert stop_result is True
        assert manager.get_plugin_status("test_plugin") == PluginStatus.STOPPED
        assert plugin.stop_called is True
        
        # 卸载插件
        unload_result = manager.unload_plugin("test_plugin")
        
        assert unload_result is True
        assert "test_plugin" not in manager._plugins
    
    def test_plugin_error_handling(self):
        """测试插件错误处理"""
        manager = PluginManager()
        
        class ErrorPlugin(BasePlugin):
            def __init__(self, name):
                info = PluginInfo(
                    name=name,
                    version="1.0.0",
                    description="Error plugin",
                    author="Test Author"
                )
                super().__init__(info)
            
            def _on_initialize(self, config):
                raise ValueError("Initialization failed")
        
        plugin = ErrorPlugin("error_plugin")
        
        # 加载插件
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin("error_plugin", "/path/to/plugin.py")
        
        # 初始化应该失败
        result = manager.initialize_plugin("error_plugin", {})
        
        assert result is False
        assert manager.get_plugin_status("error_plugin") == PluginStatus.ERROR


@pytest.mark.parametrize("plugin_count", [1, 3, 5])
def test_plugin_manager_with_different_counts(plugin_count):
    """测试不同数量插件的管理器"""
    manager = PluginManager()
    
    # 加载指定数量的插件
    for i in range(plugin_count):
        plugin = MockPlugin(f"plugin_{i}")
        with patch.object(manager._loader, 'load_plugin', return_value=plugin):
            manager.load_plugin(f"plugin_{i}", f"/path/to/plugin_{i}.py")
    
    assert len(manager._plugins) == plugin_count
    assert len(manager._plugin_status) == plugin_count
    
    # 测试列出插件
    plugins = manager.list_plugins()
    assert len(plugins) == plugin_count
    
    for i in range(plugin_count):
        assert f"plugin_{i}" in plugins
