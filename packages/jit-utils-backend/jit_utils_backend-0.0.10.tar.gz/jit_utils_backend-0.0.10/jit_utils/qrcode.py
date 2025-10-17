# -*-coding:utf-8-*-
"""
Created on 2025/01/21

@author: 臧韬

@desc: 二维码工具，暂时用于文件渲染
"""
import base64
from io import BytesIO

import qrcode


class Qrcode(object):
    """
    二维码模块，暂用于文件渲染
    """

    DEFAULT_ROW = 200
    DEFAULT_COL = 200
    DEFAULT_BOX_SIZE = 10
    DEFAULT_BORDER = 4

    def __init__(self, value: str, row=None, col=None):
        self.value = value
        # self.boxSize = boxSize or self.DEFAULT_BOX_SIZE
        # self.border = border or self.DEFAULT_BORDER
        self.row = row or self.DEFAULT_ROW
        self.col = col or self.DEFAULT_COL

    def toByte(self):
        file = self.toFile()
        data = file.read()
        return data

    def toFile(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=self.DEFAULT_BOX_SIZE,
            border=self.DEFAULT_BORDER,
        )
        # 添加数据
        qr.add_data(self.value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img._img = img.get_image().resize((self.row, self.col))
        imgBytes = BytesIO()
        img.save(imgBytes)
        imgBytes.seek(0)
        return imgBytes

    def toStr(self):
        if not self.value:
            return ""
        return "<image:{}>".format(base64.b64encode(self.toByte()).decode("utf-8"))

    def __str__(self):
        return self.toStr()
