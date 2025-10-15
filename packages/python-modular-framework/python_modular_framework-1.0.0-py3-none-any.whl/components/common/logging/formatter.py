"""
日志格式化器
- 提供多种日志输出格式
- 支持结构化日志和自定义格式
- 支持上下文信息和异常处理

主要功能：
- 简单格式输出
- 详细格式输出
- JSON格式输出
- 自定义格式支持

作者：开发团队
创建时间：2024-01-XX
最后修改：2024-01-XX
"""

import json
import traceback
from typing import Any, Dict, Optional
from datetime import datetime


class LoggingFormatter:
    """
    日志格式化器

    提供多种日志输出格式，支持结构化日志和自定义格式。
    """

    def __init__(
        self, format_type: str = "detailed", custom_format: Optional[str] = None
    ):
        """
        初始化格式化器

        Args:
            format_type (str): 格式类型
            custom_format (Optional[str]): 自定义格式字符串
        """
        self.format_type = format_type
        self.custom_format = custom_format

    def format(self, record: Dict[str, Any]) -> str:
        """
        格式化日志记录

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            str: 格式化后的日志字符串
        """
        if self.format_type == "simple":
            return self._format_simple(record)
        elif self.format_type == "detailed":
            return self._format_detailed(record)
        elif self.format_type == "json":
            return self._format_json(record)
        elif self.format_type == "custom" and self.custom_format:
            return self._format_custom(record)
        else:
            return self._format_detailed(record)

    def _format_simple(self, record: Dict[str, Any]) -> str:
        """
        简单格式输出

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            str: 简单格式的日志字符串
        """
        timestamp = record.get("timestamp", datetime.now().isoformat())
        level = record.get("level", "INFO")
        message = record.get("message", "")

        return f"[{timestamp}] {level}: {message}"

    def _format_detailed(self, record: Dict[str, Any]) -> str:
        """
        详细格式输出

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            str: 详细格式的日志字符串
        """
        timestamp = record.get("timestamp", datetime.now().isoformat())
        level = record.get("level", "INFO")
        logger_name = record.get("logger_name", "root")
        message = record.get("message", "")

        # 构建基础信息
        formatted = f"[{timestamp}] {level} [{logger_name}]: {message}"

        # 添加上下文信息
        context = record.get("context", {})
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            formatted += f" | Context: {context_str}"

        # 添加异常信息
        exception = record.get("exception")
        if exception:
            formatted += f"\nException: {exception}"
            traceback_info = record.get("traceback")
            if traceback_info:
                formatted += f"\nTraceback:\n{traceback_info}"

        # 添加额外字段
        extra = record.get("extra", {})
        if extra:
            extra_str = ", ".join([f"{k}={v}" for k, v in extra.items()])
            formatted += f" | Extra: {extra_str}"

        return formatted

    def _format_json(self, record: Dict[str, Any]) -> str:
        """
        JSON格式输出

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            str: JSON格式的日志字符串
        """
        # 确保时间戳是字符串格式
        if "timestamp" in record and isinstance(record["timestamp"], datetime):
            record["timestamp"] = record["timestamp"].isoformat()

        # 处理异常信息
        if "exception" in record and record["exception"]:
            if hasattr(record["exception"], "__dict__"):
                record["exception"] = str(record["exception"])

        return json.dumps(record, ensure_ascii=False, default=str)

    def _format_custom(self, record: Dict[str, Any]) -> str:
        """
        自定义格式输出

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            str: 自定义格式的日志字符串
        """
        if not self.custom_format:
            return self._format_detailed(record)

        # 替换格式字符串中的占位符
        formatted = self.custom_format

        # 基础字段替换
        replacements = {
            "%(timestamp)s": record.get("timestamp", datetime.now().isoformat()),
            "%(level)s": record.get("level", "INFO"),
            "%(logger_name)s": record.get("logger_name", "root"),
            "%(message)s": record.get("message", ""),
            "%(module)s": record.get("module", ""),
            "%(function)s": record.get("function", ""),
            "%(line)s": str(record.get("line", "")),
            "%(process)s": str(record.get("process", "")),
            "%(thread)s": str(record.get("thread", "")),
        }

        for placeholder, value in replacements.items():
            formatted = formatted.replace(placeholder, str(value))

        # 处理上下文信息
        context = record.get("context", {})
        if "%(context)s" in formatted:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            formatted = formatted.replace("%(context)s", context_str)

        # 处理异常信息
        exception = record.get("exception")
        if "%(exception)s" in formatted:
            exception_str = str(exception) if exception else ""
            formatted = formatted.replace("%(exception)s", exception_str)

        # 处理堆栈信息
        traceback_info = record.get("traceback")
        if "%(traceback)s" in formatted:
            traceback_str = traceback_info if traceback_info else ""
            formatted = formatted.replace("%(traceback)s", traceback_str)

        return formatted

    def format_exception(self, exc_info: tuple) -> str:
        """
        格式化异常信息

        Args:
            exc_info (tuple): 异常信息元组

        Returns:
            str: 格式化后的异常字符串
        """
        return "".join(traceback.format_exception(*exc_info))

    def extract_context(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取上下文信息

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            Dict[str, Any]: 上下文信息字典
        """
        context = {}

        # 从记录中提取上下文信息
        for key, value in record.items():
            if key not in [
                "timestamp",
                "level",
                "logger_name",
                "message",
                "module",
                "function",
                "line",
                "process",
                "thread",
                "exception",
                "traceback",
            ]:
                context[key] = value

        return context

    def should_include_traceback(self, record: Dict[str, Any]) -> bool:
        """
        判断是否应该包含堆栈信息

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            bool: 是否应该包含堆栈信息
        """
        level = record.get("level", "INFO")
        return level in ["ERROR", "CRITICAL"]

    def sanitize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理日志记录中的敏感信息

        Args:
            record (Dict[str, Any]): 日志记录

        Returns:
            Dict[str, Any]: 清理后的日志记录
        """
        sanitized = record.copy()

        # 敏感字段列表
        sensitive_fields = ["password", "token", "secret", "key", "auth"]

        def sanitize_value(value):
            if isinstance(value, str):
                for field in sensitive_fields:
                    if field.lower() in value.lower():
                        return "***REDACTED***"
            elif isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            return value

        # 清理消息
        if "message" in sanitized:
            sanitized["message"] = sanitize_value(sanitized["message"])

        # 清理上下文
        if "context" in sanitized:
            sanitized["context"] = sanitize_value(sanitized["context"])

        # 清理额外字段
        if "extra" in sanitized:
            sanitized["extra"] = sanitize_value(sanitized["extra"])

        return sanitized
