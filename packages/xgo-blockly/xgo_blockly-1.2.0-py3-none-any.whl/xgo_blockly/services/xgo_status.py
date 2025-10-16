#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGO状态读取服务
负责读取XGO机器人的各种状态信息
"""

import logging
from typing import List, Union

# 尝试导入xgolib，如果不存在则使用模拟模式
try:
    from xgolib import XGO
    XGO_AVAILABLE = True
except ImportError:
    XGO_AVAILABLE = False
    logging.warning("xgolib未安装，将使用模拟模式")


class XGOStatusService:
    """XGO状态读取服务类"""
    
    def __init__(self, robot_type="mini"):
        self.dog = None
        self.robot_type = robot_type  # 'mini', 'lite', 'rider'
        print(f"[XGO_STATUS] XGOStatusService 初始化开始，机型: {robot_type}", flush=True)
        self.init_connection()
        print("[XGO_STATUS] XGOStatusService 初始化完成", flush=True)
    
    def init_connection(self):
        """初始化XGO连接"""
        print("[XGO_STATUS] init_connection 被调用", flush=True)
        if XGO_AVAILABLE:
            try:
                print(f"[XGO_STATUS] 尝试连接XGO ({self.robot_type})...", flush=True)
                self.dog = XGO(self.robot_type)
                # 检测实际机型（通过固件版本前缀）
                firmware = self.dog.read_firmware()
                if firmware and firmware != 'Null':
                    if firmware.startswith('M'):
                        self.robot_type = 'mini'
                    elif firmware.startswith('L'):
                        self.robot_type = 'lite'
                    elif firmware.startswith('R'):
                        self.robot_type = 'rider'
                    print(f"[XGO_STATUS] 检测到机型: {self.robot_type}, 固件版本: {firmware}", flush=True)
                logging.info(f"XGO连接成功，机型: {self.robot_type}")
                print("[XGO_STATUS] XGO连接成功", flush=True)
            except Exception as e:
                logging.error(f"XGO连接失败: {str(e)}")
                print(f"[XGO_STATUS] XGO连接失败: {str(e)}", flush=True)
        else:
            logging.warning("XGO库不可用，使用模拟模式")
            print("[XGO_STATUS] XGO库不可用，使用模拟模式", flush=True)
    
    def set_robot_type(self, robot_type: str):
        """设置机器人类型"""
        if robot_type in ['mini', 'lite', 'rider']:
            self.robot_type = robot_type
            logging.info(f"机器人类型已设置为: {robot_type}")
            # 重新连接以应用新类型
            self.reconnect()
        else:
            logging.error(f"无效的机器人类型: {robot_type}")
    
    def read_motor(self) -> List[float]:
        """
        读取15个舵机的角度
        
        Returns:
            List[float]: 长度为15的列表，对应编号[11,12,13,21,22,23,31,32,33,41,42,43,51,52,53]的舵机角度
                        读取失败则返回空列表
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回空列表")
            return []
        
        try:
            # 调用XGO的read_motor方法
            motor_angles = self.dog.read_motor()
            
            # 确保返回15个值
            if isinstance(motor_angles, list) and len(motor_angles) == 15:
                logging.info(f"成功读取舵机角度: {motor_angles}")
                return motor_angles
            else:
                logging.error(f"舵机角度数据格式错误: {motor_angles}")
                return []
                
        except Exception as e:
            logging.error(f"读取舵机角度失败: {str(e)}")
            return []
    
    def read_battery(self) -> int:
        """
        读取当前电池电量
        
        Returns:
            int: 1-100的整数，代表电池剩余电量百分比，读取失败则返回0
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回电量0")
            return 0
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                battery_level = self.dog.rider_read_battery()
            else:
                battery_level = self.dog.read_battery()
            
            # 确保返回值在合理范围内
            if isinstance(battery_level, (int, float)):
                battery_level = int(battery_level)
                if 0 <= battery_level <= 100:
                    logging.info(f"成功读取电池电量: {battery_level}%")
                    return battery_level
                else:
                    logging.warning(f"电池电量值超出范围: {battery_level}")
                    return max(0, min(100, battery_level))
            else:
                logging.error(f"电池电量数据格式错误: {battery_level}")
                return 0
                
        except Exception as e:
            logging.error(f"读取电池电量失败: {str(e)}")
            return 0
    
    def read_roll(self) -> float:
        """
        读取当前Roll姿态角度
        
        Returns:
            float: Roll角度，读取失败则返回0.0
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回Roll角度0.0")
            return 0.0
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                roll_angle = self.dog.rider_read_roll()
            else:
                roll_angle = self.dog.read_roll()
            
            if isinstance(roll_angle, (int, float)):
                logging.info(f"成功读取Roll角度: {roll_angle}")
                return float(roll_angle)
            else:
                logging.error(f"Roll角度数据格式错误: {roll_angle}")
                return 0.0
                
        except Exception as e:
            logging.error(f"读取Roll角度失败: {str(e)}")
            return 0.0
    
    def read_pitch(self) -> float:
        """
        读取当前Pitch姿态角度
        
        Returns:
            float: Pitch角度，读取失败则返回0.0
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回Pitch角度0.0")
            return 0.0
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                pitch_angle = self.dog.rider_read_pitch()
            else:
                pitch_angle = self.dog.read_pitch()
            
            if isinstance(pitch_angle, (int, float)):
                logging.info(f"成功读取Pitch角度: {pitch_angle}")
                return float(pitch_angle)
            else:
                logging.error(f"Pitch角度数据格式错误: {pitch_angle}")
                return 0.0
                
        except Exception as e:
            logging.error(f"读取Pitch角度失败: {str(e)}")
            return 0.0
    
    def read_yaw(self) -> float:
        """
        读取当前Yaw姿态角度
        
        Returns:
            float: Yaw角度，读取失败则返回0.0
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回Yaw角度0.0")
            return 0.0
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                yaw_angle = self.dog.rider_read_yaw()
            else:
                yaw_angle = self.dog.read_yaw()
            
            if isinstance(yaw_angle, (int, float)):
                logging.info(f"成功读取Yaw角度: {yaw_angle}")
                return float(yaw_angle)
            else:
                logging.error(f"Yaw角度数据格式错误: {yaw_angle}")
                return 0.0
                
        except Exception as e:
            logging.error(f"读取Yaw角度失败: {str(e)}")
            return 0.0
    
    def read_imu_int16(self, direction: str) -> int:
        """
        读取IMU姿态角度（整型int16）
        
        Args:
            direction: 'roll', 'pitch', 或 'yaw'
            
        Returns:
            int: int16类型整数角度，读取失败则返回0
        """
        if not self.dog:
            logging.warning(f"XGO未初始化，返回{direction}角度0")
            return 0
        
        if direction not in ['roll', 'pitch', 'yaw']:
            logging.error(f"无效的direction参数: {direction}")
            return 0
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                angle = self.dog.rider_read_imu_int16(direction)
            else:
                angle = self.dog.read_imu_int16(direction)
            
            if isinstance(angle, (int, float)):
                logging.info(f"成功读取{direction}角度(int16): {angle}")
                return int(angle)
            else:
                logging.error(f"{direction}角度数据格式错误: {angle}")
                return 0
                
        except Exception as e:
            logging.error(f"读取{direction}角度失败: {str(e)}")
            return 0
    
    def read_firmware(self) -> str:
        """
        读取XGO固件版本号
        
        Returns:
            str: 固件版本号，读取失败则返回"Unknown"
        """
        if not self.dog:
            logging.warning("XGO未初始化，返回固件版本Unknown")
            return "Unknown"
        
        try:
            # 根据机型调用对应的方法
            if self.robot_type == 'rider':
                firmware_version = self.dog.rider_read_firmware()
            else:
                firmware_version = self.dog.read_firmware()
            
            if firmware_version and firmware_version != 'Null':
                logging.info(f"成功读取固件版本: {firmware_version}")
                return str(firmware_version)
            else:
                logging.error("固件版本数据为空")
                return "Unknown"
                
        except Exception as e:
            logging.error(f"读取固件版本失败: {str(e)}")
            return "Unknown"
    
    def read_all_status(self) -> dict:
        """
        读取所有状态信息
        
        Returns:
            dict: 包含所有状态信息的字典
        """
        return {
            'robot_type': self.robot_type,
            'motor_angles': self.read_motor(),
            'battery_level': self.read_battery(),
            'roll': self.read_roll(),
            'pitch': self.read_pitch(),
            'yaw': self.read_yaw(),
            'roll_int16': self.read_imu_int16('roll'),
            'pitch_int16': self.read_imu_int16('pitch'),
            'yaw_int16': self.read_imu_int16('yaw'),
            'firmware_version': self.read_firmware()
        }
    
    def reconnect(self):
        """
        重新连接XGO
        """
        logging.info("尝试重新连接XGO...")
        self.dog = None
        self.init_connection()


# 全局XGO状态服务实例
xgo_status_service = XGOStatusService()