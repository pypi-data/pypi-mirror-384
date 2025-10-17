"""
XGO-Mini 机型专用工具
"""
from .common import (
    xgo_battery, xgo_display_text, xgo_display_clear,
    xgo_play_http_audio, xgo_display_http_image,
    xgo_photo_understand, xgo_speech_recognition, xgo_text_to_speech,
    xgo_generate_and_display_image,
    xgo_stop, xgo_reset, xgo_read_imu, xgo_display_picture, xgo_speak,
    xgo_find_person,
    _xgo_instance, _xgo_edu
)
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock
import time
import functools


# ============= XGO-Mini运动控制函数 =============

def xgo_move_x(step: float, wait_time: float = 3.0):
    """
    控制XGO-Mini在X轴（前后）方向移动
    
    Args:
        step: 移动步幅，控制移动速度
            - 范围: [-25, 25] 对应移动速度
            - 正值: 向前移动（机身坐标系X轴正方向）
            - 负值: 向后移动（机身坐标系X轴负方向）
            - 数值越大移动越快
        wait_time: 移动持续时间，默认3.0秒
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.move('x', step)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.reset()
        direction = "向前" if step > 0 else "向后"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{direction}移动(步幅{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 移动失败: {str(e)}")])


def xgo_move_y(step: float, wait_time: float = 3.0):
    """
    控制XGO-Mini在Y轴（左右）方向移动
    
    Args:
        step: 移动步幅，控制移动速度
            - 范围: [-18, 18] 对应移动速度
            - 正值: 向左移动（机身坐标系Y轴正方向）
            - 负值: 向右移动（机身坐标系Y轴负方向）
            - 数值越大移动越快
        wait_time: 移动持续时间，默认3.0秒
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.move('y', step)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.reset()
        direction = "向左" if step > 0 else "向右"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{direction}移动(步幅{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 移动失败: {str(e)}")])


def xgo_translation(axis: str, distance: float):
    """
    控制XGO-Mini机身位置平移（足端位置不变）
    
    Args:
        axis: 平移轴向（基于机身坐标系）
            - 'x' 或 'X': 前后平移，范围: [-35, 35] mm
            - 'y' 或 'Y': 左右平移，范围: [-19.5, 19.5] mm
            - 'z' 或 'Z': 上下平移（身高调整），范围: [75, 120] mm（绝对高度）
        distance: 平移距离，单位毫米
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.translation(axis.lower(), distance)
        time.sleep(1)
        direction = {"x": "前后", "y": "左右", "z": "上下"}.get(axis.lower(), axis)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini机身{direction}平移完成(距离{distance}mm)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 平移失败: {str(e)}")])


def xgo_attitude(direction, data):
    """
    调整XGO-Mini机身姿态角度
    
    Args:
        direction: 单字符或字符列表
            - 'r': 横滚角(Roll)，范围[-20, 20]，左右倾斜
            - 'p': 俯仰角(Pitch)，范围[-22, 22]，正值抬头，负值低头
            - 'y': 偏航角(Yaw)，范围[-16, 16]，左右转头
            - 或包含以上值的列表，如['r', 'p', 'y']
        data: 数字或数字列表
            - 单个角度值，对应direction指定的轴
            - 或角度值列表，对应direction列表中各轴的角度
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.attitude(direction, data)
        time.sleep(1.5)
        
        # 格式化输出信息
        if isinstance(direction, list):
            axis_names = {'r': 'Roll', 'p': 'Pitch', 'y': 'Yaw'}
            adjustments = [f"{axis_names.get(d, d)}:{v}°" for d, v in zip(direction, data)]
            info = ", ".join(adjustments)
        else:
            axis_names = {'r': 'Roll', 'p': 'Pitch', 'y': 'Yaw'}
            info = f"{axis_names.get(direction, direction)}:{data}°"
        
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini姿态调整({info})完成，等待1.5秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌姿态调整失败: {str(e)}")])


def xgo_action(action_id: int):
    """
    执行XGO-Mini预设动作
    
    Args:
        action_id: 动作ID
            基础动作:
                1: 趴下 (2秒)
                2: 站起 (2秒)
                3: 匍匐前进 (5秒)
            运动动作:
                4: 转圈 (5秒)
                5: 踏步 (4秒) - Mini专用
                6: 蹲起 (4秒)
            姿态展示:
                7: 转动Roll (4秒)
                8: 转动Pitch (4秒)
                9: 转动Yaw (4秒)
                10: 三轴转动 (7秒)
            互动动作:
                11: 撒尿 (7秒)
                12: 坐下 (5秒)
                13: 招手 (7秒)
                14: 伸懒腰 (10秒)
                15: 波浪 (6秒)
                16: 摇摆 (6秒)
                17: 乞讨 (6秒)
                18: 找食物 (6秒)
                19: 握手 (10秒)
                20: 鸡头 (9秒)
                21: 俯卧撑 (8秒)
                22: 张望 (8秒)
                23: 跳舞 (6秒)
            255: 重置 (1秒)
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        action_names = {
            1:"趴下", 2:"站起", 3:"匍匐前进", 4:"转圈", 5:"踏步",
            6:"蹲起", 7:"转动Roll", 8:"转动Pitch", 9:"转动Yaw", 10:"三轴转动",
            11:"撒尿", 12:"坐下", 13:"招手", 14:"伸懒腰", 15:"波浪",
            16:"摇摆", 17:"乞讨", 18:"找食物", 19:"握手", 20:"鸡头",
            21:"俯卧撑", 22:"张望", 23:"跳舞", 255:"重置"
        }
        
        action_sleep_times = {
            1:2, 2:2, 3:5, 4:5, 5:4, 6:4, 7:4, 8:4, 9:4, 10:7,
            11:7, 12:5, 13:7, 14:10, 15:6, 16:6, 17:6, 18:6, 19:10,
            20:9, 21:8, 22:8, 23:6, 255:1
        }
        
        _xgo_instance.action(action_id)
        sleep_time = action_sleep_times.get(action_id, 3)
        time.sleep(sleep_time)
        
        action_name = action_names.get(action_id, f"动作{action_id}")
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini执行{action_name}动作完成，等待{sleep_time}秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 动作执行失败: {str(e)}")])



def xgo_mark_time(step: float):
    """
    控制XGO机器狗原地踏步动作（仅适用于Mini型号）
    
    Args:
        step: 抬腿高度，单位毫米，范围[10, 35]mm
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.mark_time(step)
        time.sleep(3)  # 原地踏步默认等待3秒
        _xgo_instance.reset()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO原地踏步({step}mm幅度)完成，等待3秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 原地踏步失败: {str(e)}")])


def xgo_periodic_tran(axis: str, amplitude: float, wait_time: float):
    """
    控制XGO机器狗进行周期性往复平移运动
    
    Args:
        axis: 平移轴向 ('x', 'y', 'z')
        amplitude: 周期时间，单位秒
        wait_time: 运动持续时间，单位秒
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.periodic_tran(axis, amplitude)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.reset()
        direction = {"x": "前后", "y": "左右", "z": "上下"}.get(axis, axis)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO开始{direction}方向周期性平移运动(幅度{amplitude})")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 周期性平移失败: {str(e)}")])


def xgo_periodic_rot(axis: str, amplitude: float, wait_time: float):
    """
    控制XGO机器狗进行周期性往复旋转运动
    
    Args:
        axis: 旋转轴向 ('r', 'p', 'y')
        amplitude: 周期时间，单位秒
        wait_time: 运动持续时间，单位秒
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.periodic_rot(axis, amplitude)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.reset()
        direction = {"r": "Roll轴", "p": "Pitch轴", "y": "Yaw轴"}.get(axis, axis)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO开始{direction}周期性旋转运动(幅度{amplitude})")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 周期性旋转失败: {str(e)}")])


