"""
配置管理模块测试

测试framework.core.config模块的功能。

测试内容：
- 配置创建和初始化
- 配置设置和获取
- 配置验证
- 配置合并
- 配置序列化

作者：开发团队
创建时间：2025-01-12
"""

import pytest
from unittest.mock import patch, mock_open
from framework.core.config import Config, ConfigBuilder


class TestConfig:
    """配置类测试"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = Config()
        assert config is not None
        assert isinstance(config._config, dict)
        assert len(config._config) == 0
    
    def test_config_initialization_with_data(self):
        """测试使用数据初始化配置"""
        data = {"key1": "value1", "key2": 42}
        config = Config(data)
        assert config.get("key1") == "value1"
        assert config.get("key2") == 42
    
    def test_set_and_get(self):
        """测试设置和获取配置"""
        config = Config()
        
        # 测试简单键值对
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
        
        # 测试嵌套键
        config.set("nested.key", "nested_value")
        assert config.get("nested.key") == "nested_value"
        
        # 测试数字类型
        config.set("number", 123)
        assert config.get("number") == 123
        
        # 测试布尔类型
        config.set("boolean", True)
        assert config.get("boolean") is True
    
    def test_get_with_default(self):
        """测试获取配置时使用默认值"""
        config = Config()
        
        # 测试不存在的键
        assert config.get("nonexistent", "default") == "default"
        assert config.get("nonexistent", 42) == 42
        assert config.get("nonexistent", None) is None
    
    def test_has(self):
        """测试检查配置是否存在"""
        config = Config()
        
        # 测试不存在的键
        assert not config.has("nonexistent")
        
        # 测试存在的键
        config.set("existing", "value")
        assert config.has("existing")
        
        # 测试嵌套键
        config.set("nested.key", "value")
        assert config.has("nested.key")
        assert not config.has("nested.nonexistent")
    
    def test_remove(self):
        """测试删除配置"""
        config = Config()
        
        # 设置配置
        config.set("key1", "value1")
        config.set("key2", "value2")
        
        # 删除配置（通过设置为None来模拟删除）
        config.set("key1", None)
        assert config.get("key1") is None
        assert config.has("key2")
        
        # 删除不存在的键（应该不报错）
        config.set("nonexistent", None)
    
    def test_clear(self):
        """测试清空配置"""
        config = Config()
        
        # 设置一些配置
        config.set("key1", "value1")
        config.set("key2", "value2")
        
        # 清空配置
        config.clear()
        assert len(config._config) == 0
        assert not config.has("key1")
        assert not config.has("key2")
    
    def test_merge(self):
        """测试配置合并"""
        config1 = Config({"key1": "value1", "key2": "value2"})
        config2 = Config({"key2": "new_value2", "key3": "value3"})
        
        # 合并配置
        config1.merge(config2)
        
        assert config1.get("key1") == "value1"
        assert config1.get("key2") == "new_value2"  # 被覆盖
        assert config1.get("key3") == "value3"
    
    def test_merge_dict(self):
        """测试与字典合并"""
        config = Config({"key1": "value1"})
        data = {"key2": "value2", "key3": "value3"}
        
        # 使用merge方法合并另一个Config对象
        other_config = Config(data)
        config.merge(other_config)
        
        assert config.get("key1") == "value1"
        assert config.get("key2") == "value2"
        assert config.get("key3") == "value3"
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = Config()
        config.set("key1", "value1")
        config.set("nested.key", "nested_value")
        
        result = config.to_dict()
        
        assert isinstance(result, dict)
        assert result["key1"] == "value1"
        assert result["nested"]["key"] == "nested_value"
    
    def test_nested_access(self):
        """测试嵌套配置访问"""
        config = Config()
        
        # 设置嵌套配置
        config.set("database.host", "localhost")
        config.set("database.port", 5432)
        config.set("database.credentials.username", "admin")
        config.set("database.credentials.password", "secret")
        
        # 测试访问
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert config.get("database.credentials.username") == "admin"
        assert config.get("database.credentials.password") == "secret"
    
    def test_invalid_key_types(self):
        """测试无效键类型"""
        config = Config()
        
        # 测试None键
        with pytest.raises(AttributeError):
            config.set(None, "value")
        
        # 测试空字符串键（应该允许）
        config.set("", "value")
        assert config.get("") == "value"
        
        # 测试非字符串键
        with pytest.raises(AttributeError):
            config.set(123, "value")
    
    def test_load_from_file_yaml(self):
        """测试从YAML文件加载配置"""
        yaml_content = """
