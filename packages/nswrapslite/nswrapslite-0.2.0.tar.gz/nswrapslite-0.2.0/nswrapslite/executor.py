# !/usr/bin/env python3
"""
==============================================================
Description  : 异步执行器模块 - 提供函数在不同执行器上的调度功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 17:00:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- async_executor：异步执行器装饰器，支持同步和异步函数
- syncify：同步运行异步函数装饰器
- to_future：Future执行器装饰器，将同步函数包装成返回Future的函数
- await_future_with_timeout：Future结果获取器，带超时处理和异常管理

主要特性：
- 支持在不同线程或进程执行器上运行函数
- 自动处理异常和结果返回
- 支持取消正在执行的任务
- 完整的类型注解支持
- 异步友好的接口设计
==============================================================
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any

# 使用相对导入
from .exception import handle_exception
from .utils import is_async_function

# 常量定义
DEFAULT_EXECUTOR_MAX_WORKERS = 10  # 默认线程池最大工作线程数
DEFAULT_FUTURE_TIMEOUT = 30.0  # 默认Future超时时间(秒)

# 默认线程池执行器
_default_executor = ThreadPoolExecutor(max_workers=DEFAULT_EXECUTOR_MAX_WORKERS, thread_name_prefix='XtExecutor')


def _create_future_exception_handler() -> Callable[[asyncio.Future[Any]], None]:
    """创建统一的Future异常处理回调函数"""

    def exception_handler(fut: asyncio.Future[Any]) -> None:
        # 单独处理CancelledError，因为这是预期行为
        if fut.cancelled():
            return
        try:
            exc = fut.exception()
            if exc is not None:
                # 记录异常但不重新抛出
                if isinstance(exc, BaseException) and not isinstance(exc, Exception):
                    exc = RuntimeError(f'Unexpected BaseException: {type(exc).__name__}: {exc!s}')
                handle_exception(exc, re_raise=False, custom_message='异步任务执行异常')
        except Exception as err:
            # 记录异常处理过程中的错误
            handle_exception(err, re_raise=False, custom_message='异常处理器内部错误')

    return exception_handler


def _get_event_loop() -> asyncio.AbstractEventLoop:
    """获取或创建事件循环"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        # 如果没有事件循环,创建一个新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _run_in_new_thread(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """在新线程中运行异步函数，避免与已有事件循环冲突"""
    result: list[Any] = []
    error: list[BaseException] = []

    def _run_in_new_loop():
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            # 确保func返回的是可等待对象
            coro = func(*args, **kwargs)
            result.append(new_loop.run_until_complete(coro))
        except BaseException as e:
            error.append(e)
        finally:
            new_loop.close()

    # 创建并启动新线程
    thread = threading.Thread(target=_run_in_new_loop)
    thread.start()
    thread.join()

    # 处理结果或异常
    if error:
        raise error[0] from None
    return result[0]


# 辅助函数：创建异步函数任务包装器
def _create_async_task_wrapper(func: Callable[..., Any]) -> Callable[..., asyncio.Task[Any]]:
    @wraps(func)
    def async_task_wrapper(*args: Any, **kwargs: Any) -> asyncio.Task[Any]:
        async def task_wrapper() -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as err:
                handle_exception(err, re_raise=True)

        return asyncio.create_task(task_wrapper())

    return async_task_wrapper


# 辅助函数：创建异步函数异常处理包装器
def _create_async_error_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as err:
            handle_exception(err, re_raise=True)

    return async_wrapper


# 辅助函数：创建同步函数Future包装器
def _create_sync_future_wrapper(func: Callable[..., Any], executor: ThreadPoolExecutor) -> Callable[..., asyncio.Future]:
    @wraps(func)
    def sync_future_wrapper(*args: Any, **kwargs: Any) -> asyncio.Future:
        loop = _get_event_loop()
        task_func = partial(func, *args, **kwargs)
        future = loop.run_in_executor(executor, task_func)
        future.add_done_callback(_create_future_exception_handler())
        return future

    return sync_future_wrapper


# 辅助函数：创建同步函数异步包装器
def _create_async_wrapper_for_sync_func(func: Callable[..., Any], executor: ThreadPoolExecutor) -> Callable[..., Any]:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = _get_event_loop()
        task_func = partial(func, *args, **kwargs)
        try:
            return await loop.run_in_executor(executor, task_func)
        except Exception as err:
            handle_exception(exc=err, re_raise=True)

    return async_wrapper


def async_executor(
    fn: Callable[..., Any] | None = None, *, background: bool = False, executor: ThreadPoolExecutor | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """
    异步执行器装饰器 - 将同步函数转换为异步函数执行，或增强异步函数的执行能力

    核心功能：
    - 自动识别并适配同步/异步函数
    - 支持后台执行模式，不阻塞主程序流程
    - 统一的异常处理机制
    - 支持自定义线程池执行器

    Args:
        fn: 要装饰的函数，可选（支持同步和异步函数）
        background: 是否在后台执行，默认为False
                    - False: 返回协程对象，需要await等待执行完成
                    - True: 返回Future/Task对象，立即返回不阻塞
        executor: 自定义线程池执行器，默认为None（使用默认执行器）

    Returns:
        装饰后的函数，根据参数和原函数类型返回不同对象：
        - 当background=False时：返回协程对象，需要await
        - 当background=True时：返回Future/Task对象，可后续await获取结果
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        used_executor = executor or _default_executor

        if is_async_function(func):
            if background:
                return _create_async_task_wrapper(func)
            return _create_async_error_wrapper(func)

        if background:
            return _create_sync_future_wrapper(func, used_executor)
        return _create_async_wrapper_for_sync_func(func, used_executor)

    # 处理装饰器调用方式
    return decorator(fn) if fn else decorator


