"""
数据库Repository基类
- 提供通用的CRUD操作
- 实现事务管理
- 提供查询构建器

主要类：
- BaseRepository: Repository基类
- transactional: 事务装饰器

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Callable
from contextlib import contextmanager
from functools import wraps
from datetime import datetime
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from .models import BaseModel

T = TypeVar('T', bound=BaseModel)


def transactional(func: Callable) -> Callable:
    """
    事务装饰器
    
    自动管理事务的提交和回滚。
    
    Args:
        func (Callable): 要装饰的函数
    
    Returns:
        Callable: 装饰后的函数
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'session'):
            return func(self, *args, **kwargs)
        
        try:
            result = func(self, *args, **kwargs)
            self.session.commit()
            return result
        except Exception as e:
            self.session.rollback()
            raise
    
    return wrapper


class BaseRepository(Generic[T]):
    """
    Repository基类
    
    提供通用的CRUD操作和查询功能。
    """
    
    def __init__(self, session: Session, model_class: Type[T]):
        """
        初始化Repository
        
        Args:
            session (Session): 数据库会话
            model_class (Type[T]): 模型类
        """
        self.session = session
        self.model_class = model_class
    
    @transactional
    def create(self, data: Dict[str, Any]) -> T:
        """
        创建记录
        
        Args:
            data (Dict[str, Any]): 创建数据
        
        Returns:
            T: 创建的模型实例
        """
        instance = self.model_class(**data)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        根据ID获取记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            Optional[T]: 模型实例，如果不存在则返回None
        """
        return self.session.get(self.model_class, record_id)
    
    def get_by_field(self, field_name: str, field_value: Any) -> Optional[T]:
        """
        根据字段值获取记录
        
        Args:
            field_name (str): 字段名
            field_value (Any): 字段值
        
        Returns:
            Optional[T]: 模型实例，如果不存在则返回None
        """
        stmt = select(self.model_class).where(
            getattr(self.model_class, field_name) == field_value
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def list_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        获取所有记录
        
        Args:
            limit (Optional[int]): 限制数量
            offset (Optional[int]): 偏移量
            order_by (Optional[str]): 排序字段
        
        Returns:
            List[T]: 模型实例列表
        """
        stmt = select(self.model_class)
        
        if order_by:
            if order_by.startswith('-'):
                stmt = stmt.order_by(getattr(self.model_class, order_by[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(self.model_class, order_by))
        
        if offset:
            stmt = stmt.offset(offset)
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def filter_by(self, **kwargs) -> List[T]:
        """
        根据条件过滤记录
        
        Args:
            **kwargs: 过滤条件
        
        Returns:
            List[T]: 符合条件的模型实例列表
        """
        stmt = select(self.model_class)
        
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    @transactional
    def update(self, record_id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        更新记录
        
        Args:
            record_id (int): 记录ID
            data (Dict[str, Any]): 更新数据
        
        Returns:
            Optional[T]: 更新后的模型实例，如果不存在则返回None
        """
        instance = self.get_by_id(record_id)
        if not instance:
            return None
        
        for key, value in data.items():
            if hasattr(instance, key) and key not in ['id', 'created_at']:
                setattr(instance, key, value)
        
        self.session.flush()
        self.session.refresh(instance)
        return instance
    
    @transactional
    def delete(self, record_id: int) -> bool:
        """
        删除记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            bool: 是否删除成功
        """
        instance = self.get_by_id(record_id)
        if not instance:
            return False
        
        self.session.delete(instance)
        self.session.flush()
        return True
    
    def count(self, **kwargs) -> int:
        """
        统计记录数量
        
        Args:
            **kwargs: 过滤条件
        
        Returns:
            int: 记录数量
        """
        stmt = select(self.model_class)
        
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        
        result = self.session.execute(stmt)
        return len(list(result.scalars().all()))
    
    def exists(self, record_id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            bool: 记录是否存在
        """
        return self.get_by_id(record_id) is not None
    
    @transactional
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建记录
        
        Args:
            data_list (List[Dict[str, Any]]): 创建数据列表
        
        Returns:
            List[T]: 创建的模型实例列表
        """
        instances = [self.model_class(**data) for data in data_list]
        self.session.add_all(instances)
        self.session.flush()
        
        for instance in instances:
            self.session.refresh(instance)
        
        return instances
    
    @transactional
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新记录
        
        Args:
            updates (List[Dict[str, Any]]): 更新数据列表，每项必须包含id字段
        
        Returns:
            int: 更新的记录数量
        """
        count = 0
        for update_data in updates:
            if 'id' not in update_data:
                continue
            
            record_id = update_data.pop('id')
            if self.update(record_id, update_data):
                count += 1
        
        return count
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        Yields:
            Session: 数据库会话
        """
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise


class RepositoryError(Exception):
    """Repository异常基类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message (str): 错误消息
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.details = details or {}
        super().__init__(message)


class RecordNotFoundError(RepositoryError):
    """记录未找到异常"""


class DuplicateRecordError(RepositoryError):
    """重复记录异常"""


class ExtendedBaseRepository(BaseRepository[T]):
    """
    扩展的Repository基类
    
    提供更多通用的查询和管理功能。
    """
    
    def get_by_field_list(self, field_name: str, field_values: list) -> List[T]:
        """
        根据字段值列表获取记录
        
        Args:
            field_name (str): 字段名
            field_values (list): 字段值列表
        
        Returns:
            List[T]: 模型实例列表
        """
        if not field_values:
            return []
        
        stmt = select(self.model_class).where(
            getattr(self.model_class, field_name).in_(field_values)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def get_by_multiple_fields(self, **kwargs) -> Optional[T]:
        """
        根据多个字段值获取记录
        
        Args:
            **kwargs: 字段名和值的映射
        
        Returns:
            Optional[T]: 模型实例，如果不存在则返回None
        """
        stmt = select(self.model_class)
        
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def filter_by_multiple_fields(self, **kwargs) -> List[T]:
        """
        根据多个字段值过滤记录
        
        Args:
            **kwargs: 字段名和值的映射
        
        Returns:
            List[T]: 符合条件的模型实例列表
        """
        stmt = select(self.model_class)
        
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def search_by_text(self, field_name: str, search_term: str, limit: Optional[int] = None) -> List[T]:
        """
        根据文本字段进行模糊搜索
        
        Args:
            field_name (str): 搜索字段名
            search_term (str): 搜索词
            limit (Optional[int]): 限制数量
        
        Returns:
            List[T]: 搜索结果列表
        """
        if not hasattr(self.model_class, field_name):
            return []
        
        search_pattern = f"%{search_term}%"
        stmt = select(self.model_class).where(
            getattr(self.model_class, field_name).like(search_pattern)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def search_by_multiple_text_fields(self, search_term: str, field_names: list, limit: Optional[int] = None) -> List[T]:
        """
        在多个文本字段中进行模糊搜索
        
        Args:
            search_term (str): 搜索词
            field_names (list): 搜索字段名列表
            limit (Optional[int]): 限制数量
        
        Returns:
            List[T]: 搜索结果列表
        """
        if not field_names or not search_term:
            return []
        
        search_pattern = f"%{search_term}%"
        conditions = []
        
        for field_name in field_names:
            if hasattr(self.model_class, field_name):
                conditions.append(getattr(self.model_class, field_name).like(search_pattern))
        
        if not conditions:
            return []
        
        stmt = select(self.model_class).where(or_(*conditions))
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def get_active_records(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        获取活跃记录
        
        Args:
            limit (Optional[int]): 限制数量
            offset (Optional[int]): 偏移量
        
        Returns:
            List[T]: 活跃记录列表
        """
        return self.filter_by(is_active=True, limit=limit, offset=offset)
    
    def get_inactive_records(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        获取非活跃记录
        
        Args:
            limit (Optional[int]): 限制数量
            offset (Optional[int]): 偏移量
        
        Returns:
            List[T]: 非活跃记录列表
        """
        return self.filter_by(is_active=False, limit=limit, offset=offset)
    
    def activate(self, record_id: int) -> Optional[T]:
        """
        激活记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            Optional[T]: 更新后的模型实例
        """
        return self.update(record_id, {'is_active': True})
    
    def deactivate(self, record_id: int) -> Optional[T]:
        """
        停用记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            Optional[T]: 更新后的模型实例
        """
        return self.update(record_id, {'is_active': False})
    
    def soft_delete(self, record_id: int) -> Optional[T]:
        """
        软删除记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            Optional[T]: 更新后的模型实例
        """
        return self.update(record_id, {
            'is_deleted': True,
            'deleted_at': datetime.utcnow()
        })
    
    def restore(self, record_id: int) -> Optional[T]:
        """
        恢复软删除的记录
        
        Args:
            record_id (int): 记录ID
        
        Returns:
            Optional[T]: 更新后的模型实例
        """
        return self.update(record_id, {
            'is_deleted': False,
            'deleted_at': None
        })
    
    def get_recent_records(self, days: int = 7, limit: Optional[int] = None) -> List[T]:
        """
        获取最近创建的记录
        
        Args:
            days (int): 天数
            limit (Optional[int]): 限制数量
        
        Returns:
            List[T]: 最近创建的记录列表
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(self.model_class).where(
            self.model_class.created_at >= cutoff_date
        ).order_by(self.model_class.created_at.desc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def get_updated_records(self, days: int = 7, limit: Optional[int] = None) -> List[T]:
        """
        获取最近更新的记录
        
        Args:
            days (int): 天数
            limit (Optional[int]): 限制数量
        
        Returns:
            List[T]: 最近更新的记录列表
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(self.model_class).where(
            self.model_class.updated_at >= cutoff_date
        ).order_by(self.model_class.updated_at.desc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def count_by_field(self, field_name: str, field_value: Any) -> int:
        """
        根据字段值统计记录数量
        
        Args:
            field_name (str): 字段名
            field_value (Any): 字段值
        
        Returns:
            int: 记录数量
        """
        if not hasattr(self.model_class, field_name):
            return 0
        
        stmt = select(self.model_class).where(
            getattr(self.model_class, field_name) == field_value
        )
        result = self.session.execute(stmt)
        return len(list(result.scalars().all()))
    
    def count_active(self) -> int:
        """
        统计活跃记录数量
        
        Returns:
            int: 活跃记录数量
        """
        return self.count_by_field('is_active', True)
    
    def count_inactive(self) -> int:
        """
        统计非活跃记录数量
        
        Returns:
            int: 非活跃记录数量
        """
        return self.count_by_field('is_active', False)
    
    def exists_by_field(self, field_name: str, field_value: Any) -> bool:
        """
        检查字段值是否存在
        
        Args:
            field_name (str): 字段名
            field_value (Any): 字段值
        
        Returns:
            bool: 是否存在
        """
        return self.get_by_field(field_name, field_value) is not None
    
    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        order_by: Optional[str] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        获取分页数据
        
        Args:
            page (int): 页码（从1开始）
            per_page (int): 每页数量
            order_by (Optional[str]): 排序字段
            **filters: 过滤条件
        
        Returns:
            Dict[str, Any]: 分页数据，包含items、total、pages等信息
        """
        offset = (page - 1) * per_page
        
        # 构建查询
        stmt = select(self.model_class)
        
        # 应用过滤条件
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        
        # 应用排序
        if order_by:
            if order_by.startswith('-'):
                stmt = stmt.order_by(getattr(self.model_class, order_by[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(self.model_class, order_by))
        
        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar()
        
        # 获取分页数据
        stmt = stmt.offset(offset).limit(per_page)
        result = self.session.execute(stmt)
        items = list(result.scalars().all())
        
        # 计算总页数
        pages = (total + per_page - 1) // per_page
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages
        }
