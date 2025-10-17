# -*-coding:utf-8-*-
"""
Created on 2025/1/13 15:54

@author: 'wuhao'

@desc:
"""
import os
import traceback

from jit.commons.utils.logger import log
from jit.errcode import ElementErrCode


class BaseElementException(object):
    PREFIX = "exc"

    def __init__(self, fullName, title):
        self.fullName = fullName
        self.title = title

    def getTrace(self, exc):
        trace = traceback.extract_tb(exc.__traceback__)[-1]
        filename, lineno, func, text = trace
        filename = filename.replace(os.environ["rootPath"], "").replace(os.sep, ".")
        return filename, lineno, func, text

    # def other(self,exc):
    #     """
    #     遇到未定义的异常类型处理时调用
    #     :param exc:
    #     :return:
    #     """

    def handleException(self, exc):
        exceptionName = type(exc).__name__
        log.exception(exc)
        handler = getattr(self, self.PREFIX + exceptionName, None)
        if handler:
            code = handler(exc)
            return code
        # 遇到使用者为定义的异常类型处理时调用
        elif hasattr(self, "other"):
            code = self.other(exc)
            return code
        # 没定义任何处理
        else:
            return None

    def excAttributeError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "访问了{objName}对象不存在的属性{attrName}，在文件{filename}第{lineno}行,异常代码:{text}".format(
            objName=exc.obj, attrName=exc.name, filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excValueError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "无效的值,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excTypeError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "不支持的类型操作,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excIndexError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "索引越界,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excKeyError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "字典没有这个key,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excNameError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "没有定义的变量,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excSyntaxError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "语法错误,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code

    def excZeroDivisionError(self, exc):
        filename, lineno, func, text = self.getTrace(exc)
        errMsg = "除数为0,在文件{filename}第{lineno}行,异常代码:{text}".format(
            filename=filename, lineno=lineno, text=text
        )
        code = ElementErrCode.ELEMENT_ERROR.formatReason(fullName=self.fullName, title=self.title, errMsg=errMsg)
        return code
