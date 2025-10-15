# !/usr/bin/env python3
"""
==============================================================
Description  : 装饰器工厂模块 - 提供装饰器创建和管理功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 15:00:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- decorator_factory：装饰器工厂类，管理装饰器的创建和配置
- timer_wrapper_factory：由装饰器工厂创建的计时器装饰器
- exc_wrapper_factory：由装饰器工厂创建的异常处理装饰器
- log_wrapper_factory：由装饰器工厂创建的日志装饰器



主要特性：
- 统一的装饰器创建接口
- 支持同步和异步函数的装饰器
- 保留原始函数的元数据
- 支持装饰器参数配置
- 完整的类型注解支持
==============================================================
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from time import perf_counter
from typing import Any

from xtlog import mylog

from .exception import handle_exception
from .utils import get_function_location, is_async_function

# 类型别名
type ExceptionTypes = tuple[type[Exception], ...]


# 定义钩子函数类型别名
type BeforeHook = Callable[[Callable[..., Any], tuple[Any, ...], dict[str, Any], dict[str, Any]], Any]
type AfterHook = Callable[[Callable[..., Any], tuple[Any, ...], dict[str, Any], Any, dict[str, Any]], Any]
type ExceptHook = Callable[[Callable[..., Any], tuple[Any, ...], dict[str, Any], Exception, dict[str, Any]], Any]


async def run_sync_or_async(fn: Callable[..., Any] | None, *args: Any, **kwargs: Any) -> Any:
    """执行函数，自动处理同步或异步调用

    Args:
        fn: 要执行的函数，可为None
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果，如果fn为None则返回None
    """
    if fn is None:
        return None

    if asyncio.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)

    return fn(*args, **kwargs)


def create_decorator_context() -> dict[str, Any]:
    """创建装饰器执行上下文对象

    Returns:
        空的上下文字典，用于装饰器执行过程中的数据共享
    """
    return {}


def create_async_decorator_wrapper(func: Callable, before_hook: BeforeHook | None, after_hook: AfterHook | None, except_hook: ExceptHook | None) -> Callable:
    """创建异步函数的装饰器包装器

    Args:
        func: 被装饰的函数
        before_hook: 前置钩子函数
        after_hook: 后置钩子函数
        except_hook: 异常处理钩子函数

    Returns:
        包装后的异步函数
    """

    @functools.wraps(func)
    async def async_decorator_wrapper(*args: Any, **kwargs: Any) -> Any:
        """异步函数装饰器包装器"""
        context = create_decorator_context()

        # 处理前置钩子
        if before_hook:
            hook_result = await run_sync_or_async(before_hook, func, args, kwargs, context)
            if hook_result is not None:
                return hook_result

        try:
            # 执行原函数
            result = await func(*args, **kwargs)
        except Exception as e:
            # 处理异常钩子
            if except_hook:
                hook_result = await run_sync_or_async(except_hook, func, args, kwargs, e, context)
                if hook_result is not None:
                    return hook_result
            raise

        # 处理后置钩子
        if after_hook:
            after_result = await run_sync_or_async(after_hook, func, args, kwargs, result, context)
            return after_result if after_result is not None else result
        return result

    return async_decorator_wrapper


def create_sync_decorator_wrapper(func: Callable, before_hook: BeforeHook | None, after_hook: AfterHook | None, except_hook: ExceptHook | None) -> Callable:
    """创建同步函数的装饰器包装器"""

    @functools.wraps(func)
    def sync_decorator_wrapper(*args: Any, **kwargs: Any) -> Any:
        """同步函数装饰器包装器"""
        context = create_decorator_context()

        # 处理前置钩子
        if before_hook:
            hook_result = before_hook(func, args, kwargs, context)
            if hook_result is not None:
                return hook_result

        try:
            # 执行原函数
            result = func(*args, **kwargs)
        except Exception as e:
            # 处理异常钩子
            if except_hook:
                hook_result = except_hook(func, args, kwargs, e, context)
                if hook_result is not None:
                    return hook_result
            raise

        # 处理后置钩子
        if after_hook:
            after_result = after_hook(func, args, kwargs, result, context)
            return after_result if after_result is not None else result
        return result

    return sync_decorator_wrapper


def decorator_factory(before_hook: BeforeHook | None = None, after_hook: AfterHook | None = None, except_hook: ExceptHook | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """通用装饰器工厂，支持同步/异步函数

    Args:
        before_hook: 前置钩子函数，签名为(func, args, kwargs, context)
        after_hook: 后置钩子函数，签名为(func, args, kwargs, result, context)
        except_hook: 异常钩子函数，签名为(func, args, kwargs, exc, context)

    Returns:
        Callable[[Callable], Callable]: 装饰器函数

    Example:
        >>> # 创建简单的日志装饰器
        >>> def log_before(func, args, kwargs, context):
        ...     print(f'调用函数: {func.__name__}')
        >>> @decorator_factory(before_hook=log_before)
        ... def my_function(x):
        ...     return x * 2

    Note:
        该工厂支持同步和异步函数，会自动检测函数类型并创建相应的包装器
    """

    def decorator(func: Callable) -> Callable:
        """通用装饰器"""
        if is_async_function(func):
            return create_async_decorator_wrapper(func, before_hook, after_hook, except_hook)
        return create_sync_decorator_wrapper(func, before_hook, after_hook, except_hook)

    return decorator


def timer_wrapper_factory(func: Callable[..., Any] | None = None) -> Callable[..., Any]:
    """计时装饰器工厂，记录函数执行时间

    Args:
        func: 被装饰的函数，支持直接装饰和带参数装饰两种方式

    Returns:
        Callable: 包装后的函数

    Raises:
        Exception: 被装饰函数抛出的任何异常

    Example:
        >>> @timer_wrapper
        ... def slow_function():
        ...     import time
        ...
        ...     time.sleep(1)
        ...     return '完成'

        >>> @timer_wrapper
        ... def error_function():
        ...     raise ValueError('测试异常')

        >>> # 异步函数支持
        >>> @timer_wrapper
        ... async def async_slow_function():
        ...     await asyncio.sleep(1)
        ...     return '异步完成'
    """

    def _before(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], context: dict[str, Any]) -> None:
        """执行前记录开始时间

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            context: 上下文字典
        """
        context['start'] = perf_counter()

    def _after(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], result: Any, context: dict[str, Any]) -> Any:
        """执行后记录结束时间

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            result: 函数执行结果
            context: 上下文字典
        """
        start = context.get('start')
        if start is not None:
            end = perf_counter()
            func_location = get_function_location(func)
            mylog.info(f'{func_location} 执行耗时: {end - start:.4f}秒')
        return result

    def _except(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], exc: Exception, context: dict[str, Any]) -> None:
        """异常处理钩子，记录异常发生时的执行时间

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            exc: 捕获的异常
            context: 上下文字典

        Raises:
            Exception: 重新抛出原始异常
        """
        start = context.get('start')
        if start is not None:
            end = perf_counter()
            func_location = get_function_location(func)
            mylog.error(f'[{func_location}] 失败耗时: {end - start:.4f}秒')
        raise exc

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """实际的装饰器函数

        Args:
            func: 被装饰的函数

        Returns:
            Callable: 包装后的函数
        """
        decorator_instance = decorator_factory(before_hook=_before, after_hook=_after, except_hook=_except)
        return decorator_instance(func)

    return decorator if func is None else decorator(func)


def exc_wrapper_factory(
    func: Callable[..., Any] | None = None,
    *,
    re_raise: bool = True,
    allowed_exceptions: ExceptionTypes = (Exception,),
    log_traceback: bool = True,
    custom_message: str = '',
) -> Callable[..., Any]:
    """通用异常处理装饰器，支持同步和异步函数

    Args:
        func: 被装饰的函数，支持直接装饰和带参数装饰两种方式
        re_raise: 是否重新抛出异常，默认False
        allowed_exceptions: 允许捕获的异常类型元组，默认捕获所有异常
        log_traceback: 是否记录完整堆栈信息，默认True
        custom_message: 自定义错误提示信息，默认空字符串

    Returns:
        Callable: 装饰后的函数

    Raises:
        Exception: 当re_raise=True且异常不在allowed_exceptions中时抛出

    Example:
        >>> # 基本使用，捕获所有异常并返回None
        >>> @exc_wrapper
        ... def divide(a: int, b: int) -> float:
        ...     return a / b

        >>> # 只捕获特定异常，其他异常会重新抛出
        >>> @exc_wrapper(allowed_exceptions=(ZeroDivisionError,), re_raise=False)
        ... def safe_divide(a: int, b: int) -> float:
        ...     return a / b

        >>> # 自定义错误消息
        >>> @exc_wrapper(custom_message='除法运算失败', re_raise=False)
        ... def custom_divide(a: int, b: int) -> float:
        ...     return a / b

        >>> # 异步函数支持
        >>> @exc_wrapper
        ... async def async_divide(a: int, b: int) -> float:
        ...     return a / b

    Note:
        该装饰器会自动检测函数类型并创建相应的同步或异步包装器
    """

    def _except_hook(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], exc: Exception, context: dict[str, Any]) -> Any:
        """异常钩子函数，处理捕获的异常

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            exc: 捕获的异常
            context: 上下文字典

        Raises:
            Exception: 当异常不在allowed_exceptions中时重新抛出
        """
        # 检查异常类型是否在允许捕获的列表中
        if not isinstance(exc, allowed_exceptions):
            raise exc

        # 使用统一的异常处理函数
        func_location = get_function_location(func)
        handle_exception(exc=exc, re_raise=re_raise, log_traceback=log_traceback, custom_message=f' {custom_message} {func_location}')

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """装饰器内部函数

        Args:
            func: 被装饰的函数

        Returns:
            Callable: 包装后的函数
        """
        # 使用decorator_factory创建装饰器
        decorator_instance = decorator_factory(except_hook=_except_hook)
        return decorator_instance(func)

    return decorator if func is None else decorator(func)


def log_wrapper_factory(
    func: Callable[..., Any] | None = None,
    *,
    re_raise: bool = False,
    log_args: bool = True,
    log_result: bool = True,
    log_traceback: bool = True,
    custom_message: str = '',
) -> Callable[..., Any]:
    """日志装饰器，记录函数调用信息

    Args:
        func: 被装饰的函数，支持直接装饰和带参数装饰两种方式
        re_raise: 是否重新抛出异常，默认False
        log_args: 是否记录函数参数，默认True
        log_result: 是否记录函数结果，默认True
        log_traceback: 是否记录完整堆栈信息，默认True
        custom_message: 自定义日志消息，默认空字符串

    Returns:
        Callable: 包装后的函数

    Example:
        >>> @log_wrapper
        ... def add(a: int, b: int) -> int:
        ...     return a + b

        >>> # 异步函数支持
        >>> @log_wrapper
        ... async def async_add(a: int, b: int) -> int:
        ...     return a + b

        >>> # 自定义配置
        >>> @log_wrapper(log_args=False, log_result=False)
        ... def silent_function(x):
        ...     return x * 2
    """

    def _before(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], context: dict[str, Any]) -> None:
        """日志装饰器前置钩子

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            context: 上下文字典
        """
        if log_args:
            func_location = get_function_location(func)
            mylog.debug(f' {custom_message} {func_location} args: {args}, kwargs: {kwargs}')

    def _after(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], result: Any, context: dict[str, Any]) -> Any:
        """日志装饰器后置钩子

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            result: 函数执行结果
            context: 上下文字典
        """
        if log_result:
            func_location = get_function_location(func)
            mylog.success(f'[{func_location}] result: {type(result).__name__} = {result}')
        return result

    def _except(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], exc: Exception, context: dict[str, Any]) -> Any:
        """日志装饰器异常钩子

        Args:
            func: 被装饰的函数
            args: 位置参数
            kwargs: 关键字参数
            exc: 捕获的异常
            context: 上下文字典
        """
        func_location = get_function_location(func)
        handle_exception(exc=exc, re_raise=re_raise, log_traceback=log_traceback, custom_message=f' {custom_message} {func_location}')

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """装饰器内部函数

        Args:
            func: 被装饰的函数

        Returns:
            Callable: 包装后的函数
        """
        # 使用decorator_factory创建装饰器
        decorator_instance = decorator_factory(before_hook=_before, after_hook=_after, except_hook=_except)
        return decorator_instance(func)

    return decorator if func is None else decorator(func)


__all__ = ['decorator_factory', 'exc_wrapper_factory', 'log_wrapper_factory', 'timer_wrapper_factory']
