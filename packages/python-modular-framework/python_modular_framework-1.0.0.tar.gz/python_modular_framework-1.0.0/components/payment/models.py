"""
支付数据模型
- 定义支付相关的数据模型
- 支持多种支付方式
- 提供支付流程管理
- 集成数据库存储

主要模型：
- PaymentModel: 支付模型（Pydantic）
- PaymentCreate: 支付创建模型（Pydantic）
- PaymentUpdate: 支付更新模型（Pydantic）
- PaymentMethod: 支付方式模型（Pydantic）
- PaymentTable: 支付表模型（SQLAlchemy）
- RefundTable: 退款表模型（SQLAlchemy）

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

try:
    from components.common.database.models import BaseModel as DBBaseModel
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    DBBaseModel = None


class PaymentStatus(str, Enum):
    """支付状态枚举"""

    PENDING = "pending"  # 待支付
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 支付成功
    FAILED = "failed"  # 支付失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款
    PARTIAL_REFUND = "partial_refund"  # 部分退款


class PaymentMethod(str, Enum):
    """支付方式枚举"""

    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信支付
    UNIONPAY = "unionpay"  # 银联支付
    BANK_CARD = "bank_card"  # 银行卡
    PAYPAL = "paypal"  # PayPal
    STRIPE = "stripe"  # Stripe
    CASH = "cash"  # 现金
    CREDIT = "credit"  # 信用支付


class RefundStatus(str, Enum):
    """退款状态枚举"""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 退款成功
    FAILED = "failed"  # 退款失败
    CANCELLED = "cancelled"  # 已取消


class PaymentType(str, Enum):
    """支付类型枚举"""

    PURCHASE = "purchase"  # 购买
    RECHARGE = "recharge"  # 充值
    WITHDRAW = "withdraw"  # 提现
    REFUND = "refund"  # 退款
    TRANSFER = "transfer"  # 转账
    COMMISSION = "commission"  # 佣金


class PaymentModel(BaseModel):
    """
    支付模型

    定义支付的基本信息和属性。
    """

    id: Optional[int] = Field(default=None, description="支付ID")
    order_id: str = Field(..., min_length=1, max_length=100, description="订单ID")
    user_id: int = Field(..., description="用户ID")
    amount: Decimal = Field(..., ge=0, description="支付金额")
    currency: str = Field(default="CNY", max_length=3, description="货币类型")
    payment_method: PaymentMethod = Field(..., description="支付方式")
    payment_type: PaymentType = Field(..., description="支付类型")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="支付状态")

    # 支付详情
    description: Optional[str] = Field(
        default=None, max_length=500, description="支付描述"
    )
    external_id: Optional[str] = Field(
        default=None, max_length=100, description="外部支付ID"
    )
    transaction_id: Optional[str] = Field(
        default=None, max_length=100, description="交易ID"
    )

    # 时间信息
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    paid_at: Optional[datetime] = Field(default=None, description="支付时间")
    expired_at: Optional[datetime] = Field(default=None, description="过期时间")

    # 额外信息
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    callback_url: Optional[str] = Field(default=None, description="回调URL")
    return_url: Optional[str] = Field(default=None, description="返回URL")

    # 退款信息
    refund_amount: Decimal = Field(default=Decimal("0"), ge=0, description="退款金额")
    refund_reason: Optional[str] = Field(
        default=None, max_length=500, description="退款原因"
    )
    refunded_at: Optional[datetime] = Field(default=None, description="退款时间")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """验证支付金额"""
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """验证货币类型"""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, v):
        """验证订单ID"""
        if not v.strip():
            raise ValueError("Order ID cannot be empty")
        return v.strip()

    class Config:
        """模型配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat(), Decimal: lambda v: str(v)}


