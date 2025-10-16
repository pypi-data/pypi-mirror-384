#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
包含Flask应用的所有配置项
"""

import os
import mimetypes


class Config:
    """基础配置类"""
    # Flask基础配置
    SECRET_KEY = 'xgo-blockly-secret-key'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # 静态文件配置
    @property
    def STATIC_FOLDER(self):
        """获取静态文件夹路径"""
        # 直接使用相对路径
        return os.path.join(os.path.dirname(__file__), 'dist')
    
    STATIC_URL_PATH = ''
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 8000
    DEBUG = False
    THREADED = True
    
    # MIME类型配置
    MIME_TYPES = {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.svg': 'image/svg+xml'
    }
    
    @staticmethod
    def init_mime_types():
        """初始化MIME类型"""
        for ext, mime_type in Config.MIME_TYPES.items():
            mimetypes.add_type(mime_type, ext)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """获取配置类"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])