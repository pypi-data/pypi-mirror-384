"""
XGO通用工具函数（所有机型共享）
"""
import time
import os
import requests
import json
import base64
import uuid
import tempfile
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# 全局实例变量
_xgo_instance = None
_xgo_edu = None
_model_type = None


def _detect_model_from_firmware() -> str:
    """
    通过固件版本号自动检测机型
    
    Returns:
        str: 机型类型 ('xgo-mini', 'xgo-lite', 'xgo-rider')
    """
    try:
        from xgolib import XGO
        
        # 先用默认方式创建实例读取固件版本
        temp_dog = XGO("mini")  # 临时实例，仅用于读取版本
        firmware = temp_dog.read_firmware()
        
        # 根据固件版本首字母判断机型
        if firmware and len(firmware) > 0:
            first_char = firmware[0].upper()
            if first_char == 'R':
                return 'xgo-rider'
            elif first_char == 'M':
                return 'xgo-mini'
            elif first_char == 'L':
                return 'xgo-lite'
        
        # 默认返回mini
        print(f"⚠️ 无法从固件版本'{firmware}'识别机型，使用默认xgo-mini")
        return 'xgo-mini'
        
    except Exception as e:
        print(f"⚠️ 自动检测机型失败: {e}，使用默认xgo-mini")
        return 'xgo-mini'


def _auto_init_xgo():
    """
    模块导入时自动初始化XGO实例
    通过读取固件版本号自动识别机型
    """
    global _xgo_instance, _xgo_edu, _model_type
    
    try:
        from xgolib import XGO
        from edulib import XGOEDU
        
        # 自动检测机型
        _model_type = _detect_model_from_firmware()
        
        # 根据机型初始化不同的XGO实例
        model_map = {
            'xgo-mini': 'xgomini',
            'xgo-lite': 'xgolite',
            'xgo-rider': 'xgorider'
        }
        
        xgo_model = model_map.get(_model_type, 'xgomini')
        _xgo_instance = XGO(xgo_model)
        _xgo_edu = XGOEDU()
        print(f"✓ 自动检测到{_model_type.upper()}机型并初始化成功")
        
    except Exception as e:
        print(f"⚠️ XGO自动初始化失败，进入模拟模式: {e}")
        _xgo_instance = None
        _xgo_edu = None
        _model_type = None


# 模块导入时自动初始化
_auto_init_xgo()


# 运动相关函数已移至各机型专用文件（mini.py, lite.py等）
# 因为不同机型的运动库实现不同


def xgo_battery():
    """
    读取XGO机器狗电池电量百分比
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        battery = _xgo_instance.read_battery()
        return ToolResponse(content=[TextBlock(type="text", text=f"🔋 XGO当前电池电量: {battery}%")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 读取电量失败: {str(e)}")])


def xgo_display_text(text: str, x: int = 5, y: int = 5, color: str = "WHITE", fontsize: int = 15):
    """
    XGO屏幕显示文字
    
    Args:
        text: 要显示的文字内容
        x: X坐标，默认5
        y: Y坐标，默认5
        color: 颜色，默认WHITE
        fontsize: 字体大小，默认15
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        _xgo_edu.lcd_text(x, y, text, color, fontsize)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO屏幕已显示文字: {text}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 显示文字失败: {str(e)}")])


def xgo_display_clear():
    """
    清除XGO屏幕显示
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        _xgo_edu.lcd_clear()
        return ToolResponse(content=[TextBlock(type="text", text="✓ XGO屏幕已清除")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 清屏失败: {str(e)}")])


def xgo_play_http_audio(url: str):
    """
    XGO播放HTTP音频地址
    
    Args:
        url: 音频文件的HTTP URL
    
    Returns:
        ToolResponse对象
    """
    try:
        import subprocess
        cmd = f'mplayer "{url}"'
        subprocess.run(cmd, shell=True, check=True)
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO音频播放完成: {url}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 音频播放失败: {str(e)}")])


def xgo_display_http_image(url: str, x: int = 0, y: int = 0):
    """
    XGO显示HTTP图片地址
    
    Args:
        url: 图片文件的HTTP URL
        x: X坐标，默认0
        y: Y坐标，默认0
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        import requests
        from PIL import Image
        from io import BytesIO
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        image = image.resize((320, 240))
        
        _xgo_edu.splash.paste(image, (x, y))
        _xgo_edu.display.ShowImage(_xgo_edu.splash)
        
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ XGO图片已显示: {url}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 显示HTTP图片失败: {str(e)}")])
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        image = image.resize((320, 240))
        
        _xgo_edu.splash.paste(image, (x, y))
        _xgo_edu.display.ShowImage(_xgo_edu.splash)
        
        return ToolResponse(content=[TextBlock(type="text", text=f"✓ 图片已显示: {url}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 显示HTTP图片失败: {str(e)}")])


