# -*-coding:utf-8-*-
"""
Created on 2024/12/11

@author: 臧韬

@desc: 默认描述
"""

import inspect
import types


class MethodForwarder(object):
    """
    cls方法转换器，可以将这个函数的所有方法都转换成目标函数，可以在不修改原始类的任何代码情况进行装饰。
    使用方法:
    def myfunc(args, kwargs, extends):
        # 目标函数
        return 2

    class MyClass(object):
        def func(self):
            return 1

    @ClsForward(myFunc)
    class ForwardClass(MyClass):
        pass

    >> MyClass().func()
    1

    >> ForwardClass().func()
    2

    特点：
    1. 目标函数中如果返回了 ClsForward.DoNotForward，则会执行原来的函数或者方法
    2. 目标函数的入参必须是 args, kwargs, extend
       args, kwargs 是调用这个函数的参数
       extend是一个字典，包含3个参数
        cls -> 类对象
        self -> 如果是通过实例化的对象调用的函数或方法，这里会传入实例对象
        func -> 执行的函数对象，如果是类方法，则返回的绑定到这个类的method对象。如果是成员方法和静态方法，则传入的是function对象。
    3. 可以在装饰器的入参中指定excludeFunc，函数名满足这个函数则不会转发
    参考:
    def excludeFunc(name):
        return name == "view" and name.startswith("_")

    @ClsForward(myFunc, excludeFunc=excludeFunc)
    class ForwardClass(MyClass):
        pass

    这样这个类在遇到view函数和开头为下划线的函数，则不会转换。
    excludeFunc是选传的，默认情况下忽略下划线开头的函数。
    """

    DoNotForward = object()

    def __init__(self, targetFunc, excludeFunc=None):
        self.targetFunc = targetFunc
        self.clss = None
        self.excludeFunc = excludeFunc or self.defaultExcludeFunc

    def __call__(self, clss):
        self.clss = clss

        for name in dir(clss):
            if callable(self.excludeFunc):
                if self.excludeFunc(name):
                    continue
            func = getattr(clss, name)
            if inspect.ismethod(func):
                setattr(clss, name, classmethod(self.classForward(func, self.targetFunc)))
            if inspect.isfunction(func):
                setattr(clss, name, self.classForward(func, self.targetFunc))
        return clss

    def classForward(self, func, targetFunc):

        def wrapper(*args, **kwargs):
            # 如果是实例调用方法，args第一个会传入对象
            if args and (isinstance(args[0], self.clss) or issubclass(args[0], self.clss)):
                sf, *rArgs = args
                rArgs = tuple(rArgs)
            else:
                sf = None
                rArgs = args

            extend = {
                "clss": self.clss,
                "self": sf,
                "func": func,
            }
            result = targetFunc(rArgs, kwargs, extend)
            if result is self.DoNotForward:
                if sf:
                    if inspect.isfunction(func):
                        # 实例方法
                        return types.MethodType(func, sf)(*rArgs, **kwargs)
                    else:
                        # 类方法
                        return types.MethodType(func.__func__, sf)(*rArgs, **kwargs)
                else:
                    # 静态方法
                    return func(*rArgs, **kwargs)

            return result

        return wrapper

    @staticmethod
    def defaultExcludeFunc(name):
        return name.startswith("_")
