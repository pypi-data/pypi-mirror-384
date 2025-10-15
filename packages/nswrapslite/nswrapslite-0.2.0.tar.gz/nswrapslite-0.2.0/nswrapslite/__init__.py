# !/usr/bin/env python3
"""
==============================================================
Description  : nswrapslite - Python装饰器工具库
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 17:15:00
Github       : https://github.com/sandorn/nswrapslite

Python装饰器工具库，提供各种实用的函数装饰器，包括：
- 异常处理（exc_wraps）
- 日志记录（log_wraps）
- 函数执行计时（timer_wraps）
- 重试机制（retry_wraps, retry_wraps_tenacity）
- 单例模式（SingletonMeta, singleton）
- 异步执行器（AsyncExecutor）
- 缓存装饰器（cache_wrapper）
- 验证装饰器（ensure_initialized, type_check）

主要特性：
- 同时支持同步和异步函数
- 完整的类型注解支持
- 保留原始函数的元数据
- 统一的API设计风格
- 丰富的配置选项
- 完善的异常处理机制
==============================================================
"""

from __future__ import annotations

# 导入所有公共API
from .cache import cache_wrapper
from .exception import exception_wraps
from .executor import async_executor, await_future_with_timeout, run_on_executor, syncify, to_future
from .factory import decorator_factory, exc_wrapper_factory, log_wrapper_factory, timer_wrapper_factory
from .log import logging_wraps
from .retry import retry_future, retry_request, retry_wraps, spider_retry
from .singleton import SingletonMeta, SingletonMixin, SingletonWraps, singleton
from .strategy import TimerStrategy, UnifiedWrapper
from .tenacityretry import TRETRY, tenacity_retry_wraps
from .timer import TimerWrapt, timer, timer_wraps
from .utils import get_function_location, get_function_signature, is_async_function, is_sync_function
from .validate import TypedProperty, ensure_initialized, readonly, type_check, type_check_wrapper, typed_property
from .wrapped import decorator_transformer, timing_decorator

# 版本信息
__version__ = '0.2.0'
__author__ = 'sandorn'
__email__ = 'sandorn@live.cn'

__all__ = (
    'TRETRY',
    'SingletonMeta',
    'SingletonMixin',
    'SingletonWraps',
    'TimerStrategy',
    'TimerWrapt',
    'TypedProperty',
    'UnifiedWrapper',
    'async_executor',
    'await_future_with_timeout',
    'cache_wrapper',
    'decorator_factory',
    'decorator_transformer',
    'ensure_initialized',
    'exc_wrapper_factory',
    'exception_wraps',
    'get_function_location',
    'get_function_signature',
    'is_async_function',
    'is_sync_function',
    'log_wrapper_factory',
    'logging_wraps',
    'readonly',
    'retry_future',
    'retry_request',
    'retry_wraps',
    'run_on_executor',
    'singleton',
    'spider_retry',
    'syncify',
    'tenacity_retry_wraps',
    'timer',
    'timer_wrapper_factory',
    'timer_wraps',
    'timing_decorator',
    'to_future',
    'type_check',
    'type_check_wrapper',
    'typed_property',
)
