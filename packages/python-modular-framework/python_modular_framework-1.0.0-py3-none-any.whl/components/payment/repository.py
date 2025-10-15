"""
支付Repository实现
- 实现支付数据访问层
- 提供支付和退款CRUD操作
- 实现复杂的支付查询和统计

主要类：
- PaymentRepository: 支付数据访问类
- RefundRepository: 退款数据访问类

功能：
- 支付管理（CRUD、查询、统计）
- 退款管理（CRUD、查询）
- 支付状态管理
- 支付统计查询

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

try:
    from components.common.database.repository import BaseRepository
    from .models import (
        PaymentTable, RefundTable,
        PaymentStatus, RefundStatus, PaymentMethod
    )
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    BaseRepository = None
    PaymentTable = None
    RefundTable = None


if SQLALCHEMY_AVAILABLE:
    class PaymentRepository(BaseRepository[PaymentTable]):
        """
        支付Repository
        
        提供支付数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化支付Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, PaymentTable)
        
        def get_by_order_id(self, order_id: str) -> Optional[PaymentTable]:
            """
            根据订单ID获取支付
            
            Args:
                order_id (str): 订单ID
            
            Returns:
                Optional[PaymentTable]: 支付实例，如果不存在则返回None
            """
            return self.get_by_field('order_id', order_id)
        
        def get_by_provider_transaction_id(self, provider_transaction_id: str) -> Optional[PaymentTable]:
            """
            根据第三方交易ID获取支付
            
            Args:
                provider_transaction_id (str): 第三方交易ID
            
            Returns:
                Optional[PaymentTable]: 支付实例，如果不存在则返回None
            """
            return self.get_by_field('provider_transaction_id', provider_transaction_id)
        
        def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[PaymentTable]:
            """
            获取用户的支付列表
            
            Args:
                user_id (int): 用户ID
                limit (int): 限制数量
                offset (int): 偏移量
            
            Returns:
                List[PaymentTable]: 支付列表
            """
            stmt = select(self.model_class).where(
                self.model_class.user_id == user_id
            ).order_by(desc(self.model_class.created_at)).limit(limit).offset(offset)
            
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def list_by_status(self, status: PaymentStatus, limit: int = 20, offset: int = 0) -> List[PaymentTable]:
            """
            根据状态获取支付列表
            
            Args:
                status (PaymentStatus): 支付状态
                limit (int): 限制数量
                offset (int): 偏移量
            
            Returns:
                List[PaymentTable]: 支付列表
            """
            return self.filter_by(status=status.value, limit=limit, offset=offset)
        
        def list_by_payment_method(self, payment_method: PaymentMethod, limit: int = 20, offset: int = 0) -> List[PaymentTable]:
            """
            根据支付方式获取支付列表
            
            Args:
                payment_method (PaymentMethod): 支付方式
                limit (int): 限制数量
                offset (int): 偏移量
            
            Returns:
                List[PaymentTable]: 支付列表
            """
            return self.filter_by(payment_method=payment_method.value, limit=limit, offset=offset)
        
        def list_expired_payments(self) -> List[PaymentTable]:
            """
            获取过期的支付列表
            
            Returns:
                List[PaymentTable]: 过期支付列表
            """
            stmt = select(self.model_class).where(
                and_(
                    self.model_class.status == PaymentStatus.PENDING.value,
                    self.model_class.expired_at < datetime.utcnow()
                )
            )
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def update_status(
            self, 
            payment_id: int, 
            status: PaymentStatus, 
            provider_transaction_id: Optional[str] = None,
            paid_at: Optional[datetime] = None
        ) -> bool:
            """
            更新支付状态
            
            Args:
                payment_id (int): 支付ID
                status (PaymentStatus): 新状态
                provider_transaction_id (Optional[str]): 第三方交易ID
                paid_at (Optional[datetime]): 支付时间
            
            Returns:
                bool: 是否更新成功
            """
            update_data = {'status': status.value}
            if provider_transaction_id:
                update_data['provider_transaction_id'] = provider_transaction_id
            if paid_at:
                update_data['paid_at'] = paid_at
            
            return self.update(payment_id, update_data) is not None
        
        def get_payment_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
            """
            获取支付统计信息
            
            Args:
                user_id (Optional[int]): 用户ID，如果提供则只统计该用户的支付
            
            Returns:
                Dict[str, Any]: 统计信息
            """
            query = self.session.query(self.model_class)
            if user_id:
                query = query.filter(self.model_class.user_id == user_id)
            
            # 基础统计
            total_count = query.count()
            total_amount = query.with_entities(func.sum(self.model_class.amount)).scalar() or Decimal('0')
            
            # 按状态统计
            status_stats = {}
            for status in PaymentStatus:
                count = query.filter(self.model_class.status == status.value).count()
                amount = query.filter(self.model_class.status == status.value).with_entities(
                    func.sum(self.model_class.amount)
                ).scalar() or Decimal('0')
                status_stats[status.value] = {'count': count, 'amount': float(amount)}
            
            # 按支付方式统计
            method_stats = {}
            for method in PaymentMethod:
                count = query.filter(self.model_class.payment_method == method.value).count()
                method_stats[method.value] = count
            
            return {
                'total_payments': total_count,
                'total_amount': float(total_amount),
                'status_stats': status_stats,
                'method_stats': method_stats,
            }
        
        def get_user_payment_stats(self, user_id: int) -> Dict[str, Any]:
            """
            获取用户支付统计信息
            
            Args:
                user_id (int): 用户ID
            
            Returns:
                Dict[str, Any]: 用户统计信息
            """
            return self.get_payment_stats(user_id)
        
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
        ) -> List[PaymentTable]:
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
                List[PaymentTable]: 支付列表
            """
            stmt = select(self.model_class)
            conditions = []
            
            if user_id:
                conditions.append(self.model_class.user_id == user_id)
            if status:
                conditions.append(self.model_class.status == status.value)
            if payment_method:
                conditions.append(self.model_class.payment_method == payment_method.value)
            if start_date:
                conditions.append(self.model_class.created_at >= start_date)
            if end_date:
                conditions.append(self.model_class.created_at <= end_date)
            if min_amount:
                conditions.append(self.model_class.amount >= min_amount)
            if max_amount:
                conditions.append(self.model_class.amount <= max_amount)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(desc(self.model_class.created_at)).limit(limit).offset(offset)
            
            result = self.session.execute(stmt)
            return list(result.scalars().all())

    class RefundRepository(BaseRepository[RefundTable]):
        """
        退款Repository
        
        提供退款数据的访问和管理功能。
        """
        
        def __init__(self, session: Session):
            """
            初始化退款Repository
            
            Args:
                session (Session): 数据库会话
            """
            super().__init__(session, RefundTable)
        
        def get_by_payment_id(self, payment_id: int) -> List[RefundTable]:
            """
            根据支付ID获取退款列表
            
            Args:
                payment_id (int): 支付ID
            
            Returns:
                List[RefundTable]: 退款列表
            """
            return self.filter_by(payment_id=payment_id)
        
        def get_by_provider_refund_id(self, provider_refund_id: str) -> Optional[RefundTable]:
            """
            根据第三方退款ID获取退款
            
            Args:
                provider_refund_id (str): 第三方退款ID
            
            Returns:
                Optional[RefundTable]: 退款实例，如果不存在则返回None
            """
            return self.get_by_field('provider_refund_id', provider_refund_id)
        
        def list_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[RefundTable]:
            """
            获取用户的退款列表
            
            Args:
                user_id (int): 用户ID
                limit (int): 限制数量
                offset (int): 偏移量
            
            Returns:
                List[RefundTable]: 退款列表
            """
            stmt = select(self.model_class).where(
                self.model_class.user_id == user_id
            ).order_by(desc(self.model_class.created_at)).limit(limit).offset(offset)
            
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        
        def list_by_status(self, status: RefundStatus, limit: int = 20, offset: int = 0) -> List[RefundTable]:
            """
            根据状态获取退款列表
            
            Args:
                status (RefundStatus): 退款状态
                limit (int): 限制数量
                offset (int): 偏移量
            
            Returns:
                List[RefundTable]: 退款列表
            """
            return self.filter_by(status=status.value, limit=limit, offset=offset)
        
        def update_status(
            self, 
            refund_id: int, 
            status: RefundStatus, 
            provider_refund_id: Optional[str] = None,
            processed_at: Optional[datetime] = None
        ) -> bool:
            """
            更新退款状态
            
            Args:
                refund_id (int): 退款ID
                status (RefundStatus): 新状态
                provider_refund_id (Optional[str]): 第三方退款ID
                processed_at (Optional[datetime]): 处理时间
            
            Returns:
                bool: 是否更新成功
            """
            update_data = {'status': status.value}
            if provider_refund_id:
                update_data['provider_refund_id'] = provider_refund_id
            if processed_at:
                update_data['processed_at'] = processed_at
            
            return self.update(refund_id, update_data) is not None
        
        def get_refund_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
            """
            获取退款统计信息
            
            Args:
                user_id (Optional[int]): 用户ID，如果提供则只统计该用户的退款
            
            Returns:
                Dict[str, Any]: 统计信息
            """
            query = self.session.query(self.model_class)
            if user_id:
                query = query.filter(self.model_class.user_id == user_id)
            
            # 基础统计
            total_count = query.count()
            total_amount = query.with_entities(func.sum(self.model_class.amount)).scalar() or Decimal('0')
            
            # 按状态统计
            status_stats = {}
            for status in RefundStatus:
                count = query.filter(self.model_class.status == status.value).count()
                amount = query.filter(self.model_class.status == status.value).with_entities(
                    func.sum(self.model_class.amount)
                ).scalar() or Decimal('0')
                status_stats[status.value] = {'count': count, 'amount': float(amount)}
            
            return {
                'total_refunds': total_count,
                'total_amount': float(total_amount),
                'status_stats': status_stats,
            }
        
        def get_payment_total_refunded(self, payment_id: int) -> Decimal:
            """
            获取支付的已退款总额
            
            Args:
                payment_id (int): 支付ID
            
            Returns:
                Decimal: 已退款总额
            """
            result = self.session.query(func.sum(self.model_class.amount)).filter(
                and_(
                    self.model_class.payment_id == payment_id,
                    self.model_class.status == RefundStatus.SUCCESS.value
                )
            ).scalar()
            return result or Decimal('0')
        
        def can_refund(self, payment_id: int, refund_amount: Decimal) -> bool:
            """
            检查是否可以退款
            
            Args:
                payment_id (int): 支付ID
                refund_amount (Decimal): 退款金额
            
            Returns:
                bool: 是否可以退款
            """
            # 获取支付信息
            payment_repo = PaymentRepository(self.session)
            payment = payment_repo.get_by_id(payment_id)
            if not payment or payment.status != PaymentStatus.SUCCESS:
                return False
            
            # 检查已退款金额
            already_refunded = self.get_payment_total_refunded(payment_id)
            return (already_refunded + refund_amount) <= payment.amount
else:
    PaymentRepository = None
    RefundRepository = None
