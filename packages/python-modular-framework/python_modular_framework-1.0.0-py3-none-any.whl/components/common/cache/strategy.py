"""
缓存策略实现
- 提供多种缓存淘汰策略
- 支持LRU、LFU、FIFO等策略
- 提供统一的策略接口

主要功能：
- LRU策略（最近最少使用）
- LFU策略（最少使用频率）
- FIFO策略（先进先出）
- TTL策略（基于时间过期）

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from collections import OrderedDict, defaultdict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[int] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class CacheStrategy(ABC):
    """
    缓存策略抽象基类

    定义缓存策略的标准接口，包括添加、获取、删除等操作。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化缓存策略

        Args:
            max_size (int): 最大缓存大小
        """
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key (str): 缓存键

        Returns:
            Optional[Any]: 缓存值，如果不存在或过期则返回None
        """

    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        添加缓存条目

        Args:
            key (str): 缓存键
            value (Any): 缓存值
            ttl (Optional[int]): 过期时间（秒）
        """

    @abstractmethod
    def remove(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key (str): 缓存键

        Returns:
            bool: 是否成功删除
        """

    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""

    @abstractmethod
    def evict(self) -> Optional[str]:
        """
        淘汰缓存条目

        Returns:
            Optional[str]: 被淘汰的键，如果没有可淘汰的则返回None
        """

    def size(self) -> int:
        """
        获取缓存大小

        Returns:
            int: 缓存条目数量
        """
        return len(self.cache)

    def is_full(self) -> bool:
        """
        检查缓存是否已满

        Returns:
            bool: 是否已满
        """
        return len(self.cache) >= self.max_size

    def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            int: 清理的条目数量
        """
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_access = sum(entry.access_count for entry in self.cache.values())
        avg_access = total_access / len(self.cache) if self.cache else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "usage_ratio": len(self.cache) / self.max_size,
            "total_access": total_access,
            "avg_access": avg_access,
            "strategy": self.__class__.__name__,
        }


class LRUStrategy(CacheStrategy):
    """
    LRU（最近最少使用）缓存策略

    当缓存满时，淘汰最近最少使用的条目。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化LRU策略

        Args:
            max_size (int): 最大缓存大小
        """
        super().__init__(max_size)
        self.access_order = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.is_expired():
            self.remove(key)
            return None

        # 更新访问时间和计数
        entry.last_accessed = time.time()
        entry.access_count += 1

        # 更新访问顺序
        if key in self.access_order:
            self.access_order.move_to_end(key)
        else:
            self.access_order[key] = True

        return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """添加缓存条目"""
        current_time = time.time()

        # 如果键已存在，更新值
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.last_accessed = current_time
            entry.access_count += 1
            entry.ttl = ttl
            self.access_order.move_to_end(key)
            return

        # 如果缓存已满，淘汰最久未使用的条目
        if self.is_full():
            self.evict()

        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            ttl=ttl,
        )
        self.cache[key] = entry
        self.access_order[key] = True

    def remove(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.pop(key, None)
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()

    def evict(self) -> Optional[str]:
        """淘汰最久未使用的条目"""
        if not self.access_order:
            return None

        # 获取最久未使用的键
        oldest_key = next(iter(self.access_order))
        self.remove(oldest_key)
        return oldest_key


class LFUStrategy(CacheStrategy):
    """
    LFU（最少使用频率）缓存策略

    当缓存满时，淘汰使用频率最低的条目。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化LFU策略

        Args:
            max_size (int): 最大缓存大小
        """
        super().__init__(max_size)
        self.frequency_map = defaultdict(int)
        self.frequency_groups = defaultdict(OrderedDict)
        self.min_frequency = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.is_expired():
            self.remove(key)
            return None

        # 更新访问时间和计数
        entry.last_accessed = time.time()
        entry.access_count += 1

        # 更新频率
        old_freq = self.frequency_map[key]
        new_freq = old_freq + 1
        self.frequency_map[key] = new_freq

        # 从旧频率组移除
        if key in self.frequency_groups[old_freq]:
            del self.frequency_groups[old_freq][key]
            if not self.frequency_groups[old_freq] and old_freq == self.min_frequency:
                self.min_frequency += 1

        # 添加到新频率组
        self.frequency_groups[new_freq][key] = True

        return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """添加缓存条目"""
        current_time = time.time()

        # 如果键已存在，更新值
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.last_accessed = current_time
            entry.access_count += 1
            entry.ttl = ttl

            # 更新频率
            old_freq = self.frequency_map[key]
            new_freq = old_freq + 1
            self.frequency_map[key] = new_freq

            # 从旧频率组移除
            if key in self.frequency_groups[old_freq]:
                del self.frequency_groups[old_freq][key]
                if (
                    not self.frequency_groups[old_freq]
                    and old_freq == self.min_frequency
                ):
                    self.min_frequency += 1

            # 添加到新频率组
            self.frequency_groups[new_freq][key] = True
            return

        # 如果缓存已满，淘汰频率最低的条目
        if self.is_full():
            self.evict()

        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            ttl=ttl,
        )
        self.cache[key] = entry
        self.frequency_map[key] = 1
        self.frequency_groups[1][key] = True
        self.min_frequency = 1

    def remove(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            freq = self.frequency_map[key]
            del self.cache[key]
            del self.frequency_map[key]

            if key in self.frequency_groups[freq]:
                del self.frequency_groups[freq][key]
                if not self.frequency_groups[freq] and freq == self.min_frequency:
                    # 更新最小频率
                    for f in range(freq + 1, max(self.frequency_groups.keys()) + 1):
                        if self.frequency_groups[f]:
                            self.min_frequency = f
                            break

            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.frequency_map.clear()
        self.frequency_groups.clear()
        self.min_frequency = 0

    def evict(self) -> Optional[str]:
        """淘汰频率最低的条目"""
        if not self.frequency_groups[self.min_frequency]:
            return None

        # 获取频率最低的键（FIFO）
        evict_key = next(iter(self.frequency_groups[self.min_frequency]))
        self.remove(evict_key)
        return evict_key


class FIFOStrategy(CacheStrategy):
    """
    FIFO（先进先出）缓存策略

    当缓存满时，淘汰最早添加的条目。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化FIFO策略

        Args:
            max_size (int): 最大缓存大小
        """
        super().__init__(max_size)
        self.insertion_order = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.is_expired():
            self.remove(key)
            return None

        # 更新访问时间和计数
        entry.last_accessed = time.time()
        entry.access_count += 1

        return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """添加缓存条目"""
        current_time = time.time()

        # 如果键已存在，更新值
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.last_accessed = current_time
            entry.access_count += 1
            entry.ttl = ttl
            return

        # 如果缓存已满，淘汰最早添加的条目
        if self.is_full():
            self.evict()

        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            ttl=ttl,
        )
        self.cache[key] = entry
        self.insertion_order[key] = True

    def remove(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.insertion_order.pop(key, None)
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.insertion_order.clear()

    def evict(self) -> Optional[str]:
        """淘汰最早添加的条目"""
        if not self.insertion_order:
            return None

        # 获取最早添加的键
        oldest_key = next(iter(self.insertion_order))
        self.remove(oldest_key)
        return oldest_key


class TTLStrategy(CacheStrategy):
    """
    TTL（基于时间过期）缓存策略

    基于条目的过期时间进行淘汰，过期条目会被自动清理。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化TTL策略

        Args:
            max_size (int): 最大缓存大小
        """
        super().__init__(max_size)
        self.expiration_times = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.is_expired():
            self.remove(key)
            return None

        # 更新访问时间和计数
        entry.last_accessed = time.time()
        entry.access_count += 1

        return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """添加缓存条目"""
        current_time = time.time()

        # 如果键已存在，更新值
        if key in self.cache:
            entry = self.cache[key]
            entry.value = value
            entry.last_accessed = current_time
            entry.access_count += 1
            entry.ttl = ttl
            if ttl:
                self.expiration_times[key] = current_time + ttl
            return

        # 如果缓存已满，清理过期条目
        if self.is_full():
            self.cleanup_expired()
            # 如果清理后仍然满，淘汰最旧的条目
            if self.is_full():
                self.evict()

        # 添加新条目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            ttl=ttl,
        )
        self.cache[key] = entry
        if ttl:
            self.expiration_times[key] = current_time + ttl

    def remove(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.expiration_times.pop(key, None)
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.expiration_times.clear()

    def evict(self) -> Optional[str]:
        """淘汰最旧的条目"""
        if not self.cache:
            return None

        # 找到最旧的条目
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        self.remove(oldest_key)
        return oldest_key

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        current_time = time.time()
        expired_keys = []

        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self.remove(key)

        return len(expired_keys)
