"""
日志组件配置类
- 定义日志组件的配置参数
- 支持多种日志配置选项
- 提供配置验证功能

主要功能：
- 日志级别配置
- 输出格式配置
- 日志轮转配置
- 过滤器配置

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式枚举"""

    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    CUSTOM = "custom"


class LoggingConfig(BaseModel):
    """
    日志配置类

    定义日志组件的所有配置参数，包括日志级别、输出格式、
    轮转策略、过滤器等。
    """

    # 基本配置
    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    format: LogFormat = Field(default=LogFormat.DETAILED, description="日志格式")
    custom_format: Optional[str] = Field(default=None, description="自定义格式字符串")

    # 输出配置
    console_enabled: bool = Field(default=True, description="是否启用控制台输出")
    file_enabled: bool = Field(default=False, description="是否启用文件输出")
    file_path: Optional[str] = Field(default=None, description="日志文件路径")

    # 轮转配置
    rotation_enabled: bool = Field(default=False, description="是否启用日志轮转")
    max_file_size: Optional[str] = Field(
        default="10MB", description="单个日志文件最大大小"
    )
    max_files: int = Field(default=5, description="保留的日志文件数量")
    rotation_time: Optional[str] = Field(default=None, description="轮转时间间隔")

    # 过滤器配置
    filters: List[str] = Field(default_factory=list, description="日志过滤器列表")
    exclude_filters: List[str] = Field(
        default_factory=list, description="排除过滤器列表"
    )

    # 性能配置
    async_enabled: bool = Field(default=False, description="是否启用异步日志")
    buffer_size: int = Field(default=1000, description="日志缓冲区大小")
    flush_interval: float = Field(default=1.0, description="刷新间隔（秒）")

    # 结构化日志配置
    structured_enabled: bool = Field(default=False, description="是否启用结构化日志")
    include_context: bool = Field(default=True, description="是否包含上下文信息")
    include_traceback: bool = Field(default=True, description="是否包含异常堆栈")

    # 高级配置
    propagate: bool = Field(default=True, description="是否传播到父日志器")
    disable_existing_loggers: bool = Field(
        default=False, description="是否禁用现有日志器"
    )

    @field_validator("custom_format")
    @classmethod
    def validate_custom_format(cls, v, info):
        """验证自定义格式"""
        if info.data.get("format") == LogFormat.CUSTOM and not v:
            raise ValueError("Custom format requires custom_format to be specified")
        return v

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v, info):
        """验证文件路径"""
        if info.data.get("file_enabled") and not v:
            raise ValueError("File output requires file_path to be specified")
        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v):
        """验证文件大小格式"""
        if v:
            # 支持格式：10MB, 1GB, 500KB等
            import re

            pattern = r"^(\d+)(KB|MB|GB|TB)$"
            if not re.match(pattern, v.upper()):
                raise ValueError("max_file_size must be in format like '10MB', '1GB'")
        return v

    @field_validator("rotation_time")
    @classmethod
    def validate_rotation_time(cls, v):
        """验证轮转时间格式"""
        if v:
            # 支持格式：1h, 24h, 1d, 7d等
            import re

            pattern = r"^(\d+)(h|d|w|m)$"
            if not re.match(pattern, v.lower()):
                raise ValueError(
                    "rotation_time must be in format like '1h', '24h', '1d'"
                )
        return v

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoggingConfig":
        """
        从字典创建配置

        Args:
            data (Dict[str, Any]): 配置数据

        Returns:
            LoggingConfig: 配置实例
        """
        return cls(**data)

    def merge(self, other: "LoggingConfig") -> "LoggingConfig":
        """
        合并配置

        Args:
            other (LoggingConfig): 要合并的配置

        Returns:
            LoggingConfig: 合并后的配置
        """
        merged_data = self.model_dump()
        other_data = other.model_dump()

        # 合并非None值
        for key, value in other_data.items():
            if value is not None:
                merged_data[key] = value

        return LoggingConfig(**merged_data)

    def get_file_size_bytes(self) -> Optional[int]:
        """
        获取文件大小（字节）

        Returns:
            Optional[int]: 文件大小（字节），如果未设置则返回None
        """
        if not self.max_file_size:
            return None

        size_str = self.max_file_size.upper()
        size_value = int("".join(filter(str.isdigit, size_str)))
        size_unit = "".join(filter(str.isalpha, size_str))

        multipliers = {
            "KB": 1024,
            "MB": 1024 * 1024,
            "GB": 1024 * 1024 * 1024,
            "TB": 1024 * 1024 * 1024 * 1024,
        }

        return size_value * multipliers.get(size_unit, 1)

    def get_rotation_seconds(self) -> Optional[int]:
        """
        获取轮转时间（秒）

        Returns:
            Optional[int]: 轮转时间（秒），如果未设置则返回None
        """
        if not self.rotation_time:
            return None

        time_str = self.rotation_time.lower()
        time_value = int("".join(filter(str.isdigit, time_str)))
        time_unit = "".join(filter(str.isalpha, time_str))

        multipliers = {
            "h": 3600,  # 小时
            "d": 86400,  # 天
            "w": 604800,  # 周
            "m": 2592000,  # 月（30天）
        }

        return time_value * multipliers.get(time_unit, 1)
