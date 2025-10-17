#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由处理器
包含所有API接口的路由处理逻辑
"""

import time
import threading
import json
from flask import Blueprint, request, Response, jsonify
from datetime import datetime
from ..services.code_executor import execution_manager
from ..services.xgo_status import xgo_status_service


# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/run-code', methods=['POST'])
def run_code():
    """运行Python代码的API接口"""
    try:
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': '缺少code参数'}), 400
        
        code = data['code']
        if not code.strip():
            return jsonify({'error': '代码不能为空'}), 400
        
        # 检查是否需要强制清理
        force_cleanup = data.get('force_cleanup', False)
        
        # 生成执行ID
        execution_id = f"exec_{int(time.time() * 1000)}"
        
        # 创建代码执行器
        executor = execution_manager.create_executor(execution_id)
        
        # 返回SSE响应
        def generate():
            # 定义实时日志回调函数
            def log_callback(log_entry):
                execution_manager.add_log(execution_id, log_entry)
            
            # 在新线程中执行代码
            def execute_in_thread():
                executor.execute_code(code, log_callback, force_cleanup)
            
            thread = threading.Thread(target=execute_in_thread)
            thread.daemon = True
            thread.start()
            
            # 持续发送日志
            while thread.is_alive() or execution_manager.has_logs(execution_id):
                if execution_manager.has_logs(execution_id):
                    log_entry = execution_manager.pop_log(execution_id)
                    if log_entry:
                        # 使用最简单的文本格式：时间戳  消息内容
                        timestamp = log_entry.get('timestamp', '')
                        message = log_entry.get('message', '')
                        yield f"data: {timestamp}  {message}\n\n"
                else:
                    time.sleep(0.05)  # 减少轮询间隔，提高响应速度
            
            # 清理日志
            execution_manager.clear_logs(execution_id)
        
        return Response(generate(), mimetype='text/event-stream',
                       headers={
                           'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Headers': 'Cache-Control'
                       })
        
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'XGO Blockly Server is running',
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/xgo/motor', methods=['GET'])
def read_motor_angles():
    """读取XGO舵机角度接口"""
    try:
        motor_angles = xgo_status_service.read_motor()
        return jsonify({
            'success': True,
            'data': motor_angles,
            'message': '成功读取舵机角度' if motor_angles else '读取舵机角度失败',
            'motor_ids': [11,12,13,21,22,23,31,32,33,41,42,43,51,52,53]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': [],
            'message': f'读取舵机角度异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/battery', methods=['GET'])
def read_battery_level():
    """读取XGO电池电量接口"""
    try:
        battery_level = xgo_status_service.read_battery()
        return jsonify({
            'success': True,
            'data': battery_level,
            'message': f'当前电池电量: {battery_level}%' if battery_level > 0 else '读取电池电量失败'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': 0,
            'message': f'读取电池电量异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/firmware', methods=['GET'])
def read_firmware_version():
    """读取XGO固件版本接口"""
    try:
        firmware_version = xgo_status_service.read_firmware()
        return jsonify({
            'success': True,
            'data': firmware_version,
            'message': f'固件版本: {firmware_version}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': 'Unknown',
            'message': f'读取固件版本异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/roll', methods=['GET'])
def read_roll_angle():
    """读取XGO Roll姿态角度接口"""
    try:
        roll_angle = xgo_status_service.read_roll()
        return jsonify({
            'success': True,
            'data': roll_angle,
            'message': f'当前Roll角度: {roll_angle}°'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': 0.0,
            'message': f'读取Roll角度异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/pitch', methods=['GET'])
def read_pitch_angle():
    """读取XGO Pitch姿态角度接口"""
    try:
        pitch_angle = xgo_status_service.read_pitch()
        return jsonify({
            'success': True,
            'data': pitch_angle,
            'message': f'当前Pitch角度: {pitch_angle}°'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': 0.0,
            'message': f'读取Pitch角度异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/yaw', methods=['GET'])
def read_yaw_angle():
    """读取XGO Yaw姿态角度接口"""
    try:
        yaw_angle = xgo_status_service.read_yaw()
        return jsonify({
            'success': True,
            'data': yaw_angle,
            'message': f'当前Yaw角度: {yaw_angle}°'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': 0.0,
            'message': f'读取Yaw角度异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/status', methods=['GET'])
def read_all_status():
    """读取XGO所有状态信息接口"""
    try:
        all_status = xgo_status_service.read_all_status()
        return jsonify({
            'success': True,
            'data': all_status,
            'message': '成功读取所有状态信息'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {},
            'message': f'读取状态信息异常: {str(e)}'
        }), 500


@api_bp.route('/xgo/reconnect', methods=['POST'])
def reconnect_xgo():
    """重新连接XGO接口"""
    try:
        success = xgo_status_service.reconnect()
        return jsonify({
            'success': success,
            'data': {'is_connected': success},
            'message': '重新连接成功' if success else '重新连接失败'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {'is_connected': False},
            'message': f'重新连接异常: {str(e)}'
        }), 500


@api_bp.route('/screen/cleanup', methods=['POST'])
def cleanup_screen_processes():
    """手动清理占用屏幕的进程"""
    try:
        # 创建一个临时执行器来清理进程
        from services.code_executor import CodeExecutor
        temp_executor = CodeExecutor('cleanup')
        temp_executor._kill_screen_processes()
        
        # 获取清理日志
        cleanup_logs = [log['message'] for log in temp_executor.logs]
        
        return jsonify({
            'success': True,
            'data': {'logs': cleanup_logs},
            'message': '屏幕进程清理完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {'logs': []},
            'message': f'清理屏幕进程失败: {str(e)}'
        }), 500


@api_bp.route('/processes/cleanup-all', methods=['POST'])
def cleanup_all_processes():
    """手动清理所有Python进程（谨慎使用）"""
    try:
        # 创建一个临时执行器来清理进程
        from services.code_executor import CodeExecutor
        temp_executor = CodeExecutor('cleanup_all')
        temp_executor._kill_all_python_processes()
        
        # 获取清理日志
        cleanup_logs = [log['message'] for log in temp_executor.logs]
        
        return jsonify({
            'success': True,
            'data': {'logs': cleanup_logs},
            'message': '所有Python进程清理完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {'logs': []},
            'message': f'清理Python进程失败: {str(e)}'
        }), 500


@api_bp.route('/execution/stop-all', methods=['POST'])
def stop_all_executions():
    """停止所有正在执行的代码"""
    try:
        stopped_count = execution_manager.stop_all_executions()
        
        return jsonify({
            'success': True,
            'data': {'stopped_count': stopped_count},
            'message': f'已停止 {stopped_count} 个正在运行的执行器' if stopped_count > 0 else '没有正在运行的执行器'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {'stopped_count': 0},
            'message': f'停止执行器失败: {str(e)}'
        }), 500