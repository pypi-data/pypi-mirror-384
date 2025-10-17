# -*-coding:utf-8-*-
"""
Created on 2025/02/10

@author: 臧韬

@desc: 默认描述
"""
import base64
import io

import barcode
from barcode.errors import BarcodeError
from barcode.writer import ImageWriter


class Barcode(object):
    """
    二维码模块，暂用于文件渲染
    """

    def __init__(self, value: str, codeType="code128"):
        self.value = value
        self.codeType = codeType

    def toByte(self):
        file = self.toFile()
        data = file.read()
        return data

    def toFile(self):
        obj = barcode.get(self.codeType, self.value, writer=ImageWriter())
        # 保存条形码为图像文件
        imageBuffer = io.BytesIO()
        obj.write(fp=imageBuffer)
        imageBuffer.seek(0)
        return imageBuffer

    def toStr(self):
        if not self.value:
            return ""
        try:
            b64Code = base64.b64encode(self.toByte()).decode("utf-8")
        except BarcodeError as e:
            return "ERROR:{}".format(str(e))

        return "<image:{}>".format(b64Code)

    def __str__(self):
        return self.toStr()
