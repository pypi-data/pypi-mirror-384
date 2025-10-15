"""
日志组件实现
- 实现ComponentInterface接口
- 提供统一的日志管理功能
- 支持多种日志级别和输出格式

主要功能：
- 日志级别管理
- 多种输出格式
- 日志轮转
- 结构化日志
- 异步日志支持

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import logging
import logging.handlers
import asyncio
import threading
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from framework.interfaces.component import (
    ComponentInterface,
    ComponentStatus,
    ComponentInfo,
    ComponentError,
    ComponentInitializationError,
)
from .config import LoggingConfig, LogFormat
from .formatter import LoggingFormatter


class LoggingComponent(ComponentInterface):
    """
    日志组件

    提供统一的日志管理功能，支持多种日志级别、输出格式、
    日志轮转、结构化日志等特性。
    """

    def __init__(self, name: str = "logging"):
        """
        初始化日志组件

        Args:
            name (str): 组件名称
        """
        self._name = name
        self._version = "0.1.0"
        self._description = "统一日志管理组件"
        self._dependencies = []
        self._status = ComponentStatus.UNINITIALIZED
        self._config = LoggingConfig()

        # 日志器相关
        self._logger = None
        self._handlers = []
        self._formatter = None
        self._async_queue = None
        self._async_task = None
        self._shutdown_event = threading.Event()

        # 性能统计
        self._log_count = 0
        self._error_count = 0
        self._start_time = None

    @property
    def name(self) -> str:
        """获取组件名称"""
        return self._name

    @property
    def version(self) -> str:
        """获取组件版本"""
        return self._version

    @property
    def description(self) -> str:
        """获取组件描述"""
        return self._description

    @property
    def dependencies(self) -> List[str]:
        """获取组件依赖"""
        return self._dependencies

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化日志组件

        Args:
            config (Dict[str, Any]): 组件配置参数

        Raises:
            ComponentInitializationError: 初始化失败时抛出异常
        """
        try:
            self._status = ComponentStatus.INITIALIZING

            # 更新配置
            if config:
                self._config = LoggingConfig.from_dict(config)

            # 创建日志器
            self._logger = logging.getLogger(self._name)
            self._logger.setLevel(getattr(logging, self._config.level.value))

            # 清除现有处理器
            self._logger.handlers.clear()

            # 创建格式化器
            self._formatter = LoggingFormatter(
                format_type=self._config.format.value,
                custom_format=self._config.custom_format,
            )

            # 设置处理器
            self._setup_handlers()

            # 设置异步日志
            if self._config.async_enabled:
                self._setup_async_logging()

            # 设置过滤器
            self._setup_filters()

            self._status = ComponentStatus.INITIALIZED
            self._start_time = time.time()

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentInitializationError(
                self._name, f"Failed to initialize logging component: {e}"
            )

    def start(self) -> None:
        """
        启动日志组件

        Raises:
            ComponentError: 启动失败时抛出异常
        """
        if self._status != ComponentStatus.INITIALIZED:
            raise ComponentError(
                self._name, f"Cannot start component in status {self._status}"
            )

        try:
            self._status = ComponentStatus.STARTING

            # 启动异步日志任务
            if self._config.async_enabled and self._async_queue:
                self._async_task = asyncio.create_task(self._async_log_worker())

            self._status = ComponentStatus.RUNNING

            # 记录启动日志
            self.info(
                "Logging component started",
                {
                    "level": self._config.level.value,
                    "format": self._config.format.value,
                    "async_enabled": self._config.async_enabled,
                },
            )

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to start logging component: {e}")

    def stop(self) -> None:
        """
        停止日志组件

        Raises:
            ComponentError: 停止失败时抛出异常
        """
        if self._status not in [ComponentStatus.RUNNING, ComponentStatus.STARTING]:
            return

        try:
            self._status = ComponentStatus.STOPPING

            # 记录停止日志
            self.info("Logging component stopping")

            # 停止异步日志
            if self._async_task:
                self._shutdown_event.set()
                self._async_task.cancel()
                try:
                    asyncio.get_event_loop().run_until_complete(self._async_task)
                except asyncio.CancelledError:
                    pass
                self._async_task = None

            # 关闭所有处理器
            for handler in self._handlers:
                handler.close()

            self._handlers.clear()
            self._status = ComponentStatus.STOPPED

        except Exception as e:
            self._status = ComponentStatus.ERROR
            raise ComponentError(self._name, f"Failed to stop logging component: {e}")

    def get_status(self) -> ComponentStatus:
        """获取组件状态"""
        return self._status

    def get_info(self) -> ComponentInfo:
        """获取组件信息"""
        return ComponentInfo(
            name=self._name,
            version=self._version,
            description=self._description,
            dependencies=self._dependencies,
            status=self._status,
            config=self._config.to_dict(),
            metadata={
                "log_count": self._log_count,
                "error_count": self._error_count,
                "uptime": time.time() - self._start_time if self._start_time else 0,
            },
        )

    def get_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        return self._config.to_dict()

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新组件配置

        Args:
            config (Dict[str, Any]): 新的配置参数
        """
        if self._status == ComponentStatus.RUNNING:
            # 运行时更新配置需要重新初始化
            self.stop()

        new_config = LoggingConfig.from_dict(config)
        self._config = self._config.merge(new_config)

        if self._status in [ComponentStatus.INITIALIZED, ComponentStatus.STOPPED]:
            self.initialize(self._config.to_dict())

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康检查结果
        """
        health_status = {
            "status": "healthy",
            "message": "Logging component is running normally",
            "details": {
                "component_status": self._status.value,
                "log_count": self._log_count,
                "error_count": self._error_count,
                "uptime": time.time() - self._start_time if self._start_time else 0,
                "handlers_count": len(self._handlers),
                "async_enabled": self._config.async_enabled,
            },
        }

        if self._status != ComponentStatus.RUNNING:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Component is not running: {self._status.value}"

        return health_status

    def _setup_handlers(self) -> None:
        """设置日志处理器"""
        # 控制台处理器
        if self._config.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self._create_formatter())
            self._logger.addHandler(console_handler)
            self._handlers.append(console_handler)

        # 文件处理器
        if self._config.file_enabled and self._config.file_path:
            file_handler = self._create_file_handler()
            if file_handler:
                self._logger.addHandler(file_handler)
                self._handlers.append(file_handler)

    def _create_file_handler(self) -> Optional[logging.Handler]:
        """创建文件处理器"""
        try:
            file_path = Path(self._config.file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if self._config.rotation_enabled:
                # 轮转文件处理器
                max_bytes = self._config.get_file_size_bytes()
                backup_count = self._config.max_files

                handler = logging.handlers.RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes or 10 * 1024 * 1024,  # 默认10MB
                    backupCount=backup_count,
                )
            else:
                # 普通文件处理器
                handler = logging.FileHandler(file_path)

            handler.setFormatter(self._create_formatter())
            return handler

        except Exception as e:
            self._logger.error(f"Failed to create file handler: {e}")
            return None

    def _create_formatter(self) -> logging.Formatter:
        """创建日志格式化器"""
        if self._config.format == LogFormat.JSON:
            # JSON格式使用自定义格式化器
            return JSONFormatter(self._formatter)
        else:
            # 其他格式使用标准格式化器
            format_string = self._get_format_string()
            return logging.Formatter(format_string)

    def _get_format_string(self) -> str:
        """获取格式字符串"""
        if self._config.format == LogFormat.SIMPLE:
            return "%(asctime)s - %(levelname)s - %(message)s"
        elif self._config.format == LogFormat.DETAILED:
            return "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        elif self._config.format == LogFormat.CUSTOM and self._config.custom_format:
            return self._config.custom_format
        else:
            return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def _setup_async_logging(self) -> None:
        """设置异步日志"""
        self._async_queue = Queue(maxsize=self._config.buffer_size)

    def _setup_filters(self) -> None:
        """设置日志过滤器"""
        # 这里可以添加自定义过滤器

    async def _async_log_worker(self) -> None:
        """异步日志工作器"""
        while not self._shutdown_event.is_set():
            try:
                # 从队列中获取日志记录
                record = self._async_queue.get(timeout=0.1)
                self._process_log_record(record)
            except Empty:
                continue
            except Exception as e:
                print(f"Error in async log worker: {e}")

    def _process_log_record(self, record: Dict[str, Any]) -> None:
        """处理日志记录"""
        try:
            # 使用自定义格式化器格式化记录
            formatted_message = self._formatter.format(record)

            # 记录到标准日志器
            level = getattr(logging, record.get("level", "INFO"))
            self._logger.log(level, formatted_message)

            # 更新统计
            self._log_count += 1
            if record.get("level") in ["ERROR", "CRITICAL"]:
                self._error_count += 1

        except Exception as e:
            print(f"Error processing log record: {e}")

    # 日志记录方法
    def debug(
        self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> None:
        """记录调试日志"""
        self._log("DEBUG", message, context, **kwargs)

    def info(
        self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> None:
        """记录信息日志"""
        self._log("INFO", message, context, **kwargs)

    def warning(
        self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> None:
        """记录警告日志"""
        self._log("WARNING", message, context, **kwargs)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """记录错误日志"""
        self._log("ERROR", message, context, exception=exception, **kwargs)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """记录严重错误日志"""
        self._log("CRITICAL", message, context, exception=exception, **kwargs)

    def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        **kwargs,
    ) -> None:
        """
        记录日志

        Args:
            level (str): 日志级别
            message (str): 日志消息
            context (Optional[Dict[str, Any]]): 上下文信息
            exception (Optional[Exception]): 异常对象
            **kwargs: 额外参数
        """
        if self._status != ComponentStatus.RUNNING:
            return

        # 构建日志记录
        record = {
            "timestamp": datetime.now(),
            "level": level,
            "logger_name": self._name,
            "message": message,
            "context": context or {},
            "extra": kwargs,
        }

        # 添加异常信息
        if exception:
            record["exception"] = str(exception)
            if self._config.include_traceback:
                record["traceback"] = self._formatter.format_exception(
                    exception.__traceback__
                )

        # 清理敏感信息
        if self._config.structured_enabled:
            record = self._formatter.sanitize_record(record)

        # 异步或同步处理
        if self._config.async_enabled and self._async_queue:
            try:
                self._async_queue.put_nowait(record)
            except:
                # 队列满时直接处理
                self._process_log_record(record)
        else:
            self._process_log_record(record)


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""

    def __init__(self, formatter: LoggingFormatter):
        """
        初始化JSON格式化器

        Args:
            formatter (LoggingFormatter): 日志格式化器
        """
        super().__init__()
        self.formatter = formatter

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON

        Args:
            record (logging.LogRecord): 日志记录

        Returns:
            str: JSON格式的日志字符串
        """
        # 转换为字典格式
        log_dict = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        # 添加异常信息
        if record.exc_info:
            log_dict["exception"] = record.exc_text
            log_dict["traceback"] = self.formatException(record.exc_info)

        # 添加额外字段
        for key, value in record.__dict__.items():
            if key not in log_dict and not key.startswith("_"):
                log_dict[key] = value

        return self.formatter.format(log_dict)
