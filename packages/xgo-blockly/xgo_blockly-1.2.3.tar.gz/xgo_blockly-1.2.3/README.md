# XGO Blockly 图形化编程服务器

## 简介

XGO Blockly 是专为陆吾 XGO 机器人系列设计的图形化编程和 AI 编程服务器。通过简单的安装和启动,您可以在电脑浏览器中进行图形化编程,AI 编程,控制您的陆吾 XGO机器人。

## 支持的机型

- **XGO-Lite**：轻量级四足机器狗,680g超轻设计,适合教育入门
- **XGO-Mini**：十二自由度AI机器狗,配备机械臂和500万像素摄像头,支持AI视觉和语音识别
- **XGO-Rider**：双轮足开源开发平台,基于树莓派,560g桌面级设计,支持AI边缘计算、自稳控制和地形跨越

- **未来的机型将陆续加入。**

## 安装要求

该 pip 包需要安装在陆吾 XGO 机器人系列的树莓派机器上。

## 安装步骤

1. **进入指定目录**
   ```bash
   cd /home/pi/RaspberryPi-CM5/
   ```

2. **创建或激活虚拟环境**
   
   首先检查是否已存在 `blocklyvenv` 虚拟环境：
   ```bash
   ls blocklyvenv
   ```
   
   如果不存在，请创建虚拟环境（注意：使用 `--system-site-packages` 参数确保继承系统包，避免 Picamera2 和 libcamera 依赖问题）：
   ```bash
   python3 -m venv --system-site-packages blocklyvenv
   ```
   
   激活虚拟环境：
   ```bash
   source blocklyvenv/bin/activate
   ```

3. **安装 xgo-blockly 包**
   ```bash
   pip install xgo-blockly -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. **安装 AI 识别 依赖**
   
   由于包冲突的原因，需要单独安装 MediaPipe 等几个包：
   ```bash
   pip install mediapipe -i https://pypi.tuna.tsinghua.edu.cn/
   pip install tensorflow==2.15.0 -i https://pypi.tuna.tsinghua.edu.cn/
   ```

## 启动服务

安装成功后，运行以下命令启动图形化编程和AI编程服务器：

```bash
xgo-blockly
```

## 使用方法

服务器启动后，在电脑上打开浏览器，访问树莓派的IP地址和端口号（默认端口号为8000）即可开始图形化编程和AI编程。

## 功能特性

- 🎯 **图形化编程**：拖拽式编程界面，简单易用
- 🤖 **AI编程辅助**：智能代码生成和优化建议
- 🔗 **实时控制**：直接控制陆吾机器人硬件
- 🌐 **Web界面**：跨平台浏览器访问
- 📱 **响应式设计**：支持电脑、平板等设备

## 技术支持

如有问题或需要技术支持，请联系陆吾机器人技术团队。