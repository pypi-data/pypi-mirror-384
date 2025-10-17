# -*-coding:utf-8-*-
"""
Created on 2024/11/13

@author: 臧韬

@desc: 默认描述
"""

from setuptools import setup, find_packages
from pathlib import Path

__lib_name__ = 'jit_utils_backend'

this_directory = Path(__file__).parent
read_me_path = this_directory / "README.md"

VERSION = '0.0.12'
DESCRIPTION = 'JIT Utils Backend'

# 处理 README.md 文件
try:
    LONG_DESCRIPTION = read_me_path.read_text(encoding='utf-8')
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

# 配置
setup(
    # 名称必须匹配文件名 'jit-utils-backend'
    name=__lib_name__,
    version=VERSION,
    author="JitAi",
    author_email="support@jit.pro",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        "requests",
        "qrcode",
        "python-barcode",
        "Pillow"
    ],
    python_requires=">=3.6",
    keywords=['python', 'jit', "sdk", "apiAuth", "utils", "backend"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
    ]
)
