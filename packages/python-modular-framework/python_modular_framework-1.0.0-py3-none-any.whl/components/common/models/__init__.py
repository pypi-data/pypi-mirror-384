"""
通用模型模块
- 提供通用的数据模型和接口
- 抽象数据层的公共实现

主要类：
- BaseModel: 数据模型基类
- TimestampMixin: 时间戳混入类
- StatusMixin: 状态混入类
- SoftDeleteMixin: 软删除混入类
- BasePydanticModel: Pydantic模型基类
- ModelConverter: 模型转换器
- ModelValidator: 模型验证器
- ModelSerializer: 模型序列化器

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .base_models import (
    BaseModel,
    TimestampMixin,
    StatusMixin,
    SoftDeleteMixin,
    BasePydanticModel,
    TimestampPydanticMixin,
    StatusPydanticMixin,
    SoftDeletePydanticMixin,
    BasePydanticModelWithAll,
    ModelConverter,
    ModelValidator,
    ModelSerializer
)

__all__ = [
    'BaseModel',
    'TimestampMixin',
    'StatusMixin',
    'SoftDeleteMixin',
    'BasePydanticModel',
    'TimestampPydanticMixin',
    'StatusPydanticMixin',
    'SoftDeletePydanticMixin',
    'BasePydanticModelWithAll',
    'ModelConverter',
    'ModelValidator',
    'ModelSerializer'
]
