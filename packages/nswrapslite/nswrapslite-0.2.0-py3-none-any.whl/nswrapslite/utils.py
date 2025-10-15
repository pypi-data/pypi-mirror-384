# !/usr/bin/env python3
"""
==============================================================
Description  : 核心工具函数模块
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-09-28 16:41:00
Github       : https://github.com/sandorn/nswrapslite

提供核心工具函数，支持装饰器实现。
==============================================================
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def is_async_function(func: Callable[..., Any] | None) -> bool:
    """检查函数是否为异步函数

    Args:
        func: 要检查的函数

    Returns:
        bool: 如果是异步函数返回True，否则返回False
    """
    if func is None:
        return False
    return inspect.iscoroutinefunction(func)


def is_sync_function(func: Callable[..., Any] | None) -> bool:
    """检查函数是否为同步函数

    Args:
        func: 要检查的函数

    Returns:
        bool: 如果是同步函数返回True，否则返回False
    """
    # 处理None值
    if func is None:
        return False
    return not inspect.iscoroutinefunction(func)


def get_function_signature(func: Callable[..., Any] | None) -> str:
    """获取函数的签名信息

    Args:
        func: 要获取签名的函数

    Returns:
        str: 函数的签名字符串
        print(get_function_signature(get_function_signature))
        输出: get_function_signature(func: 'Callable') -> 'str'
    """
    if func is None:
        return '()'
    try:
        sig = inspect.signature(func)
        return f'{func.__name__}{sig}'
    except (ValueError, TypeError):
        return f'{func.__name__}()'


def get_function_location(func: Callable[..., Any] | None) -> str:
    """
    获取函数的位置信息(文件、行号、函数名)，支持各种装饰器包括类装饰器

    Args:
        func: 要获取位置信息的函数，可以是普通函数、方法、装饰器包装的函数等

    Returns:
        str: 格式为 "文件路径:行号@函数名 | " 的字符串，用于日志记录
    """
    # 基础检查
    if func is None or not callable(func):
        return 'unknown:0@unknown | '

    try:
        # 首先尝试直接解包（处理普通装饰器）
        try:
            unwrapped = inspect.unwrap(func)
            # 如果解包后的函数与原函数不同，说明有装饰器
            if unwrapped is not func:
                # 递归处理解包后的函数
                return get_function_location(unwrapped)
        except (ValueError, AttributeError):
            pass  # 解包失败，继续其他方法

        # 检查是否是类装饰器的实例
        if _is_class_decorator_instance(func):
            return _handle_class_decorator_instance(func)

        # 检查是否是绑定方法
        if hasattr(func, '__self__') and hasattr(func, '__func__'):
            return _handle_bound_method(func)

        # 对于普通函数，使用 __code__ 属性
        if hasattr(func, '__code__'):
            code = func.__code__
            func_name = _get_function_name(func)
            filename = code.co_filename
            lineno = code.co_firstlineno
            return f'{filename}:{lineno}@{func_name} | '

        # 最后的回退方案
        return _get_fallback_location(func, None)

    except Exception as e:
        # 处理无法获取位置信息的情况
        return _get_fallback_location(func, e)


def _is_class_decorator_instance(obj: Any) -> bool:
    """检查对象是否是类装饰器的实例"""
    # 类装饰器的实例通常：
    # 1. 是一个类的实例（不是函数或类型）
    # 2. 可调用（有 __call__ 方法）
    # 3. 不是内置类型
    # 4. 通常包装了一个原始函数

    if not hasattr(obj, '__class__'):
        return False

    # 排除函数、方法、类型和内置对象
    if callable(obj) and not isinstance(obj, type):
        class_name = obj.__class__.__name__
        # 检查是否有常见的包装函数属性
        wrapper_attrs = ['__wrapped__', '_func', 'func', 'wrapped', '__original_func__']
        has_wrapper_attr = any(hasattr(obj, attr) for attr in wrapper_attrs)

        # 或者类名暗示它是装饰器
        is_likely_decorator = any(name in class_name.lower() for name in ['decorator', 'wrapper', 'proxy'])

        return has_wrapper_attr or is_likely_decorator

    return False


def _handle_class_decorator_instance(decorator_instance: Any) -> str:
    """处理类装饰器实例"""
    try:
        # 尝试从常见属性中获取原始函数
        wrapper_attrs = [
            '__wrapped__',  # 标准装饰器协议
            '_func',  # 常见命名
            'func',  # 常见命名
            'wrapped',  # 常见命名
            '__original_func__',  # 明确命名的原始函数
            'function',  # 有时使用
            'fn',  # 缩写
        ]

        for attr_name in wrapper_attrs:
            if hasattr(decorator_instance, attr_name):
                attr_value = getattr(decorator_instance, attr_name)
                if callable(attr_value):
                    # 递归处理找到的原始函数
                    return get_function_location(attr_value)

        # 如果找不到原始函数，尝试检查 __call__ 方法
        if callable(decorator_instance.__class__):
            call_method = decorator_instance.__class__.__call__
            if hasattr(call_method, '__func__'):
                # 对于未绑定的方法
                code = call_method.__func__.__code__
                class_name = decorator_instance.__class__.__name__
                return f'{code.co_filename}:{code.co_firstlineno}@{class_name}.__call__ | '

        # 最后的手段：使用类本身的信息
        class_name = decorator_instance.__class__.__name__
        module_name = getattr(decorator_instance.__class__, '__module__', 'unknown')
        return f'{module_name}:0@{class_name} | '

    except Exception:
        return _get_fallback_location(decorator_instance, None)


def _handle_bound_method(method: Callable[..., Any]) -> str:
    """处理绑定方法"""
    try:
        # 获取底层函数
        func = method.__func__
        code = func.__code__

        # 获取方法名和类名
        method_name = _get_function_name(func)
        class_name = method.__self__.__class__.__name__

        return f'{code.co_filename}:{code.co_firstlineno}@{class_name}.{method_name} | '
    except Exception:
        return _get_fallback_location(method, None)


def _get_function_name(func: Callable[..., Any]) -> str:
    """安全地获取函数名称"""
    try:
        # 优先使用__qualname__获取完整限定名
        if hasattr(func, '__qualname__'):
            name = func.__qualname__
            if name and name != '<unknown>':
                return name

        # 回退到__name__
        name = getattr(func, '__name__', None)
        if name and name != '<unknown>':
            return name

        # 对于lambda函数
        if hasattr(func, '__code__'):
            code_name = func.__code__.co_name
            if code_name != '<lambda>':
                return code_name
            return 'lambda'

        return 'unknown'
    except Exception:
        return 'unknown'


def _get_fallback_location(func: Callable[..., Any], error: Exception | None) -> str:
    """获取回退的位置信息"""
    try:
        # 尝试获取模块信息
        module = getattr(func, '__module__', None)
        if not module and hasattr(func, '__class__'):
            module = getattr(func.__class__, '__module__', None)

        if module and module != 'builtins':
            func_name = _get_function_name(func)
            return f'{module}:0@{func_name} | '

        # 对于内置函数或C扩展
        func_name = _get_function_name(func)
        return f'builtin:0@{func_name} | '

    except Exception:
        return 'unknown:0@unknown | '


__all__ = [
    'get_function_location',
    'is_async_function',
    'is_sync_function',
    'get_function_signature',
]
