"""
数据库组件实现
- 实现ComponentInterface接口
- 提供统一的数据库管理功能
- 支持多种数据库类型和连接池管理

主要功能：
- 多种数据库支持
- 连接池管理
- 事务处理
- 查询执行
- 数据库监控

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)
from .config import DatabaseConfig
from .pool import ConnectionPool

try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
    from sqlalchemy.orm import sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class DatabaseComponent(ComponentInterface):
    """
    数据库组件

    提供统一的数据库管理功能，支持多种数据库类型、
    连接池管理、事务处理等特性。
    """

    def __init__(self, name: str = "database"):
        """
        初始化数据库组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一数据库管理组件"
        self._dependencies = ["logging"]  # 数据库组件依赖日志组件
        self._status = ComponentStatus.UNINITIALIZED
        self._config = DatabaseConfig(database_url="sqlite:///database.db")

        # 数据库相关
        self._engine = None
        self._session_factory = None
        self._connection_pool = None
        self._metadata = None

        # 统计信息
        self._stats = {
            "queries_executed": 0,
            "transactions_committed": 0,
            "transactions_rolled_back": 0,
            "connection_errors": 0,
            "query_errors": 0,
        }
        self._start_time = None

        # 清理任务
        self._cleanup_task = None
        self._shutdown_event = threading.Event()

    @property
    def name(self) -> str:
        """获取组件名称"""
        return self._name

    @property
    def version(self) -> str:
        """获取组件版本"""
        return self._version

    @property
    def description(self) -> str:
        """获取组件描述"""
        return self._description

    @property
    def dependencies(self) -> List[str]:
        """获取组件依赖"""
        return self._dependencies

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化数据库组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 检查SQLAlchemy是否可用
            if not SQLALCHEMY_AVAILABLE:
                raise ComponentInitializationError(
                    self._name,
                    "SQLAlchemy is not available. Please install sqlalchemy package.",
                )

            # 更新配置
            if config:
                self._config = DatabaseConfig.from_dict(config)

            # 创建数据库引擎
            self._create_engine()

            # 创建会话工厂
            self._session_factory = sessionmaker(bind=self._engine)

            # 创建连接池
            self._connection_pool = DatabaseConnectionPool(self._config, self._engine)

            # 初始化元数据
            self._metadata = MetaData()

            self._status = ComponentStatus.INITIALIZED
            self._start_time = time.time()

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize database component: {e}"
            )

    def start(self) -> None:
        """
        启动数据库组件

        Raises:
            ComponentError: 启动失败时抛出异常
        """
        if self._status != ComponentStatus.INITIALIZED:
            raise ComponentError(
                self._name, f"Cannot start component in status {self._status}"
            )

        try:
            self._status = ComponentStatus.STARTING

            # 测试数据库连接
            self._test_connection()

            # 启动清理任务
            if self._config.pool_recycle > 0:
                self._start_cleanup_task()

            self._status = ComponentStatus.RUNNING

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to start database component: {e}")

    def stop(self) -> None:
        """
        停止数据库组件

        Raises:
            ComponentError: 停止失败时抛出异常
        """
        if self._status not in [ComponentStatus.RUNNING, ComponentStatus.STARTING]:
            return

        try:
            self._status = ComponentStatus.STOPPING

            # 停止清理任务
            if self._cleanup_task:
                self._shutdown_event.set()
                self._cleanup_task.cancel()
                try:
                    asyncio.get_event_loop().run_until_complete(self._cleanup_task)
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None

            # 关闭连接池
            if self._connection_pool:
                self._connection_pool.close_all_connections()

            # 关闭引擎
            if self._engine:
                self._engine.dispose()

            self._status = ComponentStatus.STOPPED

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to stop database component: {e}")

    def get_status(self) -> ComponentStatus:
        """获取组件状态"""
        return self._status

    def get_info(self) -> ComponentInfo:
        """获取组件信息"""
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self._dependencies,
            status=self._status,
            config=self._config.to_dict(),
            metadata={
                "database_type": self._config.database_type.value,
                "stats": self._stats.copy(),
                "uptime": time.time() - self._start_time if self._start_time else 0,
            },
        )

    def get_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        return self._config.to_dict()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置

        Args:
            config (Dict[str, Any]): 新的配置参数
        """
        if self._status == ComponentStatus.RUNNING:
            # 运行时更新配置需要重新初始化
            self.stop()

        new_config = DatabaseConfig.from_dict(config)
        self._config = self._config.merge(new_config)

        if self._status in [ComponentStatus.INITIALIZED, ComponentStatus.STOPPED]:
            self.initialize(self._config.to_dict())

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "status": "healthy",
            "message": "Database component is running normally",
            "details": {
                "component_status": self._status.value,
                "database_type": self._config.database_type.value,
                "connection_pool": (
                    self._connection_pool.get_pool_status()
                    if self._connection_pool
                    else {}
                ),
                "stats": self._stats.copy(),
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Component is not running: {self._status.value}"
        else:
            # 检查数据库连接
            try:
                self._test_connection()
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["message"] = f"Database connection failed: {e}"

        return health_status

    def _create_engine(self) -> None:
        """创建数据库引擎"""
        connection_url = self._config.get_connection_url()
        engine_kwargs = self._config.get_engine_kwargs()

        self._engine = create_engine(connection_url, **engine_kwargs)

    def _test_connection(self) -> None:
        """测试数据库连接"""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            self._stats["connection_errors"] += 1
            raise

    def _start_cleanup_task(self) -> None:
        """启动清理任务"""
        # 检查是否有运行的事件循环
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的事件循环，跳过异步任务
            print("No running event loop, skipping async cleanup task")
            return

        async def cleanup_worker():
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(self._config.pool_recycle)
                    if self._connection_pool:
                        self._connection_pool.cleanup_stale_connections()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._stats["connection_errors"] += 1

        self._cleanup_task = asyncio.create_task(cleanup_worker())

    # 数据库操作方法
    @contextmanager
    def get_session(self):
        """
        获取数据库会话上下文管理器

        Yields:
            Session: 数据库会话对象
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
            self._stats["transactions_committed"] += 1
        except Exception:
            session.rollback()
            self._stats["transactions_rolled_back"] += 1
            raise
        finally:
            session.close()

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行查询语句

        Args:
            query (str): SQL查询语句
            params (Optional[Dict[str, Any]]): 查询参数

        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                self._stats["queries_executed"] += 1

                # 转换为字典列表
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def execute_update(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        执行更新语句

        Args:
            query (str): SQL更新语句
            params (Optional[Dict[str, Any]]): 更新参数

        Returns:
            int: 影响的行数
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                conn.commit()
                self._stats["queries_executed"] += 1
                return result.rowcount

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def execute_insert(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        执行插入语句

        Args:
            query (str): SQL插入语句
            params (Optional[Dict[str, Any]]): 插入参数

        Returns:
            Any: 插入的主键值
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                conn.commit()
                self._stats["queries_executed"] += 1
                return (
                    result.inserted_primary_key[0]
                    if result.inserted_primary_key
                    else None
                )

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def execute_delete(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        执行删除语句

        Args:
            query (str): SQL删除语句
            params (Optional[Dict[str, Any]]): 删除参数

        Returns:
            int: 影响的行数
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                conn.commit()
                self._stats["queries_executed"] += 1
                return result.rowcount

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> None:
        """
        创建表

        Args:
            table_name (str): 表名
            columns (List[Dict[str, Any]]): 列定义
        """
        try:
            # 构建列定义
            table_columns = []
            for col_def in columns:
                col_type = col_def.get("type", "String")
                col_name = col_def.get("name")
                col_kwargs = col_def.get("kwargs", {})

                if col_type == "Integer":
                    table_columns.append(Column(col_name, Integer, **col_kwargs))
                elif col_type == "String":
                    table_columns.append(Column(col_name, String, **col_kwargs))
                # 可以添加更多类型支持

            # 创建表
            table = Table(table_name, self._metadata, *table_columns)
            table.create(self._engine, checkfirst=True)

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def drop_table(self, table_name: str) -> None:
        """
        删除表

        Args:
            table_name (str): 表名
        """
        try:
            if table_name in self._metadata.tables:
                self._metadata.tables[table_name].drop(self._engine, checkfirst=True)
        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息

        Args:
            table_name (str): 表名

        Returns:
            Dict[str, Any]: 表信息
        """
        try:
            # 获取表结构信息
            query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """

            result = self.execute_query(query, {"table_name": table_name})
            return {"table_name": table_name, "columns": result}

        except Exception as e:
            self._stats["query_errors"] += 1
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "queries_executed": self._stats["queries_executed"],
            "transactions_committed": self._stats["transactions_committed"],
            "transactions_rolled_back": self._stats["transactions_rolled_back"],
            "connection_errors": self._stats["connection_errors"],
            "query_errors": self._stats["query_errors"],
            "uptime": time.time() - self._start_time if self._start_time else 0,
        }

        # 添加连接池统计
        if self._connection_pool:
            pool_stats = self._connection_pool.get_pool_status()
            stats["connection_pool"] = pool_stats

        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "queries_executed": 0,
            "transactions_committed": 0,
            "transactions_rolled_back": 0,
            "connection_errors": 0,
            "query_errors": 0,
        }


class DatabaseConnectionPool(ConnectionPool):
    """数据库连接池实现"""

    def __init__(self, config: DatabaseConfig, engine):
        """
        初始化数据库连接池

        Args:
            config (DatabaseConfig): 数据库配置
            engine: SQLAlchemy引擎
        """
        super().__init__(config)
        self.engine = engine

    def _create_connection(self) -> Any:
        """
        创建新的数据库连接

        Returns:
            Any: 数据库连接对象
        """
        return self.engine.connect()
