"""
XGO-Lite 机型专用工具
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


# ============= XGO-Lite运动控制函数 =============

def xgo_move_x(step: float, wait_time: float = 3.0):
    """
    控制XGO-Lite在X轴（前后）方向移动
    
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
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{direction}移动(步幅{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 移动失败: {str(e)}")])


def xgo_move_y(step: float, wait_time: float = 3.0):
    """
    控制XGO-Lite在Y轴（左右）方向移动
    
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
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{direction}移动(步幅{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 移动失败: {str(e)}")])


def xgo_translation(axis: str, distance: float):
    """
    控制XGO-Lite机身位置平移（足端位置不变）
    
    Args:
        axis: 平移轴向（基于机身坐标系）
            - 'x' 或 'X': 前后平移，范围: [-25, 25] mm
            - 'y' 或 'Y': 左右平移，范围: [-18, 18] mm
            - 'z' 或 'Z': 上下平移（身高调整），范围: [60, 110] mm（绝对高度）
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
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite机身{direction}平移完成(距离{distance}mm)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 平移失败: {str(e)}")])


def xgo_attitude(direction, data):
    """
    调整XGO-Lite机身姿态角度
    
    Args:
        direction: 单字符或字符列表
            - 'r': 横滚角(Roll)，范围[-20, 20]，左右倾斜
            - 'p': 俯仰角(Pitch)，范围[-10, 10]，正值抬头，负值低头
            - 'y': 偏航角(Yaw)，范围[-12, 12]，左右转头
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
        
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite姿态调整({info})完成，等待1.5秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌姿态调整失败: {str(e)}")])


def xgo_action(action_id: int):
    """
    执行XGO-Lite预设动作
    
    Args:
        action_id: 动作ID
            基础动作:
                1: 趴下 (2秒)
                2: 站起 (2秒)
                3: 匍匐前进 (5秒)
            运动动作:
                4: 转圈 (5秒)
                5: 踏步 (4秒) - Lite支持
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
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite执行{action_name}动作完成，等待{sleep_time}秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 动作执行失败: {str(e)}")])



def xgo_mark_time(step: float):
    """
    控制XGO-Lite机器狗原地踏步动作
    足端原地上下移动，模拟踏步效果（仅适用于Lite型号）
    
    Args:
        step: 抬腿高度，单位毫米
            - 范围: [10, 25]mm（Lite专用范围）
            - 0: 停止踏步
            - 数值越大，抬腿越高
            - 对应底层命令: 0x3C MarkTime
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["MarkTime"][1] = conver2u8(data, XGOparam["MARK_TIME_LIMIT"], min_value=1)
        - Mini型号范围为[10, 35]mm
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
    控制XGO-Lite机器狗进行周期性往复平移运动
    机身在指定轴向上做周期性来回摆动（类似钟摆）
    
    Args:
        axis: 平移轴向 ('x', 'y', 'z')
            - 'x': 前后方向周期性平移
            - 'y': 左右方向周期性平移
            - 'z': 上下方向周期性平移
        amplitude: 周期时间，单位秒
            - 范围: [1.5, 8]秒（完成一次往返的时间）
            - 0: 停止周期运动
            - 数值越小，摆动频率越高
            - 对应底层命令: 0x80 PERIODIC_TRAN
        wait_time: 运动持续时间，单位秒
            - >0: 运动指定时间后自动停止并reset
            - =0: 持续运动直到手动停止
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: conver2u8(period, XGOparam["PERIOD_LIMIT"][0], min_value=1)
        - 周期范围对所有机型相同: [1.5, 8]秒
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
    控制XGO-Lite机器狗进行周期性往复旋转运动
    机身姿态在指定轴向上做周期性摇摆（类似摇头、点头、翻滚）
    
    Args:
        axis: 旋转轴向 ('r', 'p', 'y')
            - 'r': Roll轴，左右翻滚摇摆
            - 'p': Pitch轴，前后点头摇摆
            - 'y': Yaw轴，左右转头摇摆
        amplitude: 周期时间，单位秒
            - 范围: [1.5, 8]秒（完成一次往返旋转的时间）
            - 0: 停止周期运动
            - 数值越小，摇摆频率越高
            - 对应底层命令: 0x39 PERIODIC_ROT
        wait_time: 运动持续时间，单位秒
            - >0: 运动指定时间后自动停止并reset
            - =0: 持续运动直到手动停止
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: conver2u8(period, XGOparam["PERIOD_LIMIT"][0], min_value=1)
        - 周期范围对所有机型相同: [1.5, 8]秒
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
    控制XGO-Lite原地旋转（Yaw轴转动）
    机器狗绕自身中心轴旋转，不改变位置
    
    Args:
        step: 旋转速度
            - 范围: [-100, 100] 对应旋转速度
            - 正值: 向左旋转（逆时针）
            - 负值: 向右旋转（顺时针）
            - 数值越大旋转越快
            - 对应底层命令: 0x32 VYAW
        wait_time: 旋转持续时间，默认3.0秒
            - >0: 旋转指定时间后自动停止
            - =0: 持续旋转直到手动调用turn(0)
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["VYAW"][1] = conver2u8(step, XGOparam["VYAW_LIMIT"])
        - 所有机型VYAW_LIMIT均为100
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        _xgo_instance.turn(step)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.turn(0)
        direction = "向左" if step > 0 else "向右"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{direction}旋转(速度{step}, 等待{wait_time}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 旋转失败: {str(e)}")])


def xgo_gait_type(mode: str):
    """
    设置XGO-Lite步态类型
    改变机器狗的行走步态模式，影响运动效果和稳定性
    
    Args:
        mode: 步态模式
            - "trot": 小跑步态（0x00）- 默认模式，速度快，适合平地
            - "walk": 行走步态（0x01）- 稳定性高，适合复杂地形
            - "high_walk": 高抬腿行走（0x02）- 抬腿高，适合越障
            - "slow_trot": 慢速小跑（0x03）- 小跑的慢速版本
            - 对应底层命令: 0x09 GAIT_TYPE
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["GAIT_TYPE"][1] = value
        - 步态切换后需要0.5秒稳定时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        mode_map = {"trot": "小跑步态", "walk": "行走步态", "high_walk": "高抬腿行走", "slow_trot": "慢速小跑"}
        if mode not in mode_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知步态类型: {mode}, 支持: trot, walk, high_walk, slow_trot")])
        _xgo_instance.gait_type(mode)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite步态设置为{mode_map[mode]}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 步态设置失败: {str(e)}")])


def xgo_pace(mode: str):
    """
    设置XGO-Lite步伐频率（踏步速度）
    改变机器狗的步伐快慢，影响整体运动速度
    
    Args:
        mode: 频率模式
            - "normal": 正常频率（0x00）- 默认速度
            - "slow": 慢速频率（0x01）- 降低踏步频率
            - "high": 高速频率（0x02）- 提高踏步频率
            - 对应底层命令: 0x3D MOVE_MODE
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["MOVE_MODE"][1] = value
        - 步伐频率切换后需要0.5秒稳定时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        mode_map = {"normal": "正常频率", "slow": "慢速频率", "high": "高速频率"}
        if mode not in mode_map:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知频率模式: {mode}, 支持: normal, slow, high")])
        _xgo_instance.pace(mode)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite步伐频率设置为{mode_map[mode]}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 频率设置失败: {str(e)}")])


def xgo_imu(mode: int):
    """
    开启/关闭XGO-Lite IMU自稳功能
    控制机器狗是否使用IMU（惯性测量单元）进行姿态自动平衡
    
    Args:
        mode: IMU模式
            - 0: 关闭自稳 - 机器狗不会自动调整姿态保持平衡
            - 1: 开启自稳 - 机器狗自动调整姿态保持水平（推荐）
            - 对应底层命令: 0x61 IMU
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["IMU"][1] = mode
        - 开启自稳可提高在斜坡等不平地面的稳定性
        - IMU设置后需要0.3秒生效时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        if mode not in [0, 1]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 模式参数错误，必须为0(关闭)或1(开启)")])
        _xgo_instance.imu(mode)
        time.sleep(0.3)
        status = "开启" if mode == 1 else "关闭"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite IMU自稳已{status}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ IMU设置失败: {str(e)}")])


def xgo_leg(leg_id: int, x: float, y: float, z: float):
    """
    控制XGO-Lite单条腿的足端位置（笛卡尔坐标系）
    直接指定腿部足端在腿部坐标系中的三维坐标
    
    Args:
        leg_id: 腿编号
            - 1: 左前腿
            - 2: 右前腿
            - 3: 右后腿
            - 4: 左后腿
        x: X轴坐标（前后方向），单位毫米
            - 范围: [-25, 25]mm（Lite型号）
            - 正值: 向前
            - 负值: 向后
        y: Y轴坐标（左右方向），单位毫米
            - 范围: [-18, 18]mm（Lite型号）
            - 正值: 向外侧
            - 负值: 向内侧
        z: Z轴坐标（上下方向），单位毫米
            - 范围: [60, 110]mm（Lite型号，绝对高度）
            - 数值越小，腿越短（蹲下）
            - 数值越大，腿越长（站高）
            - 对应底层命令: 0x40 LEG_POS
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["LEG_POS"][index] = conver2u8(data[i], XGOparam["LEG_LIMIT"][i])
        - Mini型号范围: X[-35,35], Y[-19.5,19.5], Z[75,120]
        - 单腿控制后需要0.5秒稳定时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        if leg_id not in [1, 2, 3, 4]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-4 (1=左前, 2=右前, 3=右后, 4=左后)")])
        _xgo_instance.leg(leg_id, [x, y, z])
        time.sleep(0.5)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{leg_names[leg_id]}位置设置完成(X:{x}, Y:{y}, Z:{z})mm")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 单腿控制失败: {str(e)}")])


def xgo_motor(motor_id: int, angle: float):
    """
    控制XGO-Lite单个舵机的旋转角度
    直接控制指定舵机转动到目标角度（关节空间控制）
    
    Args:
        motor_id: 舵机编号（两位数编码：十位=腿号，个位=关节号）
            腿部舵机 (1=左前, 2=右前, 3=右后, 4=左后):
            - x1: 下关节（髋关节） - Lite范围[-70, 50]°
            - x2: 中关节（膝关节） - Lite范围[-70, 90]°
            - x3: 上关节（踝关节） - Lite范围[-30, 30]°
            例如: 11=左前腿下关节, 23=右前腿上关节
            
            机械臂舵机:
            - 51: 夹爪舵机 - 范围[0, 255]
            - 对应底层命令: 0x50 MOTOR_ANGLE
        
        angle: 目标角度，单位度
            - 范围取决于舵机类型（见motor_id说明）
            - Mini下关节范围[-73, 57]°
            - Mini中关节范围[-66, 93]°
            - Mini上关节范围[-31, 31]°
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["MOTOR_ANGLE"][index] = conver2u8(data, XGOparam["MOTOR_LIMIT"][(index-1)%3])
        - 舵机ID列表: [11,12,13, 21,22,23, 31,32,33, 41,42,43, 51,52,53]
        - 舵机转动速度由motor_speed()设置
        - 单舵机控制后需要0.5秒稳定时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        valid_ids = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51]
        if motor_id not in valid_ids:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机编号错误: {motor_id}, 有效范围: 11-13, 21-23, 31-33, 41-43, 51")])
        _xgo_instance.motor(motor_id, angle)
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite舵机{motor_id}角度设置为{angle}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机控制失败: {str(e)}")])


def xgo_motor_speed(speed: int):
    """
    设置XGO-Lite舵机转动速度
    只在单独控制舵机（motor函数）时有效，不影响预设动作
    
    Args:
        speed: 速度值
            - 范围: [1, 255]
            - 数值越大，舵机转动越快
            - 1: 最慢速度
            - 255: 最快速度
            - 对应底层命令: 0x5C MOTOR_SPEED
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["MOTOR_SPEED"][1] = speed
        - 速度为0时会自动设为1
        - 仅对motor()函数控制的舵机生效
        - 设置后需要0.2秒生效时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        if speed < 1 or speed > 255:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 速度值错误，范围为1-255")])
        _xgo_instance.motor_speed(speed)
        time.sleep(0.2)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite舵机速度设置为{speed}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机速度设置失败: {str(e)}")])


def xgo_unload_motor(leg_id: int):
    """
    卸载XGO-Lite指定腿的舵机（舵机失去力矩，可手动调整）
    关闭指定腿部或机械臂的舵机电源，使其可以手动调整
    
    Args:
        leg_id: 腿/机械臂编号
            - 1: 左前腿（舵机11, 12, 13）
            - 2: 右前腿（舵机21, 22, 23）
            - 3: 右后腿（舵机31, 32, 33）
            - 4: 左后腿（舵机41, 42, 43）
            - 5: 机械臂（舵机51, 52, 53）
            - 对应底层命令: 0x20 UNLOAD_MOTOR, value=0x10+leg_id
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["UNLOAD_MOTOR"][1] = 0x10 + leg_id
        - 卸载后舵机失去力矩，可手动调整角度
        - 用于手动调试姿态或教学模式
        - 配套函数: unload_allmotor() 卸载所有舵机
        - 卸载后需要0.3秒生效时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        if leg_id not in [1, 2, 3, 4, 5]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-5 (1-4为四条腿, 5为机械臂)")])
        _xgo_instance.unload_motor(leg_id)
        time.sleep(0.3)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿", 5: "机械臂"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{leg_names[leg_id]}舵机已卸载")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机卸载失败: {str(e)}")])


