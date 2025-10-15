"""
配置管理模块
- 提供统一的配置管理功能
- 支持多种配置源（文件、环境变量、命令行参数）
- 支持配置验证和类型转换

主要功能：
- 配置文件加载和解析
- 环境变量支持
- 配置验证
- 配置合并和覆盖

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union, List, Type
from pathlib import Path
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置异常基类"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化配置异常

        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class ConfigValidationError(ConfigError):
    """配置验证异常"""



class ConfigFileNotFoundError(ConfigError):
    """配置文件未找到异常"""



class Config:
    """
    配置管理类

    提供统一的配置管理功能，支持多种配置源和配置验证。
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        初始化配置管理器

        Args:
            config_data (Optional[Dict[str, Any]]): 初始配置数据
        """
        self._config: Dict[str, Any] = config_data or {}
        self._validators: Dict[str, Type[BaseModel]] = {}
        self._env_prefix: str = ""
        self._config_files: List[str] = []

    def set_env_prefix(self, prefix: str) -> None:
        """
        设置环境变量前缀

        Args:
            prefix (str): 环境变量前缀
        """
        self._env_prefix = prefix

    def load_from_file(
        self, file_path: Union[str, Path], required: bool = True
    ) -> None:
        """
        从文件加载配置

        Args:
            file_path (Union[str, Path]): 配置文件路径
            required (bool): 文件是否必需

        Raises:
            ConfigFileNotFoundError: 文件不存在且为必需时抛出异常
            ConfigError: 文件解析失败时抛出异常
        """
        file_path = Path(file_path)

        if not file_path.exists():
            if required:
                raise ConfigFileNotFoundError(f"Config file not found: {file_path}")
            logger.warning(f"Config file not found: {file_path}")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif file_path.suffix.lower() == ".json":
                    data = json.load(f)
                else:
                    raise ConfigError(
                        f"Unsupported config file format: {file_path.suffix}"
                    )

            if data:
                self._config.update(data)
                self._config_files.append(str(file_path))
                logger.info(f"Loaded config from file: {file_path}")

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigError(f"Failed to parse config file {file_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config file {file_path}: {e}")

    def load_from_env(self, prefix: Optional[str] = None) -> None:
        """
        从环境变量加载配置

        Args:
            prefix (Optional[str]): 环境变量前缀，如果为None则使用设置的前缀
        """
        env_prefix = prefix or self._env_prefix

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # 移除前缀并转换为配置键
                config_key = key[len(env_prefix) :].lower()
                if config_key.startswith("_"):
                    config_key = config_key[1:]

                # 将下划线分隔的键转换为嵌套字典
                keys = config_key.split("_")
                self._set_nested_value(self._config, keys, self._parse_env_value(value))

        logger.info(
            f"Loaded config from environment variables with prefix: {env_prefix}"
        )

    def _parse_env_value(self, value: str) -> Any:
        """
        解析环境变量值

        Args:
            value (str): 环境变量值

        Returns:
            Any: 解析后的值
        """
        # 尝试解析为JSON
        if value.startswith("{") or value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # 尝试解析为布尔值
        if value.lower() in ["true", "false"]:
            return value.lower() == "true"

        # 尝试解析为数字
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # 返回字符串
        return value

    def _set_nested_value(
        self, config: Dict[str, Any], keys: List[str], value: Any
    ) -> None:
        """
        设置嵌套字典值

        Args:
            config (Dict[str, Any]): 配置字典
            keys (List[str]): 键路径
            value (Any): 要设置的值
        """
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key (str): 配置键，支持点号分隔的嵌套键
            default (Any): 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        current = self._config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值

        Args:
            key (str): 配置键，支持点号分隔的嵌套键
            value (Any): 配置值
        """
        keys = key.split(".")
        self._set_nested_value(self._config, keys, value)

    def has(self, key: str) -> bool:
        """
        检查配置键是否存在

        Args:
            key (str): 配置键

        Returns:
            bool: 是否存在
        """
        keys = key.split(".")
        current = self._config

        try:
            for k in keys:
                current = current[k]
            return True
        except (KeyError, TypeError):
            return False

    def register_validator(self, section: str, validator: Type[BaseModel]) -> None:
        """
        注册配置验证器

        Args:
            section (str): 配置节名称
            validator (Type[BaseModel]): Pydantic验证器类
        """
        self._validators[section] = validator

    def validate(self, section: Optional[str] = None) -> None:
        """
        验证配置

        Args:
            section (Optional[str]): 要验证的配置节，如果为None则验证所有注册的节

        Raises:
            ConfigValidationError: 验证失败时抛出异常
        """
        if section:
            sections = [section]
        else:
            sections = list(self._validators.keys())

        for sec in sections:
            if sec not in self._validators:
                continue

            validator_class = self._validators[sec]
            config_data = self.get(sec, {})

            try:
                validator_class(**config_data)
            except ValidationError as e:
                raise ConfigValidationError(
                    f"Config validation failed for section '{sec}': {e}"
                )

    def merge(self, other_config: "Config") -> None:
        """
        合并其他配置

        Args:
            other_config (Config): 要合并的配置对象
        """
        self._deep_merge(self._config, other_config._config)

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        深度合并字典

        Args:
            base (Dict[str, Any]): 基础字典
            update (Dict[str, Any]): 更新字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self._config.copy()

    def save_to_file(self, file_path: Union[str, Path], format: str = "yaml") -> None:
        """
        保存配置到文件

        Args:
            file_path (Union[str, Path]): 文件路径
            format (str): 文件格式 ('yaml' 或 'json')
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    yaml.dump(
                        self._config, f, default_flow_style=False, allow_unicode=True
                    )
                elif format.lower() == "json":
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                else:
                    raise ConfigError(f"Unsupported format: {format}")

            logger.info(f"Saved config to file: {file_path}")

        except Exception as e:
            raise ConfigError(f"Failed to save config to file {file_path}: {e}")

    def get_config_files(self) -> List[str]:
        """
        获取已加载的配置文件列表

        Returns:
            List[str]: 配置文件路径列表
        """
        return self._config_files.copy()

    def clear(self) -> None:
        """
        清空配置
        """
        self._config.clear()
        self._config_files.clear()
        self._validators.clear()


class ConfigBuilder:
    """
    配置构建器

    提供链式API来构建配置。
    """

    def __init__(self):
        """初始化配置构建器"""
        self._config = Config()

    def with_file(
        self, file_path: Union[str, Path], required: bool = True
    ) -> "ConfigBuilder":
        """
        添加配置文件

        Args:
            file_path (Union[str, Path]): 配置文件路径
            required (bool): 文件是否必需

        Returns:
            ConfigBuilder: 构建器实例
        """
        self._config.load_from_file(file_path, required)
        return self

    def with_env(self, prefix: str = "") -> "ConfigBuilder":
        """
        添加环境变量

        Args:
            prefix (str): 环境变量前缀

        Returns:
            ConfigBuilder: 构建器实例
        """
        self._config.set_env_prefix(prefix)
        self._config.load_from_env()
        return self

    def with_defaults(self, defaults: Dict[str, Any]) -> "ConfigBuilder":
        """
        添加默认配置

        Args:
            defaults (Dict[str, Any]): 默认配置

        Returns:
            ConfigBuilder: 构建器实例
        """
        self._config.merge(Config(defaults))
        return self

    def with_validator(
        self, section: str, validator: Type[BaseModel]
    ) -> "ConfigBuilder":
        """
        添加验证器

        Args:
            section (str): 配置节名称
            validator (Type[BaseModel]): 验证器类

        Returns:
            ConfigBuilder: 构建器实例
        """
        self._config.register_validator(section, validator)
        return self

    def build(self) -> Config:
        """
        构建配置对象

        Returns:
            Config: 配置对象
        """
        return self._config