def xgo_photo_understand(prompt: str = "图中描绘的是什么景象?", filename: str = "photo_understand", api_key: str = None):
    """
    AI拍照理解
    
    Args:
        prompt: 提问内容，默认"图中描绘的是什么景象?"
        filename: 照片文件名（不含扩展名），默认"photo_understand"
        api_key: 阿里云API密钥
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        import cv2
        
        # 拍照
        path = "/home/pi/xgoPictures/"
        photo_filename = filename + ".jpg"
        photo_path = os.path.join(path, photo_filename)
        
        # 在屏幕上显示拍照状态
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, "📸 正在拍照...", "YELLOW", 14)
        except Exception as lcd_e:
            print(f"⚠️ 屏幕显示失败: {lcd_e}")
        
        # 停止摄像头预览模式
        _xgo_edu.camera_still = False
        time.sleep(0.6)
        
        # 确保摄像头已初始化
        if _xgo_edu.picam2 is None:
            _xgo_edu.open_camera()
        
        # 使用Picamera2捕获图像
        image = _xgo_edu.picam2.capture_array()
        cv2.imwrite(photo_path, image)
        print('photo captured for understanding!')
        
        # 读取照片并转换为base64
        if not os.path.exists(photo_path):
            return ToolResponse(content=[TextBlock(type="text", text="❌ 照片文件不存在")])
        
        with open(photo_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 检查API密钥
        if not api_key:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 未提供API密钥，无法调用视觉理解服务")])
        
        # 在屏幕上显示分析状态
        try:
            _xgo_edu.lcd_text(5, 30, "⏳ AI分析中...", "CYAN", 12)
        except:
            pass
        
        # 构建请求数据（使用compatible-mode端点）
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen-vl-max",
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are a helpful assistant."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": "data:image/jpeg;base64," + image_data
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }
        
        print(f"📸 正在调用视觉理解API分析照片: {photo_filename}")
        
        # 调用阿里云通义千问视觉API
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                
                # 在XGO屏幕上显示部分结果
                try:
                    display_text = answer[:50] + "..." if len(answer) > 50 else answer
                    _xgo_edu.lcd_clear()
                    _xgo_edu.lcd_text(5, 5, "图片理解结果:", "YELLOW", 12)
                    _xgo_edu.lcd_text(5, 25, display_text, "WHITE", 10)
                except:
                    pass
                
                # 构建返回消息
                result_msg = (
                    f"📸 XGO拍照并理解完成\n"
                    f"照片: {photo_filename}\n"
                    f"问题: {prompt}\n"
                    f"理解结果: {answer}"
                )
                return ToolResponse(content=[TextBlock(type="text", text=result_msg)])
            else:
                return ToolResponse(content=[TextBlock(type="text", text="❌ API返回数据格式异常")])
        else:
            error_msg = "API请求失败: " + str(response.status_code) + " - " + str(response.text)
            return ToolResponse(content=[TextBlock(type="text", text="❌ " + error_msg)])
            
    except Exception as e:
        error_msg = "❌ 拍照理解失败: " + str(e)
        return ToolResponse(content=[TextBlock(type="text", text=error_msg)])


def xgo_speech_recognition(seconds: int = 3, api_key: str = None):
    """
    语音识别
    
    Args:
        seconds: 录音时长(秒)，默认3秒
        api_key: 阿里云API密钥
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        # 录音
        temp_audio = f"/tmp/speech_{uuid.uuid4().hex}.wav"
        
        # 在XGO屏幕上显示录音状态
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, "🎤 正在录音...", "YELLOW", 14)
            _xgo_edu.lcd_text(5, 30, f"时长: {seconds}秒", "WHITE", 12)
        except Exception as lcd_e:
            print(f"⚠️ 屏幕显示失败: {lcd_e}")
        
        os.system(f"arecord -d {seconds} -f S16_LE -r 16000 -c 1 -t wav {temp_audio}")
        
        # 检查API密钥
        if not api_key:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 未提供API密钥，无法调用语音识别服务")])
        
        # 读取音频文件并转换为base64
        if not os.path.exists(temp_audio):
            return ToolResponse(content=[TextBlock(type="text", text="❌ 录音文件不存在")])
        
        with open(temp_audio, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # 在屏幕上显示识别状态
        try:
            _xgo_edu.lcd_text(5, 55, "⏳ 正在识别...", "CYAN", 12)
        except:
            pass
        
        # 构建请求数据（使用qwen3-omni模型）
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen3-omni-30b-a3b-captioner",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": "data:audio/wav;base64," + audio_data
                            }
                        }
                    ]
                }
            ]
        }
        
        print(f"🎤 正在识别语音（{seconds}秒录音）...")
        
        # 调用阿里云通义千问语音识别API
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        # 清理临时文件
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                recognition_text = result["choices"][0]["message"]["content"]
                
                # 在XGO屏幕上显示识别结果
                try:
                    display_text = recognition_text[:50] + "..." if len(recognition_text) > 50 else recognition_text
                    _xgo_edu.lcd_clear()
                    _xgo_edu.lcd_text(5, 5, "语音识别结果:", "YELLOW", 12)
                    _xgo_edu.lcd_text(5, 25, display_text, "WHITE", 10)
                except:
                    pass
                
                return ToolResponse(content=[TextBlock(type="text", text=f"🎤 XGO语音识别结果({seconds}秒): '{recognition_text}'")])            
            else:
                return ToolResponse(content=[TextBlock(type="text", text="❌ API返回数据格式异常")])
        else:
            error_msg = "API请求失败: " + str(response.status_code) + " - " + str(response.text)
            return ToolResponse(content=[TextBlock(type="text", text="❌ " + error_msg)])
            
    except Exception as e:
        error_msg = "❌ 语音识别失败: " + str(e)
        return ToolResponse(content=[TextBlock(type="text", text=error_msg)])


