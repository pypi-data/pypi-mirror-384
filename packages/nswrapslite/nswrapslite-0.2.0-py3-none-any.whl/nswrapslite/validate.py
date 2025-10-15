#!/usr/bin/env python3
"""
==============================================================
Description  : 属性验证和类型检查模块 - 提供变量初始化检查和类型验证功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-01 13:00:00
Github       : https://github.com/sandorn/nswrapslite

本模块提供以下核心功能：
- ensure_initialized：确保对象属性已初始化的装饰器
- TypedProperty：属性类型检查描述符，支持类型验证和None值控制
- type_check：类属性类型检查装饰器
- type_check_wrapper：函数参数类型检查装饰器
- typed_property：TypedProperty的便捷函数版本
- readonly：只读属性装饰器

主要特性：
- 支持基本类型和联合类型检查
- 灵活控制是否允许None值
- 与Python描述符协议完全兼容
- 提供友好的错误信息
- 完整的类型提示支持
==============================================================
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any


def ensure_initialized(var_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """确保变量已初始化装饰器

    Args:
        var_name: 需要检查是否初始化的变量名

    Returns:
        装饰后的函数

    Raises:
        RuntimeError: 当变量未初始化时抛出
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(self: object, *args: Any, **kwargs: Any) -> Any:
            if not hasattr(self, var_name):
                # 修复缺少basemsg参数的问题，使用正确的参数名
                raise RuntimeError(f'{var_name} not initialized') from None
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class TypedProperty:
    """属性类型检查描述符
    用于在赋值时强制执行类型检查
    与__slots__不兼容，因为直接操作__dict__
    """

    def __init__(self, name: str, expected_type: type | tuple[type, ...], allow_none: bool = False) -> None:
        self.name = name
        self.expected_type = expected_type
        self.allow_none = allow_none
        # 添加__name__属性以支持类型检查
        if isinstance(expected_type, tuple):
            self.__name__ = ' | '.join(t.__name__ for t in expected_type)
        else:
            self.__name__ = expected_type.__name__

    def __get__(self, instance: object, cls: type) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance: object, value: Any) -> None:
        # 检查值是否为None且允许None
        if value is None:
            if self.allow_none:
                instance.__dict__[self.name] = value
                return
            raise TypeError(f'{self.name} cannot be None')

        # 检查类型
        if not isinstance(value, self.expected_type):
            expected_names = ' or '.join(t.__name__ for t in self.expected_type) if isinstance(self.expected_type, tuple) else self.expected_type.__name__
            raise TypeError(f'{self.name} must be of type {expected_names}, got {type(value).__name__} instead')

        instance.__dict__[self.name] = value

    def __delete__(self, instance: object) -> None:
        if self.name in instance.__dict__:
            del instance.__dict__[self.name]


def type_check(**kwargs: type | tuple[type, ...] | dict[str, Any]) -> Callable[[type], type]:
    """类型检查装饰器
    为类属性添加类型检查功能

    参数:
        **kwargs: 属性名和期望类型的映射，可以是:
            - 属性名=类型: 基本用法，指定属性的类型
            - 属性名=(类型1, 类型2, ...): 支持联合类型
            - 属性名={'type': 类型, 'allow_none': True}: 高级用法，指定类型和None值处理

    返回:
        装饰后的类

    示例:
        @type_check(name=str, age=int)
        class Person:
            pass

        @type_check(name=str, age=(int, float), score={'type': int, 'allow_none': True})
        class Student:
            pass

    注意:
        - 与__slots__不兼容，因为使用__dict__存储属性
        - 所有装饰的属性必须通过实例赋值，不能在类级别定义
    """

    def decorate(cls: type) -> type:
        for name, type_info in kwargs.items():
            # 处理高级配置格式
            if isinstance(type_info, dict):
                expected_type = type_info.get('type', Any)
                allow_none = type_info.get('allow_none', False)
                setattr(cls, name, TypedProperty(name, expected_type, allow_none))
            else:
                # 处理基本格式（直接是类型或类型元组）
                setattr(cls, name, TypedProperty(name, type_info))
        return cls

    return decorate


