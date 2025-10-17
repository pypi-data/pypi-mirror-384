# -*-coding:utf-8-*-
"""
Created on 2023/10/25 20:04

@author: 'wuhao'

@desc: 简单说明
"""
import hashlib
import math
import os
import random
import re
import string
import uuid

CHARS = string.ascii_letters + string.digits


def randomString(size=8):
    chars = random.choices(CHARS, k=size)
    return "".join(chars)


def randomNum(size=6):
    """生成随机6位数字，用于手机号验证码"""
    num = "%0{}d".format(size) % random.randint(0, 10**size - 1)
    return num


def getUuidStr():
    return str(uuid.uuid4()).replace("-", "")


def md5Bytes(b):
    """
    md5加密
    :param b: 文件的二进制数据
    :return: str: md5字符串
    """
    return hashlib.md5(b).hexdigest()


def md5Str(normalStr, encodeType="utf-8"):
    """
    md5加密
    :param normalStr: 普通python字符串
    :param encodeType: 编码方式
    :return str: md5字符串
    """
    return md5Bytes(normalStr.encode(encodeType))


def lowercase(name):
    if not name:
        return ""
    return name[0].lower() + name[1:]


def capitalize(name):
    if not name:
        return ""
    return name[0].upper() + name[1:]


def getFileMd5(filename):
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = open(filename, "rb")
    while True:
        b = f.read(4096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()


def getRandomField(k=4):
    character = string.ascii_lowercase + string.digits
    charArray = random.choices(character, k=k)
    res = "fk" + "".join(charArray)
    return res


def getRandom(k=8):
    character = string.ascii_lowercase + string.digits
    charArray = random.choices(character, k=k)
    return "".join(charArray)


def genrSublist(orgList, sliceSize):
    """
    for tempList in genrSublist(range(20), 5):
        print(tempList)

    [0, 1, 2, 3, 4]
    [5, 6, 7, 8, 9]
    [10, 11, 12, 13, 14]
    [15, 16, 17, 18, 19]
    """
    sliceCount = int(math.ceil(len(orgList) / float(sliceSize)))
    for i in range(sliceCount):
        yield orgList[i * sliceSize : (i + 1) * sliceSize]


def renderTemplateString(source, **context):
    # 使用正则表达式查找所有的变量 {{var_name}}
    pattern = r"\{\{(\w+)\}\}"

    def replaceVar(match):
        var_name = match.group(1)  # 获取变量名
        return str(context.get(var_name, ""))  # 从上下文中获取变量值，如果不存在则返回空字符串

    rendered = re.sub(pattern, replaceVar, source)

    return rendered
