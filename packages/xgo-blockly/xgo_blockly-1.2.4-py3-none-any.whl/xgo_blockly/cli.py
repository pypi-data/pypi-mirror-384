#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGO Blockly CLI
命令行入口点，用于启动XGO Blockly服务器
"""

import os
import sys
import argparse
from .app import create_app


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XGO Blockly Server')
    parser.add_argument('--host', default='0.0.0.0', help='主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='端口号 (默认: 8000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', choices=['development', 'production', 'testing'], 
                       default='production', help='配置环境 (默认: production)')
    
    args = parser.parse_args()
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = args.config
    
    # 创建应用
    app = create_app(args.config)
    
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
    print(f"服务器地址: http://{args.host}:{args.port}")
    
    try:
        # 启动服务器
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()