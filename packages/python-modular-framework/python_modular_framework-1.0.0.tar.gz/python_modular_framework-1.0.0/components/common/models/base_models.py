"""
通用数据模型基类
- 提供通用的数据模型和接口
- 抽象数据层的公共实现
- 提供统一的模型转换和验证

主要类：
- BaseModel: 数据模型基类
- TimestampMixin: 时间戳混入类
- StatusMixin: 状态混入类
- SoftDeleteMixin: 软删除混入类

功能：
- 通用字段定义
- 模型转换方法
- 验证方法
- 序列化方法

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Any, Dict, Optional, Type, TypeVar
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel, Field

try:
    from sqlalchemy import Column, Integer, DateTime, Boolean, String, Text
    from sqlalchemy.ext.declarative import declarative_base

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = None
    Integer = None
    DateTime = None
    Boolean = None
    String = None
    Text = None
    declarative_base = None


T = TypeVar("T", bound="BaseModel")


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class TimestampMixin:
        """时间戳混入类"""

        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(
            DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
        )

    class StatusMixin:
        """状态混入类"""

        is_active = Column(Boolean, default=True, nullable=False)
        status = Column(String(50), default="active", nullable=False)

    class SoftDeleteMixin:
        """软删除混入类"""

        is_deleted = Column(Boolean, default=False, nullable=False)
        deleted_at = Column(DateTime, nullable=True)

    class BaseModel(Base, TimestampMixin, StatusMixin, SoftDeleteMixin):
        """
        数据模型基类

        提供通用的字段和方法。
        """

        __abstract__ = True

        id = Column(Integer, primary_key=True, autoincrement=True)
        description = Column(Text, nullable=True)

        def to_dict(self) -> Dict[str, Any]:
            """
            转换为字典

            Returns:
                Dict[str, Any]: 字典表示
            """
            result = {}
            for column in self.__table__.columns:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
            return result

        def to_pydantic(
            self, pydantic_model: Type[PydanticBaseModel]
        ) -> PydanticBaseModel:
            """
            转换为Pydantic模型

            Args:
                pydantic_model (Type[PydanticBaseModel]): Pydantic模型类

            Returns:
                PydanticBaseModel: Pydantic模型实例
            """
            return pydantic_model(**self.to_dict())

        def update_from_dict(self, data: Dict[str, Any]) -> None:
            """
            从字典更新字段

            Args:
                data (Dict[str, Any]): 更新数据
            """
            for key, value in data.items():
                if hasattr(self, key) and key not in ["id", "created_at"]:
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()

        def soft_delete(self) -> None:
            """软删除"""
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

        def restore(self) -> None:
            """恢复软删除"""
            self.is_deleted = False
            self.deleted_at = None
            self.updated_at = datetime.utcnow()

        def activate(self) -> None:
            """激活"""
            self.is_active = True
            self.status = "active"
            self.updated_at = datetime.utcnow()

        def deactivate(self) -> None:
            """停用"""
            self.is_active = False
            self.status = "inactive"
            self.updated_at = datetime.utcnow()

        def is_available(self) -> bool:
            """
            检查是否可用（活跃且未删除）

            Returns:
                bool: 是否可用
            """
            return self.is_active and not self.is_deleted

        def __repr__(self) -> str:
            return f"<{self.__class__.__name__}(id={self.id})>"

else:
    Base = None
    TimestampMixin = None
    StatusMixin = None
    SoftDeleteMixin = None
    BaseModel = None


class BasePydanticModel(PydanticBaseModel):
    """
    Pydantic模型基类

    提供通用的Pydantic模型功能。
    """

    class Config:
        """Pydantic配置"""

        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True


class TimestampPydanticMixin(BasePydanticModel):
    """时间戳Pydantic混入类"""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StatusPydanticMixin(BasePydanticModel):
    """状态Pydantic混入类"""

    is_active: bool = Field(default=True)
    status: str = Field(default="active")


class SoftDeletePydanticMixin(BasePydanticModel):
    """软删除Pydantic混入类"""

    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)


class BasePydanticModelWithAll(
    BasePydanticModel,
    TimestampPydanticMixin,
    StatusPydanticMixin,
    SoftDeletePydanticMixin,
):
    """
    包含所有通用字段的Pydantic模型基类
    """

    id: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)


class ModelConverter:
    """
    模型转换器

    提供SQLAlchemy模型和Pydantic模型之间的转换功能。
    """

    @staticmethod
    def sqlalchemy_to_pydantic(
        sqlalchemy_model: BaseModel, pydantic_model: Type[PydanticBaseModel]
    ) -> PydanticBaseModel:
        """
        将SQLAlchemy模型转换为Pydantic模型

        Args:
            sqlalchemy_model (BaseModel): SQLAlchemy模型实例
            pydantic_model (Type[PydanticBaseModel]): Pydantic模型类

        Returns:
            PydanticBaseModel: Pydantic模型实例
        """
        return sqlalchemy_model.to_pydantic(pydantic_model)

    @staticmethod
    def pydantic_to_dict(pydantic_model: PydanticBaseModel) -> Dict[str, Any]:
        """
        将Pydantic模型转换为字典

        Args:
            pydantic_model (PydanticBaseModel): Pydantic模型实例

        Returns:
            Dict[str, Any]: 字典表示
        """
        return pydantic_model.model_dump()

    @staticmethod
    def dict_to_pydantic(
        data: Dict[str, Any], pydantic_model: Type[PydanticBaseModel]
    ) -> PydanticBaseModel:
        """
        将字典转换为Pydantic模型

        Args:
            data (Dict[str, Any]): 字典数据
            pydantic_model (Type[PydanticBaseModel]): Pydantic模型类

        Returns:
            PydanticBaseModel: Pydantic模型实例
        """
        return pydantic_model(**data)


class ModelValidator:
    """
    模型验证器

    提供模型数据的验证功能。
    """

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
        """
        验证必需字段

        Args:
            data (Dict[str, Any]): 数据字典
            required_fields (list): 必需字段列表

        Raises:
            ValueError: 缺少必需字段
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"缺少必需字段: {', '.join(missing_fields)}")

    @staticmethod
    def validate_field_types(
        data: Dict[str, Any], field_types: Dict[str, Type]
    ) -> None:
        """
        验证字段类型

        Args:
            data (Dict[str, Any]): 数据字典
            field_types (Dict[str, Type]): 字段类型映射

        Raises:
            TypeError: 字段类型错误
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    raise TypeError(
                        f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(data[field]).__name__}"
                    )

    @staticmethod
    def validate_field_values(
        data: Dict[str, Any], field_validators: Dict[str, callable]
    ) -> None:
        """
        验证字段值

        Args:
            data (Dict[str, Any]): 数据字典
            field_validators (Dict[str, callable]): 字段验证器映射

        Raises:
            ValueError: 字段值无效
        """
        for field, validator in field_validators.items():
            if field in data and data[field] is not None:
                if not validator(data[field]):
                    raise ValueError(f"字段 '{field}' 值无效: {data[field]}")


class ModelSerializer:
    """
    模型序列化器

    提供模型的序列化和反序列化功能。
    """

    @staticmethod
    def serialize_datetime(obj: datetime) -> str:
        """
        序列化日期时间

        Args:
            obj (datetime): 日期时间对象

        Returns:
            str: ISO格式字符串
        """
        return obj.isoformat()

    @staticmethod
    def serialize_model(model: BaseModel) -> Dict[str, Any]:
        """
        序列化模型

        Args:
            model (BaseModel): 模型实例

        Returns:
            Dict[str, Any]: 序列化后的字典
        """
        result = model.to_dict()

        # 处理日期时间字段
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = ModelSerializer.serialize_datetime(value)

        return result

    @staticmethod
    def serialize_models(models: list) -> list:
        """
        序列化模型列表

        Args:
            models (list): 模型实例列表

        Returns:
            list: 序列化后的字典列表
        """
        return [ModelSerializer.serialize_model(model) for model in models]