def run_on_executor(executor: ThreadPoolExecutor | None = None, background: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异步装饰器 - async_executor的别名函数
    - 支持同步函数使用 executor 加速
    - 异步函数和同步函数都可以使用 `await` 语法等待返回结果
    - 异步函数和同步函数都支持后台任务，无需等待
    Args:
        executor: 函数执行器, 装饰同步函数的时候使用
        background: 是否后台执行，默认False
    """
    return async_executor(background=background, executor=executor)


def syncify(fn: Callable[..., Any] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """
    同步运行异步函数装饰器 - 将异步函数转换为可直接调用的同步函数

    核心功能：
    - 自动适配异步和同步函数
    - 智能事件循环管理（处理循环已运行、未创建等情况）
    - 统一的异常处理机制

    Args:
        fn: 要装饰的函数（支持同步和异步函数），可选

    Returns:
        同步函数，可以直接调用而不需要await
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if is_async_function(func):
                try:
                    loop = _get_event_loop()
                    if loop.is_running():
                        # 如果有正在运行的事件循环，在新线程中运行
                        return _run_in_new_thread(func, *args, **kwargs)
                    # 直接运行协程
                    return loop.run_until_complete(func(*args, **kwargs))
                except Exception as err:
                    # 异常处理函数可能返回默认值，需要明确返回
                    handle_exception(err, re_raise=False)
            else:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    # 异常处理函数可能返回默认值，需要明确返回
                    handle_exception(err, re_raise=False)

        return sync_wrapper

    # 处理装饰器调用方式
    return decorator(fn) if fn else decorator


def to_future(fn: Callable[..., Any] | None = None, *, executor: ThreadPoolExecutor | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
    """
    Future执行器装饰器 - 将同步函数包装成返回asyncio.Future对象的函数

    核心功能：
    - 将同步函数转换为返回Future的函数
    - 支持自定义线程池执行器
    - 自动异常捕获和处理

    Args:
        fn: 要装饰的同步函数，可选
        executor: 自定义线程池执行器，默认为None（使用默认执行器）

    Returns:
        装饰后的函数，返回asyncio.Future对象，可通过await获取结果
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                loop = _get_event_loop()
                used_executor = executor or _default_executor
                partial_func = partial(func, *args, **kwargs)
                future = loop.run_in_executor(used_executor, partial_func)
                future.add_done_callback(_create_future_exception_handler())
                return future
            except Exception as err:
                # 创建一个已完成的future并设置异常
                loop = _get_event_loop()
                future = loop.create_future()
                future.set_exception(err)
                return future

        return wrapper

    return decorator(fn) if fn else decorator


async def await_future_with_timeout(future: asyncio.Future, timeout: float | None = DEFAULT_FUTURE_TIMEOUT) -> Any:
    """
    Future结果获取器 - 等待Future完成并返回结果，带超时处理和异常管理

    核心功能：
    - 等待Future完成并获取结果
    - 自动超时处理，避免永久阻塞
    - 统一的异常处理机制
    - 自动取消超时的Future
    - 可配置的超时时间
    - 智能状态检查和取消逻辑

    Args:
        future: 要等待的Future对象
        timeout: 超时时间(秒)，默认为DEFAULT_FUTURE_TIMEOUT(30秒)，None表示无超时

    Returns:
        Future完成后的结果

    Raises:
        TimeoutError: 当Future在指定时间内未完成时
        asyncio.CancelledError: 当Future被取消时
        其他可能的异常: 由Future执行过程中抛出的原始异常

    示例:
        # 假设已有一个Future对象
        future = some_async_operation()

        try:
            # 等待Future完成并获取结果
            result = await await_future_with_timeout(future, timeout=10.0)
            print(f"结果: {result}")
        except TimeoutError:
            print("操作超时")
        except Exception as e:
            print(f"发生错误: {e}")
    """
    # 状态检查：如果future已经完成，直接返回结果
    if future.done():
        try:
            return future.result()
        except Exception as err:
            handle_exception(exc=err, re_raise=True)

    # 设置默认超时时间
    effective_timeout = timeout if timeout is not None else DEFAULT_FUTURE_TIMEOUT

    try:
        # 添加超时机制，避免永久等待
        return await asyncio.wait_for(future, timeout=effective_timeout)
    except Exception as exc:
        # 处理超时异常的特殊逻辑
        if isinstance(exc, TimeoutError) and not future.done():
            try:
                # 使用更安全的方式取消任务
                if future.cancel():
                    # 尝试等待一小段时间让取消生效
                    with contextlib.suppress(TimeoutError, asyncio.CancelledError):
                        await asyncio.wait_for(future, timeout=0.5)
            except Exception as cancel_err:
                # 记录取消过程中的异常，但不影响主流程
                handle_exception(exc=cancel_err, re_raise=False, custom_message='取消任务时发生异常')

        # 统一处理所有异常，设置 re_raise=True 让调用方处理
        # 对于非Exception类型的异常(如CancelledError)进行转换
        if not isinstance(exc, Exception):
            exc = RuntimeError(f'非Exception类型异常: {type(exc).__name__}: {exc}')

        handle_exception(exc=exc, re_raise=True)


# 导出模块公共接口
__all__ = [
    'async_executor',
    'await_future_with_timeout',
    'run_on_executor',
    'syncify',
    'to_future',
]
