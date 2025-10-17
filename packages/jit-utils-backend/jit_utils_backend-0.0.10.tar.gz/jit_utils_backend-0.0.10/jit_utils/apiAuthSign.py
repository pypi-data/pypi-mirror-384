# -*-coding:utf-8-*-
"""
Created on 2024/11/09

@author: 臧韬

@desc: 默认描述
"""

import base64
import hashlib
import json
import time

from jit.commons.utils.logger import log


class Sign(object):
    """
    这个签名算法用于认证服务和api授权元素
    """

    EXPIRE_TIME = 5 * 60 * 1000
    # 签名返回的错误信息，如果是错误信息，返回空tuple，兼容原来通过bool方法校验签名是否通过的写法
    TIME_OUT_ERROR = []
    SIGN_CHECK_ERROR = []
    SIGN_CHECK_SUCCESS = [0]

    def __init__(self, secret):
        self.secret = secret

    def encode(self, args, timestamp, debug=False):
        return self.getSign({**args, "timestamp": timestamp, "secret": self.secret}, debug=debug)

    @staticmethod
    def getSign(args, debug=False):
        nArgs = {}
        for k, v in args.items():
            nArgs[k.lower()] = v
        sortedKeys = sorted(nArgs.keys())
        params = []
        for key in sortedKeys:
            value = nArgs[key]
            if not isinstance(value, str):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            params.append(f"{key}={value}")
        if debug:
            # 隐藏secret
            for idx, param in enumerate(params):
                if param.split("=")[0] == "secret":
                    params[idx] = "secret=*********************"

            paramStr = "&".join(params)

            apiAuthDebug = {
                "paramStr": paramStr,
            }
            log.debug(",".join("{k}:{v}".format(k=k, v=v) for k, v in apiAuthDebug.items()))
            if hasattr(app.request, "respExtraData"):
                app.request.respExtraData["apiAuthDebug"] = apiAuthDebug
        return hashlib.sha1(base64.b64encode("&".join(params).encode("utf-8"))).hexdigest()

    def verify(self, args):
        args = args.copy()
        timestamp = args.pop("timestamp")
        if abs(int(time.time() * 1000) - int(timestamp)) > self.EXPIRE_TIME:
            return self.TIME_OUT_ERROR
        signature = args.pop("accessSign")
        debug = app.request.headers.get("debug") == "1"
        if signature == self.encode(args, timestamp, debug=debug):
            return self.SIGN_CHECK_SUCCESS
        else:
            return self.SIGN_CHECK_ERROR
