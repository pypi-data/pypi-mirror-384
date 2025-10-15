"""
支付组件包
- 提供支付管理功能
- 支持多种支付方式
- 提供支付流程管理
- 集成数据库存储

主要组件：
- PaymentComponent: 支付组件主类
- PaymentService: 支付服务类
- PaymentModel: 支付数据模型
- PaymentServiceInterface: 支付服务接口
- Repository: 数据访问层

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from .component import PaymentComponent
from .service import OptimizedPaymentService
from .models import (
    PaymentModel,
    PaymentCreate,
    PaymentUpdate,
    PaymentMethod,
    PaymentStatus,
    RefundStatus,
    PaymentTable,
    RefundTable,
)
from .interfaces import PaymentServiceInterface, PaymentError

# 尝试导入Repository（可能不可用）
try:
    from .repository import PaymentRepository, RefundRepository
    _repository_available = True
except ImportError:
    _repository_available = False
    PaymentRepository = None
    RefundRepository = None

__version__ = "0.1.0"
__author__ = "开发团队"

__all__ = [
    # 组件
    "PaymentComponent",
    # 服务
    "OptimizedPaymentService",
    # 接口
    "PaymentServiceInterface",
    "PaymentError",
    # 模型
    "PaymentModel",
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentMethod",
    "PaymentStatus",
    "RefundStatus",
    # 数据库表模型
    "PaymentTable",
    "RefundTable",
]

# 如果Repository可用，添加到导出列表
if _repository_available:
    __all__.extend([
        "PaymentRepository",
        "RefundRepository",
    ])