def xgo_load_motor(leg_id: int):
    """
    加载XGO-Lite指定腿的舵机（恢复舵机力矩）
    恢复指定腿部或机械臂的舵机电源，使其恢复锁定状态
    
    Args:
        leg_id: 腿/机械臂编号
            - 1: 左前腿（舵机11, 12, 13）
            - 2: 右前腿（舵机21, 22, 23）
            - 3: 右后腿（舵机31, 32, 33）
            - 4: 左后腿（舵机41, 42, 43）
            - 5: 机械臂（舵机51, 52, 53）
            - 对应底层命令: 0x20 LOAD_MOTOR, value=0x20+leg_id
    
    Returns:
        ToolResponse对象
    
    Note:
        - 底层实现: XGOorder["LOAD_MOTOR"][1] = 0x20 + leg_id
        - 加载后舵机恢复力矩，锁定在当前角度
        - 与unload_motor()配对使用
        - 配套函数: load_allmotor() 加载所有舵机
        - 加载后需要0.3秒生效时间
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        if leg_id not in [1, 2, 3, 4, 5]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 腿编号错误，必须为1-5 (1-4为四条腿, 5为机械臂)")])
        _xgo_instance.load_motor(leg_id)
        time.sleep(0.3)
        leg_names = {1: "左前腿", 2: "右前腿", 3: "右后腿", 4: "左后腿", 5: "机械臂"}
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite{leg_names[leg_id]}舵机已加载")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 舵机加载失败: {str(e)}")])


def xgo_read_roll():
    """
    读取XGO-Lite的横滚角(Roll)
    通过IMU传感器获取机身左右倾斜角度
    
    Returns:
        ToolResponse对象，包含当前Roll角度信息
    
    Note:
        - 对应底层命令: 0x62 ROLL（读取模式）
        - 底层实现: read -> Byte2Float() -> round(roll, 2)
        - 返回值单位: 度（°）
        - 0°: 机身水平
        - 正值: 向左倾斜
        - 负值: 向右倾斜
        - 读取超时时间: 1秒
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        roll = _xgo_instance.read_roll()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite当前Roll角度: {roll}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Roll读取失败: {str(e)}")])


