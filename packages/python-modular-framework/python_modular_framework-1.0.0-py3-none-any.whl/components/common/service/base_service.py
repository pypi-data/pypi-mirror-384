"""
基础服务类
- 提供服务的通用功能和生命周期管理
- 抽象服务层的公共实现
- 提供统一的错误处理和配置管理

主要类：
- BaseService: 服务基类
- ServiceConfig: 服务配置基类

功能：
- 服务生命周期管理
- 数据库会话管理
- 配置管理
- 错误处理
- 日志记录

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime
import logging

try:
    from sqlalchemy.orm import Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Session = None

T = TypeVar('T')


class ServiceConfig:
    """
    服务配置基类
    
    提供服务的通用配置管理功能。
    """
    
    def __init__(self, **kwargs):
        """
        初始化服务配置
        
        Args:
            **kwargs: 配置参数
        """
        self._config = kwargs
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        验证配置参数
        
        Raises:
            ValueError: 配置参数无效
        """
        # 子类可以重写此方法进行特定验证
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key (str): 配置键
            default (Any): 默认值
        
        Returns:
            Any: 配置值
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key (str): 配置键
            value (Any): 配置值
        """
        self._config[key] = value
    
    def update(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config (Dict[str, Any]): 新配置
        """
        self._config.update(config)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self._config.copy()


class BaseService(ABC, Generic[T]):
    """
    服务基类
    
    提供服务的通用功能和生命周期管理。
    """
    
    def __init__(
        self,
        session: Session,
        config: Optional[ServiceConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化服务
        
        Args:
            session (Session): 数据库会话
            config (Optional[ServiceConfig]): 服务配置
            logger (Optional[logging.Logger]): 日志记录器
        """
        if not SQLALCHEMY_AVAILABLE or session is None:
            raise ValueError("数据库会话是必需的，请确保SQLAlchemy已安装并提供了有效的数据库会话")
        
        self._session = session
        self._config = config or ServiceConfig()
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._running = False
        self._started_at: Optional[datetime] = None
        self._stopped_at: Optional[datetime] = None
        
        # 初始化服务特定的组件
        self._initialize_components()
    
    @abstractmethod
    def _initialize_components(self) -> None:
        """
        初始化服务特定的组件
        
        子类必须实现此方法来初始化特定的Repository、缓存等组件。
        """
    
    def start(self) -> None:
        """
        启动服务
        
        执行服务启动逻辑，包括初始化检查、资源分配等。
        """
        if self._running:
            self._logger.warning(f"{self.__class__.__name__} 已经在运行中")
            return
        
        try:
            self._logger.info(f"正在启动 {self.__class__.__name__}")
            self._on_start()
            self._running = True
            self._started_at = datetime.utcnow()
            self._logger.info(f"{self.__class__.__name__} 启动成功")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__} 启动失败: {e}")
            raise
    
    def stop(self) -> None:
        """
        停止服务
        
        执行服务停止逻辑，包括资源清理、连接关闭等。
        """
        if not self._running:
            self._logger.warning(f"{self.__class__.__name__} 已经停止")
            return
        
        try:
            self._logger.info(f"正在停止 {self.__class__.__name__}")
            self._on_stop()
            self._running = False
            self._stopped_at = datetime.utcnow()
            self._logger.info(f"{self.__class__.__name__} 停止成功")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__} 停止失败: {e}")
            raise
    
    def is_running(self) -> bool:
        """
        检查服务是否运行中
        
        Returns:
            bool: 服务是否运行中
        """
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        return {
            "service_name": self.__class__.__name__,
            "is_running": self._running,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "stopped_at": self._stopped_at.isoformat() if self._stopped_at else None,
            "uptime_seconds": (
                (datetime.utcnow() - self._started_at).total_seconds()
                if self._started_at and self._running else 0
            ),
            "config": self._config.to_dict()
        }
    
    def _on_start(self) -> None:
        """
        服务启动时的钩子方法
        
        子类可以重写此方法执行特定的启动逻辑。
        """
    
    def _on_stop(self) -> None:
        """
        服务停止时的钩子方法
        
        子类可以重写此方法执行特定的停止逻辑。
        """
    
    def _validate_required_config(self, required_keys: list) -> None:
        """
        验证必需的配置项
        
        Args:
            required_keys (list): 必需的配置键列表
        
        Raises:
            ValueError: 缺少必需的配置项
        """
        missing_keys = []
        for key in required_keys:
            if key not in self._config._config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_keys)}")
    
    def _log_operation(self, operation: str, **kwargs) -> None:
        """
        记录操作日志
        
        Args:
            operation (str): 操作名称
            **kwargs: 操作参数
        """
        self._logger.info(f"执行操作: {operation}, 参数: {kwargs}")
    
    def _handle_error(self, error: Exception, operation: str, **kwargs) -> None:
        """
        处理错误
        
        Args:
            error (Exception): 错误对象
            operation (str): 操作名称
            **kwargs: 操作参数
        """
        self._logger.error(f"操作失败: {operation}, 参数: {kwargs}, 错误: {error}")
    
    @property
    def session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            Session: 数据库会话
        """
        return self._session
    
    @property
    def config(self) -> ServiceConfig:
        """
        获取服务配置
        
        Returns:
            ServiceConfig: 服务配置
        """
        return self._config
    
    @property
    def logger(self) -> logging.Logger:
        """
        获取日志记录器
        
        Returns:
            logging.Logger: 日志记录器
        """
        return self._logger


class ServiceError(Exception):
    """服务异常基类"""
    
    def __init__(self, message: str, service_name: str = None, details: Optional[Dict[str, Any]] = None):
        """
        初始化服务异常
        
        Args:
            message (str): 错误消息
            service_name (str): 服务名称
            details (Optional[Dict[str, Any]]): 错误详情
        """
        self.service_name = service_name
        self.details = details or {}
        super().__init__(message)


class ServiceNotRunningError(ServiceError):
    """服务未运行异常"""


class ServiceConfigurationError(ServiceError):
    """服务配置错误异常"""
