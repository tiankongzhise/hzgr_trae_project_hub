"""日志管理模块"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger as loguru_logger

from ..config import get_settings

# 全局日志配置状态
_logging_configured = False
_loggers: Dict[str, Any] = {}


class InterceptHandler(logging.Handler):
    """将标准logging重定向到loguru"""
    
    def emit(self, record: logging.LogRecord) -> None:
        # 获取对应的loguru级别
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # 查找调用者
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """设置日志配置"""
    global _logging_configured
    
    if _logging_configured:
        return
    
    settings = get_settings()
    
    # 移除默认的loguru处理器
    loguru_logger.remove()
    
    # 控制台输出
    loguru_logger.add(
        sys.stdout,
        format=settings.logging.format,
        level=settings.logging.level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 文件输出 - 普通日志
    log_file = settings.log_dir / f"{settings.app_name}.log"
    loguru_logger.add(
        log_file,
        format=settings.logging.format,
        level=settings.logging.level,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        backtrace=True,
        diagnose=True,
    )
    
    # 文件输出 - 错误日志
    error_log_file = settings.log_dir / f"{settings.app_name}_error.log"
    loguru_logger.add(
        error_log_file,
        format=settings.logging.format,
        level="ERROR",
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
        backtrace=True,
        diagnose=True,
    )
    
    # 数据库写入失败专用日志
    db_error_log_file = settings.log_dir / f"db_write_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    loguru_logger.add(
        db_error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="ERROR",
        filter=lambda record: "db_write_error" in record["extra"],
        rotation="1 day",
        retention="90 days",
        compression="gz",
    )
    
    # 性能监控日志
    performance_log_file = settings.log_dir / f"{settings.app_name}_performance.log"
    loguru_logger.add(
        performance_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        filter=lambda record: "performance" in record["extra"],
        rotation="1 day",
        retention="30 days",
        compression="gz",
    )
    
    # 拦截标准logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 设置第三方库的日志级别
    for logger_name in ["httpx", "sqlalchemy", "asyncpg"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    _logging_configured = True
    loguru_logger.info(f"日志系统已初始化，日志目录: {settings.log_dir}")


def get_logger(name: str) -> Any:
    """获取日志记录器"""
    global _loggers
    
    if not _logging_configured:
        setup_logging()
    
    if name not in _loggers:
        # 为每个模块创建带有上下文的logger
        _loggers[name] = loguru_logger.bind(name=name)
    
    return _loggers[name]


def log_db_write_error(error_message: str, **kwargs) -> None:
    """记录数据库写入错误"""
    logger = get_logger("database")
    logger.bind(db_write_error=True).error(f"数据库写入失败: {error_message}", **kwargs)


def log_performance(func_name: str, execution_time: float, **kwargs) -> None:
    """记录性能信息"""
    logger = get_logger("performance")
    logger.bind(performance=True).info(
        f"函数 {func_name} 执行时间: {execution_time:.4f}秒",
        **kwargs
    )


def log_function_call(
    func_name: str,
    start_time: datetime,
    end_time: datetime,
    args: Optional[tuple] = None,
    kwargs_dict: Optional[dict] = None,
    result: Optional[Any] = None,
    error: Optional[Exception] = None,
) -> None:
    """记录函数调用信息"""
    logger = get_logger("function_calls")
    execution_time = (end_time - start_time).total_seconds()
    
    log_data = {
        "function": func_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "execution_time": execution_time,
    }
    
    settings = get_settings()
    
    if settings.monitoring.log_parameters and args:
        log_data["args"] = str(args)
    
    if settings.monitoring.log_parameters and kwargs_dict:
        log_data["kwargs"] = str(kwargs_dict)
    
    if settings.monitoring.log_return_values and result is not None:
        log_data["result"] = str(result)[:500]  # 限制长度
    
    if error:
        log_data["error"] = str(error)
        logger.bind(performance=True).error(
            f"函数 {func_name} 执行失败: {error}",
            **log_data
        )
    else:
        logger.bind(performance=True).info(
            f"函数 {func_name} 执行完成，耗时 {execution_time:.4f}秒",
            **log_data
        )


class DatabaseErrorLogger:
    """数据库错误日志记录器"""
    
    def __init__(self):
        self.logger = get_logger("database_errors")
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        data: Optional[dict] = None,
        retry_count: int = 0,
    ) -> None:
        """记录数据库操作错误"""
        error_data = {
            "session_id": self.session_id,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
        }
        
        if data:
            error_data["data"] = str(data)[:1000]  # 限制长度
        
        self.logger.bind(db_write_error=True).error(
            f"数据库操作失败 [{operation}]: {error}",
            **error_data
        )
    
    def log_retry(
        self,
        operation: str,
        retry_count: int,
        max_retries: int,
        delay: float,
    ) -> None:
        """记录重试信息"""
        self.logger.bind(db_write_error=True).warning(
            f"数据库操作重试 [{operation}]: 第{retry_count}/{max_retries}次，延迟{delay}秒",
            session_id=self.session_id,
            operation=operation,
            retry_count=retry_count,
            max_retries=max_retries,
            delay=delay,
        )
    
    def log_final_failure(
        self,
        operation: str,
        final_error: Exception,
        total_retries: int,
    ) -> None:
        """记录最终失败信息"""
        self.logger.bind(db_write_error=True).critical(
            f"数据库操作最终失败 [{operation}]: {final_error}，已重试{total_retries}次",
            session_id=self.session_id,
            operation=operation,
            final_error=str(final_error),
            total_retries=total_retries,
        )
