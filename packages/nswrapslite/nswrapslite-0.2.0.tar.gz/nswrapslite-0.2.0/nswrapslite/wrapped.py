# !/usr/bin/env python3
"""
==============================================================
Description  : 函数装饰器转换模块
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 12:30:00
Github       : https://github.com/sandorn/nswrapslite

基于函数转换模式的装饰器实现，提供同步到异步、异步到同步的函数转换能力，
支持灵活的函数包装和装饰器创建。
==============================================================
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any

from xtlog import mylog

from .utils import is_async_function


def decorator_transformer(wrapper_func: Callable[..., Any]) -> Callable[..., Any]:
    """装饰器转换器 - 自动处理同步/异步函数的装饰器工厂

    这个装饰器工厂允许你专注于装饰逻辑实现，而无需关心被装饰函数是同步还是异步的。
    它会自动检测函数类型并应用合适的包装策略。

    参数说明:
        wrapper_func: 包装函数，接收(func, args, kwargs)参数，处理实际的装饰逻辑

    返回值:
        可应用于同步或异步函数的装饰器
    """

    def create_decorator(func: Callable) -> Callable:
        """创建实际的装饰器函数"""

        if is_async_function(func):
            # 异步函数装饰器
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                """异步函数包装器"""
                # 如果包装器函数也是异步的，直接await调用
                if is_async_function(wrapper_func):
                    return await wrapper_func(func, args, kwargs)
                # 包装器函数是同步的，直接调用
                return wrapper_func(func, args, kwargs)

            return async_wrapper
        # 同步函数装饰器

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            """同步函数包装器"""
            # 如果包装器函数是异步的，需要在事件循环中运行
            if is_async_function(wrapper_func):
                try:
                    # 尝试获取当前运行的事件循环
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # 没有正在运行的事件循环，创建一个新的
                    return asyncio.run(wrapper_func(func, args, kwargs))
                else:
                    # 有正在运行的事件循环，直接传递协程给run_coroutine_threadsafe
                    coro = wrapper_func(func, args, kwargs)
                    # 在同步上下文中等待协程完成
                    return asyncio.run_coroutine_threadsafe(coro, loop).result()
            else:
                # 包装器函数是同步的，直接调用
                return wrapper_func(func, args, kwargs)

        return sync_wrapper

    return create_decorator


# 示例：创建计时装饰器
@decorator_transformer
async def timing_decorator(func, args, kwargs):
    """计时装饰器实现 - 记录函数执行耗时

    自动检测函数类型并记录执行时间，支持同步和异步函数。
    """
    start_time = perf_counter()
    try:
        # 根据被装饰函数的类型决定是否使用await
        if is_async_function(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)
    finally:
        end_time = perf_counter()
        mylog.info(f'{func.__name__} 执行耗时: {end_time - start_time:.4f}秒')


__all__ = [
    'decorator_transformer',
    'timing_decorator',
]
