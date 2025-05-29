"""重试机制模块"""

import asyncio
import random
from typing import Any, Callable, Optional, Type, Union, Tuple
from dataclasses import dataclass
from datetime import datetime

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    exponential_backoff: bool = True


class AsyncRetry:
    """异步重试器"""
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        retry_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
        stop_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = (),
        before_sleep: Optional[Callable[[int, float], None]] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        on_final_failure: Optional[Callable[[Exception, int], None]] = None,
    ):
        """
        初始化异步重试器
        
        Args:
            config: 重试配置
            retry_on: 需要重试的异常类型
            stop_on: 不需要重试的异常类型（优先级高于retry_on）
            before_sleep: 睡眠前的回调函数
            on_retry: 重试时的回调函数
            on_final_failure: 最终失败时的回调函数
        """
        self.config = config or RetryConfig()
        self.retry_on = retry_on if isinstance(retry_on, tuple) else (retry_on,)
        self.stop_on = stop_on if isinstance(stop_on, tuple) else (stop_on,)
        self.before_sleep = before_sleep
        self.on_retry = on_retry
        self.on_final_failure = on_final_failure
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        if self.config.exponential_backoff:
            delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
        else:
            delay = self.config.base_delay
        
        # 限制最大延迟
        delay = min(delay, self.config.max_delay)
        
        # 添加抖动
        if self.config.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def _should_retry(self, exception: Exception) -> bool:
        """判断是否应该重试"""
        # 如果异常在停止列表中，不重试
        if self.stop_on and isinstance(exception, self.stop_on):
            return False
        
        # 如果异常在重试列表中，重试
        return isinstance(exception, self.retry_on)
    
    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数调用"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # 检查是否应该重试
                if not self._should_retry(e):
                    logger.error(f"遇到不可重试异常: {type(e).__name__}: {e}")
                    raise
                
                # 如果是最后一次尝试，不再重试
                if attempt >= self.config.max_attempts:
                    if self.on_final_failure:
                        self.on_final_failure(e, attempt)
                    logger.error(f"重试{attempt}次后仍然失败: {type(e).__name__}: {e}")
                    raise
                
                # 计算延迟时间
                delay = self._calculate_delay(attempt)
                
                # 调用重试回调
                if self.on_retry:
                    self.on_retry(attempt, e)
                
                logger.warning(
                    f"第{attempt}次尝试失败，{delay:.2f}秒后重试: {type(e).__name__}: {e}"
                )
                
                # 调用睡眠前回调
                if self.before_sleep:
                    self.before_sleep(attempt, delay)
                
                # 等待
                await asyncio.sleep(delay)
        
        # 理论上不会到达这里
        if last_exception:
            raise last_exception


class DatabaseRetry(AsyncRetry):
    """数据库专用重试器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        # 数据库相关的可重试异常
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            # 可以根据使用的数据库驱动添加更多异常
        )
        
        # 数据库相关的不可重试异常（事务性错误）
        stop_exceptions = (
            # 这些需要根据实际使用的数据库驱动来定义
            # IntegrityError,  # 完整性约束违反
            # UniqueViolation,  # 唯一约束违反
            # ForeignKeyViolation,  # 外键约束违反
        )
        
        super().__init__(
            config=config or RetryConfig(max_attempts=3, base_delay=1.0),
            retry_on=retry_exceptions,
            stop_on=stop_exceptions,
            on_retry=self._on_database_retry,
            on_final_failure=self._on_database_final_failure,
        )
    
    def _on_database_retry(self, attempt: int, exception: Exception) -> None:
        """数据库重试回调"""
        from .logger import DatabaseErrorLogger
        
        error_logger = DatabaseErrorLogger()
        error_logger.log_retry(
            operation="database_operation",
            retry_count=attempt,
            max_retries=self.config.max_attempts,
            delay=self._calculate_delay(attempt),
        )
    
    def _on_database_final_failure(self, exception: Exception, attempts: int) -> None:
        """数据库最终失败回调"""
        from .logger import DatabaseErrorLogger
        
        error_logger = DatabaseErrorLogger()
        error_logger.log_final_failure(
            operation="database_operation",
            final_error=exception,
            total_retries=attempts - 1,
        )


class LLMRetry(AsyncRetry):
    """LLM调用专用重试器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        # LLM相关的可重试异常
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            # 可以根据使用的LLM API添加更多异常
            # RateLimitError,
            # APIConnectionError,
        )
        
        # LLM相关的不可重试异常
        stop_exceptions = (
            # AuthenticationError,  # 认证错误
            # InvalidRequestError,  # 无效请求
            ValueError,  # 参数错误
        )
        
        super().__init__(
            config=config or RetryConfig(max_attempts=3, base_delay=2.0, max_delay=30.0),
            retry_on=retry_exceptions,
            stop_on=stop_exceptions,
            on_retry=self._on_llm_retry,
        )
    
    def _on_llm_retry(self, attempt: int, exception: Exception) -> None:
        """LLM重试回调"""
        logger.warning(
            f"LLM调用第{attempt}次失败: {type(exception).__name__}: {exception}"
        )


class NetworkRetry(AsyncRetry):
    """网络请求专用重试器"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        # 网络相关的可重试异常
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            # httpx相关异常
            # httpx.ConnectError,
            # httpx.TimeoutException,
            # httpx.NetworkError,
        )
        
        # 网络相关的不可重试异常
        stop_exceptions = (
            # httpx.HTTPStatusError,  # HTTP状态错误（如404, 401等）
            ValueError,  # 参数错误
        )
        
        super().__init__(
            config=config or RetryConfig(max_attempts=3, base_delay=1.0, max_delay=10.0),
            retry_on=retry_exceptions,
            stop_on=stop_exceptions,
        )


# 便捷函数
async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    retry_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
    stop_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = (),
    **kwargs
) -> Any:
    """便捷的异步重试函数"""
    retrier = AsyncRetry(
        config=config,
        retry_on=retry_on,
        stop_on=stop_on,
    )
    return await retrier(func, *args, **kwargs)


async def retry_database_operation(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """便捷的数据库操作重试函数"""
    retrier = DatabaseRetry(config=config)
    return await retrier(func, *args, **kwargs)


async def retry_llm_call(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """便捷的LLM调用重试函数"""
    retrier = LLMRetry(config=config)
    return await retrier(func, *args, **kwargs)


async def retry_network_request(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """便捷的网络请求重试函数"""
    retrier = NetworkRetry(config=config)
    return await retrier(func, *args, **kwargs)
