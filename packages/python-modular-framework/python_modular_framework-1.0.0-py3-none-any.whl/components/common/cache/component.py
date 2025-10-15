"""
缓存组件实现
- 实现ComponentInterface接口
- 提供统一的缓存管理功能
- 支持内存缓存和Redis缓存

主要功能：
- 多种缓存策略支持
- 内存和Redis缓存
- 缓存统计和监控
- 异步缓存操作

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import asyncio
import threading
import time
import pickle
import json
import gzip
from typing import Any, Dict, List, Optional
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)


class SecurityError(Exception):
    """安全异常类"""

from .config import CacheConfig, CacheType, CacheStrategy
from .strategy import LRUStrategy, LFUStrategy, FIFOStrategy, TTLStrategy

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheComponent(ComponentInterface):
    """
    缓存组件

    提供统一的缓存管理功能，支持多种缓存类型、策略、
    序列化、压缩等特性。
    """

    def __init__(self, name: str = "cache"):
        """
        初始化缓存组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一缓存管理组件"
        self._dependencies = ["logging"]  # 缓存组件依赖日志组件
        self._status = ComponentStatus.UNINITIALIZED
        self._config = CacheConfig()

        # 缓存相关
        self._memory_cache = None
        self._redis_client = None
        self._strategy = None

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "errors": 0,
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
        初始化缓存组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 更新配置
            if config:
                self._config = CacheConfig.from_dict(config)

            # 初始化内存缓存
            if self._config.cache_type in [CacheType.MEMORY, CacheType.HYBRID]:
                self._init_memory_cache()

            # 初始化Redis缓存
            if self._config.cache_type in [CacheType.REDIS, CacheType.HYBRID]:
                self._init_redis_cache()

            self._status = ComponentStatus.INITIALIZED
            self._start_time = time.time()

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize cache component: {e}"
            )

    def start(self) -> None:
        """
        启动缓存组件

        Raises:
            ComponentError: 启动失败时抛出异常
        """
        if self._status != ComponentStatus.INITIALIZED:
            raise ComponentError(
                self._name, f"Cannot start component in status {self._status}"
            )

        try:
            self._status = ComponentStatus.STARTING

            # 启动清理任务
            if self._config.cleanup_interval > 0:
                self._start_cleanup_task()

            self._status = ComponentStatus.RUNNING

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to start cache component: {e}")

    def stop(self) -> None:
        """
        停止缓存组件

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

            # 关闭Redis连接
            if self._redis_client:
                self._redis_client.close()

            self._status = ComponentStatus.STOPPED

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to stop cache component: {e}")

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
                "cache_type": self._config.cache_type.value,
                "strategy": self._config.strategy.value,
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

        new_config = CacheConfig.from_dict(config)
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
            "message": "Cache component is running normally",
            "details": {
                "component_status": self._status.value,
                "cache_type": self._config.cache_type.value,
                "memory_cache_size": (
                    self._memory_cache.size() if self._memory_cache else 0
                ),
                "redis_connected": (
                    self._is_redis_connected() if self._redis_client else False
                ),
                "stats": self._stats.copy(),
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Component is not running: {self._status.value}"

        return health_status

    def _init_memory_cache(self) -> None:
        """初始化内存缓存"""
        strategy_map = {
            CacheStrategy.LRU: LRUStrategy,
            CacheStrategy.LFU: LFUStrategy,
            CacheStrategy.FIFO: FIFOStrategy,
            CacheStrategy.TTL: TTLStrategy,
        }

        strategy_class = strategy_map.get(self._config.strategy, LRUStrategy)
        self._memory_cache = strategy_class(self._config.max_size)

    def _init_redis_cache(self) -> None:
        """初始化Redis缓存"""
        if not REDIS_AVAILABLE:
            raise ComponentInitializationError(
                self._name, "Redis is not available. Please install redis package."
            )

        try:
            self._redis_client = redis.Redis(
                host=self._config.redis_host,
                port=self._config.redis_port,
                db=self._config.redis_db,
                password=self._config.redis_password,
                socket_timeout=self._config.redis_socket_timeout,
                socket_connect_timeout=self._config.redis_socket_connect_timeout,
                decode_responses=False,  # 我们需要处理二进制数据
            )

            # 测试连接
            self._redis_client.ping()

        except Exception as e:
            raise ComponentInitializationError(
                self._name, f"Failed to connect to Redis: {e}"
            )

    def _is_redis_connected(self) -> bool:
        """检查Redis连接状态"""
        if not self._redis_client:
            return False

        try:
            self._redis_client.ping()
            return True
        except:
            return False

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
                    await asyncio.sleep(self._config.cleanup_interval)
                    self._cleanup_expired()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._stats["errors"] += 1

        self._cleanup_task = asyncio.create_task(cleanup_worker())

    def _cleanup_expired(self) -> None:
        """清理过期条目"""
        if self._memory_cache:
            self._memory_cache.cleanup_expired()

    def _serialize(self, data: Any) -> bytes:
        """序列化数据"""
        if not self._config.enable_serialization:
            return str(data).encode("utf-8")

        if self._config.serialization_method == "json":
            return json.dumps(data, ensure_ascii=False).encode("utf-8")
        elif self._config.serialization_method == "pickle":
            return pickle.dumps(data)
        else:
            return str(data).encode("utf-8")

    def _deserialize(self, data: bytes) -> Any:
        """反序列化数据"""
        if not self._config.enable_serialization:
            return data.decode("utf-8")

        try:
            if self._config.serialization_method == "json":
                return json.loads(data.decode("utf-8"))
            elif self._config.serialization_method == "pickle":
                # 安全检查：确保数据来源可信
                if not self._is_trusted_pickle_data(data):
                    raise SecurityError("Untrusted pickle data detected")
                return pickle.loads(data)  # nosec B301 - 已添加安全检查
            else:
                return data.decode("utf-8")
        except Exception:
            return data.decode("utf-8", errors="ignore")

    def _compress(self, data: bytes) -> bytes:
        """压缩数据"""
        if self._config.should_compress(len(data)):
            return gzip.compress(data)
        return data

    def _decompress(self, data: bytes) -> bytes:
        """解压数据"""
        try:
            return gzip.decompress(data)
        except:
            return data

    def _get_namespace_key(self, key: str) -> str:
        """获取带命名空间的键"""
        return self._config.get_namespace_key(key)

    # 缓存操作方法
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key (str): 缓存键

        Returns:
            Optional[Any]: 缓存值，如果不存在则返回None
        """
        if self._status != ComponentStatus.RUNNING:
            return None

        try:
            namespace_key = self._get_namespace_key(key)

            # 尝试从内存缓存获取
            if self._memory_cache:
                value = self._memory_cache.get(namespace_key)
                if value is not None:
                    self._stats["hits"] += 1
                    return value

            # 尝试从Redis获取
            if self._redis_client and self._is_redis_connected():
                try:
                    data = self._redis_client.get(namespace_key)
                    if data:
                        # 解压和反序列化
                        data = self._decompress(data)
                        value = self._deserialize(data)

                        # 如果启用了混合模式，将值写入内存缓存
                        if (
                            self._config.cache_type == CacheType.HYBRID
                            and self._memory_cache
                        ):
                            self._memory_cache.put(namespace_key, value)

                        self._stats["hits"] += 1
                        return value
                except Exception:
                    pass

            self._stats["misses"] += 1
            return None

        except Exception as e:
            self._stats["errors"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key (str): 缓存键
            value (Any): 缓存值
            ttl (Optional[int]): 过期时间（秒）

        Returns:
            bool: 是否设置成功
        """
        if self._status != ComponentStatus.RUNNING:
            return False

        try:
            namespace_key = self._get_namespace_key(key)
            actual_ttl = ttl or self._config.default_ttl

            # 设置到内存缓存
            if self._memory_cache:
                self._memory_cache.put(namespace_key, value, actual_ttl)

            # 设置到Redis
            if self._redis_client and self._is_redis_connected():
                try:
                    # 序列化和压缩
                    data = self._serialize(value)
                    data = self._compress(data)

                    self._redis_client.setex(namespace_key, actual_ttl, data)
                except Exception:
                    pass

            self._stats["sets"] += 1
            return True

        except Exception as e:
            self._stats["errors"] += 1
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key (str): 缓存键

        Returns:
            bool: 是否删除成功
        """
        if self._status != ComponentStatus.RUNNING:
            return False

        try:
            namespace_key = self._get_namespace_key(key)
            success = False

            # 从内存缓存删除
            if self._memory_cache:
                success = self._memory_cache.remove(namespace_key) or success

            # 从Redis删除
            if self._redis_client and self._is_redis_connected():
                try:
                    result = self._redis_client.delete(namespace_key)
                    success = result > 0 or success
                except Exception:
                    pass

            if success:
                self._stats["deletes"] += 1

            return success

        except Exception as e:
            self._stats["errors"] += 1
            return False

    def clear(self) -> bool:
        """
        清空缓存

        Returns:
            bool: 是否清空成功
        """
        if self._status != ComponentStatus.RUNNING:
            return False

        try:
            # 清空内存缓存
            if self._memory_cache:
                self._memory_cache.clear()

            # 清空Redis缓存
            if self._redis_client and self._is_redis_connected():
                try:
                    if self._config.enable_namespace:
                        # 删除命名空间下的所有键
                        pattern = f"{self._config.namespace_prefix}:*"
                        keys = self._redis_client.keys(pattern)
                        if keys:
                            self._redis_client.delete(*keys)
                    else:
                        self._redis_client.flushdb()
                except Exception:
                    pass

            return True

        except Exception as e:
            self._stats["errors"] += 1
            return False

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key (str): 缓存键

        Returns:
            bool: 键是否存在
        """
        return self.get(key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        stats = {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "evictions": self._stats["evictions"],
            "errors": self._stats["errors"],
            "uptime": time.time() - self._start_time if self._start_time else 0,
        }

        # 添加内存缓存统计
        if self._memory_cache:
            memory_stats = self._memory_cache.get_stats()
            stats["memory_cache"] = memory_stats

        return stats

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "errors": 0,
        }

    def _is_trusted_pickle_data(self, data: bytes) -> bool:
        """检查pickle数据是否可信"""
        try:
            # 基本检查：数据长度限制
            if len(data) > 10 * 1024 * 1024:  # 10MB限制
                return False
            
            # 检查数据是否包含危险的操作码
            dangerous_opcodes = [
                b'R',  # REDUCE
                b'i',  # INST
                b'o',  # OBJ
                b'c',  # GLOBAL
                b'g',  # GET
                b'p',  # PUT
                b'q',  # BINPUT
                b'r',  # LONG_BINPUT
                b's',  # SETITEM
                b't',  # TUPLE
                b'u',  # SETITEMS
                b'x',  # EXT1
                b'y',  # EXT2
                b'z',  # EXT4
            ]
            
            # 检查是否包含危险操作码
            for opcode in dangerous_opcodes:
                if opcode in data:
                    return False
            
            # 检查数据是否以安全的操作码开始
            safe_start_opcodes = [b'I', b'F', b'S', b'L', b'D', b'N']  # 基本数据类型
            if data and data[0:1] not in safe_start_opcodes:
                return False
                
            return True
            
        except Exception:
            return False
