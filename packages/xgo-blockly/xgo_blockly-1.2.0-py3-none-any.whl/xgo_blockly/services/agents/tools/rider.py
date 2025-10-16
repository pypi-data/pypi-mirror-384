"""
XGO-Rider 机型专用工具
"""
from .common import (
    xgo_display_text, xgo_display_clear,
    xgo_play_http_audio, xgo_display_http_image,
    xgo_photo_understand, xgo_speech_recognition, xgo_text_to_speech,
    xgo_generate_and_display_image,
    _xgo_instance, _xgo_edu
)
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock
import time
import functools


# ============= XGO-Rider运动控制函数 =============

def xgo_move_x(speed: float, runtime: float = 0):
    """
    控制XGO-Rider在X轴（前后）方向移动
    
    Args:
        speed: 移动速度，范围[-1.5, 1.5] m/s
            - 正值: 向前移动
            - 负值: 向后移动
        runtime: 移动持续时间(秒)，0表示持续移动直到下次命令
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_move_x(speed, runtime)
        direction = "向前" if speed > 0 else "向后"
        if runtime > 0:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider{direction}移动(速度{speed}m/s, 持续{runtime}秒)")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider{direction}移动(速度{speed}m/s)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 移动失败: {str(e)}")])  


def xgo_move_y(speed: float, runtime: float = 0):
    """
    控制XGO-Rider在Y轴方向移动（Rider不支持，保留接口兼容性）
    
    Args:
        speed: 移动速度（Rider不支持Y轴移动）
        runtime: 移动持续时间
    
    Returns:
        ToolResponse对象
    """
    return ToolResponse(content=[TextBlock(type="text", text="⚠️ XGO-Rider不支持Y轴横向移动")])


def xgo_translation(axis: str, distance: float):
    """
    控制XGO-Rider机身位置平移
    
    Args:
        axis: 平移轴向
            - 'z' 或 'Z': 上下平移（身高调整），范围: [60, 120] mm（绝对高度）
            - Rider仅支持Z轴平移
        distance: 平移距离，单位毫米
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if axis.lower() == 'z':
            _xgo_instance.rider_height(distance)
            time.sleep(1)
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider身高调整完成(高度{distance}mm)")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"⚠️ XGO-Rider仅支持Z轴平移，不支持{axis.upper()}轴")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 平移失败: {str(e)}")])  


def xgo_attitude(direction, data):
    """
    调整XGO-Rider机身姿态角度
    
    Args:
        direction: 单字符或字符列表
            - 'r': 横滚角(Roll)，范围[-17, 17]
            - 'p': 俯仰角(Pitch)（Rider不支持）
            - 'y': 偏航角(Yaw)（Rider不支持）
        data: 数字或数字列表，对应direction的角度值
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if isinstance(direction, list):
            # 多轴调整，Rider仅支持Roll
            for d, v in zip(direction, data):
                if d.lower() == 'r':
                    _xgo_instance.rider_roll(v)
            time.sleep(1.5)
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider姿态调整完成(仅Roll轴有效)")])  
        else:
            if direction.lower() == 'r':
                _xgo_instance.rider_roll(data)
                time.sleep(1.5)
                return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider Roll调整至{data}°")])
            else:
                return ToolResponse(content=[TextBlock(type="text", text=f"⚠️ XGO-Rider仅支持Roll轴姿态调整")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 姿态调整失败: {str(e)}")])  


def xgo_action(action_id: int):
    """
    执行XGO-Rider预设动作
    
    Args:
        action_id: 动作ID
            基础动作:
                1: 趴下 (3秒)
                2: 站起 (3秒)
                255: 重置 (1秒)
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        action_names = {
            1: "趴下", 2: "站起", 255: "重置"
        }
        
        action_sleep_times = {
            1: 3, 2: 3, 3: 5, 4: 5, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 7,
            11: 7, 12: 5, 13: 7, 14: 10, 15: 6, 16: 6, 17: 4, 18: 6, 19: 10, 20: 9,
            21: 8, 22: 7, 23: 6, 24: 7, 128: 10, 129: 10, 130: 10, 255: 1
        }
        
        _xgo_instance.rider_action(action_id, wait=True)
        sleep_time = action_sleep_times.get(action_id, 3)
        
        action_name = action_names.get(action_id, f"动作{action_id}")
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider执行{action_name}动作完成，等待{sleep_time}秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 动作执行失败: {str(e)}")])  


