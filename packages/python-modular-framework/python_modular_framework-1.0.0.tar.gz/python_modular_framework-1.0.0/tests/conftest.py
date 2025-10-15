"""
pytest配置文件

该文件包含pytest的全局配置和共享的fixture。

主要功能：
- 测试环境配置
- 共享fixture定义
- 测试数据管理
- 测试工具函数

作者：开发团队
创建时间：2025-01-12
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from framework.core.config import Config
from framework.core.application import Application
from framework.core.container import Container


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config() -> Config:
    """创建测试配置"""
    config = Config()
    config.set("debug", True)
    config.set("log_level", "DEBUG")
    config.set("test_mode", True)
    return config


@pytest.fixture
def test_app(test_config: Config) -> Application:
    """创建测试应用"""
    app = Application("test-app", "1.0.0")
    app.configure(test_config.to_dict())
    return app


@pytest.fixture
def test_container() -> Container:
    """创建测试容器"""
    return Container()


@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """示例配置数据"""
    return {
        "app_name": "test_app",
        "debug": True,
        "log_level": "INFO",
        "components": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db"
            },
            "cache": {
                "type": "memory",
                "max_size": 1000
            }
        },
        "middleware": {
            "logging": {
                "level": "INFO"
            }
        }
    }


@pytest.fixture
def mock_component_config() -> Dict[str, Any]:
    """模拟组件配置"""
    return {
        "name": "test_component",
        "config": {
            "setting1": "value1",
            "setting2": 42,
            "enabled": True
        }
    }


@pytest.fixture
def mock_middleware_config() -> Dict[str, Any]:
    """模拟中间件配置"""
    return {
        "name": "test_middleware",
        "config": {
            "enabled": True,
            "priority": 100
        }
    }


@pytest.fixture
def mock_plugin_config() -> Dict[str, Any]:
    """模拟插件配置"""
    return {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "dependencies": [],
        "config": {
            "enabled": True
        }
    }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "component: marks tests as component tests"
    )
    config.addinivalue_line(
        "markers", "middleware: marks tests as middleware tests"
    )
    config.addinivalue_line(
        "markers", "plugin: marks tests as plugin tests"
    )


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为测试文件添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 为测试类添加标记
        if "component" in item.name.lower():
            item.add_marker(pytest.mark.component)
        elif "middleware" in item.name.lower():
            item.add_marker(pytest.mark.middleware)
        elif "plugin" in item.name.lower():
            item.add_marker(pytest.mark.plugin)


# 测试报告钩子（需要pytest-html插件时才启用）
# 注意：这些钩子需要pytest-html插件，如果未安装会导致错误
# 暂时注释掉，需要时可以启用
# def pytest_html_report_title(report):
#     """设置HTML报告标题"""
#     report.title = "Python模块化框架测试报告"
# 
# def pytest_html_results_summary(prefix, summary, postfix):
#     """自定义HTML报告摘要"""
#     import datetime
#     prefix.extend([
#         "<p>测试框架: Python模块化框架</p>",
#         "<p>测试时间: " + str(datetime.datetime.now()) + "</p>"
#     ])