def xgo_periodic_rot(axis: str, amplitude: float, wait_time: float):
    """
    控制XGO机器狗进行周期性往复旋转运动
    
    Args:
        axis: 旋转轴向 ('r', 'p', 'y')
        amplitude: 周期时间，单位秒
        wait_time: 运动持续时间，单位秒
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.periodic_rot(axis, amplitude)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.reset()
        direction = {"r": "Roll轴", "p": "Pitch轴", "y": "Yaw轴"}.get(axis, axis)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO开始{direction}周期性旋转运动(幅度{amplitude})")])  
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 周期性旋转失败: {str(e)}")])


def xgo_turn(step: float, wait_time: float = 3.0):
    """
    控制XGO-Mini原地旋转
    
    Args:
        step: 旋转速度
            - 范围: [-100, 100]
            - 正值: 向左旋转（逆时针）
            - 负值: 向右旋转（顺时针）
            - 数值越大旋转越快
        wait_time: 旋转持续时间，默认3.0秒
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.turn(step)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.turn(0)
        direction = "向左" if step > 0 else "向右"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{direction}旋转(速度{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 旋转失败: {str(e)}")])


def xgo_gait_type(mode: str):
    """
    设置XGO-Mini步态类型
    
    Args:
        mode: 步态模式
            - "trot": 小跑步态（默认）
            - "walk": 行走步态
            - "high_walk": 高抬腿行走
            - "slow_trot": 慢速小跑
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        mode_map = {
            "trot": "小跑步态",
            "walk": "行走步态",
            "high_walk": "高抬腿行走",
            "slow_trot": "慢速小跑"
        }
        
        if mode not in mode_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知步态类型: {mode}, 支持: trot, walk, high_walk, slow_trot")])
        
        _xgo_instance.gait_type(mode)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini步态设置为{mode_map[mode]}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 步态设置失败: {str(e)}")])


def xgo_pace(mode: str):
    """
    设置XGO-Mini步伐频率
    
    Args:
        mode: 频率模式
            - "normal": 正常频率
            - "slow": 慢速频率
            - "high": 高速频率
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        mode_map = {
            "normal": "正常频率",
            "slow": "慢速频率",
            "high": "高速频率"
        }
        
        if mode not in mode_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知频率模式: {mode}, 支持: normal, slow, high")])
        
        _xgo_instance.pace(mode)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini步伐频率设置为{mode_map[mode]}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 频率设置失败: {str(e)}")])


def xgo_imu(mode: int):
    """
    开启/关闭XGO-Mini IMU自稳功能
    
    Args:
        mode: 0=关闭自稳, 1=开启自稳
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if mode not in [0, 1]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 模式参数错误，必须为0(关闭)或1(开启)")])
        
        _xgo_instance.imu(mode)
        time.sleep(0.3)
        status = "开启" if mode == 1 else "关闭"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini IMU自稳已{status}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ IMU设置失败: {str(e)}")])


def xgo_leg(leg_id: int, x: float, y: float, z: float):
    """
    控制XGO-Mini单条腿的位置
    
    Args:
        leg_id: 腿编号 (1=左前, 2=右前, 3=右后, 4=左后)
        x: X轴位置，范围[-35, 35]mm
        y: Y轴位置，范围[-19.5, 19.5]mm
        z: Z轴位置，范围[75, 120]mm
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if leg_id not in [1, 2, 3, 4]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-4 (1=左前, 2=右前, 3=右后, 4=左后)")])
        
        _xgo_instance.leg(leg_id, [x, y, z])
        time.sleep(0.5)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{leg_names[leg_id]}位置设置完成(X:{x}, Y:{y}, Z:{z})mm")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 单腿控制失败: {str(e)}")])


