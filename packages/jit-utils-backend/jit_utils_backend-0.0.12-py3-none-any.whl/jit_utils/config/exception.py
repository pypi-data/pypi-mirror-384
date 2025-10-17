# -*-coding:utf-8-*-
"""
Created on 2023/10/23

@author: 臧韬

@desc: 默认描述
"""

from jit.errcode import Code


class TlConfigException(Code):
    DEFAULT_RESULT = "配置信息错误"

    def __init__(self, reason=DEFAULT_RESULT, code=-2, msg=None, solution=None):
        super(TlConfigException, self).__init__(code=code, reason=reason, msg=msg, solution=solution)
