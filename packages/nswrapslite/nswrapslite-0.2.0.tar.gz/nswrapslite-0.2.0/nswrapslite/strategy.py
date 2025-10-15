# !/usr/bin/env python3
"""
==============================================================
Description  : 装饰器策略基类模块 - 提供装饰器实现的核心策略和基础类
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 14:00:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- BaseWrapper：装饰器基类，提供装饰器的通用逻辑和接口
- SyncWrapper：同步函数包装器，处理同步函数的装饰逻辑
- AsyncWrapper：异步函数包装器，处理异步函数的装饰逻辑
- UnifiedWrapper：统一函数包装器，同时支持同步和异步函数
- 支持元数据保留和原始函数特征继承

主要特性：
- 统一的装饰器实现框架
- 自动识别并适配同步/异步函数
- 保留原始函数的元数据（名称、文档、签名等）
- 支持装饰器堆叠和组合使用
- 完整的类型注解支持
==============================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any

from .utils import is_async_function


class BaseWrapper(ABC):
    """装饰器基类

    所有装饰器的抽象基类，提供统一的接口和基础功能。
    """

    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs

    def __call__(self, func: Callable) -> Callable:
        if is_async_function(func):
            return self._wrap_async(func)
        return self._wrap_sync(func)

    @abstractmethod
    def _wrap_sync(self, func: Callable) -> Callable:
        """包装同步函数"""
        pass

    @abstractmethod
    def _wrap_async(self, func: Callable) -> Callable:
        """包装异步函数"""
        pass


class SyncWrapper(BaseWrapper):
    """同步函数装饰器基类

    专门用于同步函数的装饰器基类，不支持异步函数。
    """

    def _wrap_async(self, func: Callable) -> Callable:
        """包装异步函数（不支持）"""
        raise TypeError(f'{self.__class__.__name__} 不支持异步函数')

    def _wrap_sync(self, func: Callable) -> Callable:
        """包装同步函数"""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._execute_sync(func, args, kwargs)

        return wrapper

    @abstractmethod
    def _execute_sync(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行同步函数"""
        pass


class AsyncWrapper(BaseWrapper):
    """异步函数装饰器基类

    专门用于异步函数的装饰器基类，不支持同步函数。
    """

    def _wrap_sync(self, func: Callable) -> Callable:
        """包装同步函数（不支持）"""
        raise TypeError(f'{self.__class__.__name__} 不支持同步函数')

    def _wrap_async(self, func: Callable) -> Callable:
        """包装异步函数"""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self._execute_async(func, args, kwargs)

        return wrapper

    @abstractmethod
    async def _execute_async(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行异步函数"""
        pass


class UnifiedWrapper(BaseWrapper):
    """通用函数装饰器基类

    同时支持同步和异步函数的装饰器基类，提供统一的接口实现。
    """

    def _wrap_sync(self, func: Callable) -> Callable:
        """包装同步函数"""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._execute_sync(func, args, kwargs)

        return wrapper

    def _wrap_async(self, func: Callable) -> Callable:
        """包装异步函数"""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self._execute_async(func, args, kwargs)

        return wrapper

    def _execute_sync(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行同步函数"""
        return func(*args, **kwargs)

    async def _execute_async(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行异步函数"""
        return await func(*args, **kwargs)


class TimerStrategy(UnifiedWrapper):
    """计时器装饰器类实现

    基于类的计时器装饰器实现，提供更多配置选项。
    """

    def __init__(self, log_level: str = 'INFO', log_args: bool = False, log_result: bool = False) -> None:
        """初始化计时器装饰器

        Args:
            log_level: 日志级别
            log_args: 是否记录参数
            log_result: 是否记录结果
        """
        super().__init__(log_level=log_level, log_args=log_args, log_result=log_result)

    def _execute_sync(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行同步函数"""
        start_time = perf_counter()

        try:
            result = func(*args, **kwargs)
            end_time = perf_counter()
            duration = end_time - start_time

            # 记录日志
            _log_timing(func, args, kwargs, result, duration, self.config.get('log_level', 'INFO'), self.config.get('log_args', False), self.config.get('log_result', False))

            return result

        except Exception as exc:
            end_time = perf_counter()
            duration = end_time - start_time

            # 记录错误日志
            _log_timing(func, args, kwargs, None, duration, self.config.get('log_level', 'INFO'), self.config.get('log_args', False), self.config.get('log_result', False), exc)
            raise

    async def _execute_async(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """执行异步函数"""
        start_time = perf_counter()

        try:
            result = await func(*args, **kwargs)
            end_time = perf_counter()
            duration = end_time - start_time

            # 记录日志
            _log_timing(func, args, kwargs, result, duration, self.config.get('log_level', 'INFO'), self.config.get('log_args', False), self.config.get('log_result', False))

            return result

        except Exception as exc:
            end_time = perf_counter()
            duration = end_time - start_time

            # 记录错误日志
            _log_timing(func, args, kwargs, None, duration, self.config.get('log_level', 'INFO'), self.config.get('log_args', False), self.config.get('log_result', False), exc)
            raise


def _log_timing(
    func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], result: Any | None, duration: float, log_level: str, log_args: bool, log_result: bool, exception: Exception | None = None
) -> None:
    """记录计时日志

    Args:
        func: 被计时的函数
        args: 位置参数
        kwargs: 关键字参数
        result: 函数结果
        duration: 执行时间
        log_level: 日志级别
        log_args: 是否记录参数
        log_result: 是否记录结果
        exception: 异常信息
    """
    from xtlog import mylog

    # 构建日志消息，避免使用大括号
    message_parts = ['函数 ', func.__name__, ' 执行耗时: ', f'{duration:.4f} 秒']

    if log_args:
        args_str = ', '.join(f'{arg!r}' for arg in args)
        kwargs_str = ', '.join(f'{k}={v!r}' for k, v in kwargs.items())
        params = ', '.join(filter(None, [args_str, kwargs_str]))
        message_parts.extend([' | 参数: ', params])

    if log_result and result is not None:
        message_parts.extend([' | 结果: ', f'{result!r}'])

    if exception:
        message_parts.extend([' | 异常: ', f'{exception!r}'])

    log_message = ''.join(message_parts)
    log_message = log_message.replace('{', '{{').replace('}', '}}')
    # 使用动态日志级别调用，简化逻辑
    getattr(mylog, log_level.lower())(log_message, callfrom=func)


# 导出模块公共接口
__all__ = [
    'TimerStrategy',
    'UnifiedWrapper',
]