def xgo_motor(motor_id: int, angle: float):
    """
    控制XGO-Mini单个舵机角度
    
    Args:
        motor_id: 舵机编号
            - 11,12,13: 左前腿(下/中/上)
            - 21,22,23: 右前腿(下/中/上)
            - 31,32,33: 右后腿(下/中/上)
            - 41,42,43: 左后腿(下/中/上)
            - 51: 机械臂夹爪
        angle: 舵机角度，范围根据舵机位置不同:
            - 下关节: [-73, 57]°
            - 中关节: [-66, 93]°
            - 上关节: [-31, 31]°
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        valid_ids = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51]
        if motor_id not in valid_ids:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机编号错误: {motor_id}, 有效范围: 11-13, 21-23, 31-33, 41-43, 51")])
        
        _xgo_instance.motor(motor_id, angle)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini舵机{motor_id}角度设置为{angle}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机控制失败: {str(e)}")])


def xgo_motor_speed(speed: int):
    """
    设置XGO-Mini舵机转动速度（仅在单独控制舵机时有效）
    
    Args:
        speed: 速度值，范围[1, 255]，值越大速度越快
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if speed < 1 or speed > 255:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 速度值错误，范围为1-255")])
        
        _xgo_instance.motor_speed(speed)
        time.sleep(0.2)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini舵机速度设置为{speed}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机速度设置失败: {str(e)}")])