class PaymentCreate(BaseModel):
    """
    支付创建模型

    用于创建新支付时的数据验证。
    """

    order_id: str = Field(..., min_length=1, max_length=100, description="订单ID")
    user_id: int = Field(..., description="用户ID")
    amount: Decimal = Field(..., ge=0, description="支付金额")
    currency: str = Field(default="CNY", max_length=3, description="货币类型")
    payment_method: PaymentMethod = Field(..., description="支付方式")
    payment_type: PaymentType = Field(..., description="支付类型")
    description: Optional[str] = Field(
        default=None, max_length=500, description="支付描述"
    )
    callback_url: Optional[str] = Field(default=None, description="回调URL")
    return_url: Optional[str] = Field(default=None, description="返回URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    expired_at: Optional[datetime] = Field(default=None, description="过期时间")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """验证支付金额"""
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """验证货币类型"""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, v):
        """验证订单ID"""
        if not v.strip():
            raise ValueError("Order ID cannot be empty")
        return v.strip()


class PaymentUpdate(BaseModel):
    """
    支付更新模型

    用于更新支付信息时的数据验证。
    """

    status: Optional[PaymentStatus] = Field(default=None, description="支付状态")
    external_id: Optional[str] = Field(
        default=None, max_length=100, description="外部支付ID"
    )
    transaction_id: Optional[str] = Field(
        default=None, max_length=100, description="交易ID"
    )
    paid_at: Optional[datetime] = Field(default=None, description="支付时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    refund_amount: Optional[Decimal] = Field(default=None, ge=0, description="退款金额")
    refund_reason: Optional[str] = Field(
        default=None, max_length=500, description="退款原因"
    )
    refunded_at: Optional[datetime] = Field(default=None, description="退款时间")


class PaymentQuery(BaseModel):
    """
    支付查询模型

    用于支付查询时的参数。
    """

    user_id: Optional[int] = Field(default=None, description="用户ID")
    order_id: Optional[str] = Field(default=None, description="订单ID")
    status: Optional[PaymentStatus] = Field(default=None, description="支付状态")
    payment_method: Optional[PaymentMethod] = Field(
        default=None, description="支付方式"
    )
    payment_type: Optional[PaymentType] = Field(default=None, description="支付类型")
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """模型配置"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class RefundRequest(BaseModel):
    """
    退款请求模型

    用于退款请求时的数据验证。
    """

    payment_id: int = Field(..., description="支付ID")
    refund_amount: Optional[Decimal] = Field(default=None, ge=0, description="退款金额")
    reason: str = Field(..., min_length=1, max_length=500, description="退款原因")
    notify_url: Optional[str] = Field(default=None, description="通知URL")

    @field_validator("refund_amount")
    @classmethod
    def validate_refund_amount(cls, v):
        """验证退款金额"""
        if v is not None and v <= 0:
            raise ValueError("Refund amount must be positive")
        return v


class PaymentCallback(BaseModel):
    """
    支付回调模型

    用于处理支付回调时的数据验证。
    """

    payment_id: int = Field(..., description="支付ID")
    external_id: str = Field(..., description="外部支付ID")
    transaction_id: Optional[str] = Field(default=None, description="交易ID")
    status: PaymentStatus = Field(..., description="支付状态")
    amount: Decimal = Field(..., ge=0, description="支付金额")
    paid_at: Optional[datetime] = Field(default=None, description="支付时间")
    signature: Optional[str] = Field(default=None, description="签名")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """验证支付金额"""
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class PaymentStats(BaseModel):
    """
    支付统计模型

    用于返回支付统计信息。
    """

    total_payments: int = Field(..., description="总支付数")
    total_amount: Decimal = Field(..., description="总支付金额")
    success_payments: int = Field(..., description="成功支付数")
    success_amount: Decimal = Field(..., description="成功支付金额")
    failed_payments: int = Field(..., description="失败支付数")
    pending_payments: int = Field(..., description="待支付数")
    refunded_payments: int = Field(..., description="已退款数")
    refunded_amount: Decimal = Field(..., description="退款金额")
    payments_by_method: Dict[str, int] = Field(
        ..., description="按支付方式分组的支付数"
    )
    payments_by_status: Dict[str, int] = Field(..., description="按状态分组的支付数")


# SQLAlchemy数据库表模型
if SQLALCHEMY_AVAILABLE:
    class PaymentTable(DBBaseModel):
        """
        支付数据库表模型
        
        对应数据库中的payments表。
        """
        
        __tablename__ = 'payments'
        
        # 基本信息
        order_id = Column(String(100), nullable=False, index=True)
        user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
        
        # 支付信息
        amount = Column(Numeric(10, 2), nullable=False)
        currency = Column(String(3), nullable=False, default='CNY')
        payment_method = Column(String(50), nullable=False, index=True)
        payment_provider = Column(String(50), nullable=False, index=True)
        
        # 状态信息
        status = Column(String(20), nullable=False, default=PaymentStatus.PENDING.value, index=True)
        provider_transaction_id = Column(String(200), nullable=True, index=True)
        
        # 时间信息
        paid_at = Column(DateTime, nullable=True)
        expired_at = Column(DateTime, nullable=True)
        
        # 元数据
        metadata_json = Column(Text, nullable=True)
        description = Column(Text, nullable=True)
        
        # 关系
        refunds = relationship("RefundTable", back_populates="payment")
        
        # 索引
        __table_args__ = (
            Index('idx_payment_order', 'order_id'),
            Index('idx_payment_user', 'user_id'),
            Index('idx_payment_status', 'status'),
            Index('idx_payment_method', 'payment_method'),
            Index('idx_payment_provider', 'payment_provider'),
            Index('idx_payment_provider_tx', 'provider_transaction_id'),
            Index('idx_payment_created_at', 'created_at'),
        )
        
        def to_pydantic(self) -> 'PaymentModel':
            """
            转换为Pydantic模型
            
            Returns:
                PaymentModel: Pydantic支付模型
            """
            return PaymentModel(
                id=self.id,
                order_id=self.order_id,
                user_id=self.user_id,
                amount=self.amount,
                currency=self.currency,
                payment_method=PaymentMethod(self.payment_method),
                payment_provider=self.payment_provider,
                status=PaymentStatus(self.status),
                provider_transaction_id=self.provider_transaction_id,
                paid_at=self.paid_at,
                expired_at=self.expired_at,
                created_at=self.created_at,
                updated_at=self.updated_at,
                metadata=eval(self.metadata_json) if self.metadata_json else {},
                description=self.description,
            )

    class RefundTable(DBBaseModel):
        """
        退款数据库表模型
        
        对应数据库中的refunds表。
        """
        
        __tablename__ = 'refunds'
        
        # 关联信息
        payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False, index=True)
        user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
        
        # 退款信息
        amount = Column(Numeric(10, 2), nullable=False)
        currency = Column(String(3), nullable=False, default='CNY')
        reason = Column(Text, nullable=True)
        
        # 状态信息
        status = Column(String(20), nullable=False, default=RefundStatus.PENDING.value, index=True)
        provider_refund_id = Column(String(200), nullable=True, index=True)
        
        # 时间信息
        processed_at = Column(DateTime, nullable=True)
        
        # 元数据
        metadata_json = Column(Text, nullable=True)
        
        # 关系
        payment = relationship("PaymentTable", back_populates="refunds")
        
        # 索引
        __table_args__ = (
            Index('idx_refund_payment', 'payment_id'),
            Index('idx_refund_user', 'user_id'),
            Index('idx_refund_status', 'status'),
            Index('idx_refund_provider', 'provider_refund_id'),
            Index('idx_refund_created_at', 'created_at'),
        )
        
        def to_pydantic(self) -> 'RefundModel':
            """
            转换为Pydantic模型
            
            Returns:
                RefundModel: Pydantic退款模型
            """
            return RefundModel(
                id=self.id,
                payment_id=self.payment_id,
                user_id=self.user_id,
                amount=self.amount,
                currency=self.currency,
                reason=self.reason,
                status=RefundStatus(self.status),
                provider_refund_id=self.provider_refund_id,
                processed_at=self.processed_at,
                created_at=self.created_at,
                updated_at=self.updated_at,
                metadata=eval(self.metadata_json) if self.metadata_json else {},
            )
else:
    PaymentTable = None
    RefundTable = None

    class Config:
        """模型配置"""

        json_encoders = {Decimal: lambda v: str(v)}
