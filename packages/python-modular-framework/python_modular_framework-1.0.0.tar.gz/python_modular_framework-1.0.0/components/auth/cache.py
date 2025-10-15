"""
权限认证缓存管理
- 提供Redis缓存支持
- 缓存用户权限和角色信息
- 实现缓存失效策略

主要类：
- AuthCacheManager: 权限认证缓存管理器

功能：
- 用户权限缓存
- 用户角色缓存
- JWT令牌验证缓存
- 缓存失效管理

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import json
from typing import List, Optional, Dict, Any, Union

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class AuthCacheManager:
    """
    权限认证缓存管理器
    
    使用Redis缓存用户权限、角色和令牌验证结果。
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        key_prefix: str = "auth:",
        default_ttl: int = 1800  # 30分钟
    ):
        """
        初始化缓存管理器
        
        Args:
            redis_client: Redis客户端实例
            key_prefix: 缓存键前缀
            default_ttl: 默认TTL（秒）
        """
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.enabled = REDIS_AVAILABLE and redis_client is not None
    
    def _make_key(self, key_type: str, identifier: Union[str, int]) -> str:
        """
        生成缓存键
        
        Args:
            key_type: 键类型
            identifier: 标识符
        
        Returns:
            str: 完整的缓存键
        """
        return f"{self.key_prefix}{key_type}:{identifier}"
    
    def _serialize(self, data: Any) -> str:
        """
        序列化数据
        
        Args:
            data: 要序列化的数据
        
        Returns:
            str: 序列化后的字符串
        """
        if isinstance(data, (dict, list)):
            return json.dumps(data, default=str)
        return str(data)
    
    def _deserialize(self, data: str) -> Any:
        """
        反序列化数据
        
        Args:
            data: 要反序列化的字符串
        
        Returns:
            Any: 反序列化后的数据
        """
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），None使用默认值
        
        Returns:
            bool: 是否设置成功
        """
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = self._serialize(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存值，如果不存在则返回None
        """
        if not self.enabled:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return self._deserialize(data)
            return None
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否删除成功
        """
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的缓存
        
        Args:
            pattern: 键模式
        
        Returns:
            int: 删除的键数量
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    # 用户权限缓存
    def cache_user_permissions(self, user_id: int, permissions: List[Dict[str, Any]], ttl: int = 1800) -> bool:
        """
        缓存用户权限
        
        Args:
            user_id: 用户ID
            permissions: 权限列表
            ttl: TTL（秒）
        
        Returns:
            bool: 是否缓存成功
        """
        key = self._make_key("user_permissions", user_id)
        return self.set(key, permissions, ttl)
    
    def get_user_permissions(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        获取用户权限缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            Optional[List[Dict[str, Any]]]: 权限列表，如果不存在则返回None
        """
        key = self._make_key("user_permissions", user_id)
        return self.get(key)
    
    def invalidate_user_permissions(self, user_id: int) -> bool:
        """
        失效用户权限缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否失效成功
        """
        key = self._make_key("user_permissions", user_id)
        return self.delete(key)
    
    # 用户角色缓存
    def cache_user_roles(self, user_id: int, roles: List[Dict[str, Any]], ttl: int = 3600) -> bool:
        """
        缓存用户角色
        
        Args:
            user_id: 用户ID
            roles: 角色列表
            ttl: TTL（秒）
        
        Returns:
            bool: 是否缓存成功
        """
        key = self._make_key("user_roles", user_id)
        return self.set(key, roles, ttl)
    
    def get_user_roles(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        获取用户角色缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            Optional[List[Dict[str, Any]]]: 角色列表，如果不存在则返回None
        """
        key = self._make_key("user_roles", user_id)
        return self.get(key)
    
    def invalidate_user_roles(self, user_id: int) -> bool:
        """
        失效用户角色缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否失效成功
        """
        key = self._make_key("user_roles", user_id)
        return self.delete(key)
    
    # 权限检查缓存
    def cache_permission_check(
        self, 
        user_id: int, 
        resource: str, 
        action: str, 
        result: bool, 
        ttl: int = 300
    ) -> bool:
        """
        缓存权限检查结果
        
        Args:
            user_id: 用户ID
            resource: 资源名称
            action: 权限动作
            result: 检查结果
            ttl: TTL（秒）
        
        Returns:
            bool: 是否缓存成功
        """
        key = self._make_key("permission_check", f"{user_id}:{resource}:{action}")
        return self.set(key, result, ttl)
    
    def get_permission_check(self, user_id: int, resource: str, action: str) -> Optional[bool]:
        """
        获取权限检查缓存
        
        Args:
            user_id: 用户ID
            resource: 资源名称
            action: 权限动作
        
        Returns:
            Optional[bool]: 检查结果，如果不存在则返回None
        """
        key = self._make_key("permission_check", f"{user_id}:{resource}:{action}")
        return self.get(key)
    
    def invalidate_permission_check(self, user_id: int, resource: str, action: str) -> bool:
        """
        失效权限检查缓存
        
        Args:
            user_id: 用户ID
            resource: 资源名称
            action: 权限动作
        
        Returns:
            bool: 是否失效成功
        """
        key = self._make_key("permission_check", f"{user_id}:{resource}:{action}")
        return self.delete(key)
    
    # JWT令牌验证缓存
    def cache_token_validation(self, token: str, payload: Dict[str, Any], ttl: int = 300) -> bool:
        """
        缓存JWT令牌验证结果
        
        Args:
            token: 令牌字符串
            payload: 令牌载荷
            ttl: TTL（秒）
        
        Returns:
            bool: 是否缓存成功
        """
        # 使用令牌的哈希值作为键，避免存储完整令牌
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = self._make_key("token_validation", token_hash)
        return self.set(key, payload, ttl)
    
    def get_token_validation(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取JWT令牌验证缓存
        
        Args:
            token: 令牌字符串
        
        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，如果不存在则返回None
        """
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = self._make_key("token_validation", token_hash)
        return self.get(key)
    
    def invalidate_token_validation(self, token: str) -> bool:
        """
        失效JWT令牌验证缓存
        
        Args:
            token: 令牌字符串
        
        Returns:
            bool: 是否失效成功
        """
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        key = self._make_key("token_validation", token_hash)
        return self.delete(key)
    
    # 批量失效
    def invalidate_user_cache(self, user_id: int) -> int:
        """
        失效用户的所有缓存
        
        Args:
            user_id: 用户ID
        
        Returns:
            int: 失效的缓存数量
        """
        patterns = [
            f"{self.key_prefix}user_permissions:{user_id}",
            f"{self.key_prefix}user_roles:{user_id}",
            f"{self.key_prefix}permission_check:{user_id}:*",
        ]
        
        count = 0
        for pattern in patterns:
            count += self.delete_pattern(pattern)
        
        return count
    
    def invalidate_all_cache(self) -> int:
        """
        失效所有权限认证缓存
        
        Returns:
            int: 失效的缓存数量
        """
        pattern = f"{self.key_prefix}*"
        return self.delete_pattern(pattern)
    
    # 缓存统计
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except Exception:
            return {"enabled": True, "error": "Failed to get stats"}


class NoOpCacheManager:
    """
    空操作缓存管理器
    
    当Redis不可用时使用，所有操作都返回默认值。
    """
    
    def __init__(self):
        self.enabled = False
    
    def __getattr__(self, name):
        """所有方法都返回默认值"""
        if name.startswith('cache_'):
            return lambda *args, **kwargs: False
        elif name.startswith('get_'):
            return lambda *args, **kwargs: None
        elif name.startswith('invalidate_'):
            return lambda *args, **kwargs: True
        elif name.startswith('delete'):
            return lambda *args, **kwargs: 0
        else:
            return lambda *args, **kwargs: None


def create_cache_manager(
    redis_url: Optional[str] = None,
    redis_client: Optional[Any] = None,
    **kwargs
) -> Union[AuthCacheManager, NoOpCacheManager]:
    """
    创建缓存管理器
    
    Args:
        redis_url: Redis连接URL
        redis_client: Redis客户端实例
        **kwargs: 其他参数
    
    Returns:
        Union[AuthCacheManager, NoOpCacheManager]: 缓存管理器实例
    """
    if not REDIS_AVAILABLE:
        return NoOpCacheManager()
    
    if redis_client:
        return AuthCacheManager(redis_client=redis_client, **kwargs)
    
    if redis_url:
        try:
            client = redis.from_url(redis_url)
            # 测试连接
            client.ping()
            return AuthCacheManager(redis_client=client, **kwargs)
        except Exception:
            return NoOpCacheManager()
    
    return NoOpCacheManager()
