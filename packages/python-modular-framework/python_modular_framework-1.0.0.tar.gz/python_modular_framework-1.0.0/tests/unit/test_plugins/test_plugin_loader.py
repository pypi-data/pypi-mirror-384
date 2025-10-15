"""
插件加载器测试

测试framework.core.plugin模块中的插件加载器。

测试内容：
- 插件加载器功能
- 插件发现机制
- 插件加载过程
- 错误处理

作者：开发团队
创建时间：2025-01-12
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch, mock_open
from framework.core.plugin import (
    PluginLoader,
    PluginInfo,
    PluginInterface,
    BasePlugin,
    PluginError
)


class MockPlugin(BasePlugin):
    """模拟插件用于测试"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        info = PluginInfo(
            name=name,
            version=version,
            description=f"Mock plugin {name}",
            author="Test Author"
        )
        super().__init__(info)


class TestPluginLoader:
    """插件加载器测试"""
    
    def test_plugin_loader_initialization(self):
        """测试插件加载器初始化"""
        loader = PluginLoader()
        
        assert loader.plugin_dirs == []
        assert loader._loaded_modules == {}
    
    def test_plugin_loader_initialization_with_dirs(self):
        """测试使用目录初始化插件加载器"""
        plugin_dirs = ["/path/to/plugins1", "/path/to/plugins2"]
        loader = PluginLoader(plugin_dirs)
        
        assert loader.plugin_dirs == plugin_dirs
    
    def test_discover_plugins_empty_dirs(self):
        """测试在空目录中发现插件"""
        loader = PluginLoader()
        
        plugins = loader.discover_plugins()
        
        assert plugins == {}
    
    def test_discover_plugins_nonexistent_dir(self):
        """测试在不存在目录中发现插件"""
        loader = PluginLoader(["/nonexistent/dir"])
        
        plugins = loader.discover_plugins()
        
        assert plugins == {}
    
    def test_load_plugin_nonexistent_path(self):
        """测试加载不存在的插件"""
        loader = PluginLoader()
        
        plugin = loader.load_plugin("/nonexistent/plugin.py")
        
        assert plugin is None
    
    def test_load_plugin_invalid_file(self):
        """测试加载无效的插件文件"""
        loader = PluginLoader()
        
        # 模拟加载失败
        with patch.object(loader, '_load_plugin_from_file', return_value=None):
            plugin = loader.load_plugin("/path/to/invalid.py")
        
        assert plugin is None


