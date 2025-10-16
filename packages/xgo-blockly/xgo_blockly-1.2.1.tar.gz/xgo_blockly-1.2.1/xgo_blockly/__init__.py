#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGO Blockly Package
一个提供XGO机器人图形化编程的Web服务器包
"""

__version__ = "1.0.0"
__author__ = "XGO Team"
__description__ = "XGO Blockly - 图形化编程Web服务器"

from .app import create_app

__all__ = ['create_app']