def xgo_rider_turn(speed: float, runtime: float = 0):
    """
    控制XGO-Rider原地旋转
    
    Args:
        speed: 旋转角速度，范围[-360, 360] °/s
            - 正值: 向左旋转（逆时针）
            - 负值: 向右旋转（顺时针）
        runtime: 旋转持续时间(秒)，0表示持续旋转
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_turn(speed, runtime)
        direction = "向左" if speed > 0 else "向右"
        if runtime > 0:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider{direction}旋转(角速度{speed}°/s, 持续{runtime}秒)")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider{direction}旋转(角速度{speed}°/s)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 旋转失败: {str(e)}")])  


def xgo_rider_reset_odom():
    """
    重置XGO-Rider里程计
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_reset_odom()
        time.sleep(0.5)
        return ToolResponse(content=[TextBlock(type="text", text="✓ XGO-Rider里程计已重置")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 里程计重置失败: {str(e)}")])  


def xgo_rider_balance_roll(mode: int):
    """
    开启/关闭XGO-Rider Roll轴自平衡
    
    Args:
        mode: 0=关闭自平衡, 1=开启自平衡
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if mode not in [0, 1]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 模式参数错误，必须为0(关闭)或1(开启)")])
        
        _xgo_instance.rider_balance_roll(mode)
        time.sleep(0.3)
        status = "开启" if mode == 1 else "关闭"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider Roll轴自平衡已{status}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 自平衡设置失败: {str(e)}")])  


def xgo_rider_perform(mode: int):
    """
    开启/关闭XGO-Rider循环表演模式
    
    Args:
        mode: 0=关闭表演, 1=开启表演
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if mode not in [0, 1]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 模式参数错误，必须为0(关闭)或1(开启)")])
        
        _xgo_instance.rider_perform(mode)
        time.sleep(0.3)
        status = "开启" if mode == 1 else "关闭"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider表演模式已{status}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 表演模式设置失败: {str(e)}")])  


def xgo_rider_calibration(state: str):
    """
    XGO-Rider软件标定（请谨慎使用）
    
    Args:
        state: 'start'=开始标定, 'end'=结束标定
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if state not in ['start', 'end']:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 状态参数错误，必须为'start'或'end'")])
        
        _xgo_instance.rider_calibration(state)
        time.sleep(0.5)
        status = "开始" if state == 'start' else "结束"
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider标定已{status}")])  
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 标定操作失败: {str(e)}")])  


def xgo_rider_periodic_roll(period: float, wait_time: float = 0):
    """
    控制XGO-Rider进行周期性Roll轴摇摆
    
    Args:
        period: 周期时间，范围[1, 2]秒
        wait_time: 运动持续时间，0表示持续运动
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_periodic_roll(period)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.rider_periodic_roll(0)
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider周期性Roll摇摆完成(周期{period}秒, 持续{wait_time}秒)")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider开始周期性Roll摇摆(周期{period}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 周期性摇摆失败: {str(e)}")])  


def xgo_rider_periodic_z(period: float, wait_time: float = 0):
    """
    控制XGO-Rider进行周期性Z轴升降
    
    Args:
        period: 周期时间，范围[1, 2]秒
        wait_time: 运动持续时间，0表示持续运动
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_periodic_z(period)
        if wait_time > 0:
            time.sleep(wait_time)
            _xgo_instance.rider_periodic_z(0)
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider周期性升降完成(周期{period}秒, 持续{wait_time}秒)")])
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider开始周期性升降(周期{period}秒)")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 周期性升降失败: {str(e)}")])  


def xgo_rider_read_battery():
    """
    读取XGO-Rider电池电量
    
    Returns:
        ToolResponse对象，包含当前电池电量百分比
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        battery = _xgo_instance.rider_read_battery()
        # 根据电量返回不同的提示
        if battery >= 80:
            status = "🔋 电量充足"
        elif battery >= 50:
            status = "🔋 电量正常"
        elif battery >= 20:
            status = "⚠️ 电量偏低"
        else:
            status = "❗ 电量严重不足，请及时充电"
        
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider电池电量: {battery}% - {status}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 电池读取失败: {str(e)}")])


