#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态文件路由处理器
负责Vue3应用和静态资源的托管
"""

import os
import mimetypes
from flask import Blueprint, send_from_directory, current_app


# 创建静态文件蓝图
static_bp = Blueprint('static_files', __name__)


@static_bp.route('/')
def serve_index():
    """提供Vue3应用的index.html"""
    return send_from_directory(current_app.static_folder, 'index.html')


@static_bp.route('/<path:path>')
def serve_static_files(path):
    """提供静态文件"""
    try:
        # 获取文件扩展名并设置正确的MIME类型
        file_path = os.path.join(current_app.static_folder, path)
        if os.path.isfile(file_path):
            # 根据文件扩展名确定MIME类型
            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype:
                response = send_from_directory(current_app.static_folder, path)
                response.headers['Content-Type'] = mimetype
                return response
        
        return send_from_directory(current_app.static_folder, path)
    except FileNotFoundError:
        # 如果文件不存在，返回index.html（用于Vue路由）
        return send_from_directory(current_app.static_folder, 'index.html')


@static_bp.errorhandler(404)
def not_found(error):
    """404错误处理，返回index.html用于Vue路由"""
    return send_from_directory(current_app.static_folder, 'index.html')