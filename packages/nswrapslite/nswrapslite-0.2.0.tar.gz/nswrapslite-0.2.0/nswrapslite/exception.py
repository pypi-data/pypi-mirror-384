# !/usr/bin/env python3
"""
==============================================================
Description  : 异常处理模块 - 提供异常捕获和处理功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 15:30:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- handle_exception：异常处理函数，记录异常信息
- exception_wraps：异常捕获和处理装饰器，支持同步和异步函数

主要特性：
- 同时支持同步和异步函数的异常处理
- 详细的异常信息记录（函数名、参数、异常类型、堆栈）
- 支持自定义异常处理逻辑
- 保留原始函数的元数据
- 完整的类型注解支持
==============================================================
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any

from xtlog import mylog

# 使用相对导入
from .utils import is_async_function

# 类型别名
ExceptionTypes = tuple[type[Exception], ...]


def handle_exception(
    exc: BaseException | None = None,
    re_raise: bool = False,
    handler: Callable[..., Any] | None = None,
    log_traceback: bool = True,
    custom_message: str = '',
) -> BaseException | None:
    """
    统一的异常处理函数，提供完整的异常捕获、记录和处理机制

    Args:
        exc: 异常对象
        re_raise: 是否重新抛出异常，默认False（不抛出异常）
        handler: 异常处理函数，默认None（不处理）
        log_traceback: 是否记录完整堆栈信息，默认True
        custom_message: 自定义错误提示信息，默认''

    Returns:
        Any: 如果re_raise=True，重新抛出异常
        None: 如果re_raise=False，返回错误exc

    Example:
        >>> # 基本使用
        >>> try:
        ...     result = 10 / 0
        ... except Exception as e:
        ...     # 记录异常但不中断程序
        ...     handle_exception(e, re_raise=False)
        >>> print(result)  # 输出: ZeroDivisionError
    """

    # 构建错误信息
    error_type = type(exc).__name__
    error_msg = str(exc)

    # 统一的日志格式
    error_message = f' {custom_message}except: {error_type}({error_msg})'
    mylog.error(error_message)

    # 调用异常处理函数
    if handler:
        handler(exc)

    # 如果需要,记录完整堆栈信息
    if log_traceback and exc is not None:  # 确保有异常对象
        # 显式传入异常的类型、值和追踪信息
        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        mylog.error(f'traceback | {tb_str}')
    elif log_traceback:
        mylog.error('traceback | No exception traceback available (exc is None)')

    # 根据需要重新抛出异常
    if re_raise and exc is not None:
        raise exc

    return exc


def exception_wraps(
    fn: Callable[..., Any] | None = None,
    *,
    re_raise: bool = False,
    handler: Callable[[Exception], Any] | None = None,
    allowed_exceptions: ExceptionTypes = (Exception,),
    log_traceback: bool = True,
    custom_message: str = '',
) -> Callable:
    """
    通用异常处理装饰器 - 支持同步和异步函数

    Args:
        func: 被装饰的函数(支持直接装饰和带参数装饰两种方式)
        re_raise: 是否重新抛出异常，默认True（抛出异常）
        handler: 异常处理函数，默认None（不处理）
        allowed_exceptions: 允许捕获的异常类型元组，默认捕获所有异常
        log_traceback: 是否记录完整堆栈信息，默认True
        custom_message: 自定义错误提示信息，默认None

    Returns:
        装饰后的函数，保持原函数签名和功能

    Example:
        >>> # 基本使用，捕获所有异常并返回None
        >>> @exc_wraps
        ... def divide(a, b):
        ...     return a / b

        >>> # 只捕获特定异常，其他异常会重新抛出
        >>> @exc_wraps(allowed_exceptions=(ZeroDivisionError,), re_raise=False)
        ... def safe_divide(a, b):
        ...     return a / b

        >>> # 自定义错误消息
        >>> @exc_wraps(custom_message='除法运算失败', re_raise=False)
        ... def custom_divide(a, b):
        ...     return a / b

        >>> # 异步函数支持
        >>> @exc_wraps
        ... async def async_divide(a, b):
        ...     return a / b
    """

    def decorator(func: Callable) -> Callable:
        """装饰器函数"""

        if is_async_function(func):
            # 异步函数异常捕获装饰器
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                """异步异常捕获包装器"""
                try:
                    return await func(*args, **kwargs)
                except allowed_exceptions as exc:
                    return handle_exception(exc, re_raise, handler, log_traceback, custom_message)

            return async_wrapper

        # 同步函数异常捕获装饰器
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """同步异常捕获包装器"""
            try:
                return func(*args, **kwargs)
            except allowed_exceptions as exc:
                return handle_exception(exc, re_raise, handler, log_traceback, custom_message)

        return sync_wrapper

    return decorator if fn is None else decorator(fn)


__all__ = ['exception_wraps']