def xgo_unload_motor(leg_id: int):
    """
    卸载XGO-Mini指定腿的舵机（舵机失去力矩，可手动调整）
    
    Args:
        leg_id: 腿编号 (1=左前, 2=右前, 3=右后, 4=左后, 5=机械臂)
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if leg_id not in [1, 2, 3, 4, 5]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-5 (1-4为四条腿, 5为机械臂)")])
        
        _xgo_instance.unload_motor(leg_id)
        time.sleep(0.3)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿", 5: "机械臂"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{leg_names[leg_id]}舵机已卸载")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机卸载失败: {str(e)}")])


def xgo_load_motor(leg_id: int):
    """
    加载XGO-Mini指定腿的舵机（恢复舵机力矩）
    
    Args:
        leg_id: 腿编号 (1=左前, 2=右前, 3=右后, 4=左后, 5=机械臂)
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if leg_id not in [1, 2, 3, 4, 5]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-5 (1-4为四条腿, 5为机械臂)")])
        
        _xgo_instance.load_motor(leg_id)
        time.sleep(0.3)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿", 5: "机械臂"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini{leg_names[leg_id]}舵机已加载")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机加载失败: {str(e)}")])


def xgo_read_roll():
    """
    读取XGO-Mini的横滚角(Roll)
    
    Returns:
        ToolResponse对象，包含当前Roll角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        roll = _xgo_instance.read_roll()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini当前Roll角度: {roll}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Roll读取失败: {str(e)}")])


def xgo_read_pitch():
    """
    读取XGO-Mini的俯仰角(Pitch)
    
    Returns:
        ToolResponse对象，包含当前Pitch角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        pitch = _xgo_instance.read_pitch()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini当前Pitch角度: {pitch}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Pitch读取失败: {str(e)}")])


def xgo_read_yaw():
    """
    读取XGO-Mini的偏航角(Yaw)
    
    Returns:
        ToolResponse对象，包含当前Yaw角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        yaw = _xgo_instance.read_yaw()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Mini当前Yaw角度: {yaw}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Yaw读取失败: {str(e)}")])


def xgo_read_motor():
    """
    读取XGO-Mini所有舵机的当前角度
    
    Returns:
        ToolResponse对象，包含15个舵机的角度列表
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        angles = _xgo_instance.read_motor()
        if angles and len(angles) >= 12:
            result = f"✓ XGO-Mini舵机角度:\n"
            result += f"  左前腿: [{angles[0]:.1f}°, {angles[1]:.1f}°, {angles[2]:.1f}°]\n"
            result += f"  右前腿: [{angles[3]:.1f}°, {angles[4]:.1f}°, {angles[5]:.1f}°]\n"
            result += f"  右后腿: [{angles[6]:.1f}°, {angles[7]:.1f}°, {angles[8]:.1f}°]\n"
            result += f"  左后腿: [{angles[9]:.1f}°, {angles[10]:.1f}°, {angles[11]:.1f}°]"
            if len(angles) >= 13:
                result += f"\n  机械臂: {angles[12]:.1f}°"
            return ToolResponse(content=[TextBlock(type="text", text=result)])
        else:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 读取舵机角度失败")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机角度读取失败: {str(e)}")])


