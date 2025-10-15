# !/usr/bin/env python3
"""
==============================================================
Description  : 日志装饰器模块 - 提供函数执行日志记录功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 14:45:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- logging_wraps：函数执行日志装饰器，支持同步和异步函数

主要特性：
- 同时支持同步和异步函数
- 详细的函数执行日志（开始、结束、耗时、参数、返回值）
- 异常捕获和日志记录
- 支持不同的日志级别配置
- 保留原始函数的元数据
- 完整的类型注解支持
==============================================================
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from xtlog import mylog

from .exception import handle_exception
from .utils import get_function_location, is_async_function


def _create_sync_wrapper(func: Callable[..., Any], log_args: bool, log_result: bool, re_raise: bool, log_traceback: bool, custom_message: str) -> Callable[..., Any]:
    """创建同步函数包装器"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数信息用于日志记录
        log_context = get_function_location(func)

        if log_args:
            mylog.debug(f'{log_context} | Args: {args} | Kwargs: {kwargs}')

        try:
            result: Any = func(*args, **kwargs)
            if log_result:
                mylog.success(f'{log_context} | Result: {type(result).__name__} = {result}')
            return result
        except Exception as err:
            return handle_exception(exc=err, re_raise=re_raise, log_traceback=log_traceback, custom_message=f'{custom_message} {log_context}')

    return wrapper


def _create_async_wrapper(func: Callable[..., Any], log_args: bool, log_result: bool, re_raise: bool, log_traceback: bool, custom_message: str) -> Callable[..., Any]:
    """创建异步函数包装器"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 获取函数信息用于日志记录
        log_context = get_function_location(func)

        if log_args:
            mylog.debug(f'{log_context} | Args: {args} | Kwargs: {kwargs}')

        try:
            result: Any = await func(*args, **kwargs)
            if log_result:
                mylog.success(f'{log_context} | Result: {type(result).__name__} = {result}')
            return result
        except Exception as err:
            return handle_exception(exc=err, re_raise=re_raise, log_traceback=log_traceback, custom_message=f'{custom_message} {log_context}')

    return wrapper


def logging_wraps(
    func: Callable[..., Any] | None = None,
    *,
    re_raise: bool = False,
    log_args: bool = True,
    log_result: bool = True,
    log_traceback: bool = True,
    custom_message: str = '',
) -> Callable[..., Any]:
    """
    简化版日志装饰器

    这个装饰器可以为函数自动添加日志记录功能，包括：
    - 记录函数调用时的参数
    - 记录函数的返回值
    - 自动处理同步和异步函数
    - 支持异常处理和重新抛出

    Args:
        func: 被装饰的函数（装饰器语法糖参数）
        log_args: 是否记录函数参数，默认为True
        log_result: 是否记录函数返回值，默认为True
        log_traceback: 是否记录完整堆栈信息，默认为True
        re_raise: 是否重新抛出异常，默认为True
        custom_message: 自定义日志消息，默认""

    Returns:
        Callable: 装饰后的函数

    Example:
        >>> @log_wraps
        >>> def my_function(x, y):
        >>>     return x + y

        >>> @log_wraps(log_args=True, log_result=False)
        >>> async def async_function(data):
        >>>     return await process_data(data)
    """

    def decorator(func_inner: Callable[..., Any]) -> Callable[..., Any]:
        """实际的装饰器实现"""
        if is_async_function(func_inner):
            return _create_async_wrapper(func_inner, log_args, log_result, re_raise, log_traceback, custom_message)

        return _create_sync_wrapper(func_inner, log_args, log_result, re_raise, log_traceback, custom_message)

    return decorator(func) if func else decorator


# 导出模块公共接口
__all__ = ['logging_wraps']
