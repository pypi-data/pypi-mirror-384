# -*-coding:utf-8-*-
"""
Created on 2023/7/12

@author: 臧韬

@desc: 默认描述
"""
import copy
from abc import ABCMeta, abstractmethod


class BaseMatchRole(metaclass=ABCMeta):
    successMsg = ""

    @abstractmethod
    def hash(self, data) -> int:
        """
        将 Dict 数据按照自定义的方式进行hash，返回一个hash int
        如果这里返回的是None，则被认为不合格数据，将不进行匹配
        """
        pass


class MatchResultNumEnum:
    success = 0
    oldOnly = -1
    newOnly = 1


# 这个的 作用是 给MatchTool.match返回值 构建返回 数据
class MatchResult(object):
    DEFAULT_SUCCESS_RESULT_STRING = "匹配成功"
    DEFAULT_OLD_ONLY_RESULT_STRING = "只有旧数据匹配"
    DEFAULT_NEW_ONLY_RESULT_STRING = "只有新数据匹配"

    def __init__(self, oldData=None, newData=None, resultStr=None):
        self.oldData = oldData
        self.newData = newData
        self.resultStr = resultStr

    @property
    def resultNum(self):
        if self.oldData and self.newData:
            return MatchResultNumEnum.success
        if self.oldData:
            return MatchResultNumEnum.oldOnly
        if self.newData:
            return MatchResultNumEnum.newOnly

    @property
    def matchResultStr(self):
        if self.resultStr:
            return self.resultStr
        if self.resultNum == MatchResultNumEnum.success:
            return self.DEFAULT_SUCCESS_RESULT_STRING
        if self.resultNum == MatchResultNumEnum.oldOnly:
            return self.DEFAULT_OLD_ONLY_RESULT_STRING
        if self.resultNum == MatchResultNumEnum.newOnly:
            return self.DEFAULT_NEW_ONLY_RESULT_STRING
        return "未知错误"

    def toDict(self):
        return {
            "oldData": self.oldData,
            "newData": self.newData,
            "resultStr": self.resultStr,
            "matchResultStr": self.matchResultStr,
        }

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.matchResultStr)


class MatchHashData(object):
    def __init__(self, data, hashList=None):
        self.data = data
        self.hashList = hashList


class MatchTool(object):
    """
    匹配工具，自定义匹配规则，只要有一个匹配成功，则算匹配成功。
    """

    matchRoles = []
    matchResultCls = MatchResult

    @classmethod
    def match(cls, oldList: list, newList: list):
        # 避免污染数据源
        oldList = copy.deepcopy(oldList)
        newList = copy.deepcopy(newList)

        result = []
        # 循环是判断匹配规则，可能会thirdDeptId 等多个匹配规则 或判断
        for matchRole in cls.matchRoles:
            oldHashMap = cls.getHashMap(oldList, matchRole())
            newHashMap = cls.getHashMap(newList, matchRole())
            hashSet = set(oldHashMap.keys()) | set(newHashMap.keys())
            for h in hashSet:
                oldData = oldHashMap.get(h)
                newData = newHashMap.get(h)
                if oldData and newData:
                    # 匹配成功，只要匹配成功，这个数据就不用进行下个匹配规则
                    oldHashMap.pop(h)
                    newHashMap.pop(h)
                    result.append(cls.matchResultCls(oldData, newData, matchRole.successMsg))

            # 通过一次匹配规则后，将已经匹配的数据对从列表中删除
            oldList = list(oldHashMap.values())
            newList = list(newHashMap.values())

        # 经过所有匹配规则中，将未匹配到的数据也加到匹配结果中
        for oldData in oldList:
            # 只有老数据，没有新数据匹配
            result.append(cls.matchResultCls(oldData=oldData))

        for newData in newList:
            # 只有新数据，没有老数据匹配
            result.append(cls.matchResultCls(newData=newData))

        return result

    @classmethod
    def getHashMap(cls, dataList, matchRole: BaseMatchRole) -> dict:
        """
        将多个数据，按照hash规则转换成map
        """
        hashMap = {}
        for data in dataList:
            h = matchRole.hash(data)
            if h is None:
                h = hash(str(data))
            hashMap.setdefault(h, data)
        return hashMap
