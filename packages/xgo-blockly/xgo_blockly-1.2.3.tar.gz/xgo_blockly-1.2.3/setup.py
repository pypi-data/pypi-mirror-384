#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xgo-blockly",
    version="1.2.3",
    author="XGO Team",
    author_email="support@xgo.com",
    description="XGO Blockly - 图形化编程Web服务器",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/xgo-robotics/xgo-blockly",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Flask",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "xgo-blockly=xgo_blockly.cli:main",
        ],
    },
    package_data={
        "xgo_blockly": [
            "dist/**/*",
            "dist/*",
            "dist/assets/*",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="xgo robot blockly programming education",
    project_urls={
        "Bug Reports": "https://github.com/xgo-robotics/xgo-blockly/issues",
        "Source": "https://github.com/xgo-robotics/xgo-blockly",
        "Documentation": "https://docs.xgo.com/",
    },
)