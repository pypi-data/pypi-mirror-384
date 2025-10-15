"""
缓存组件配置类
- 定义缓存组件的配置参数
- 支持多种缓存配置选项
- 提供配置验证功能

主要功能：
- 缓存类型配置
- 缓存策略配置
- 过期时间配置
- 性能参数配置

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CacheType(str, Enum):
    """缓存类型枚举"""

    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"


class CacheStrategy(str, Enum):
    """缓存策略枚举"""

    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于时间过期


class CacheConfig(BaseModel):
    """
    缓存配置类

    定义缓存组件的所有配置参数，包括缓存类型、策略、
    过期时间、性能参数等。
    """

    # 基本配置
    cache_type: CacheType = Field(default=CacheType.MEMORY, description="缓存类型")
    strategy: CacheStrategy = Field(default=CacheStrategy.LRU, description="缓存策略")
    default_ttl: int = Field(default=3600, description="默认过期时间（秒）")
    max_size: int = Field(default=1000, description="最大缓存条目数")

    # Redis配置
    redis_host: str = Field(default="localhost", description="Redis主机地址")
    redis_port: int = Field(default=6379, description="Redis端口")
    redis_db: int = Field(default=0, description="Redis数据库编号")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    redis_connection_pool_size: int = Field(default=10, description="Redis连接池大小")
    redis_socket_timeout: int = Field(default=5, description="Redis套接字超时时间")
    redis_socket_connect_timeout: int = Field(
        default=5, description="Redis连接超时时间"
    )

    # 性能配置
    enable_compression: bool = Field(default=False, description="是否启用压缩")
    compression_threshold: int = Field(default=1024, description="压缩阈值（字节）")
    enable_serialization: bool = Field(default=True, description="是否启用序列化")
    serialization_method: str = Field(default="pickle", description="序列化方法")

    # 统计配置
    enable_statistics: bool = Field(default=True, description="是否启用统计")
    statistics_interval: int = Field(default=60, description="统计间隔（秒）")

    # 高级配置
    enable_namespace: bool = Field(default=True, description="是否启用命名空间")
    namespace_prefix: str = Field(default="cache", description="命名空间前缀")
    enable_versioning: bool = Field(default=False, description="是否启用版本控制")
    version_ttl: int = Field(default=86400, description="版本过期时间（秒）")

    # 清理配置
    cleanup_interval: int = Field(default=300, description="清理间隔（秒）")
    cleanup_threshold: float = Field(default=0.8, description="清理阈值（使用率）")

    # 安全配置
    enable_encryption: bool = Field(default=False, description="是否启用加密")
    encryption_key: Optional[str] = Field(default=None, description="加密密钥")

    @field_validator("default_ttl")
    @classmethod
    def validate_default_ttl(cls, v):
        """验证默认TTL"""
        if v <= 0:
            raise ValueError("default_ttl must be positive")
        return v

    @field_validator("max_size")
    @classmethod
    def validate_max_size(cls, v):
        """验证最大大小"""
        if v <= 0:
            raise ValueError("max_size must be positive")
        return v

    @field_validator("redis_port")
    @classmethod
    def validate_redis_port(cls, v):
        """验证Redis端口"""
        if not (1 <= v <= 65535):
            raise ValueError("redis_port must be between 1 and 65535")
        return v

    @field_validator("redis_db")
    @classmethod
    def validate_redis_db(cls, v):
        """验证Redis数据库编号"""
        if v < 0:
            raise ValueError("redis_db must be non-negative")
        return v

    @field_validator("serialization_method")
    @classmethod
    def validate_serialization_method(cls, v):
        """验证序列化方法"""
        allowed_methods = ["pickle", "json", "msgpack", "none"]
        if v not in allowed_methods:
            raise ValueError(f"serialization_method must be one of {allowed_methods}")
        return v

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v, info):
        """验证加密密钥"""
        if info.data.get("enable_encryption") and not v:
            raise ValueError("encryption_key is required when encryption is enabled")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheConfig":
        """
        从字典创建配置

        Args:
            data (Dict[str, Any]): 配置数据

        Returns:
            CacheConfig: 配置实例
        """
        return cls(**data)

    def merge(self, other: "CacheConfig") -> "CacheConfig":
        """
        合并配置

        Args:
            other (CacheConfig): 要合并的配置

        Returns:
            CacheConfig: 合并后的配置
        """
        merged_data = self.model_dump()
        other_data = other.model_dump()

        # 合并非None值
        for key, value in other_data.items():
            if value is not None:
                merged_data[key] = value

        return CacheConfig(**merged_data)

    def get_redis_url(self) -> str:
        """
        获取Redis连接URL

        Returns:
            str: Redis连接URL
        """
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_namespace_key(self, key: str) -> str:
        """
        获取带命名空间的键

        Args:
            key (str): 原始键

        Returns:
            str: 带命名空间的键
        """
        if self.enable_namespace:
            return f"{self.namespace_prefix}:{key}"
        return key

    def should_compress(self, data_size: int) -> bool:
        """
        判断是否应该压缩数据

        Args:
            data_size (int): 数据大小（字节）

        Returns:
            bool: 是否应该压缩
        """
        return self.enable_compression and data_size >= self.compression_threshold

    def get_cleanup_threshold_count(self) -> int:
        """
        获取清理阈值数量

        Returns:
            int: 清理阈值数量
        """
        return int(self.max_size * self.cleanup_threshold)