# 修复property相关问题
def typed_property(name: str, expected_type: type | tuple[type, ...], allow_none: bool = False) -> property:
    """创建类型检查的property属性

    为类属性创建带有类型检查的property装饰器，使用Python标准property机制

    参数:
        name: 属性名称
        expected_type: 期望的类型，可以是单个类型或类型元组（联合类型）
        allow_none: 是否允许属性值为None，默认为False

    返回:
        带有类型检查功能的property对象
        (使用property装饰器确保正确类型)

    示例:
        class Person:
            name = typed_property('name', str)
            age = typed_property('age', int)
            score = typed_property('score', (int, float), allow_none=True)

    注意:
        - 与slots兼容，因为使用getattr/setattr而不是直接操作__dict__
        - 属性值实际存储在以下划线为前缀的私有属性中
    """
    storage_name = f'_{name}'

    # 定义getter方法
    def getter(self: object) -> Any:
        return getattr(self, storage_name, None)

    # 定义setter方法
    def setter(self: object, value: Any) -> None:
        # 检查值是否为None且允许None
        if value is None:
            if allow_none:
                setattr(self, storage_name, value)
                return
            raise TypeError(f'{name} cannot be None')

        # 检查类型
        if not isinstance(value, expected_type):
            expected_names = ' or '.join(t.__name__ for t in expected_type) if isinstance(expected_type, tuple) else expected_type.__name__
            raise TypeError(f'{name} must be of type {expected_names}, got {type(value).__name__} instead')

        setattr(self, storage_name, value)

    # 定义deleter方法
    def deleter(self: object) -> None:
        if hasattr(self, storage_name):
            delattr(self, storage_name)

    # 创建并返回property对象
    return property(fget=getter, fset=setter, fdel=deleter)


def readonly(name: str) -> property:
    """
    创建只读属性的property生成器

    为类创建一个只读属性，隐藏真实的存储属性名
    与__slots__兼容，使用getattr/setattr机制

    参数:
        name: 存储属性的名称

    返回:
        只读的property对象

    示例:
        class Person:
            def __init__(self, name):
                self._name = name  # 注意：这里必须使用下划线前缀存储实际值
            name = readonly('_name')

        p = Person("Alice")
        print(p.name)  # 输出: Alice
        p.name = "Bob"  # 抛出AttributeError: 无法修改只读属性
    """
    storage_name = name

    # 定义getter方法
    def getter(self: object) -> Any:
        return getattr(self, storage_name)

    # 定义setter方法
    def setter(self: object, value: Any) -> None:
        """尝试设置只读属性时抛出AttributeError"""
        raise AttributeError(f"'{self.__class__.__name__}.{storage_name.lstrip('_')}' is read-only")

    # 定义deleter方法
    def deleter(self: object) -> None:
        """尝试删除只读属性时抛出AttributeError"""
        raise AttributeError(f"Cannot delete read-only attribute '{self.__class__.__name__}.{storage_name.lstrip('_')}'")

    # 创建并返回property对象
    return property(getter, setter, deleter)


def type_check_wrapper(
    *types: type | tuple[type, ...],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    参数类型检查装饰器，支持同步函数、实例方法、类方法和联合类型（元组类型）。
    :param types: 期望的参数类型，可以是单个类型或类型元组（联合类型）
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 检查是否是类方法调用（第一个参数是self或cls）
            start_index = 0
            if args and hasattr(args[0], '__class__') and args[0].__class__.__name__ != 'type':
                # 如果是实例方法，跳过self参数
                start_index = 1
            elif args and hasattr(args[0], '__name__') and isinstance(args[0], type):
                # 如果是类方法，跳过cls参数
                start_index = 1

            # 从start_index开始检查参数类型
            for i, (a, t) in enumerate(zip(args[start_index:], types, strict=False)):
                if not isinstance(a, t):
                    # 处理元组类型（联合类型）
                    type_names = ' or '.join([ty.__name__ for ty in t]) if isinstance(t, tuple) else t.__name__
                    raise TypeError(f'参数 {i + start_index} 应为 {type_names}, 实际为 {type(a).__name__}')
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    'TypedProperty',
    'ensure_initialized',
    'readonly',
    'type_check',
    'type_check_wrapper',
    'typed_property',
]
