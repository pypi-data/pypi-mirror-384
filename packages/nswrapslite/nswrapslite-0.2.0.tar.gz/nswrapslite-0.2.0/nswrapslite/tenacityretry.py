# !/usr/bin/env python3
"""
==============================================================
Description  : 重试机制模块 - 提供函数执行失败自动重试功能（基于tenacity库）
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-09-06 11:30:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- tenacity_retry_wraps：函数重试装饰器，同时支持同步和异步函数
- RetryHandler：重试处理器，管理重试逻辑和异常处理
- 自动识别同步/异步函数，提供一致的重试体验
- 支持自定义重试次数、等待时间和异常类型

主要特性：
- 基于tenacity库实现的高效重试机制
- 自动适配同步和异步函数
- 可配置的重试策略和等待时间范围
- 自定义的异常类型筛选和处理
- 丰富的回调函数支持
- 异常静默处理和默认返回值机制
- 统一的异常日志记录
==============================================================
"""

from __future__ import annotations

import smtplib
import socket
import ssl
from collections.abc import Callable
from functools import wraps
from typing import Any

import aiohttp
import requests
import urllib3.exceptions
from tenacity import RetryCallState, retry, retry_if_exception_type, stop_after_attempt, wait_random

from .exception import handle_exception
from .utils import get_function_location, is_async_function

TRETRY = retry(
    reraise=True,  # 保留最后一次错误
    stop=stop_after_attempt(3),
    wait=wait_random(),
)


class RetryHandler:
    """重试处理器 - 管理重试逻辑、异常处理和回调函数

    核心功能：
    - 维护可重试异常类型列表
    - 提供重试前和错误回调函数
    - 判断异常是否应该重试
    - 处理全局配置和状态管理
    """

    # 默认可重试异常类型
    RETRYABLE_EXCEPTIONS = (
        # 网络连接异常
        TimeoutError,
        ConnectionError,
        ConnectionRefusedError,
        ConnectionResetError,
        ConnectionAbortedError,
        BrokenPipeError,
        # DNS解析
        socket.gaierror,
        # SSL/TLS异常
        ssl.SSLError,
        ssl.SSLZeroReturnError,
        ssl.SSLWantReadError,
        ssl.SSLWantWriteError,
        ssl.SSLSyscallError,
        ssl.SSLEOFError,
        # HTTP客户端异常 (requests)
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ContentDecodingError,
        requests.exceptions.TooManyRedirects,
        requests.exceptions.ProxyError,
        # 异步HTTP异常 (aiohttp)
        aiohttp.ClientError,
        aiohttp.ClientConnectionError,
        aiohttp.ClientResponseError,
        aiohttp.ClientPayloadError,
        aiohttp.ServerTimeoutError,
        aiohttp.ServerDisconnectedError,
        aiohttp.ClientConnectorError,
        # 其他
        smtplib.SMTPServerDisconnected,
        urllib3.exceptions.HTTPError,
        urllib3.exceptions.ProxyError,
    )

    def __init__(
        self,
        max_retries: int = 3,
        delay: float = 2.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
        retry_on_result: Callable[[Any], bool] | None = None,
        re_raise: bool = False,
        handler: Callable[[Exception], Any] | None = None,
        log_traceback: bool = True,
        custom_message: str = '',
    ) -> None:
        self.max_retries = max_retries
        self.delay = delay
        self.exceptions = exceptions
        self.retry_on_result = retry_on_result
        self.re_raise = re_raise
        self.handler = handler
        self.log_traceback = log_traceback
        self.custom_message = custom_message  # 策略级别的默认消息

    def err_back(self, retry_state: RetryCallState):
        """重试失败回调 - 记录错误日志并返回默认值

        Args:
            retry_state: tenacity的重试状态对象
        """
        if retry_state.outcome is None:
            return None

        exc = retry_state.outcome.exception()
        if exc is None:
            # 没有异常，可能是成功但需要重试的情况
            return None

        # 记录重试统计信息
        attempt_number = getattr(retry_state, 'attempt_number', 0)
        msg = f'{self.custom_message}重试({attempt_number})次失败 |'

        handle_exception(exc=exc, re_raise=self.re_raise, handler=self.handler, log_traceback=self.log_traceback, custom_message=msg)

        return exc


def _create_tenacity_adapter(max_retries: int, delay: float, exceptions: tuple[type[Exception], ...], handler: Callable[..., Any] | None) -> Callable:
    """创建tenacity重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 等待时间范围（秒）
        exceptions: 需要重试的异常类型元组
        handler: 重试处理器实例

    Returns:
        配置好的tenacity重试装饰器
    """
    retry_condition = retry_if_exception_type(exceptions)

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_random(0, delay),
        retry=retry_condition,
        retry_error_callback=handler,
    )


def tenacity_retry_wraps(
    fn: Callable[..., Any] | None = None,
    max_retries: int = 3,
    delay: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    retry_on_result: Callable[[Any], bool] | None = None,
    re_raise: bool = False,
    handler: Callable[[Exception], Any] | None = None,
    log_traceback: bool = True,
    custom_message: str = '',
) -> Callable:
    """重试装饰器 - 基于tenacity库，提供函数执行失败自动重试功能，支持同步和异步函数

    核心功能：
    - 自动识别并适配同步/异步函数
    - 可配置最大重试次数和等待时间范围
    - 可自定义重试的异常类型
    - 支持重试前后的回调函数
    - 提供异常静默处理和默认返回值机制
    - 统一的异常日志记录

    Args:
        fn: 被装饰的函数
        max_retries: 最大重试次数，默认3
        delay: 最大等待时间（秒），默认2.0
        exceptions: 触发重试的异常类型元组，默认(Exception,)
        retry_on_result: 自定义结果判断函数，默认None
        re_raise: 是否重新抛出异常，默认False
        handler: 异常处理函数，默认retry_handler.err_back
        log_traceback: 是否记录完整堆栈信息，默认True
        custom_message: 自定义错误提示信息，默认空字符串

    Returns:
        装饰后的函数，保持原函数签名和类型
    """

    def decorator(func: Callable) -> Callable:
        # 创建RetryHandler实例,设置基础消息和默认返回
        func_location = get_function_location(func)

        retry_handler = RetryHandler(
            max_retries=max_retries,
            delay=delay,
            exceptions=exceptions,
            retry_on_result=retry_on_result,
            re_raise=re_raise,
            handler=handler,
            log_traceback=log_traceback,
            custom_message=f'{custom_message} {func_location}',
        )

        # 创建tenacity的retry装饰器
        tenacity_retry = _create_tenacity_adapter(max_retries, delay, exceptions, handler or retry_handler.err_back)
        # 同步函数包装器

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return tenacity_retry(func)(*args, **kwargs)
            except Exception as exc:
                handle_exception(exc=exc, re_raise=re_raise, handler=handler, log_traceback=log_traceback, custom_message=custom_message)

        # 异步函数包装器
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 使用tenacity_retry包装函数调用
                return await tenacity_retry(func)(*args, **kwargs)
            except Exception as exc:
                handle_exception(exc=exc, re_raise=re_raise, handler=handler, log_traceback=log_traceback, custom_message=custom_message)

        # 根据函数类型返回相应的包装器
        if is_async_function(func):
            return async_wrapper
        return sync_wrapper

    return decorator if fn is None else decorator(fn)


__all__ = [
    'TRETRY',
    'tenacity_retry_wraps',
]