def xgo_text_to_speech(text: str, voice: str = "Cherry", api_key: str = None):
    """
    文本转语音并播放
    
    Args:
        text: 要合成的文本内容
        voice: 音色选择，默认"Cherry"(芊悦)
        api_key: 阿里云API密钥
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        # 检查API密钥
        if not api_key:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 未提供API密钥，无法调用语音合成服务")])
        
        # 检查文本内容
        if not text or not text.strip():
            return ToolResponse(content=[TextBlock(type="text", text="❌ 文本内容不能为空")])
        
        # 音色映射和验证
        voice_options = {
            "Cherry": "芊悦-阳光积极、亲切自然小姐姐", "Ethan": "晨煦-标准普通话，带部分北方口音。阳光、温暖、活力、朝气", 
            "Nofish": "不吃鱼-不会翘舌音的设计师", "Jennifer": "詹妮弗-品牌级、电影质感般美语女声",
            "Ryan": "甜茶-节奏拉满，戏感炸裂，真实与张力共舞", "Katerina": "卡捷琳娜-御姐音色，韵律回味十足", 
            "Elias": "墨讲师-既保持学科严谨性，又通过叙事技巧将复杂知识转化为可消化的认知模块", "Jada": "上海-阿珍-风风火火的沪上阿姐",
            "Dylan": "北京-晓东-北京胡同里长大的少年", "Sunny": "四川-晴儿-甜到你心里的川妹子", 
            "li": "南京-老李-耐心的瑜伽老师", "Marcus": "陕西-秦川-面宽话短，心实声沉——老陕的味道",
            "Roy": "闽南-阿杰-诙谐直爽、市井活泼的台湾哥仔形象", "Peter": "天津-李彼得-天津相声，专业捧人", 
            "Rocky": "粤语-阿强-幽默风趣的阿强，在线陪聊", "Kiki": "粤语-阿清-甜美的港妹闺蜜", 
            "Eric": "四川-程川-一个跳脱市井的四川成都男子"
        }
        
        if voice not in voice_options:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 不支持的音色: {voice}，支持的音色: {', '.join(voice_options.keys())}")])        
        
        # 构建请求数据
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen3-tts-flash",
            "input": {
                "text": text,
                "voice": voice
            }
        }
        
        print(f"🎤 正在合成语音: {text[:50]}... (音色: {voice}-{voice_options[voice]})")
        
        # 调用阿里云语音合成API
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "output" in result and "audio" in result["output"] and "url" in result["output"]["audio"]:
                audio_url = result["output"]["audio"]["url"]
                
                # 在XGO屏幕上显示合成信息
                try:
                    display_text = text[:40] + "..." if len(text) > 40 else text
                    _xgo_edu.lcd_clear()
                    _xgo_edu.lcd_text(5, 5, "语音合成播放:", "YELLOW", 12)
                    _xgo_edu.lcd_text(5, 25, f"音色: {voice}", "CYAN", 10)
                    _xgo_edu.lcd_text(5, 45, display_text, "WHITE", 10)
                except Exception as lcd_e:
                    print(f"⚠️ 屏幕显示失败: {lcd_e}")
                
                # 直接调用现有的HTTP音频播放方法
                play_result = xgo_play_http_audio(audio_url)
                
                return ToolResponse(content=[TextBlock(type="text", text=f"🎤 XGO语音合成完成并播放\n文本: {text}\n音色: {voice}({voice_options[voice]})")])   
            
            elif "output" in result and "audio" in result["output"] and "data" in result["output"]["audio"]:
                # 对于base64编码的音频数据，暂时不支持，建议使用audio_url格式
                return ToolResponse(content=[TextBlock(type="text", text="❌ API返回base64音频数据，暂不支持此格式，请联系开发者更新API调用方式")])
            else:
                return ToolResponse(content=[TextBlock(type="text", text="❌ API返回数据格式异常，未找到音频数据")])
        else:
            error_msg = "API请求失败: " + str(response.status_code) + " - " + str(response.text)
            return ToolResponse(content=[TextBlock(type="text", text="❌ " + error_msg)])
            
    except Exception as e:
        error_msg = "❌ 语音合成失败: " + str(e)
        return ToolResponse(content=[TextBlock(type="text", text=error_msg)])


def xgo_generate_and_display_image(prompt: str, size: str = "960*720", api_key: str = None):
    """
    AI生成图片并显示
    
    Args:
        prompt: 图片生成提示词
        size: 图片尺寸，默认"960*720"
        api_key: 阿里云API密钥
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        # 检查API密钥
        if not api_key:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 未提供API密钥，无法调用图片生成服务")])
        
        # 检查提示词
        if not prompt or not prompt.strip():
            return ToolResponse(content=[TextBlock(type="text", text="❌ 图片生成提示词不能为空")])
        
        # 在XGO屏幕上显示生成状态
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, "🎨 正在生成图片...", "YELLOW", 14)
            display_prompt = prompt[:30] + "..." if len(prompt) > 30 else prompt
            _xgo_edu.lcd_text(5, 30, display_prompt, "WHITE", 10)
        except Exception as lcd_e:
            print(f"⚠️ 屏幕显示失败: {lcd_e}")
        
        # 构建创建任务的请求数据
        headers = {
            "X-DashScope-Async": "enable",
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        }
        
        create_data = {
            "model": "wan2.2-t2i-flash",
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "size": size,
                "n": 1,
                "prompt_extend": True,
                "watermark": True
            }
        }
        
        print(f"🎨 正在创建图片生成任务: {prompt[:50]}...")
        
        # 第一步：创建图片生成任务
        create_response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
            headers=headers,
            json=create_data,
            timeout=30
        )
        
        if create_response.status_code != 200:
            error_msg = "创建任务失败: " + str(create_response.status_code) + " - " + str(create_response.text)
            return ToolResponse(content=[TextBlock(type="text", text="❌ " + error_msg)])
        
        create_result = create_response.json()
        
        if "output" not in create_result or "task_id" not in create_result["output"]:
            return ToolResponse(content=[TextBlock(type="text", text="❌ 创建任务返回数据格式异常")])
        
        task_id = create_result["output"]["task_id"]
        print(f"✓ 图片生成任务已创建，任务ID: {task_id}")
        
        # 在屏幕上更新状态
        try:
            _xgo_edu.lcd_text(5, 55, f"任务ID: {task_id[:20]}...", "CYAN", 8)
            _xgo_edu.lcd_text(5, 75, "⏳ 等待生成完成...", "ORANGE", 10)
        except:
            pass
        
        # 第二步：轮询查询任务状态
        query_headers = {
            "Authorization": "Bearer " + api_key
        }
        
        max_attempts = 30  # 最多查询30次
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # 等待3秒后查询
            time.sleep(3)
            
            print(f"📋 第{attempt}次查询任务状态: {task_id}")
            
            query_response = requests.get(
                f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                headers=query_headers,
                timeout=15
            )
            
            if query_response.status_code != 200:
                print(f"⚠️ 查询失败: {query_response.status_code}")
                continue
            
            query_result = query_response.json()
            
            if "output" not in query_result:
                print("⚠️ 查询返回数据格式异常")
                continue
            
            task_status = query_result["output"].get("task_status", "UNKNOWN")
            print(f"📊 任务状态: {task_status}")
            
            # 在屏幕上更新查询进度
            try:
                _xgo_edu.lcd_text(5, 95, f"查询次数: {attempt}/{max_attempts}", "WHITE", 8)
                _xgo_edu.lcd_text(5, 115, f"状态: {task_status}", "CYAN", 10)
            except:
                pass
            
            if task_status == "SUCCEEDED":
                # 任务成功，获取图片URL
                if "results" in query_result["output"] and len(query_result["output"]["results"]) > 0:
                    result = query_result["output"]["results"][0]
                    image_url = result.get("url", "")
                    actual_prompt = result.get("actual_prompt", prompt)
                    
                    if image_url:
                        print(f"✓ 图片生成成功: {image_url}")
                        
                        # 在屏幕上显示成功信息
                        try:
                            _xgo_edu.lcd_clear()
                            _xgo_edu.lcd_text(5, 5, "✓ 图片生成成功!", "GREEN", 12)
                            _xgo_edu.lcd_text(5, 25, "正在显示图片...", "YELLOW", 10)
                        except:
                            pass
                        
                        # 调用现有的HTTP图片显示方法
                        display_result = xgo_display_http_image(image_url, 0, 0)
                        
                        result_msg = (
                            f"🎨 XGO图片生成并显示完成\n"
                            f"原始提示词: {prompt}\n"
                            f"优化提示词: {actual_prompt}\n"
                            f"图片尺寸: {size}\n"
                            f"生成耗时: {attempt * 3}秒\n"
                            f"图片URL: {image_url}"
                        )
                        return ToolResponse(content=[TextBlock(type="text", text=result_msg)])
                    else:
                        return ToolResponse(content=[TextBlock(type="text", text="❌ 任务成功但未找到图片URL")])
                else:
                    return ToolResponse(content=[TextBlock(type="text", text="❌ 任务成功但结果格式异常")])
            
            elif task_status == "FAILED":
                error_info = query_result["output"].get("error", "未知错误")
                return ToolResponse(content=[TextBlock(type="text", text=f"❌ 图片生成失败: {error_info}")])
            
            elif task_status in ["PENDING", "RUNNING"]:
                # 继续等待
                continue
            else:
                return ToolResponse(content=[TextBlock(type="text", text=f"❌ 未知任务状态: {task_status}")])
        
        # 超时处理
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 图片生成超时（已等待{max_attempts * 3}秒），请稍后重试")])
        
    except Exception as e:
        error_msg = "❌ 图片生成失败: " + str(e)
        # 在屏幕上显示错误信息
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, "❌ 生成失败", "RED", 14)
            _xgo_edu.lcd_text(5, 30, str(e)[:40], "WHITE", 8)
        except:
            pass
        return ToolResponse(content=[TextBlock(type="text", text=error_msg)])