def xgo_read_pitch():
    """
    读取XGO-Lite的俯仰角(Pitch)
    通过IMU传感器获取机身前后倾斜角度
    
    Returns:
        ToolResponse对象，包含当前Pitch角度信息
    
    Note:
        - 对应底层命令: 0x63 PITCH（读取模式）
        - 底层实现: read -> Byte2Float() -> round(pitch, 2)
        - 返回值单位: 度（°）
        - 0°: 机身水平
        - 正值: 抬头（前端向上）
        - 负值: 低头（前端向下）
        - 读取超时时间: 1秒
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        pitch = _xgo_instance.read_pitch()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite当前Pitch角度: {pitch}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Pitch读取失败: {str(e)}")])


def xgo_read_yaw():
    """
    读取XGO-Lite的偏航角(Yaw)
    通过IMU传感器获取机身旋转方向角度（相对于初始化时的方向）
    
    Returns:
        ToolResponse对象，包含当前Yaw角度信息
    
    Note:
        - 对应底层命令: 0x64 YAW（读取模式）
        - 底层实现: read -> Byte2Float() -> round(yaw, 2)
        - 返回值单位: 度（°）
        - 0°: 初始化时的朝向
        - 正值: 向左旋转（逆时针）
        - 负值: 向右旋转（顺时针）
        - 初始化时会记录init_yaw作为零点参考
        - 读取超时时间: 1秒
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        yaw = _xgo_instance.read_yaw()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Lite当前Yaw角度: {yaw}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Yaw读取失败: {str(e)}")])


