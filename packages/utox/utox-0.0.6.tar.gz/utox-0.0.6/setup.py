# -*- coding: utf-8 -*-
# @Time    : 2025-07-24 16:49
# @Author  : luyi
from setuptools import find_packages, setup


setup(
    name="utox",
    version="0.0.6",
    author="ly",
    author_email="2662017230@qq.com",
    description="my utils",
    url="https://github.com/bme6/utox",
    # 你要安装的包，通过 setuptools.find_packages 找到当前目录下有哪些包
    # packages=find_packages(exclude=['core', '__pycache__']),
    include_package_data=True,
    package_data={"utox": ["*.so", "*.pyd"]},
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    zip_safe=False,
)