def xgo_rider_read_roll():
    """
    读取XGO-Rider的横滚角(Roll)
    
    Returns:
        ToolResponse对象，包含当前Roll角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        roll = _xgo_instance.rider_read_roll()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider当前Roll角度: {roll}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Roll读取失败: {str(e)}")])  


def xgo_rider_read_pitch():
    """
    读取XGO-Rider的俯仰角(Pitch)
    
    Returns:
        ToolResponse对象，包含当前Pitch角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        pitch = _xgo_instance.rider_read_pitch()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider当前Pitch角度: {pitch}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Pitch读取失败: {str(e)}")])  


def xgo_rider_read_yaw():
    """
    读取XGO-Rider的偏航角(Yaw)
    
    Returns:
        ToolResponse对象，包含当前Yaw角度
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        yaw = _xgo_instance.rider_read_yaw()
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider当前Yaw角度: {yaw}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ Yaw读取失败: {str(e)}")])  


def xgo_rider_led(index: int, r: int, g: int, b: int):
    """
    控制XGO-Rider LED灯颜色
    
    Args:
        index: LED编号(0-5)
        r: 红色分量(0-255)
        g: 绿色分量(0-255)
        b: 蓝色分量(0-255)
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if not (0 <= index <= 5):
            return ToolResponse(content=[TextBlock(type="text", text="❌ LED编号错误，范围为0-5")])
        
        if not all(0 <= val <= 255 for val in [r, g, b]):
            return ToolResponse(content=[TextBlock(type="text", text="❌ RGB值错误，范围为0-255")])
        
        _xgo_instance.rider_led(index, [r, g, b])
        time.sleep(0.2)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO-Rider LED{index}颜色设置为RGB({r},{g},{b})")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ LED控制失败: {str(e)}")])  


def xgo_rider_reset():
    """
    重置XGO-Rider到初始状态
    
    Returns:
        ToolResponse对象
    """
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.rider_reset()
        time.sleep(1)
        return ToolResponse(content=[TextBlock(type="text", text="✓ XGO-Rider已重置")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 重置失败: {str(e)}")])  




def register_tools(toolkit, api_key: str):
    """
    注册Rider专用工具到toolkit
    
    Args:
        toolkit: AgentScope工具包实例
        api_key: API密钥（用于AI功能）
    """
 
    # 创建工具组
    toolkit.create_tool_group("xgo_rider", "XGO-Rider控制工具", active=True)
    
    # 注册基础运动工具
    toolkit.register_tool_function(xgo_move_x, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_move_y, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_translation, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_attitude, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_action, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_turn, group_name="xgo_rider")
    
    # 注册系统控制工具
    toolkit.register_tool_function(xgo_rider_reset, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_reset_odom, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_balance_roll, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_perform, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_calibration, group_name="xgo_rider")
    
    # 注册周期性运动工具
    toolkit.register_tool_function(xgo_rider_periodic_roll, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_periodic_z, group_name="xgo_rider")
    
    # 注册传感器读取工具
    toolkit.register_tool_function(xgo_rider_read_battery, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_read_roll, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_read_pitch, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_rider_read_yaw, group_name="xgo_rider")
    
    # 注册LED控制工具
    toolkit.register_tool_function(xgo_rider_led, group_name="xgo_rider")
    
    # 注册显示和语音工具
    toolkit.register_tool_function(xgo_display_text, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_display_clear, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_play_http_audio, group_name="xgo_rider")
    toolkit.register_tool_function(xgo_display_http_image, group_name="xgo_rider")
    
    
    # 注册需要API密钥的AI工具
    if api_key:
        photo_understand_with_key = functools.partial(xgo_photo_understand, api_key=api_key)
        speech_recognition_with_key = functools.partial(xgo_speech_recognition, api_key=api_key)
        text_to_speech_with_key = functools.partial(xgo_text_to_speech, api_key=api_key)
        generate_image_with_key = functools.partial(xgo_generate_and_display_image, api_key=api_key)
        
        toolkit.register_tool_function(photo_understand_with_key, group_name="xgo_rider")
        toolkit.register_tool_function(speech_recognition_with_key, group_name="xgo_rider")
        toolkit.register_tool_function(text_to_speech_with_key, group_name="xgo_rider")
        toolkit.register_tool_function(generate_image_with_key, group_name="xgo_rider")
    
    print("✓ XGO-Rider工具集注册完成")