def xgo_read_motor():
    """
    读取XGO-Lite所有舵机的当前角度
    一次性获取12个腿部舵机和机械臂舵机的实时角度
    
    Returns:
        ToolResponse对象，包含所有舵机角度信息
        返回列表格式（长度15）:
        - [0-2]: 左前腿（下、中、上关节）
        - [3-5]: 右前腿（下、中、上关节）
        - [6-8]: 右后腿（下、中、上关节）
        - [9-11]: 左后腿（下、中、上关节）
        - [12]: 机械臂夹爪
        - [13-14]: 保留（机械臂扩展）
    
    Note:
        - 对应底层命令: 0x50 MOTOR_ANGLE（读取模式，长度15）
        - 底层实现: read(15) -> conver2float() -> round(angle, 2)
        - 返回值单位: 度（°）
        - 角度范围因舵机类型而异（见motor()函数说明）
        - 读取超时时间: 1秒
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    try:
        angles = _xgo_instance.read_motor()
        if angles and len(angles) >= 12:
            result = f"✓ XGO-Lite舵机角度:\n"
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
    XGO-Lite机械臂快捷控制（预设动作）
    通过预定义动作控制机械臂的夹爪和位置
    
    Args:
        action: 动作类型
            - "open": 张开夹爪 - 设置夹爪位置为120
            - "close": 闭合夹爪 - 设置夹爪位置为0
            - "up": 抬起机械臂 - 设置机械臂位置为120
            - "down": 放下机械臂 - 设置机械臂位置为0
    
    Returns:
        ToolResponse对象
    
    Note:
        - 对应底层命令: 0x71 CLAW
        - 底层实现: XGOorder["CLAW"][1] = conver2u8(pos, [0, 255])
        - 夹爪位置范围: [0, 255]（0=完全闭合, 255=完全张开）
        - 动作执行后需要1.5秒稳定时间
        - 更精细控制可使用arm()、arm_polar()、claw()函数
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
    寻找指定颜色的小球（Lite专用视觉功能）
    使用摄像头进行HSV颜色空间检测，识别并定位特定颜色的小球
    
    Args:
        color: 小球颜色
            - 'red': 红色小球，HSV范围[0-10, 43-255, 46-255]
            - 'green': 绿色小球，HSV范围[35-77, 43-255, 46-255]
            - 'blue': 蓝色小球，HSV范围[100-124, 43-255, 46-255]
        max_search_time: 最大搜索时间(秒)，默认30秒
            - 超时后停止搜索并返回失败
    
    Returns:
        ToolResponse对象，包含:
        - 成功: 小球位置(x, y)、半径(radius)、估算距离(cm)
        - 失败: 超时或未找到小球
    
    技术细节:
        - 图像处理: BGR->HSV颜色空间转换
        - 颜色检测: cv2.inRange() HSV阈值分割
        - 形态学: erode(2次) + dilate(2次) 去噪
        - 轮廓检测: cv2.findContours() + cv2.minEnclosingCircle()
        - 最小半径阈值: 10像素
        - 距离估算: 320*2/radius (基于小球直径4cm、焦距320px)
    
    Note:
        - 需要_xgo_edu.open_camera()初始化摄像头
        - 搜索结果会显示在XGO屏幕上
        - 检测间隔: 0.1秒/帧
        - 依赖库: cv2(OpenCV), numpy
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
    XGO-Lite机器狗识别并抓取指定颜色的小球（完整抓取流程）
    集成视觉识别、运动控制、机械臂抓取的完整自主操作流程
    
    Args:
        color: 要抓取的小球颜色
            - 'red'/'r': 红色小球，HSV范围[0-15, 120-255, 60-255] + [160-180, 120-255, 60-255]
            - 'green'/'g': 绿色小球，HSV范围[40-80, 80-255, 60-255]
            - 'blue'/'b': 蓝色小球，HSV范围[90-130, 100-255, 60-255]
        max_search_time: 最大搜索时间(秒)，默认30秒
            - 超时后停止搜索并返回失败
        max_grab_attempts: 最大抓取尝试次数，默认3次
    
    Returns:
        ToolResponse对象，包含:
        - 成功: 搜索次数、抓取次数、总耗时
        - 失败: 未找到小球或抓取失败原因
    
    流程步骤:
        1. 初始化: 机器狗趻下(translation z=60, attitude p=10)
        2. 搜索阶段: 视觉检测 + 运动调整
           - 距离调整: >16.9cm向前, <11.9cm向后
           - 位置调整: 居中对齐(X偏差>20px时左右移动)
           - 搜索策略: 每4次未找到时旋转60°
        3. 抓取阶段: 机械臂动作序列
           - 打开夹爪: claw(0)
           - 伸出机械臂: arm_polar(226°, 130mm)
           - 闭合夹爪: claw(245)
           - 验证抓取: read_motor()[12] > -60°
           - 成功后抬起: arm_polar(90°, 100mm)
        4. 收尾: 站起(action 2) + reset()
    
    技术细节:
        - 图像处理: HoughCircles()霍夫圆变换
        - 形态学: MORPH_OPEN + MORPH_CLOSE
        - 距离估算: 600/radius (cm)
        - 摄像头必须分辨率: 320x240 (picam2)
        - 抓取验证: 读取夹爪舵机角度
    
    Note:
        - 搜索最大尝试次数: 25次
        - 目标距离范围: 11.9-16.9cm
        - 中心对齐阈值: 20像素
        - 抓取间隔: 1秒
        - 摄像头重启间隔: 每5次尝试
        - 执行完毕后自动关闭摄像头
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
            _xgo_instance.translation('z', 60)
            _xgo_instance.attitude('p', 10)
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
            
            return ToolResponse(content=[TextBlock(type="text", text=f"✅ XGO-Lite成功抓取{color_name}小球！搜索次数:{search_attempts}, 抓取次数:{grab_attempts}, 耗时:{total_time}秒")])
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
    注册Lite专用工具到AgentScope工具包
    按功能分类注册所有XGO-Lite机型支持的控制函数
    
    Args:
        toolkit: AgentScope工具包实例
            - 用于管理和组织工具函数
            - 支持工具分组管理
        api_key: API密钥（用于AI功能）
            - 用于图像理解、语音识别、语音合成等AI功能
            - 如果api_key为None，则不注册AI相关工具
    
    工具分类:
        1. 运动控制工具 (14个):
           - 基础移动: xgo_move_x, xgo_move_y, xgo_turn
           - 姿态控制: xgo_translation, xgo_attitude
           - 预设动作: xgo_action, xgo_stop
           - 周期运动: xgo_mark_time, xgo_periodic_tran, xgo_periodic_rot
           - 步态配置: xgo_gait_type, xgo_pace
           - 自稳控制: xgo_imu
           - 视觉跟踪: xgo_find_person
        
        2. 单腿和舵机控制 (5个):
           - 单腿控制: xgo_leg
           - 舵机控制: xgo_motor, xgo_motor_speed
           - 舵机加卸载: xgo_unload_motor, xgo_load_motor
        
        3. 传感器读取 (5个):
           - 电池状态: xgo_battery
           - IMU姿态: xgo_read_roll, xgo_read_pitch, xgo_read_yaw
           - 舵机角度: xgo_read_motor
        
        4. 显示和语音 (4个):
           - 显示控制: xgo_display_text, xgo_display_clear
           - 多媒体: xgo_play_http_audio, xgo_display_http_image
        
        5. Lite专用功能 (3个):
           - 机械臂: xgo_arm_control
           - 视觉识别: xgo_find_ball
           - 自主抓取: xgo_catch_ball
        
        6. AI功能 (4个, 需要API密钥):
           - 图像理解: xgo_photo_understand
           - 语音识别: xgo_speech_recognition
           - 语音合成: xgo_text_to_speech
           - 图像生成: xgo_generate_and_display_image
    
    Note:
        - 所有工具都注册到"xgo_lite"工具组
        - AI功能使用functools.partial预绑定api_key
        - 注册完成后打印确认信息
    """
    
    # 创建工具组
    toolkit.create_tool_group("xgo_lite", "XGO-Lite控制工具", active=True)
    
    # 注册Lite运动工具
    toolkit.register_tool_function(xgo_move_x, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_move_y, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_turn, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_translation, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_attitude, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_action, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_stop, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_mark_time, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_periodic_tran, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_periodic_rot, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_gait_type, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_pace, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_imu, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_find_person, group_name="xgo_lite")
    
    # 注册单腿和舵机控制
    toolkit.register_tool_function(xgo_leg, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_motor, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_motor_speed, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_unload_motor, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_load_motor, group_name="xgo_lite")
    
    # 注册通用工具
    toolkit.register_tool_function(xgo_battery, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_read_roll, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_read_pitch, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_read_yaw, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_read_motor, group_name="xgo_lite")
    
    # 注册显示和语音工具
    toolkit.register_tool_function(xgo_display_text, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_display_clear, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_play_http_audio, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_display_http_image, group_name="xgo_lite")
    
    # 注册Lite专用工具
    toolkit.register_tool_function(xgo_arm_control, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_find_ball, group_name="xgo_lite")
    toolkit.register_tool_function(xgo_catch_ball, group_name="xgo_lite")
    
    # 注册需要API密钥的AI工具
    if api_key:
        photo_understand_with_key = functools.partial(xgo_photo_understand, api_key=api_key)
        speech_recognition_with_key = functools.partial(xgo_speech_recognition, api_key=api_key)
        text_to_speech_with_key = functools.partial(xgo_text_to_speech, api_key=api_key)
        generate_image_with_key = functools.partial(xgo_generate_and_display_image, api_key=api_key)
        
        toolkit.register_tool_function(photo_understand_with_key, group_name="xgo_lite")
        toolkit.register_tool_function(speech_recognition_with_key, group_name="xgo_lite")
        toolkit.register_tool_function(text_to_speech_with_key, group_name="xgo_lite")
        toolkit.register_tool_function(generate_image_with_key, group_name="xgo_lite")
    
    print("✓ XGO-Lite工具集注册完成")
