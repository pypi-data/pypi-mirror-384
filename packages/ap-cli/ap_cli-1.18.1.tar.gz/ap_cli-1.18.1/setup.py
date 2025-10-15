#!/usr/bin/env python3
"""
AP CLI - 基于AI的学习工具安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip()
                    and not line.startswith("#")]

setup(
    name="ap-cli",
    version="1.18.1",
    author="yangjh",
    author_email="yangjh@xbmu.edu.cn",
    description="一个帮助用户通过提问-生成-测验循环来学习新概念的命令行工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangjh-xbmu/ap",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ap=ap.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