def xgo_arm_control(action: str):
    """
    XGO-Mini机械臂控制
    
    Args:
        action: 动作类型
            - "open": 张开夹爪
            - "close": 闭合夹爪
            - "up": 抬起机械臂
            - "down": 放下机械臂
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        action_map = {
            "open": (1, 120),    # (位置, 速度)
            "close": (1, 0),
            "up": (1, 120),
            "down": (1, 0)
        }
        
        if action not in action_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知的机械臂动作: {action}, 支持: open, close, up, down")])
        
        pos, speed = action_map[action]
        _xgo_instance.claw(pos, speed)
        time.sleep(1.5)
        
        action_name = {"open": "张开", "close": "闭合", "up": "抬起", "down": "放下"}.get(action, action)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO机械臂{action_name}动作完成")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 机械臂控制失败: {str(e)}")])


def xgo_find_ball(color: str, max_search_time: float = 30.0):
    """
    寻找指定颜色的小球（Mini专用视觉功能）
    
    Args:
        color: 小球颜色 ('red', 'green', 'blue')
        max_search_time: 最大搜索时间(秒)，默认30秒
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None or _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人或教育库不可用（可能处于模拟模式）")])
    
    try:
        import cv2
        import numpy as np
        
        # 颜色映射
        color_map = {
            'red': {'name': '红色', 'lower': [0, 43, 46], 'upper': [10, 255, 255]},
            'green': {'name': '绿色', 'lower': [35, 43, 46], 'upper': [77, 255, 255]},
            'blue': {'name': '蓝色', 'lower': [100, 43, 46], 'upper': [124, 255, 255]}
        }
        
        if color not in color_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 不支持的颜色: {color}, 支持: red, green, blue")])
        
        color_info = color_map[color]
        color_name = color_info['name']
        
        # 初始化摄像头
        try:
            _xgo_edu.open_camera()
            time.sleep(1)
        except Exception as cam_e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 摄像头初始化失败: {str(cam_e)}")])
        
        # 在屏幕显示搜索状态
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, f"🔍 搜索{color_name}小球", "YELLOW", 14)
        except:
            pass
        
        start_time = time.time()
        found = False
        
        # 搜索循环
        while time.time() - start_time < max_search_time:
            try:
                # 捕获图像
                image = _xgo_edu.picam2.capture_array()
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # 颜色检测
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, 
                                 np.array(color_info['lower']), 
                                 np.array(color_info['upper']))
                
                # 形态学处理
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)
                
                # 寻找轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if len(contours) > 0:
                    # 找到最大轮廓
                    largest_contour = max(contours, key=cv2.contourArea)
                    ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
                    
                    if radius > 10:  # 最小半径阈值
                        found = True
                        
                        # 估算距离(基于半径大小)
                        # 假设小球直径约4cm，摄像头焦距约320像素
                        distance_cm = int(320 * 2 / radius) if radius > 0 else 0
                        
                        # 在屏幕显示结果
                        try:
                            _xgo_edu.lcd_clear()
                            _xgo_edu.lcd_text(5, 5, f"✓ 找到{color_name}小球", "GREEN", 14)
                            _xgo_edu.lcd_text(5, 25, f"位置:({int(x)}, {int(y)})", "WHITE", 12)
                            _xgo_edu.lcd_text(5, 45, f"半径:{int(radius)}", "WHITE", 12)
                            _xgo_edu.lcd_text(5, 65, f"距离:约{distance_cm}cm", "CYAN", 12)
                        except:
                            pass
                        
                        return ToolResponse(content=[TextBlock(type="text", text=f"✓ 找到{color_name}小球！位置:({int(x)}, {int(y)}), 半径:{int(radius)}, 距离:约{distance_cm}cm")])
                
            except Exception as detect_e:
                print(f"⚠️ 检测失败: {detect_e}")
            
            # 继续搜索...
            time.sleep(0.1)
        
        if not found:
            try:
                _xgo_edu.lcd_clear()
                _xgo_edu.lcd_text(5, 5, f"❌ 未找到{color_name}小球", "RED", 14)
            except:
                pass
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 搜索超时，未找到{color_name}小球")])
            
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 小球搜索失败: {str(e)}")])


