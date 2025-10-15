"""
数据库连接池管理
- 提供数据库连接池的管理功能
- 支持连接的生命周期管理
- 提供连接监控和统计

主要功能：
- 连接池创建和管理
- 连接获取和释放
- 连接健康检查
- 连接统计和监控

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import time
import threading
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import DatabaseConfig
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConnectionInfo:
    """连接信息"""

    connection: Any
    created_at: datetime
    last_used: datetime
    use_count: int
    is_active: bool = True


class ConnectionPool:
    """
    数据库连接池

    管理数据库连接的创建、获取、释放和回收。
    """

    def __init__(self, config: "DatabaseConfig"):
        """
        初始化连接池

        Args:
            config (DatabaseConfig): 数据库配置
        """
        self.config = config
        self._pool: List[ConnectionInfo] = []
        self._lock = threading.RLock()
        self._stats = {
            "total_created": 0,
            "total_acquired": 0,
            "total_released": 0,
            "total_closed": 0,
            "active_connections": 0,
            "pool_size": 0,
            "max_pool_size": config.pool_size,
            "overflow_count": 0,
        }
        self._start_time = time.time()

    def get_connection(self) -> Any:
        """
        获取数据库连接

        Returns:
            Any: 数据库连接对象

        Raises:
            Exception: 获取连接失败时抛出异常
        """
        with self._lock:
            # 尝试从池中获取可用连接
            for i, conn_info in enumerate(self._pool):
                if conn_info.is_active and self._is_connection_healthy(conn_info):
                    conn_info.last_used = datetime.now()
                    conn_info.use_count += 1
                    self._stats["total_acquired"] += 1
                    return conn_info.connection

            # 如果没有可用连接，创建新连接
            if len(self._pool) < self.config.pool_size + self.config.max_overflow:
                connection = self._create_connection()
                conn_info = ConnectionInfo(
                    connection=connection,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    use_count=1,
                )
                self._pool.append(conn_info)
                self._stats["total_created"] += 1
                self._stats["total_acquired"] += 1
                self._stats["active_connections"] += 1

                if len(self._pool) > self.config.pool_size:
                    self._stats["overflow_count"] += 1

                return connection

            # 连接池已满，等待或抛出异常
            raise Exception("Connection pool exhausted")

    def release_connection(self, connection: Any) -> None:
        """
        释放数据库连接

        Args:
            connection (Any): 数据库连接对象
        """
        with self._lock:
            for conn_info in self._pool:
                if conn_info.connection == connection:
                    conn_info.last_used = datetime.now()
                    self._stats["total_released"] += 1
                    break

    def close_connection(self, connection: Any) -> None:
        """
        关闭数据库连接

        Args:
            connection (Any): 数据库连接对象
        """
        with self._lock:
            for i, conn_info in enumerate(self._pool):
                if conn_info.connection == connection:
                    try:
                        connection.close()
                    except Exception:
                        pass
                    conn_info.is_active = False
                    self._stats["total_closed"] += 1
                    self._stats["active_connections"] -= 1
                    break

    def close_all_connections(self) -> None:
        """关闭所有连接"""
        with self._lock:
            for conn_info in self._pool:
                if conn_info.is_active:
                    try:
                        conn_info.connection.close()
                    except Exception:
                        pass
                    conn_info.is_active = False

            self._pool.clear()
            self._stats["active_connections"] = 0

    def cleanup_stale_connections(self) -> int:
        """
        清理过期连接

        Returns:
            int: 清理的连接数量
        """
        with self._lock:
            stale_connections = []
            current_time = datetime.now()

            for conn_info in self._pool:
                # 检查连接是否过期
                if (
                    current_time - conn_info.created_at
                ).total_seconds() > self.config.pool_recycle:
                    stale_connections.append(conn_info)
                # 检查连接是否健康
                elif not self._is_connection_healthy(conn_info):
                    stale_connections.append(conn_info)

            # 关闭过期连接
            for conn_info in stale_connections:
                try:
                    conn_info.connection.close()
                except Exception:
                    pass
                conn_info.is_active = False
                self._stats["total_closed"] += 1
                self._stats["active_connections"] -= 1

            # 从池中移除过期连接
            self._pool = [conn for conn in self._pool if conn not in stale_connections]

            return len(stale_connections)

    def get_pool_status(self) -> Dict[str, Any]:
        """
        获取连接池状态

        Returns:
            Dict[str, Any]: 连接池状态信息
        """
        with self._lock:
            active_count = sum(1 for conn in self._pool if conn.is_active)
            total_requests = self._stats["total_acquired"]
            avg_use_count = (
                sum(conn.use_count for conn in self._pool) / len(self._pool)
                if self._pool
                else 0
            )

            return {
                "pool_size": len(self._pool),
                "active_connections": active_count,
                "max_pool_size": self.config.pool_size,
                "max_overflow": self.config.max_overflow,
                "overflow_count": self._stats["overflow_count"],
                "total_created": self._stats["total_created"],
                "total_acquired": self._stats["total_acquired"],
                "total_released": self._stats["total_released"],
                "total_closed": self._stats["total_closed"],
                "avg_use_count": avg_use_count,
                "uptime": time.time() - self._start_time,
            }

    def _create_connection(self) -> Any:
        """
        创建新的数据库连接

        Returns:
            Any: 数据库连接对象
        """
        # 这里需要根据具体的数据库类型创建连接
        # 实际实现中会使用SQLAlchemy或其他数据库驱动
        raise NotImplementedError("Subclasses must implement _create_connection")

    def _is_connection_healthy(self, conn_info: ConnectionInfo) -> bool:
        """
        检查连接是否健康

        Args:
            conn_info (ConnectionInfo): 连接信息

        Returns:
            bool: 连接是否健康
        """
        try:
            if self.config.pool_pre_ping:
                # 执行ping操作检查连接
                conn_info.connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection_context(self):
        """
        获取连接上下文管理器

        Yields:
            Any: 数据库连接对象
        """
        connection = None
        try:
            connection = self.get_connection()
            yield connection
        finally:
            if connection:
                self.release_connection(connection)

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        with self._lock:
            active_count = sum(1 for conn in self._pool if conn.is_active)
            total_count = len(self._pool)

            health_status = {
                "status": "healthy",
                "message": "Connection pool is healthy",
                "details": {
                    "active_connections": active_count,
                    "total_connections": total_count,
                    "pool_utilization": (
                        active_count / self.config.pool_size
                        if self.config.pool_size > 0
                        else 0
                    ),
                    "overflow_usage": (
                        self._stats["overflow_count"] / self.config.max_overflow
                        if self.config.max_overflow > 0
                        else 0
                    ),
                },
            }

            # 检查连接池使用率
            if active_count >= self.config.pool_size * 0.9:
                health_status["status"] = "warning"
                health_status["message"] = "Connection pool is nearly full"

            # 检查溢出使用
            if self._stats["overflow_count"] > 0:
                health_status["status"] = "warning"
                health_status["message"] = (
                    "Connection pool is using overflow connections"
                )

            return health_status
