"""
数据库组件配置类
- 定义数据库组件的配置参数
- 支持多种数据库配置选项
- 提供配置验证功能

主要功能：
- 数据库类型配置
- 连接池配置
- 事务配置
- 性能参数配置

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DatabaseType(str, Enum):
    """数据库类型枚举"""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"


class DatabaseConfig(BaseModel):
    """
    数据库配置类

    定义数据库组件的所有配置参数，包括数据库类型、连接信息、
    连接池配置、事务配置等。
    """

    # 基本配置
    database_type: DatabaseType = Field(
        default=DatabaseType.SQLITE, description="数据库类型"
    )
    database_url: str = Field(description="数据库连接URL")
    database_name: Optional[str] = Field(default=None, description="数据库名称")

    # 连接配置
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口")
    username: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")

    # 连接池配置
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="获取连接超时时间（秒）")
    pool_recycle: int = Field(default=3600, description="连接回收时间（秒）")
    pool_pre_ping: bool = Field(default=True, description="连接前是否ping")

    # 连接参数
    connect_timeout: int = Field(default=10, description="连接超时时间（秒）")
    socket_timeout: int = Field(default=30, description="套接字超时时间（秒）")
    charset: str = Field(default="utf8mb4", description="字符集")

    # 事务配置
    autocommit: bool = Field(default=False, description="是否自动提交")
    isolation_level: str = Field(default="READ_COMMITTED", description="隔离级别")
    transaction_timeout: int = Field(default=300, description="事务超时时间（秒）")

    # 性能配置
    echo: bool = Field(default=False, description="是否打印SQL语句")
    echo_pool: bool = Field(default=False, description="是否打印连接池信息")
    pool_reset_on_return: str = Field(
        default="rollback", description="连接返回时的重置方式"
    )

    # 高级配置
    enable_ssl: bool = Field(default=False, description="是否启用SSL")
    ssl_cert: Optional[str] = Field(default=None, description="SSL证书路径")
    ssl_key: Optional[str] = Field(default=None, description="SSL密钥路径")
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA证书路径")

    # 监控配置
    enable_metrics: bool = Field(default=True, description="是否启用指标收集")
    metrics_interval: int = Field(default=60, description="指标收集间隔（秒）")

    # 备份配置
    enable_backup: bool = Field(default=False, description="是否启用备份")
    backup_interval: int = Field(default=86400, description="备份间隔（秒）")
    backup_retention: int = Field(default=7, description="备份保留天数")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v, info):
        """验证数据库URL"""
        if not v:
            raise ValueError("database_url is required")

        # 检查URL格式
        if not (
            v.startswith("sqlite:///")
            or v.startswith("postgresql://")
            or v.startswith("mysql://")
            or v.startswith("oracle://")
            or v.startswith("mssql://")
        ):
            raise ValueError("Invalid database URL format")

        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """验证端口号"""
        if not (1 <= v <= 65535):
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("pool_size")
    @classmethod
    def validate_pool_size(cls, v):
        """验证连接池大小"""
        if v <= 0:
            raise ValueError("pool_size must be positive")
        return v

    @field_validator("max_overflow")
    @classmethod
    def validate_max_overflow(cls, v):
        """验证最大溢出连接数"""
        if v < 0:
            raise ValueError("max_overflow must be non-negative")
        return v

    @field_validator("isolation_level")
    @classmethod
    def validate_isolation_level(cls, v):
        """验证隔离级别"""
        allowed_levels = [
            "READ_UNCOMMITTED",
            "READ_COMMITTED",
            "REPEATABLE_READ",
            "SERIALIZABLE",
        ]
        if v not in allowed_levels:
            raise ValueError(f"isolation_level must be one of {allowed_levels}")
        return v

    @field_validator("pool_reset_on_return")
    @classmethod
    def validate_pool_reset_on_return(cls, v):
        """验证连接重置方式"""
        allowed_values = ["rollback", "commit", "none"]
        if v not in allowed_values:
            raise ValueError(f"pool_reset_on_return must be one of {allowed_values}")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConfig":
        """
        从字典创建配置

        Args:
            data (Dict[str, Any]): 配置数据

        Returns:
            DatabaseConfig: 配置实例
        """
        return cls(**data)

    def merge(self, other: "DatabaseConfig") -> "DatabaseConfig":
        """
        合并配置

        Args:
            other (DatabaseConfig): 要合并的配置

        Returns:
            DatabaseConfig: 合并后的配置
        """
        merged_data = self.model_dump()
        other_data = other.model_dump()

        # 合并非None值
        for key, value in other_data.items():
            if value is not None:
                merged_data[key] = value

        return DatabaseConfig(**merged_data)

    def get_connection_url(self) -> str:
        """
        获取连接URL

        Returns:
            str: 连接URL
        """
        if self.database_url:
            return self.database_url

        # 根据数据库类型构建URL
        if self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database_name or 'database.db'}"
        elif self.database_type == DatabaseType.POSTGRESQL:
            auth = (
                f"{self.username}:{self.password}@"
                if self.username and self.password
                else ""
            )
            return f"postgresql://{auth}{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == DatabaseType.MYSQL:
            auth = (
                f"{self.username}:{self.password}@"
                if self.username and self.password
                else ""
            )
            return f"mysql://{auth}{self.host}:{self.port}/{self.database_name}?charset={self.charset}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """
        获取SQLAlchemy引擎参数

        Returns:
            Dict[str, Any]: 引擎参数
        """
        kwargs = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_reset_on_return": self.pool_reset_on_return,
        }

        # 添加SSL配置
        if self.enable_ssl:
            ssl_kwargs = {}
            if self.ssl_cert:
                ssl_kwargs["sslcert"] = self.ssl_cert
            if self.ssl_key:
                ssl_kwargs["sslkey"] = self.ssl_key
            if self.ssl_ca:
                ssl_kwargs["sslrootcert"] = self.ssl_ca
            if ssl_kwargs:
                kwargs["connect_args"] = ssl_kwargs

        return kwargs

    def get_connection_kwargs(self) -> Dict[str, Any]:
        """
        获取连接参数

        Returns:
            Dict[str, Any]: 连接参数
        """
        return {
            "connect_timeout": self.connect_timeout,
            "socket_timeout": self.socket_timeout,
            "charset": self.charset,
            "autocommit": self.autocommit,
        }