class TestPluginLoaderWithTempDir:
    """使用临时目录的插件加载器测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = PluginLoader([self.temp_dir])
    
    def teardown_method(self):
        """清理测试方法"""
        shutil.rmtree(self.temp_dir)
    
    def test_discover_plugins_from_file(self):
        """测试从文件发现插件"""
        # 创建插件文件
        plugin_file = os.path.join(self.temp_dir, "test_plugin.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        super().__init__(info)

# 创建插件实例
plugin = TestPlugin()
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 发现插件
        plugins = self.loader.discover_plugins()
        
        assert "test_plugin" in plugins
        assert plugins["test_plugin"].name == "test_plugin"
        assert plugins["test_plugin"].version == "1.0.0"
    
    def test_discover_plugins_from_directory(self):
        """测试从目录发现插件"""
        # 创建插件目录
        plugin_dir = os.path.join(self.temp_dir, "test_plugin")
        os.makedirs(plugin_dir)
        
        # 创建插件入口文件
        plugin_file = os.path.join(plugin_dir, "__init__.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        super().__init__(info)

# 创建插件实例
plugin = TestPlugin()
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 发现插件
        plugins = self.loader.discover_plugins()
        
        assert "test_plugin" in plugins
        assert plugins["test_plugin"].name == "test_plugin"
    
    def test_discover_plugins_ignore_invalid_files(self):
        """测试忽略无效的插件文件"""
        # 创建无效的插件文件
        invalid_file = os.path.join(self.temp_dir, "invalid_plugin.py")
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("This is not a valid plugin file")
        
        # 创建有效的插件文件
        valid_file = os.path.join(self.temp_dir, "valid_plugin.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class ValidPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="valid_plugin",
            version="1.0.0",
            description="Valid plugin",
            author="Test Author"
        )
        super().__init__(info)

plugin = ValidPlugin()
'''
        
        with open(valid_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 发现插件
        plugins = self.loader.discover_plugins()
        
        # 应该只发现有效插件
        assert "valid_plugin" in plugins
        assert "invalid_plugin" not in plugins
    
    def test_discover_plugins_ignore_private_files(self):
        """测试忽略私有文件"""
        # 创建私有文件
        private_file = os.path.join(self.temp_dir, "__private__.py")
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write("# Private file")
        
        # 创建有效插件文件
        valid_file = os.path.join(self.temp_dir, "valid_plugin.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class ValidPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="valid_plugin",
            version="1.0.0",
            description="Valid plugin",
            author="Test Author"
        )
        super().__init__(info)

plugin = ValidPlugin()
'''
        
        with open(valid_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 发现插件
        plugins = self.loader.discover_plugins()
        
        # 应该只发现有效插件
        assert "valid_plugin" in plugins
        assert len(plugins) == 1
    
    def test_load_plugin_from_file(self):
        """测试从文件加载插件"""
        # 创建插件文件
        plugin_file = os.path.join(self.temp_dir, "test_plugin.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        super().__init__(info)

plugin = TestPlugin()
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 加载插件
        plugin = self.loader.load_plugin(plugin_file)
        
        assert plugin is not None
        assert plugin.info.name == "test_plugin"
        assert plugin.info.version == "1.0.0"
    
    def test_load_plugin_from_directory(self):
        """测试从目录加载插件"""
        # 创建插件目录
        plugin_dir = os.path.join(self.temp_dir, "test_plugin")
        os.makedirs(plugin_dir)
        
        # 创建插件入口文件
        plugin_file = os.path.join(plugin_dir, "__init__.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        super().__init__(info)

plugin = TestPlugin()
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 加载插件
        plugin = self.loader.load_plugin(plugin_dir)
        
        assert plugin is not None
        assert plugin.info.name == "test_plugin"
    
    def test_load_plugin_directory_without_entry_file(self):
        """测试加载没有入口文件的目录"""
        # 创建没有入口文件的目录
        plugin_dir = os.path.join(self.temp_dir, "empty_plugin")
        os.makedirs(plugin_dir)
        
        # 尝试加载插件
        plugin = self.loader.load_plugin(plugin_dir)
        
        assert plugin is None
    
    def test_load_plugin_with_syntax_error(self):
        """测试加载有语法错误的插件"""
        # 创建有语法错误的插件文件
        plugin_file = os.path.join(self.temp_dir, "syntax_error_plugin.py")
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write("This is a syntax error plugin file with invalid Python syntax")
        
        # 尝试加载插件
        plugin = self.loader.load_plugin(plugin_file)
        
        assert plugin is None
    
    def test_load_plugin_without_plugin_instance(self):
        """测试加载没有插件实例的文件"""
        # 创建没有插件实例的文件
        plugin_file = os.path.join(self.temp_dir, "no_plugin.py")
        plugin_content = '''
from framework.core.plugin import BasePlugin, PluginInfo

class TestPlugin(BasePlugin):
    def __init__(self):
        info = PluginInfo(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )
        super().__init__(info)

# 没有创建插件实例
'''
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(plugin_content)
        
        # 尝试加载插件
        plugin = self.loader.load_plugin(plugin_file)
        
        assert plugin is None


class TestPluginLoaderMocked:
    """使用模拟的插件加载器测试"""
    
    def test_discover_plugins_with_mock(self):
        """测试使用模拟发现插件"""
        loader = PluginLoader()
        
        # 模拟文件系统操作
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['test_plugin.py']), \
             patch.object(loader, '_load_plugin_from_file') as mock_load:
            
            mock_plugin = MockPlugin("test_plugin")
            mock_load.return_value = mock_plugin
            
            plugins = loader.discover_plugins()
            
            assert "test_plugin" in plugins
            assert plugins["test_plugin"].name == "test_plugin"
            mock_load.assert_called_once()
    
    def test_load_plugin_with_mock(self):
        """测试使用模拟加载插件"""
        loader = PluginLoader()
        
        # 模拟文件系统操作
        with patch('os.path.isdir', return_value=False), \
             patch.object(loader, '_load_plugin_from_file') as mock_load:
            
            mock_plugin = MockPlugin("test_plugin")
            mock_load.return_value = mock_plugin
            
            plugin = loader.load_plugin("/path/to/plugin.py")
            
            assert plugin == mock_plugin
            mock_load.assert_called_once_with("/path/to/plugin.py")
    
    def test_load_plugin_from_dir_with_mock(self):
        """测试使用模拟从目录加载插件"""
        loader = PluginLoader()
        
        # 模拟文件系统操作
        with patch('os.path.isdir', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch.object(loader, '_load_plugin_from_file') as mock_load:
            
            mock_plugin = MockPlugin("test_plugin")
            mock_load.return_value = mock_plugin
            
            plugin = loader.load_plugin("/path/to/plugin_dir")
            
            assert plugin == mock_plugin
            mock_load.assert_called_once()
    
    def test_load_plugin_exception_handling(self):
        """测试插件加载异常处理"""
        loader = PluginLoader()
        
        # 模拟加载异常
        with patch('os.path.isdir', return_value=False), \
             patch.object(loader, '_load_plugin_from_file', side_effect=Exception("Load error")):
            
            plugin = loader.load_plugin("/path/to/plugin.py")
            
            assert plugin is None


@pytest.mark.parametrize("plugin_name,plugin_version", [
    ("plugin1", "1.0.0"),
    ("plugin2", "2.1.0"),
    ("my-plugin", "0.1.0"),
])
def test_plugin_loader_with_different_plugins(plugin_name, plugin_version):
    """测试加载不同参数的插件"""
    loader = PluginLoader()
    
    # 模拟插件加载
    with patch.object(loader, '_load_plugin_from_file') as mock_load:
        mock_plugin = MockPlugin(plugin_name, plugin_version)
        mock_load.return_value = mock_plugin
        
        plugin = loader.load_plugin("/path/to/plugin.py")
        
        assert plugin.info.name == plugin_name
        assert plugin.info.version == plugin_version


@pytest.mark.parametrize("file_count", [1, 3, 5])
def test_plugin_loader_discover_multiple_plugins(file_count):
    """测试发现多个插件"""
    loader = PluginLoader()
    
    # 模拟多个插件文件
    plugin_files = [f"plugin_{i}.py" for i in range(file_count)]
    
    with patch('os.path.exists', return_value=True), \
         patch('os.listdir', return_value=plugin_files), \
         patch.object(loader, '_load_plugin_from_file') as mock_load:
        
        # 设置模拟返回值
        mock_plugins = [MockPlugin(f"plugin_{i}") for i in range(file_count)]
        mock_load.side_effect = mock_plugins
        
        plugins = loader.discover_plugins()
        
        assert len(plugins) == file_count
        for i in range(file_count):
            assert f"plugin_{i}" in plugins
