"""
数据库模型基类
- 提供通用的数据库模型基类
- 自动管理时间戳字段
- 提供通用的序列化方法

主要类：
- BaseModel: 数据库模型基类
- TimestampMixin: 时间戳混入类

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# 创建基类
Base = declarative_base()


class TimestampMixin:
    """
    时间戳混入类
    
    为模型自动添加创建时间和更新时间字段。
    """
    
    @declared_attr
    def created_at(cls):
        """创建时间"""
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        """更新时间"""
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )


class BaseModel(Base, TimestampMixin):
    """
    数据库模型基类
    
    所有数据库模型的基类，提供通用的ID字段和时间戳字段。
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 处理datetime类型
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典更新模型
        
        Args:
            data (Dict[str, Any]): 要更新的数据
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"

