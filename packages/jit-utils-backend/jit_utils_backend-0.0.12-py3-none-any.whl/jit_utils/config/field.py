# -*-coding:utf-8-*-

"""
Created on 2023/9/20

@author: 臧韬

@desc: 默认描述
"""
from .exception import TlConfigException


class NoneType(object):
    def __bool__(self):
        return False


class AnyType(object):
    pass


class Inf(float):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(Inf, cls).__new__(cls, "inf")
        return cls.__instance

    def __gt__(self, other):
        return False

    def __str__(self):
        return "无穷大"

    def __neg__(self):
        return NegInf()

    def __invert__(self):
        return NegInf()

    def __floordiv__(self, other):
        return self

    def __truediv__(self, other):
        return self


class NegInf(float):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(NegInf, cls).__new__(cls, "-inf")
        return cls.__instance

    def __gt__(self, other):
        return True

    def __str__(self):
        return "无穷小"

    def __neg__(self):
        return Inf()

    def __invert__(self):
        return Inf()


inf = Inf()

# print("<<<<<<<<<<<<<基类被加载")


class Field(object):
    """
    这是一个基类字段
    """

    def __init__(self, argType=AnyType, required=True, default=None, checkFunc=None, transformFunc=None):
        self.argType = argType
        # 当一个字段设置了默认值，那么设置成必传就没有意义
        self.required = False if default else required
        self.default = default
        self.checkFunc = checkFunc
        self.transformFunc = transformFunc

        self.name = None

    def check(self, value):
        if self.required and value is None:
            raise TlConfigException("该字段必传! field={f}".format(f=self.name))
        if self.argType is not AnyType and not isinstance(value, self.argType):
            raise TlConfigException(
                "该参数应该传入的数据类型是={at}, 收到的数据类型={vt}! 值={v}, 字段名={f}".format(
                    at=self.argType.__name__, vt=type(value).__name__, v=str(value), f=self.__class__.__name__
                )
            )
        if callable(self.checkFunc):
            self.checkFunc(value)

    def transform(self, value):
        if value is NoneType:
            return value
        if callable(self.transformFunc):
            try:
                return self.transformFunc(value)
            except Exception as e:
                raise e
        return value


# print("Field: {}".format(id(Field)))


class StringField(Field):
    """
    字符串字段
    """

    DEFAULT_MAX_LEN = 65535
    DEFAULT_MIN_LEN = 0

    def __init__(
        self,
        argType=str,
        required=True,
        default=None,
        maxLen=DEFAULT_MAX_LEN,
        minLen=DEFAULT_MIN_LEN,
        transformFunc=str,
    ):
        super(StringField, self).__init__(
            argType=argType, required=required, default=default, checkFunc=self.stringCheck, transformFunc=transformFunc
        )

        self.maxLen = maxLen
        self.minLen = minLen

    def lengthCheck(self, value, maxLen, minLen):
        if minLen == maxLen and len(value) != minLen:
            raise TlConfigException("{name}的长度应该是 {minLen}".format(name=self.name, minLen=minLen))
        if not minLen <= len(value) <= maxLen:
            raise TlConfigException(
                "{name}的长度必须介于 {minLen} 到 {maxLen} 之前".format(name=self.name, minLen=minLen, maxLen=maxLen)
            )

    def stringCheck(self, value):
        self.lengthCheck(value, maxLen=self.maxLen, minLen=self.minLen)


class IntField(Field):
    DEFAULT_MAX_NUM = inf
    DEFAULT_MIN_NUM = -inf

    def __init__(self, argType=int, required=True, maxNum=DEFAULT_MAX_NUM, minNum=DEFAULT_MIN_NUM, default=None):
        super(IntField, self).__init__(
            argType=argType, required=required, default=default, checkFunc=self.intCheck, transformFunc=self.toInt
        )

        self.maxNum = maxNum
        self.minNum = minNum

    def rangeCheck(self, value, maxNum, minNum):
        if not minNum <= value <= maxNum:
            raise TlConfigException(
                "{name} 的取值范围是 {minNum} 到 {maxNum}".format(name=self.name, minNum=minNum, maxNum=maxNum)
            )

    def toInt(self, value):
        if isinstance(value, str):
            if not value.isnumeric():
                raise TlConfigException("{name} 必须传入数字".format(name=self.name))
        return int(value)

    def intCheck(self, value):
        self.rangeCheck(value=value, maxNum=self.maxNum, minNum=self.minNum)
