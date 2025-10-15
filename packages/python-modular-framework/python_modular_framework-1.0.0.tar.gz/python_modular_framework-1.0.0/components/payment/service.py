"""
支付服务实现（优化版）
- 继承BaseService基类
- 使用ExtendedBaseRepository
- 提供支付管理的核心业务逻辑
- 支持多种支付方式和支付流程
- 集成数据库存储

主要功能：
- 支付创建和管理
- 支付流程处理
- 退款管理
- 支付统计
- 数据库持久化

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

try:
    from components.common.service import BaseService, ServiceConfig
    from components.common.database.repository import ExtendedBaseRepository
    from .repository import PaymentRepository, RefundRepository
    from sqlalchemy.orm import Session
    REPOSITORY_AVAILABLE = True
except ImportError:
    REPOSITORY_AVAILABLE = False
    BaseService = None
    ServiceConfig = None
    ExtendedBaseRepository = None
    PaymentRepository = None
    RefundRepository = None
    Session = None

from .models import (
    PaymentModel,
    PaymentCreate,
    RefundRequest,
    PaymentStats,
    PaymentStatus,
    PaymentMethod,
)
from .interfaces import PaymentServiceInterface, PaymentError, PaymentNotFoundError


class PaymentServiceConfig(ServiceConfig):
    """
    支付服务配置
    
    继承ServiceConfig，添加支付服务特定的配置项。
    """
    
    def __init__(self, **kwargs):
        """
        初始化支付服务配置
        
        Args:
            **kwargs: 配置参数
        """
        # 设置默认配置
        default_config = {
            'payment_timeout': kwargs.get('payment_timeout', 1800),  # 30分钟
            'refund_timeout': kwargs.get('refund_timeout', 86400),   # 24小时
            'max_payment_amount': kwargs.get('max_payment_amount', 100000),  # 最大支付金额
            'min_payment_amount': kwargs.get('min_payment_amount', 0.01),    # 最小支付金额
            'supported_currencies': kwargs.get('supported_currencies', ['CNY', 'USD', 'EUR']),
            'auto_refund_enabled': kwargs.get('auto_refund_enabled', False),
            'webhook_retry_times': kwargs.get('webhook_retry_times', 3),
        }
        
        # 合并用户配置
        default_config.update(kwargs)
        super().__init__(**default_config)
    
    def _validate_config(self) -> None:
        """
        验证配置参数
        
        Raises:
            ValueError: 配置参数无效
        """
        if self._config['max_payment_amount'] <= 0:
            raise ValueError("最大支付金额必须大于0")
        
        if self._config['min_payment_amount'] < 0:
            raise ValueError("最小支付金额不能小于0")
        
        if self._config['max_payment_amount'] <= self._config['min_payment_amount']:
            raise ValueError("最大支付金额必须大于最小支付金额")
        
        if not self._config['supported_currencies']:
            raise ValueError("必须支持至少一种货币")


class OptimizedPaymentService(BaseService, PaymentServiceInterface):
    """
    支付服务（优化版）

    继承BaseService，提供支付管理的核心业务逻辑，包括支付创建、
    支付流程处理、退款管理等功能。仅支持数据库存储。
    """

    def __init__(
        self, 
        supported_methods: List[PaymentMethod], 
        session: Session,
        config: Optional[PaymentServiceConfig] = None
    ):
        """
        初始化支付服务

        Args:
            supported_methods (List[PaymentMethod]): 支持的支付方式
            session (Session): 数据库会话
            config (Optional[PaymentServiceConfig]): 服务配置
        """
        # 初始化配置
        self._payment_config = config or PaymentServiceConfig()
        
        # 初始化基类
        super().__init__(session, self._payment_config)
        
        self.supported_methods = supported_methods

        # 支付提供商配置
        self._provider_configs = {
            PaymentMethod.ALIPAY: {
                "app_id": self._payment_config.get("alipay_app_id", ""),
                "private_key": self._payment_config.get("alipay_private_key", ""),
                "public_key": self._payment_config.get("alipay_public_key", ""),
            },
            PaymentMethod.WECHAT: {
                "app_id": self._payment_config.get("wechat_app_id", ""),
                "mch_id": self._payment_config.get("wechat_mch_id", ""),
                "api_key": self._payment_config.get("wechat_api_key", ""),
            },
        }

    def _initialize_components(self) -> None:
        """初始化服务特定的组件"""
        self._payment_repo = PaymentRepository(self._session)
        self._refund_repo = RefundRepository(self._session)

    def _on_start(self) -> None:
        """服务启动时的钩子方法"""
        self._logger.info("支付服务启动，开始初始化支付提供商配置")

    def _on_stop(self) -> None:
        """服务停止时的钩子方法"""
        self._logger.info("支付服务停止，清理支付提供商连接")

    def create_payment(self, payment_data: PaymentCreate) -> PaymentModel:
        """
        创建支付

        Args:
            payment_data (PaymentCreate): 支付创建数据

        Returns:
            PaymentModel: 创建的支付模型

        Raises:
            PaymentError: 支付创建失败
        """
        self._log_operation("create_payment", order_id=payment_data.order_id, amount=payment_data.amount)
        
        try:
            # 验证支付方式是否支持
            if payment_data.payment_method not in self.supported_methods:
                raise PaymentError(f"不支持的支付方式: {payment_data.payment_method}")

            # 验证支付金额
            self._validate_payment_amount(payment_data.amount)

            # 验证货币是否支持
            if payment_data.currency not in self._payment_config.get('supported_currencies', []):
                raise PaymentError(f"不支持的货币: {payment_data.currency}")

            # 创建支付记录
            payment_table = self._payment_repo.create({
                'order_id': payment_data.order_id,
                'user_id': payment_data.user_id,
                'amount': payment_data.amount,
                'currency': payment_data.currency,
                'payment_method': payment_data.payment_method.value,
                'payment_provider': self._get_provider_name(payment_data.payment_method),
                'status': PaymentStatus.PENDING.value,
                'description': payment_data.description,
                'expired_at': datetime.utcnow() + timedelta(seconds=self._payment_config.get('payment_timeout')),
            })

            return payment_table.to_pydantic(PaymentModel)

        except Exception as e:
            self._handle_error(e, "create_payment", order_id=payment_data.order_id)
            if isinstance(e, PaymentError):
                raise
            raise PaymentError(f"创建支付失败: {e}")

    def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        """
        根据ID获取支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Optional[PaymentModel]: 支付模型，如果不存在则返回None
        """
        payment_table = self._payment_repo.get_by_id(payment_id)
        return payment_table.to_pydantic(PaymentModel) if payment_table else None

    def get_payment_by_order_id(self, order_id: str) -> Optional[PaymentModel]:
        """
        根据订单ID获取支付

        Args:
            order_id (str): 订单ID

        Returns:
            Optional[PaymentModel]: 支付模型，如果不存在则返回None
        """
        payment_table = self._payment_repo.get_by_order_id(order_id)
        return payment_table.to_pydantic(PaymentModel) if payment_table else None

    def update_payment_status(
        self, 
        payment_id: int, 
        status: PaymentStatus,
        provider_transaction_id: Optional[str] = None
    ) -> bool:
        """
        更新支付状态

        Args:
            payment_id (int): 支付ID
            status (PaymentStatus): 新状态
            provider_transaction_id (Optional[str]): 第三方交易ID

        Returns:
            bool: 是否更新成功
        """
        self._log_operation("update_payment_status", payment_id=payment_id, status=status.value)
        
        try:
            paid_at = datetime.utcnow() if status == PaymentStatus.SUCCESS else None
            return self._payment_repo.update_status(
                payment_id, status, provider_transaction_id, paid_at
            )
        except Exception as e:
            self._handle_error(e, "update_payment_status", payment_id=payment_id, status=status.value)
            return False

    def process_payment(self, payment_id: int) -> Dict[str, Any]:
        """
        处理支付

        Args:
            payment_id (int): 支付ID

        Returns:
            Dict[str, Any]: 支付处理结果
        """
        self._log_operation("process_payment", payment_id=payment_id)
        
        try:
            payment = self.get_payment_by_id(payment_id)
            if not payment:
                raise PaymentNotFoundError(f"支付记录不存在: {payment_id}")

            if payment.status != PaymentStatus.PENDING:
                raise PaymentError(f"支付状态不正确: {payment.status}")

            # 检查支付是否过期
            if payment.expired_at and payment.expired_at < datetime.utcnow():
                raise PaymentError("支付已过期")

            # 模拟支付处理
            provider_name = self._get_provider_name(payment.payment_method)
            transaction_id = f"{provider_name}_{uuid.uuid4().hex[:16]}"

            # 更新支付状态
            success = self.update_payment_status(
                payment_id, 
                PaymentStatus.SUCCESS,
                transaction_id
            )

            if success:
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "status": PaymentStatus.SUCCESS.value,
                    "message": "支付成功"
                }
            else:
                return {
                    "success": False,
                    "message": "支付处理失败"
                }

        except Exception as e:
            self._handle_error(e, "process_payment", payment_id=payment_id)
            return {
                "success": False,
                "message": f"支付处理异常: {e}"
            }

    def refund_payment(self, refund_request: RefundRequest) -> Dict[str, Any]:
        """
        退款处理

        Args:
            refund_request (RefundRequest): 退款请求

        Returns:
            Dict[str, Any]: 退款处理结果
        """
        self._log_operation("refund_payment", payment_id=refund_request.payment_id)
        
        try:
            payment = self.get_payment_by_id(refund_request.payment_id)
            if not payment:
                raise PaymentNotFoundError(f"支付记录不存在: {refund_request.payment_id}")

            if payment.status != PaymentStatus.SUCCESS:
                raise PaymentError(f"只有成功的支付才能退款: {payment.status}")

            # 检查退款金额
            refund_amount = refund_request.refund_amount or payment.amount
            if refund_amount > payment.amount:
                raise PaymentError("退款金额不能超过支付金额")

            # 检查是否可以退款
            if not self._refund_repo.can_refund(payment.id, refund_amount):
                raise PaymentError("退款金额超过可退款额度")

            # 创建退款记录
            refund_table = self._refund_repo.create({
                'payment_id': payment.id,
                'user_id': payment.user_id,
                'amount': refund_amount,
                'currency': payment.currency,
                'reason': refund_request.reason,
                'status': 'pending',
            })

            # 模拟退款处理
            refund_id = f"refund_{uuid.uuid4().hex[:16]}"
            success = self._refund_repo.update_status(
                refund_table.id, 
                'success',
                refund_id,
                datetime.utcnow()
            )

            if success:
                return {
                    "success": True,
                    "refund_id": refund_id,
                    "amount": float(refund_amount),
                    "message": "退款成功"
                }
            else:
                return {
                    "success": False,
                    "message": "退款处理失败"
                }

        except Exception as e:
            self._handle_error(e, "refund_payment", payment_id=refund_request.payment_id)
            return {
                "success": False,
                "message": f"退款处理异常: {e}"
            }

    def get_payment_stats(self, user_id: Optional[int] = None) -> PaymentStats:
        """
        获取支付统计

        Args:
            user_id (Optional[int]): 用户ID，如果提供则只统计该用户的支付

        Returns:
            PaymentStats: 支付统计信息
        """
        try:
            stats = self._payment_repo.get_payment_stats(user_id)
            
            return PaymentStats(
                total_payments=stats['total_payments'],
                total_amount=Decimal(str(stats['total_amount'])),
                success_payments=stats['status_stats'].get('success', {}).get('count', 0),
                success_amount=Decimal(str(stats['status_stats'].get('success', {}).get('amount', 0))),
                failed_payments=stats['status_stats'].get('failed', {}).get('count', 0),
                pending_payments=stats['status_stats'].get('pending', {}).get('count', 0),
                refunded_payments=0,  # 需要实现
                refunded_amount=Decimal('0'),  # 需要实现
                payments_by_method=stats['method_stats'],
                payments_by_status=stats['status_stats'],
            )
        except Exception as e:
            self._handle_error(e, "get_payment_stats", user_id=user_id)
            return PaymentStats(
                total_payments=0,
                total_amount=Decimal('0'),
                success_payments=0,
                success_amount=Decimal('0'),
                failed_payments=0,
                pending_payments=0,
                refunded_payments=0,
                refunded_amount=Decimal('0'),
                payments_by_method={},
                payments_by_status={},
            )

    def get_user_payments(self, user_id: int, limit: int = 20, offset: int = 0) -> List[PaymentModel]:
        """
        获取用户支付列表

        Args:
            user_id (int): 用户ID
            limit (int): 限制数量
            offset (int): 偏移量

        Returns:
            List[PaymentModel]: 支付列表
        """
        try:
            payment_tables = self._payment_repo.list_by_user(user_id, limit, offset)
            return [payment.to_pydantic(PaymentModel) for payment in payment_tables]
        except Exception as e:
            self._handle_error(e, "get_user_payments", user_id=user_id)
            return []

    def get_pending_payments(self, limit: int = 20, offset: int = 0) -> List[PaymentModel]:
        """
        获取待处理支付列表

        Args:
            limit (int): 限制数量
            offset (int): 偏移量

        Returns:
            List[PaymentModel]: 支付列表
        """
        try:
            payment_tables = self._payment_repo.list_by_status(PaymentStatus.PENDING, limit, offset)
            return [payment.to_pydantic(PaymentModel) for payment in payment_tables]
        except Exception as e:
            self._handle_error(e, "get_pending_payments")
            return []

    def get_expired_payments(self) -> List[PaymentModel]:
        """
        获取过期支付列表

        Returns:
            List[PaymentModel]: 支付列表
        """
        try:
            payment_tables = self._payment_repo.list_expired_payments()
            return [payment.to_pydantic(PaymentModel) for payment in payment_tables]
        except Exception as e:
            self._handle_error(e, "get_expired_payments")
            return []

    def cancel_payment(self, payment_id: int) -> bool:
        """
        取消支付

        Args:
            payment_id (int): 支付ID

        Returns:
            bool: 是否取消成功
        """
        self._log_operation("cancel_payment", payment_id=payment_id)
        
        try:
            payment = self.get_payment_by_id(payment_id)
            if not payment:
                return False

            if payment.status != PaymentStatus.PENDING:
                return False

            return self.update_payment_status(payment_id, PaymentStatus.CANCELLED)
        except Exception as e:
            self._handle_error(e, "cancel_payment", payment_id=payment_id)
            return False

    def search_payments(
        self,
        user_id: Optional[int] = None,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[PaymentModel]:
        """
        搜索支付记录

        Args:
            user_id (Optional[int]): 用户ID
            status (Optional[PaymentStatus]): 支付状态
            payment_method (Optional[PaymentMethod]): 支付方式
            start_date (Optional[datetime]): 开始日期
            end_date (Optional[datetime]): 结束日期
            min_amount (Optional[Decimal]): 最小金额
            max_amount (Optional[Decimal]): 最大金额
            limit (int): 限制数量
            offset (int): 偏移量

        Returns:
            List[PaymentModel]: 支付列表
        """
        try:
            payment_tables = self._payment_repo.search_payments(
                user_id=user_id,
                status=status,
                payment_method=payment_method,
                start_date=start_date,
                end_date=end_date,
                min_amount=min_amount,
                max_amount=max_amount,
                limit=limit,
                offset=offset
            )
            return [payment.to_pydantic(PaymentModel) for payment in payment_tables]
        except Exception as e:
            self._handle_error(e, "search_payments")
            return []

    def _get_provider_name(self, payment_method: PaymentMethod) -> str:
        """
        获取支付提供商名称

        Args:
            payment_method (PaymentMethod): 支付方式

        Returns:
            str: 提供商名称
        """
        provider_map = {
            PaymentMethod.ALIPAY: "alipay",
            PaymentMethod.WECHAT: "wechat",
            PaymentMethod.UNIONPAY: "unionpay",
            PaymentMethod.BANK_CARD: "bank_card",
            PaymentMethod.PAYPAL: "paypal",
            PaymentMethod.STRIPE: "stripe",
        }
        return provider_map.get(payment_method, "unknown")

    def _validate_payment_amount(self, amount: Decimal) -> None:
        """
        验证支付金额

        Args:
            amount (Decimal): 支付金额

        Raises:
            PaymentError: 金额无效
        """
        min_amount = Decimal(str(self._payment_config.get('min_payment_amount', 0.01)))
        max_amount = Decimal(str(self._payment_config.get('max_payment_amount', 100000)))

        if amount < min_amount:
            raise PaymentError(f"支付金额不能小于{min_amount}")
        
        if amount > max_amount:
            raise PaymentError(f"支付金额不能大于{max_amount}")
