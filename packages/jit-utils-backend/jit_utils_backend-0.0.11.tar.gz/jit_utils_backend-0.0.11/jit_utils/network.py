# -*-coding:utf-8-*-
"""
Created on 2024/10/31 11:08

@author: 'wuhao'

@desc:
"""
import socket


def checkConnect(host, port, timeout=0.3):
    """
    检查ip和端口是否合法
    :param ip:
    :param port:
    :return:
    """
    try:
        port = int(port)
    except ValueError:
        return False
    if not (0 <= port <= 65535):
        return False
    if host.startswith("127") and host != "127.0.0.1":
        return False
    # 检查ip port 是否开启
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except:  # noqa E722
        return False
    finally:
        s.close()
