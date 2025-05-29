"""装饰器模块"""

import asyncio
import functools
import inspect
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Union

from .logger import get_logger, log_function_call
from ..config import get_settings

F = TypeVar('F', bound=Callable[..., Any])

logger = get_logger(__name__)


def monitor_performance(
    log_args: bool = None,
    log_result: bool = None,
    log_execution_time: bool = None,
) -> Callable[[F], F]:
    """性能监控装饰器
    
    Args:
        log_args: 是否记录参数，None时使用配置文件设置
        log_result: 是否记录返回值，None时使用配置文件设置
        log_execution_time: 是否记录执行时间，None时使用配置文件设置
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            settings = get_settings()
            
            # 使用传入参数或配置文件设置
            should_log_args = log_args if log_args is not None else settings.monitoring.log_parameters
            should_log_result = log_result if log_result is not None else settings.monitoring.log_return_values
            should_log_time = log_execution_time if log_execution_time is not None else settings.monitoring.log_execution_time
            
            if not settings.monitoring.enable_performance_tracking:
                return await func(*args, **kwargs)
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = datetime.now()
            result = None
            error = None
            
            try:
                if settings.monitoring.log_function_calls:
                    logger.info(f"开始执行函数: {func_name}")
                
                result = await func(*args, **kwargs)
                return result
            
            except Exception as e:
                error = e
                logger.error(f"函数执行异常: {func_name} - {e}")
                raise
            
            finally:
                end_time = datetime.now()
                
                if should_log_time or settings.monitoring.log_function_calls:
                    log_function_call(
                        func_name=func_name,
                        start_time=start_time,
                        end_time=end_time,
                        args=args if should_log_args else None,
                        kwargs_dict=kwargs if should_log_args else None,
                        result=result if should_log_result else None,
                        error=error,
                    )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            settings = get_settings()
            
            # 使用传入参数或配置文件设置
            should_log_args = log_args if log_args is not None else settings.monitoring.log_parameters
            should_log_result = log_result if log_result is not None else settings.monitoring.log_return_values
            should_log_time = log_execution_time if log_execution_time is not None else settings.monitoring.log_execution_time
            
            if not settings.monitoring.enable_performance_tracking:
                return func(*args, **kwargs)
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = datetime.now()
            result = None
            error = None
            
            try:
                if settings.monitoring.log_function_calls:
                    logger.info(f"开始执行函数: {func_name}")
                
                result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                error = e
                logger.error(f"函数执行异常: {func_name} - {e}")
                raise
            
            finally:
                end_time = datetime.now()
                
                if should_log_time or settings.monitoring.log_function_calls:
                    log_function_call(
                        func_name=func_name,
                        start_time=start_time,
                        end_time=end_time,
                        args=args if should_log_args else None,
                        kwargs_dict=kwargs if should_log_args else None,
                        result=result if should_log_result else None,
                        error=error,
                    )
        
        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_failure(
    max_retries: Optional[int] = None,
    delay: Optional[float] = None,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    exclude_exceptions: tuple = (),
) -> Callable[[F], F]:
    """失败重试装饰器
    
    Args:
        max_retries: 最大重试次数，None时使用配置文件设置
        delay: 重试延迟时间，None时使用配置文件设置
        backoff_factor: 退避因子，每次重试延迟时间乘以此因子
        exceptions: 需要重试的异常类型
        exclude_exceptions: 不需要重试的异常类型
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            settings = get_settings()
            
            # 使用传入参数或配置文件设置
            retries = max_retries if max_retries is not None else settings.retry.max_retries
            retry_delay = delay if delay is not None else settings.retry.retry_delay
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except exclude_exceptions as e:
                    logger.error(f"函数 {func_name} 遇到不可重试异常: {e}")
                    raise
                
                except exceptions as e:
                    if attempt == retries:
                        logger.error(f"函数 {func_name} 重试{retries}次后仍然失败: {e}")
                        raise
                    
                    current_delay = retry_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"函数 {func_name} 第{attempt + 1}次执行失败，{current_delay:.2f}秒后重试: {e}"
                    )
                    await asyncio.sleep(current_delay)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            settings = get_settings()
            
            # 使用传入参数或配置文件设置
            retries = max_retries if max_retries is not None else settings.retry.max_retries
            retry_delay = delay if delay is not None else settings.retry.retry_delay
            
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except exclude_exceptions as e:
                    logger.error(f"函数 {func_name} 遇到不可重试异常: {e}")
                    raise
                
                except exceptions as e:
                    if attempt == retries:
                        logger.error(f"函数 {func_name} 重试{retries}次后仍然失败: {e}")
                        raise
                    
                    current_delay = retry_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"函数 {func_name} 第{attempt + 1}次执行失败，{current_delay:.2f}秒后重试: {e}"
                    )
                    import time
                    time.sleep(current_delay)
        
        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def database_operation(
    operation_name: str,
    log_errors: bool = True,
    retry_on_network_error: bool = True,
) -> Callable[[F], F]:
    """数据库操作装饰器
    
    Args:
        operation_name: 操作名称
        log_errors: 是否记录错误日志
        retry_on_network_error: 是否在网络错误时重试
    """
    def decorator(func: F) -> F:
        # 定义需要重试的网络相关异常
        network_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        
        # 定义不需要重试的事务性异常
        transaction_exceptions = (
            # SQLAlchemy相关异常需要根据实际情况添加
            # IntegrityError, UniqueViolation等
        )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            from ..utils.logger import DatabaseErrorLogger
            
            error_logger = DatabaseErrorLogger()
            settings = get_settings()
            
            for attempt in range(settings.retry.max_retries + 1):
                try:
                    start_time = datetime.now()
                    result = await func(*args, **kwargs)
                    end_time = datetime.now()
                    
                    execution_time = (end_time - start_time).total_seconds()
                    logger.info(
                        f"数据库操作 [{operation_name}] 成功完成，耗时 {execution_time:.4f}秒"
                    )
                    return result
                
                except transaction_exceptions as e:
                    if log_errors:
                        error_logger.log_error(operation_name, e, kwargs)
                    logger.error(f"数据库操作 [{operation_name}] 事务性错误，不重试: {e}")
                    raise
                
                except network_exceptions as e:
                    if not retry_on_network_error:
                        if log_errors:
                            error_logger.log_error(operation_name, e, kwargs)
                        raise
                    
                    if attempt == settings.retry.max_retries:
                        if log_errors:
                            error_logger.log_final_failure(operation_name, e, attempt)
                        logger.error(f"数据库操作 [{operation_name}] 重试{attempt}次后仍然失败: {e}")
                        raise
                    
                    current_delay = settings.retry.retry_delay * (2 ** attempt)
                    if log_errors:
                        error_logger.log_retry(operation_name, attempt + 1, settings.retry.max_retries, current_delay)
                    
                    logger.warning(
                        f"数据库操作 [{operation_name}] 第{attempt + 1}次失败，{current_delay:.2f}秒后重试: {e}"
                    )
                    await asyncio.sleep(current_delay)
                
                except Exception as e:
                    if log_errors:
                        error_logger.log_error(operation_name, e, kwargs)
                    logger.error(f"数据库操作 [{operation_name}] 未知错误: {e}")
                    raise
        
        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            # 同步版本类似，这里简化处理
            return func
    
    return decorator


def cache_result(
    ttl: int = 300,  # 缓存时间（秒）
    key_func: Optional[Callable] = None,  # 自定义缓存键函数
) -> Callable[[F], F]:
    """结果缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_func: 自定义缓存键生成函数
    """
    cache = {}
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 检查缓存
            now = datetime.now().timestamp()
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if now - timestamp < ttl:
                    logger.debug(f"缓存命中: {func.__name__}")
                    return result
                else:
                    del cache[cache_key]
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, now)
            logger.debug(f"缓存存储: {func.__name__}")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 检查缓存
            now = datetime.now().timestamp()
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if now - timestamp < ttl:
                    logger.debug(f"缓存命中: {func.__name__}")
                    return result
                else:
                    del cache[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[cache_key] = (result, now)
            logger.debug(f"缓存存储: {func.__name__}")
            return result
        
        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