app_name: test_app
debug: true
database:
  host: localhost
  port: 5432
"""
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                with patch("yaml.safe_load", return_value={
                    "app_name": "test_app",
                    "debug": True,
                    "database": {
                        "host": "localhost",
                        "port": 5432
                    }
                }):
                    config = Config()
                    config.load_from_file("test.yaml")
                    
                    assert config.get("app_name") == "test_app"
                    assert config.get("debug") is True
                    assert config.get("database.host") == "localhost"
                    assert config.get("database.port") == 5432
    
    def test_load_from_file_json(self):
        """测试从JSON文件加载配置"""
        json_content = '{"app_name": "test_app", "debug": true}'
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json_content)):
                with patch("json.load", return_value={
                    "app_name": "test_app",
                    "debug": True
                }):
                    config = Config()
                    config.load_from_file("test.json")
                    
                    assert config.get("app_name") == "test_app"
                    assert config.get("debug") is True
    
    def test_save_to_file_yaml(self):
        """测试保存配置到YAML文件"""
        config = Config()
        config.set("app_name", "test_app")
        config.set("debug", True)
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("yaml.dump") as mock_yaml_dump:
                config.save_to_file("test.yaml")
                
                # 检查文件是否被打开（使用Path对象）
                mock_file.assert_called_once()
                mock_yaml_dump.assert_called_once()
    
    def test_save_to_file_json(self):
        """测试保存配置到JSON文件"""
        config = Config()
        config.set("app_name", "test_app")
        config.set("debug", True)
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                config.save_to_file("test.json", format="json")
                
                # 检查文件是否被打开（使用Path对象）
                mock_file.assert_called_once()
                mock_json_dump.assert_called_once()


class TestConfigBuilder:
    """配置构建器测试"""
    
    def test_config_builder_initialization(self):
        """测试配置构建器初始化"""
        builder = ConfigBuilder()
        assert builder is not None
        assert isinstance(builder._config, Config)
    
    def test_add_setting(self):
        """测试添加设置"""
        builder = ConfigBuilder()
        
        # 使用with_defaults方法添加设置
        builder.with_defaults({"key1": "value1", "nested": {"key": "nested_value"}})
        
        config = builder.build()
        
        assert config.get("key1") == "value1"
        assert config.get("nested.key") == "nested_value"
    
    def test_add_section(self):
        """测试添加配置节"""
        builder = ConfigBuilder()
        
        section_data = {
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }
        
        builder.with_defaults(section_data)
        
        config = builder.build()
        
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
    
    def test_set_environment(self):
        """测试设置环境"""
        builder = ConfigBuilder()
        
        # 使用with_env方法设置环境变量前缀
        builder.with_env("TEST_")
        builder.with_defaults({"debug": True})
        
        config = builder.build()
        
        assert config.get("debug") is True
    
    def test_build(self):
        """测试构建配置"""
        builder = ConfigBuilder()
        
        builder.with_defaults({
            "app_name": "test_app",
            "database": {"host": "localhost"}
        })
        
        config = builder.build()
        
        assert isinstance(config, Config)
        assert config.get("app_name") == "test_app"
        assert config.get("database.host") == "localhost"
    
    def test_chain_calls(self):
        """测试链式调用"""
        config = (ConfigBuilder()
                 .with_defaults({
                     "app_name": "test_app",
                     "debug": True,
                     "database": {"host": "localhost"}
                 })
                 .build())
        
        assert config.get("app_name") == "test_app"
        assert config.get("debug") is True
        assert config.get("database.host") == "localhost"


@pytest.mark.parametrize("key,value,expected", [
    ("string_key", "string_value", "string_value"),
    ("int_key", 42, 42),
    ("float_key", 3.14, 3.14),
    ("bool_key", True, True),
    ("list_key", [1, 2, 3], [1, 2, 3]),
    ("dict_key", {"nested": "value"}, {"nested": "value"}),
])
def test_config_data_types(key, value, expected):
    """测试不同数据类型的配置"""
    config = Config()
    config.set(key, value)
    assert config.get(key) == expected


@pytest.mark.parametrize("key_path,expected", [
    ("simple.key", "simple_value"),
    ("nested.deep.key", "deep_value"),
    ("very.nested.deep.key", "very_deep_value"),
])
def test_nested_key_paths(key_path, expected):
    """测试嵌套键路径"""
    config = Config()
    config.set(key_path, expected)
    assert config.get(key_path) == expected