def xgo_stop():
    """
    停止XGO机器狗当前运动
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.stop()
        return ToolResponse(content=[TextBlock(type="text", text="✓ XGO已停止运动")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 停止失败: {str(e)}")])


def xgo_reset():
    """
    重置XGO机器狗到初始标准状态
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        _xgo_instance.reset()
        time.sleep(2)
        return ToolResponse(content=[TextBlock(type="text", text="✓ XGO已重置到初始状态，等待2秒")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 重置失败: {str(e)}")])


def xgo_read_imu(axis: str):
    """
    读取XGO机器人IMU数据
    
    Args:
        axis: 要读取的轴向数据 ('roll', 'pitch', 'yaw')
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance
    if _xgo_instance is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人不可用（可能处于模拟模式）")])
    
    try:
        if axis == "roll":
            value = _xgo_instance.roll
        elif axis == "pitch":
            value = _xgo_instance.pitch
        elif axis == "yaw":
            value = _xgo_instance.yaw
        else:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 不支持的轴向: {axis}")])
        
        axis_names = {"roll": "翻滚", "pitch": "俯仰", "yaw": "偏航"}
        axis_name = axis_names.get(axis, axis)
        return ToolResponse(content=[TextBlock(type="text", text=f"📐 XGO {axis_name}角度: {value}°")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 读取IMU数据失败: {str(e)}")])


def xgo_display_picture(filename: str, x: int = 0, y: int = 0):
    """
    在XGO屏幕上显示图片
    
    Args:
        filename: 图片文件名(jpg格式，位于/home/pi/xgoPictures/目录)
        x: 显示位置x坐标，默认0
        y: 显示位置y坐标，默认0
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        _xgo_edu.lcd_picture(filename, x, y)
        return ToolResponse(content=[TextBlock(type="text", text=f"🖼️ XGO屏幕显示图片: {filename} (位置: {x},{y})")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 显示图片失败: {str(e)}")])


def xgo_speak(filename: str):
    """
    XGO播放音频文件
    
    Args:
        filename: 音频文件名(位于/home/pi/Music/目录)
    
    Returns:
        ToolResponse对象
    """
    global _xgo_edu
    if _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGOEDU教育库不可用（可能处于模拟模式）")])
    
    try:
        os.system("mplayer /home/pi/Music/" + filename)
        return ToolResponse(content=[TextBlock(type="text", text=f"🔊 XGO播放音频: {filename}")])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 播放音频失败: {str(e)}")])


def xgo_find_person(max_search_time: float = 45.0):
    """
    XGO机器狗寻找人类目标
    
    Args:
        max_search_time: 最大搜索时间(秒)，默认45.0秒
    
    Returns:
        ToolResponse对象
    """
    global _xgo_instance, _xgo_edu
    if _xgo_instance is None or _xgo_edu is None:
        return ToolResponse(content=[TextBlock(type="text", text="❌ XGO机器人或教育库不可用（可能处于模拟模式）")])
    
    try:
        # 确保摄像头可用
        try:
            _xgo_edu.open_camera()
            time.sleep(1)
        except Exception as cam_e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 摄像头初始化失败: {str(cam_e)}")])
        
        # 在屏幕显示搜索状态
        try:
            _xgo_edu.lcd_clear()
            _xgo_edu.lcd_text(5, 5, "🔍 搜索人类目标", "YELLOW", 14)
        except:
            pass
        
        start_time = time.time()
        found = False
        
        # 搜索循环
        while time.time() - start_time < max_search_time:
            try:
                # 使用人脸检测 (返回 [x, y, w, h] 或 None)
                face_rect = _xgo_edu.face_detect()
                
                if face_rect is not None:
                    found = True
                    x, y, w, h = face_rect
                    
                    # 在屏幕显示结果
                    try:
                        _xgo_edu.lcd_clear()
                        _xgo_edu.lcd_text(5, 5, "✓ 找到人类目标", "GREEN", 14)
                        _xgo_edu.lcd_text(5, 25, f"位置:({int(x)}, {int(y)})", "WHITE", 12)
                        _xgo_edu.lcd_text(5, 45, f"大小:{int(w)}x{int(h)}", "WHITE", 12)
                    except:
                        pass
                    
                    return ToolResponse(content=[TextBlock(type="text", text=f"✓ 找到人类目标！位置:({int(x)}, {int(y)}), 大小:{int(w)}x{int(h)}")])
                
            except Exception as detect_e:
                print(f"⚠️ 检测失败: {detect_e}")
            
            # 继续搜索...
            time.sleep(0.1)
        
        if not found:
            try:
                _xgo_edu.lcd_clear()
                _xgo_edu.lcd_text(5, 5, "❌ 未找到人类目标", "RED", 14)
            except:
                pass
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ 搜索超时，未找到人类目标")])
            
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"❌ 人类搜索失败: {str(e)}")])
