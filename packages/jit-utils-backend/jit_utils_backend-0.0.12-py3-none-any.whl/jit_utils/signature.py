"""
Created on 2024/8/14 14:24

@author: 'wuhao'

@desc:
"""

import base64
import hashlib
import json
from decimal import Decimal


def formatNumber(obj):
    if isinstance(obj, (float, int)) and not isinstance(obj, bool):
        # 保证不使用科学计数法，保留 10 位精度
        obj = Decimal(str(obj))
        return format(obj, ".32f").rstrip("0").rstrip(".")
    elif isinstance(obj, dict):
        return {k: formatNumber(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [formatNumber(i) for i in obj]
    else:
        return obj


def uniqueParams(paramDict, signKey="sign"):
    parmList = []
    for key in sorted(paramDict.keys(), reverse=True):
        if key == signKey:
            continue
        parmList.append("{key}{val}".format(key=key, val=paramDict[key]))
    return "".join(parmList), len(parmList)


def generateSignature(string, interval, divisor=1.4):
    signString = hashlib.sha1(base64.b64encode(bytes(string, encoding="utf-8"))).hexdigest()
    signStringLen = len(signString)
    sampleCount = int(interval * divisor)
    if sampleCount >= signStringLen:
        return signString
    cycle = int(signStringLen / sampleCount)
    rr = "".join(signString[int(i * cycle)] for i in range(sampleCount))
    return rr


def getSign(paramDict):
    paramDict = formatNumber(paramDict)
    for k, v in paramDict.items():
        if isinstance(v, (list, dict)):
            paramDict[k] = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        else:
            paramDict[k] = v
    uString, lenValue = uniqueParams(paramDict)
    return generateSignature(uString, lenValue)
