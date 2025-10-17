# -*-coding:utf-8-*-
"""
Created on 2024/04/28

@author: 臧韬

@desc: 默认描述
"""
import requests

from .signature import getSign
from .time import getTimestamp


class SpaceSender:
    @classmethod
    def sendApi(cls, entry, appId, element: str, func: str, argDict: dict, headers: dict = None):
        """
        myapp之间接口转发
        :param entry: 请求入口
        :param appId: 发送给哪个app
        :param element: 元素的fullName(通常是svc)
        :param func: 具体调用的函数
        :param argDict: 具体请求数据
        :param headers: 具体请求头
        :return:
        """
        path = "/api/{appId}/{element}/{func}".format(
            appId=appId.replace(".", "/"), element=element.replace(".", "/"), func=func
        )
        headers = headers or {}
        url = "{entry}{path}".format(entry=entry, path=path)
        token = headers.get("token", "")
        timestamp = str(getTimestamp())
        paramDict = {"path": path, "token": token, "timestamp": timestamp, **argDict}
        sign = getSign(paramDict)
        headers["sign"] = sign
        headers["timestamp"] = timestamp
        headers["Domain"] = entry
        response = requests.post(url, json=argDict, headers=headers)
        if response.status_code != 200:
            raise Exception("请求失败")
        respJson = response.json()
        return respJson
