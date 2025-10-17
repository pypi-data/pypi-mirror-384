#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGO Blockly Server
Flask服务器，提供Python代码执行和Vue3静态文件托管功能
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from .config import get_config

# 在导入其他模块之前先配置logging，确保所有模块的日志都能输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ],
    force=True  # 强制重新配置logging
)

from .routes.api import api_bp
from .routes.static import static_bp


def create_app(config_name=None):
    """应用工厂函数"""
    # 获取配置
    config_class = get_config(config_name)
    
    # 创建Flask应用
    config_instance = config_class()
    app = Flask(__name__, 
                static_folder=config_instance.STATIC_FOLDER, 
                static_url_path=config_class.STATIC_URL_PATH)
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 配置Flask应用日志
    app.logger.setLevel(logging.INFO)
    # 确保日志输出到控制台
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    
    # 初始化MIME类型
    config_class.init_mime_types()
    
    # 初始化扩展
    CORS(app)  # 允许跨域请求
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(static_bp)
    
    # 注册全局错误处理器
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理，返回index.html用于Vue路由"""
        from flask import send_from_directory, abort
        if app.static_folder is None:
            abort(404, description="Static folder not configured")
        return send_from_directory(app.static_folder, 'index.html')
    
    return app


if __name__ == '__main__':
    # 检查dist目录是否存在
    dist_path = os.path.join(os.path.dirname(__file__), 'dist')
    if not os.path.exists(dist_path):
        print("警告: dist目录不存在，请先构建Vue3项目")
        print("运行命令: cd ../blockly-vue3 && npm run build")
        print("然后将dist目录复制到当前目录")
    
    # 获取配置
    config_class = get_config()
    
    print("启动XGO Blockly Server...")
    print("API接口:")
    print("  - POST /api/run-code - 运行Python代码（SSE响应）")
    print("  - GET /api/health - 健康检查")
    print("XGO状态读取接口:")
    print("  - GET /api/xgo/motor - 读取舵机角度")
    print("  - GET /api/xgo/battery - 读取电池电量")
    print("  - GET /api/xgo/roll - 读取Roll姿态角度")
    print("  - GET /api/xgo/pitch - 读取Pitch姿态角度")
    print("  - GET /api/xgo/yaw - 读取Yaw姿态角度")
    print("  - GET /api/xgo/status - 读取所有状态信息")
    print("  - POST /api/xgo/reconnect - 重新连接XGO")
    print("静态文件托管:")
    print("  - / - Vue3应用主页")
    print("  - /<path> - 静态资源文件")
    
    # 创建应用实例
    app = create_app()
    
    # 启动Flask应用
    app.run(
        host=config_class.HOST,
        port=config_class.PORT,
        debug=config_class.DEBUG,
        threaded=config_class.THREADED
    )