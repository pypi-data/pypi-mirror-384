# -*-coding:utf-8-*-
"""
Created on 2023/10/23

@author: 臧韬

@desc: 默认描述
"""
from .field import Field, NoneType

__all__ = ["TlConfig"]


class TlConfigMeta(type):
    def __new__(mcs, name, bases, attrs):
        _fieldMap = {}
        _newAttrs = {"_fieldMap": _fieldMap}

        for key, value in attrs.items():
            if isinstance(value, Field):
                # 字段名写入到字段对象中
                value.name = key
                _fieldMap[key] = value
            else:
                _newAttrs[key] = value

        _cls = super(TlConfigMeta, mcs).__new__(mcs, name, bases, _newAttrs)
        return _cls


class TlConfig(metaclass=TlConfigMeta):
    _autoCheck = True

    def __init__(self, **kwargs):
        self._originData = kwargs
        self._transformData = {}
        self._isTransform = False
        for key, value in self._fieldMap.items():
            super(TlConfig, self).__setattr__(key, NoneType)
        if self._autoCheck:
            self.check()

    def check(self):
        if not self._isTransform:
            for fieldKey, field in self._fieldMap.items():
                value = self._originData.get(fieldKey, NoneType)
                setattr(self, fieldKey, value)
            self._isTransform = True

    def checkOne(self, field, value):
        value = field.transform(value)
        if value is NoneType and field.default is not NoneType:
            value = field.default
        field.check(value)
        self._transformData[field.name] = value
        super(TlConfig, self).__setattr__(field.name, value)

        return value

    def toDict(self):
        if not self._isTransform:
            print("警告，该配置没有经过校验和转换，请先调用 self.check()")
        return self._transformData

    def __setattr__(self, key, value):
        if not self._autoCheck:
            super(TlConfig, self).__setattr__("_isTransform", False)
        if key in self._fieldMap:
            self._originData[key] = value
            if self._autoCheck:
                field = self._fieldMap[key]
                self.checkOne(field, value)
        else:
            super(TlConfig, self).__setattr__(key, value)

    @classmethod
    def getParamInfo(cls):
        return list(cls._fieldMap.keys())

    def __getattribute__(self, item):
        """
        DEBUG 代码排查模式，尽快删除
        :param item:
        :return:
        """
        value = super(TlConfig, self).__getattribute__(item)
        if item.startswith("__"):
            return value
        # log.debug("DEBUG MODE: CLS:{}, KEY:{}, VALUE:{}".format(self.__class__.__name__, item, str(value)))
        return value