def xgo_catch_ball(color: str, max_search_time: float = 30.0, max_grab_attempts: int = 3):
    """
    XGO-Mini机器狗识别并抓取指定颜色的小球（完整抓取流程）
    
    Args:
        color: 要抓取的小球颜色 ('red', 'green', 'blue')
        max_search_time: 最大搜索时间(秒)，默认30秒
        max_grab_attempts: 最大抓取尝试次数，默认3次
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None or _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人或教育库不可用（可能处于模拟模式）")])
    
    try:
        import cv2
        import numpy as np
        
        # 颜色映射
        color_map = {
            'red': '红色', 'r': '红色',
            'green': '绿色', 'g': '绿色',
            'blue': '蓝色', 'b': '蓝色'
        }
        
        color_lower = color.lower()
        if color_lower not in color_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 不支持的颜色: {color}，支持: red, green, blue")])
        
        color_name = color_map[color_lower]
        
        # HSV颜色范围
        color_ranges = {
            'red': {
                'lower1': np.array([0, 120, 60]),
                'upper1': np.array([15, 255, 255]),
                'lower2': np.array([160, 120, 60]),
                'upper2': np.array([180, 255, 255])
            },
            'blue': {
                'lower1': np.array([90, 100, 60]),
                'upper1': np.array([130, 255, 255]),
                'lower2': np.array([90, 100, 60]),
                'upper2': np.array([130, 255, 255])
            },
            'green': {
                'lower1': np.array([40, 80, 60]),
                'upper1': np.array([80, 255, 255]),
                'lower2': np.array([40, 80, 60]),
                'upper2': np.array([80, 255, 255])
            }
        }
        
        def detect_ball(frame, target_color):
            """检测特定颜色的小球"""
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            ranges = color_ranges[target_color]
            
            # 创建掩码
            if target_color == 'red':
                mask1 = cv2.inRange(hsv, ranges['lower1'], ranges['upper1'])
                mask2 = cv2.inRange(hsv, ranges['lower2'], ranges['upper2'])
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = cv2.inRange(hsv, ranges['lower1'], ranges['upper1'])
            
            # 形态学处理
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # 应用掩码
            masked = cv2.bitwise_and(frame, frame, mask=mask)
            gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 2)
            
            # 霍夫圆变换
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=25,
                param1=40,
                param2=18,
                minRadius=10,
                maxRadius=80
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                if len(circles) > 0:
                    max_circle = max(circles, key=lambda c: c[2])
                    return int(max_circle[0]), int(max_circle[1]), int(max_circle[2])
            
            return 0, 0, 0
        
        def calculate_distance(radius):
            """根据半径估算距离(cm)"""
            if radius == 0:
                return float('inf')
            return 600 / radius
        
        def make_lie_down():
            """让机器狗趴下"""
            _xgo_instance.translation('z', 75)
            _xgo_instance.attitude('p', 25)
            time.sleep(1)
        
        def check_grab_success():
            """检查抓取是否成功"""
            try:
                motor_angles = _xgo_instance.read_motor()
                if motor_angles and len(motor_angles) >= 15:
                    claw_angle = motor_angles[12]
                    return claw_angle > -60
                return False
            except:
                return False
        
        def attempt_catch():
            """执行一次抓取"""
            # 打开夹爪
            _xgo_instance.claw(0)
            time.sleep(0.5)
            
            # 移动机械臂到抓取位置
            _xgo_instance.arm_polar(226, 130)
            time.sleep(2)
            
            # 闭合夹爪
            _xgo_instance.claw(245)
            time.sleep(1.5)
            
            # 检测成功
            success = check_grab_success()
            
            if success:
                # 抬起展示
                _xgo_instance.arm_polar(90, 100)
                time.sleep(1)
                _xgo_instance.attitude('p', 10)
                time.sleep(1)
                return True
            else:
                # 重置
                _xgo_instance.claw(0)
                time.sleep(0.5)
                _xgo_instance.arm_polar(90, 100)
                time.sleep(1)
                return False
        
        # 显示任务开始
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, f"🤖 抓取{color_name}小球", "YELLOW", 14)
        except:
            pass
        
        # 趴下准备
        make_lie_down()
        
        # 初始化摄像头
        try:
            if _xgo_edu.picam2 is None:
                _xgo_edu.open_camera()
                time.sleep(2)
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 摄像头初始化失败: {str(e)}")])
        
        # 搜索小球
        start_time = time.time()
        search_attempts = 0
        max_search_attempts = 25
        found_ball = False
        
        while search_attempts < max_search_attempts and not found_ball:
            if max_search_time > 0 and (time.time() - start_time) > max_search_time:
                _xgo_instance.reset()
                return ToolResponse(content=[TextBlock(type="text", text=f"⏰ 搜索超时，未找到{color_name}小球")])
            
            try:
                if _xgo_edu.picam2 is None:
                    _xgo_edu.open_camera()
                    time.sleep(1)
                
                if _xgo_edu.picam2 is not None:
                    frame = _xgo_edu.picam2.capture_array()
                    ball_x, ball_y, ball_radius = detect_ball(frame, color_lower)
                    
                    if ball_radius > 0:
                        distance = calculate_distance(ball_radius)
                        
                        if distance > 16.9:
                            _xgo_instance.move('x', 3)
                            time.sleep(1.2)
                            _xgo_instance.stop()
                        elif distance < 11.9:
                            _xgo_instance.move('x', -3)
                            time.sleep(0.8)
                            _xgo_instance.stop()
                        elif 11.9 <= distance <= 16.9:
                            # 调整左右位置
                            center_x = 160
                            if abs(ball_x - center_x) > 20:
                                if ball_x > center_x:
                                    _xgo_instance.move('y', 3)
                                    time.sleep(0.6)
                                    _xgo_instance.stop()
                                else:
                                    _xgo_instance.move('y', -3)
                                    time.sleep(0.6)
                                    _xgo_instance.stop()
                                continue
                            
                            found_ball = True
                            break
                    else:
                        if search_attempts % 4 == 3:
                            _xgo_instance.turn(60)
                            time.sleep(0.8)
                            _xgo_instance.stop()
                            time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ 检测异常: {e}")
                if search_attempts % 5 == 0:
                    try:
                        if hasattr(_xgo_edu, 'picam2') and _xgo_edu.picam2 is not None:
                            _xgo_edu.picam2.stop()
                            _xgo_edu.picam2.close()
                            time.sleep(1)
                        _xgo_edu.picam2 = None
                        time.sleep(1)
                        _xgo_edu.open_camera()
                        time.sleep(2)
                    except:
                        pass
            
            search_attempts += 1
            time.sleep(0.6)
        
        # 尝试抓取
        grabbed_successfully = False
        grab_attempts = 0
        
        if found_ball:
            try:
                _xgo_edu.lcd_clear()
                _xgo_edu.lcd_text(5, 5, f"🤖 抓取{color_name}小球", "ORANGE", 14)
            except:
                pass
            
            while grab_attempts < max_grab_attempts and not grabbed_successfully:
                grabbed_successfully = attempt_catch()
                grab_attempts += 1
                
                if not grabbed_successfully and grab_attempts < max_grab_attempts:
                    time.sleep(1)
        
        # 站起
        _xgo_instance.action(2)
        time.sleep(3)
        _xgo_instance.reset()
        
        # 清理摄像头
        try:
            if _xgo_edu.picam2 is not None:
                _xgo_edu.picam2.stop()
                _xgo_edu.picam2.close()
        except:
            pass
        
        # 返回结果
        total_time = int(time.time() - start_time)
        
        if grabbed_successfully:
            try:
                _xgo_edu.lcd_clear()
                _xgo_edu.lcd_text(5, 5, "✅ 抓取成功!", "GREEN", 16)
                _xgo_edu.lcd_text(5, 35, f"{color_name}小球已抓取", "WHITE", 12)
            except:
                pass
            
            return ToolResponse(content=[TextBlock(type="text", text=f"✅ XGO-Mini成功抓取{color_name}小球！搜索次数:{search_attempts}, 抓取次数:{grab_attempts}, 耗时:{total_time}秒")])
        else:
            try:
                _xgo_edu.lcd_clear()
                _xgo_edu.lcd_text(5, 5, "❌ 抓取失败", "RED", 16)
            except:
                pass
            
            if found_ball:
                return ToolResponse(content=[TextBlock(type="text", text=f"❌ 找到{color_name}小球但抓取失败，尝试{grab_attempts}次，耗时{total_time}秒")])
            else:
                return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未找到{color_name}小球，搜索{search_attempts}次，耗时{total_time}秒")])
    
    except Exception as e:
        try:
            _xgo_instance.reset()
        except:
            pass
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 抓取异常: {str(e)}")])


def register_tools(toolkit, api_key: str):
    """
    注册Mini专用工具到toolkit
    
    Args:
        toolkit: AgentScope工具包实例
        api_key: API密钥（用于AI功能）
    """
    
    # 创建工具组
    toolkit.create_tool_group("xgo_mini", "XGO-Mini控制工具", active=True)
    
    # 注册Mini运动工具
    toolkit.register_tool_function(xgo_move_x, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_move_y, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_turn, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_translation, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_attitude, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_action, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_stop, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_mark_time, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_periodic_tran, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_periodic_rot, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_gait_type, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_pace, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_imu, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_find_person, group_name="xgo_mini")
    
    # 注册单腿和舵机控制
    toolkit.register_tool_function(xgo_leg, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_motor, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_motor_speed, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_unload_motor, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_load_motor, group_name="xgo_mini")
    
    # 注册通用工具
    toolkit.register_tool_function(xgo_battery, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_read_roll, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_read_pitch, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_read_yaw, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_read_motor, group_name="xgo_mini")
    
    # 注册显示和语音工具
    toolkit.register_tool_function(xgo_display_text, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_display_clear, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_play_http_audio, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_display_http_image, group_name="xgo_mini")
    
    # 注册Mini专用工具
    toolkit.register_tool_function(xgo_arm_control, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_find_ball, group_name="xgo_mini")
    toolkit.register_tool_function(xgo_catch_ball, group_name="xgo_mini")
    
    # 注册需要API密钥的AI工具
    if api_key:
        photo_understand_with_key = functools.partial(xgo_photo_understand, api_key=api_key)
        speech_recognition_with_key = functools.partial(xgo_speech_recognition, api_key=api_key)
        text_to_speech_with_key = functools.partial(xgo_text_to_speech, api_key=api_key)
        generate_image_with_key = functools.partial(xgo_generate_and_display_image, api_key=api_key)
        
        toolkit.register_tool_function(photo_understand_with_key, group_name="xgo_mini")
        toolkit.register_tool_function(speech_recognition_with_key, group_name="xgo_mini")
        toolkit.register_tool_function(text_to_speech_with_key, group_name="xgo_mini")
        toolkit.register_tool_function(generate_image_with_key, group_name="xgo_mini")
    
    print("✓ XGO-Mini工具集注册完成")
