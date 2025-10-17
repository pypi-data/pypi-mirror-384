#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码执行器服务
负责Python代码的执行和日志管理
"""

import os
import sys
import subprocess
import tempfile
import time
import shutil
import signal
import psutil
from datetime import datetime


class CodeExecutor:
    """Python代码执行器"""
    
    def __init__(self, execution_id):
        self.execution_id = execution_id
        self.logs = []
        self.is_running = False
        self.current_process = None  # 追踪当前进程
        self.start_time = None  # 执行开始时间
        self.last_output_time = None  # 最后一次输出时间
        
    def stop_execution(self):
        """停止当前执行的代码"""
        if self.current_process and self.current_process.poll() is None:
            try:
                pid = self.current_process.pid
                self.log(f"正在停止代码执行... (PID: {pid})", "INFO")
                
                # 尝试终止子进程树
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    
                    # 先终止所有子进程
                    for child in children:
                        try:
                            self.log(f"终止子进程: PID={child.pid}", "INFO")
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # 等待子进程结束
                    gone, alive = psutil.wait_procs(children, timeout=3)
                    
                    # 强制杀死仍存活的子进程
                    for p in alive:
                        try:
                            self.log(f"强制终止子进程: PID={p.pid}", "WARNING")
                            p.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # 先尝试优雅终止主进程
                self.current_process.terminate()
                self.current_process.wait(timeout=3)
                self.log(f"进程已终止 (PID: {pid})", "SUCCESS")
            except subprocess.TimeoutExpired:
                # 如果优雅终止失败，强制杀死
                self.log(f"强制终止进程... (PID: {pid})", "WARNING")
                self.current_process.kill()
                self.current_process.wait()
                self.log(f"进程已强制终止 (PID: {pid})", "SUCCESS")
            except Exception as e:
                self.log(f"停止执行时出错: {str(e)}", "ERROR")
            finally:
                self.is_running = False
                self.current_process = None
                self.start_time = None
                self.last_output_time = None
        
    def get_execution_status(self):
        """获取当前执行状态，用于调试"""
        status = {
            'execution_id': self.execution_id,
            'is_running': self.is_running,
            'has_process': self.current_process is not None,
            'process_alive': self.current_process and self.current_process.poll() is None,
        }
        
        if self.start_time:
            status['elapsed_time'] = time.time() - self.start_time
            status['start_time'] = datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        if self.last_output_time:
            status['no_output_duration'] = time.time() - self.last_output_time
            status['last_output_time'] = datetime.fromtimestamp(self.last_output_time).strftime('%Y-%m-%d %H:%M:%S')
        
        if self.current_process:
            status['process_pid'] = self.current_process.pid
            try:
                proc = psutil.Process(self.current_process.pid)
                status['process_status'] = proc.status()
                status['cpu_percent'] = proc.cpu_percent()
                status['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                status['num_threads'] = proc.num_threads()
                
                # 获取子进程信息
                children = proc.children(recursive=True)
                status['num_children'] = len(children)
                status['children_pids'] = [child.pid for child in children]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                status['process_status'] = 'not_found'
        
        return status
    
    def check_if_stuck(self):
        """检查是否卡住"""
        if not self.is_running or not self.current_process:
            return False, "未运行"
        
        # 检查进程是否还活着
        if self.current_process.poll() is not None:
            return True, "进程已结束但状态未更新"
        
        # 检查是否长时间无输出
        if self.last_output_time:
            no_output_duration = time.time() - self.last_output_time
            if no_output_duration > 60:  # 60秒无输出
                return True, f"无输出{no_output_duration:.1f}秒，可能卡住"
        
        # 检查进程状态和CPU使用率
        try:
            proc = psutil.Process(self.current_process.pid)
            proc_status = proc.status()
            cpu_percent = proc.cpu_percent(interval=1.0)
            
            # disk-sleep 状态通常表示在等待I/O，可能卡住
            if proc_status == psutil.STATUS_DISK_SLEEP:
                return True, f"进程处于磁盘睡眠状态(disk-sleep)，可能在等待I/O操作"
            
            # sleeping状态且CPU使用率极低，可能卡住
            if proc_status == psutil.STATUS_SLEEPING and cpu_percent < 0.1:
                # 但要排除正常的sleep操作（通过无输出时间判断）
                if self.last_output_time and (time.time() - self.last_output_time) > 30:
                    return True, f"进程休眠且30秒无输出，可能卡住"
            
            # CPU使用率极低且运行时间较长
            if cpu_percent < 0.1 and self.start_time:
                elapsed = time.time() - self.start_time
                if elapsed > 120:  # 运行超过2分钟但CPU极低
                    return True, f"CPU使用率{cpu_percent:.1f}%，已运行{elapsed:.0f}秒，可能卡住"
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True, "进程不存在"
        
        return False, "正常运行"

    def log(self, message, level='INFO'):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': str(message)
        }
        self.logs.append(log_entry)
        return log_entry
    def _kill_all_python_processes(self):
        """清理所有非当前执行的Python进程（谨慎使用）"""
        killed_processes = []
        current_pid = os.getpid()  # 当前Python进程的PID
        
        try:
            # 查找所有Python进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == current_pid:
                        continue  # 跳过当前进程
                    
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            
                            # 跳过当前正在执行的进程
                            if self.current_process and proc.info['pid'] == self.current_process.pid:
                                continue
                            
                            # 跳过系统关键进程（避免误杀）
                            if any(keyword in cmdline_str.lower() for keyword in 
                                   ['site-packages', 'pip', 'setuptools', 'wheel', 'vscode', 'pycharm']):
                                continue
                            
                            proc_obj = psutil.Process(proc.info['pid'])
                            self.log(f"发现Python进程: PID={proc.info['pid']}, 命令: {cmdline_str}", "INFO")
                            
                            # 先尝试优雅终止
                            proc_obj.terminate()
                            try:
                                proc_obj.wait(timeout=3)
                                killed_processes.append(f"PID {proc.info['pid']} ({cmdline_str})")
                                self.log(f"已终止进程: PID={proc.info['pid']}", "SUCCESS")
                            except psutil.TimeoutExpired:
                                # 强制杀死
                                proc_obj.kill()
                                proc_obj.wait()
                                killed_processes.append(f"PID {proc.info['pid']} ({cmdline_str}) [强制]")
                                self.log(f"强制终止进程: PID={proc.info['pid']}", "WARNING")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 进程已经不存在或无权访问，忽略
                    continue
                except Exception as e:
                    self.log(f"检查进程时出错: {str(e)}", "WARNING")
                    continue
                    
        except Exception as e:
            self.log(f"查承Python进程时出错: {str(e)}", "ERROR")
            
        if killed_processes:
            self.log(f"已清理 {len(killed_processes)} 个Python进程", "SUCCESS")
        else:
            self.log("未发现需要清理的Python进程", "INFO")
    
    def _kill_screen_processes(self):
        """查找并终止占用屏幕资源的进程（特别main.py）"""
        killed_processes = []
        try:
            # 查找所有Python进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            # 检查是否是main.py或其他屏幕相关的程序
                            cmdline_str = ' '.join(cmdline)
                            
                            # 检测条件：
                            # 1. 屏幕相关的代码
                            # 2. 临时执行文件且处于disk-sleep状态
                            is_screen_related = ('main.py' in cmdline_str or 
                                'lcd' in cmdline_str.lower() or 
                                'display' in cmdline_str.lower() or
                                'screen' in cmdline_str.lower())
                            
                            is_stuck_temp_file = (
                                'exec_exec_' in cmdline_str and 
                                '.xgo-blockly/code_execution' in cmdline_str and
                                proc.info.get('status') in ['disk-sleep', 'sleeping']
                            )
                            
                            if is_screen_related or is_stuck_temp_file:
                                # 跳过当前正在执行的进程
                                if self.current_process and proc.pid == self.current_process.pid:
                                    continue
                                    
                                proc_obj = psutil.Process(proc.info['pid'])
                                reason = "屏幕相关" if is_screen_related else f"卡住的临时执行文件({proc.info.get('status', 'unknown')})"
                                self.log(f"发现{reason}进程: PID={proc.info['pid']}, 命令: {cmdline_str[:80]}", "INFO")
                                
                                # 先尝试优雅终止
                                proc_obj.terminate()
                                try:
                                    proc_obj.wait(timeout=3)
                                    killed_processes.append(f"PID {proc.info['pid']} ({reason})")
                                    self.log(f"已终止进程: PID={proc.info['pid']}", "SUCCESS")
                                except psutil.TimeoutExpired:
                                    # 强制杀死
                                    proc_obj.kill()
                                    proc_obj.wait()
                                    killed_processes.append(f"PID {proc.info['pid']} ({reason}) [强制]")
                                    self.log(f"强制终止进程: PID={proc.info['pid']}", "WARNING")
                                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 进程已经不存在或无权访问，忽略
                    continue
                except Exception as e:
                    self.log(f"检查进程时出错: {str(e)}", "WARNING")
                    continue
                    
        except Exception as e:
            self.log(f"查找屏幕进程时出错: {str(e)}", "ERROR")
            
        if killed_processes:
            self.log(f"已清理 {len(killed_processes)} 个进程", "SUCCESS")
        else:
            self.log("未发现需要清理的进程", "INFO")
    
    def _is_screen_related_code(self, code):
        """检测代码是否与屏幕相关"""
        # 更精确的屏幕关键词检测，避免误判
        screen_keywords = [
            'lcd_', 'xgo_edu.lcd', 'show_image', 'screen_',
             'lcd_clear', 'lcd_text', 'lcd_picture', 'lcd_circle',
            'lcd_rectangle', 'lcd_line', 'lcd_round','XGOAgent'
        ]
        
        code_lower = code.lower()
        
        # 排除豆瓣AI相关的误判关键词
        excluded_contexts = [
            'doubao_multimodal_chat',  # 豆瓣多模态函数
            'image_url',               # 图片URL相关
            'video_url',               # 视频URL相关
            'display_text_on_screen',  # 这个是edulib中的函数，但在豆瓣AI代码中可能出现
            'response.json()',         # API响应
            'requests.',               # HTTP请求相关
            'json.',                   # JSON处理
            'print(',                  # 打印输出
        ]
        
        # 检查是否在排除的上下文中
        for excluded in excluded_contexts:
            if excluded.lower() in code_lower:
                # 如果包含排除的上下文，进行更严格的检查
                for keyword in screen_keywords:
                    if keyword.lower() in code_lower:
                        # 检查关键词是否在真正的屏幕操作上下文中
                        lines = code.split('\n')
                        for line in lines:
                            line_lower = line.lower()
                            if keyword.lower() in line_lower:
                                # 检查这一行是否真的是屏幕操作
                                if any(exclude.lower() in line_lower for exclude in excluded_contexts):
                                    continue  # 跳过排除的上下文
                                else:
                                    return True  # 真正的屏幕操作
                return False  # 在排除上下文中，不是屏幕操作
        
        # 如果不在排除上下文中，按原逻辑检查
        for keyword in screen_keywords:
            if keyword.lower() in code_lower:
                return True
        return False
    
    def execute_code(self, code, log_callback=None, force_cleanup=False):
        """
        执行Python代码，支持实时日志回调
        
        Args:
            code: 要执行的Python代码
            log_callback: 实时日志回调函数
            force_cleanup: 是否强制清理所有之前的进程（默认False，只清理屏幕相关进程）
        """
        self.is_running = True
        self.start_time = time.time()
        self.last_output_time = time.time()
        self.log(f"开始执行... (ID: {self.execution_id})", "INFO")
        if log_callback:
            log_callback(self.logs[-1])
        
        # 检查是否需要清理进程
        should_cleanup = force_cleanup or self._is_screen_related_code(code)
        
        if should_cleanup:
            if force_cleanup:
                self.log("强制清理模式：正在清理所有占用资源的进程...", "INFO")
            else:
                self.log("检测到屏幕相关代码，正在清理占用屏幕的进程...", "INFO")
            
            if log_callback:
                log_callback(self.logs[-1])
            
            if force_cleanup:
                self._kill_all_python_processes()
            else:
                self._kill_screen_processes()
            
            # 短暂等待确保进程完全终止
            time.sleep(0.5)
        
        process = None
        try:
            # 获取执行目录，兼容pip安装和开发环境
            exec_dir = self._get_execution_dir()
            
            # 确保执行目录存在
            if not os.path.exists(exec_dir):
                os.makedirs(exec_dir)
            
            # 创建执行文件路径
            exec_file = os.path.join(exec_dir, f'exec_{self.execution_id}.py')
            
            # 预处理代码，自动注入编码处理
            processed_code = self._preprocess_code(code)
            
            # 写入预处理后的代码到执行文件
            with open(exec_file, 'w', encoding='utf-8') as f:
                f.write(processed_code)
            
            # 设置执行环境，添加services目录到Python路径
            services_dir = self._get_services_dir()
            env = os.environ.copy()
            if services_dir and os.path.exists(services_dir):
                env['PYTHONPATH'] = services_dir
            env['PYTHONUNBUFFERED'] = '1'  # 强制Python输出不缓冲
            # 修复Windows编码问题
            env['PYTHONIOENCODING'] = 'utf-8'  # 强制Python使用UTF-8编码
            if os.name == 'nt':  # Windows系统
                env['PYTHONUTF8'] = '1'  # 启用UTF-8模式
            
            # 使用subprocess执行代码，实时捕获输出
            process = subprocess.Popen(
                [sys.executable, '-u', exec_file],  # -u参数确保输出不缓冲
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并stderr到stdout
                universal_newlines=True,
                encoding='utf-8',  # 明确指定utf-8编码
                errors='replace',  # 遇到编码错误时替换为占位符
                bufsize=0,  # 无缓冲
                cwd=exec_dir,
                env=env
            )
            
            # 保存当前进程引用
            self.current_process = process
            
            # 实时读取输出（带超时检测）
            import select
            timeout_seconds = 300  # 5分钟超时
            no_output_timeout = 60  # 60秒无输出超时
            
            while True:
                # 检查总超时
                elapsed = time.time() - self.start_time
                if elapsed > timeout_seconds:
                    self.log(f"执行超时 ({timeout_seconds}秒)，强制终止", "WARNING")
                    process.kill()
                    break
                
                # 检查无输出超时
                no_output_elapsed = time.time() - self.last_output_time
                if no_output_elapsed > no_output_timeout:
                    self.log(f"无输出超时 ({no_output_timeout}秒)，可能卡住，强制终止", "WARNING")
                    process.kill()
                    break
                
                # 非阻塞读取（使用select，仅Unix系统）
                if os.name != 'nt':  # Unix系统
                    import select
                    ready, _, _ = select.select([process.stdout], [], [], 1.0)
                    if not ready:
                        # 检查进程是否已结束
                        if process.poll() is not None:
                            break
                        continue
                
                # 读取一行输出
                try:
                    output = process.stdout.readline()
                except Exception as e:
                    self.log(f"读取输出时出错: {str(e)}", "ERROR")
                    break
                    
                if output == '' and process.poll() is not None:
                    break
                    
                if output.strip():
                    self.last_output_time = time.time()
                    log_entry = self.log(output.strip(), "OUTPUT")
                    if log_callback:
                        log_callback(log_entry)
                else:
                    # 即使是空行，也更新最后输出时间（说明进程还在运行）
                    if output == '':
                        pass
                    else:
                        self.last_output_time = time.time()
            
            # 等待进程结束（带超时）
            try:
                return_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("进程未正常结束，强制终止", "WARNING")
                process.kill()
                return_code = process.wait()
            
            # 计算执行时间
            execution_time = time.time() - self.start_time
            
            if return_code == 0:
                log_entry = self.log(f"代码执行完成 (耗时: {execution_time:.2f}秒)", "SUCCESS")
            elif return_code == -9 or return_code == -15:  # SIGKILL or SIGTERM
                log_entry = self.log(f"程序被终止 (耗时: {execution_time:.2f}秒)", "WARNING")
            else:
                log_entry = self.log(f"程序异常退出 (退出码: {return_code}, 耗时: {execution_time:.2f}秒)", "ERROR")
            
            if log_callback:
                log_callback(log_entry)
                
        except Exception as e:
            log_entry = self.log(f"执行失败: {str(e)}", "ERROR")
            if log_callback:
                log_callback(log_entry)
        finally:
            # 清理执行文件
            try:
                if 'exec_file' in locals() and os.path.exists(exec_file):
                    os.unlink(exec_file)
            except Exception:
                pass  # 静默清理，不显示清理信息
            
            # 确保进程被终止
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
            
            # 清理进程引用
            self.current_process = None
            self.is_running = False
    
    def _get_execution_dir(self):
        """
        获取代码执行目录，兼容pip安装和开发环境
        """
        try:
            # 首先尝试使用用户主目录
            home_dir = os.path.expanduser('~')
            exec_dir = os.path.join(home_dir, '.xgo-blockly', 'code_execution')
            return exec_dir
        except Exception:
            # 如果失败，使用临时目录
            import tempfile
            return os.path.join(tempfile.gettempdir(), 'xgo_blockly_execution')
    
    def _get_services_dir(self):
        """
        获取services目录路径，兼容pip安装和开发环境
        """
        try:
            # 方法1: 尝试使用当前模块的路径（pip安装后）
            current_file = os.path.abspath(__file__)
            # 当前文件是 services/code_executor.py
            services_dir = os.path.dirname(current_file)
            if os.path.exists(services_dir):
                return services_dir
            
            # 方法2: 尝试使用开发环境的路径结构
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            dev_services_dir = os.path.join(project_root, 'xgo-blockly-server', 'services')
            if os.path.exists(dev_services_dir):
                return dev_services_dir
            
            # 方法3: 尝试使用相对路径
            relative_services_dir = os.path.join(project_root, 'services')
            if os.path.exists(relative_services_dir):
                return relative_services_dir
                
        except Exception as e:
            # 日志记录错误，但不影响程序运行
            pass
        
        # 如果所有方法都失败，返回 None
        return None
    
    def _preprocess_code(self, code):
        """
        预处理代码，自动注入编码处理和其他必要的初始化代码
        """
        # 编码处理代码模板
        encoding_fix = '''# -*- coding: utf-8 -*-
# 自动注入的Windows编码处理
import os
import sys

# 修复Windows编码问题
if os.name == 'nt':  # Windows系统
    try:
        import codecs
        # 检查是否已经设置过编码
        if not hasattr(sys.stdout, '_wrapped'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stdout._wrapped = True
        if not hasattr(sys.stderr, '_wrapped'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
            sys.stderr._wrapped = True
    except Exception as e:
        # 如果编码设置失败，不影响程序正常运行
        pass

# 自动添加services目录到sys.path以支持edulib等模块导入
try:
    services_dir = r"{services_dir}"
    if services_dir and services_dir != "None" and os.path.exists(services_dir):
        if services_dir not in sys.path:
            sys.path.insert(0, services_dir)
except Exception:
    pass

'''
        
        # 获取services目录
        services_dir = self._get_services_dir()
        if services_dir is None:
            services_dir = "None"
        
        # 格式化编码修复代码，插入services目录路径
        encoding_fix = encoding_fix.format(services_dir=services_dir.replace('\\', '\\\\') if services_dir != "None" else "None")
        
        # 检查是否已经包含编码处理
        lines = code.split('\n')
        has_encoding_fix = any('Windows编码问题' in line or 'codecs.getwriter' in line for line in lines)
        
        if has_encoding_fix:
            # 已经包含编码处理，直接返回
            return code
        
        # 找到第一个非注释、非空行的位置
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                insert_pos = i
                break
        
        # 在适当位置插入编码处理代码
        if insert_pos == 0:
            # 如果没有找到非注释行，就插入到最前面
            return encoding_fix + code
        else:
            # 在第一个非注释行之前插入
            result_lines = lines[:insert_pos] + [encoding_fix] + lines[insert_pos:]
            return '\n'.join(result_lines)


class ExecutionManager:
    """执行管理器，管理多个代码执行任务"""
    
    def __init__(self):
        self.execution_logs = {}
        self.active_executors = {}  # 追踪活跃的执行器
        self.max_concurrent_executions = 1  # 最大并发执行数
        self.debug_mode = True  # 调试模式
    
    def create_executor(self, execution_id):
        """创建代码执行器"""
        # 检查是否有卡住的执行器
        self._check_and_cleanup_stuck_executors()
        
        # 停止之前的所有执行器
        stopped = self.stop_all_executions()
        if stopped > 0 and self.debug_mode:
            print(f"[调试] 创建新执行器前停止了 {stopped} 个执行器")
        
        executor = CodeExecutor(execution_id)
        self.execution_logs[execution_id] = []
        self.active_executors[execution_id] = executor
        
        if self.debug_mode:
            print(f"[调试] 创建执行器: {execution_id}")
            print(f"[调试] 当前活跃执行器数: {len(self.active_executors)}")
        
        return executor
    
    def _check_and_cleanup_stuck_executors(self):
        """检查并清理卡住的执行器"""
        stuck_executors = []
        
        for execution_id, executor in list(self.active_executors.items()):
            is_stuck, reason = executor.check_if_stuck()
            if is_stuck:
                stuck_executors.append((execution_id, reason))
                if self.debug_mode:
                    print(f"[调试] 发现卡住的执行器: {execution_id}, 原因: {reason}")
                try:
                    executor.stop_execution()
                except Exception as e:
                    print(f"[错误] 停止卡住的执行器时出错: {e}")
        
        return stuck_executors
    
    def get_all_execution_status(self):
        """获取所有执行器的状态"""
        status_list = []
        for execution_id, executor in self.active_executors.items():
            status = executor.get_execution_status()
            is_stuck, reason = executor.check_if_stuck()
            status['is_stuck'] = is_stuck
            status['stuck_reason'] = reason
            status_list.append(status)
        return status_list
    
    def print_debug_info(self):
        """打印调试信息"""
        print("\n=" * 50)
        print("执行管理器调试信息")
        print("=" * 50)
        print(f"活跃执行器数: {len(self.active_executors)}")
        print(f"执行日志数: {len(self.execution_logs)}")
        
        for status in self.get_all_execution_status():
            print(f"\n执行器: {status['execution_id']}")
            print(f"  运行状态: {status['is_running']}")
            print(f"  进程存在: {status['has_process']}")
            print(f"  进程活着: {status['process_alive']}")
            if 'elapsed_time' in status:
                print(f"  已运行: {status['elapsed_time']:.1f}秒")
            if 'no_output_duration' in status:
                print(f"  无输出: {status['no_output_duration']:.1f}秒")
            if status['is_stuck']:
                print(f"  状态: 卡住 - {status['stuck_reason']}")
            if 'process_pid' in status:
                print(f"  PID: {status['process_pid']}")
                print(f"  CPU: {status.get('cpu_percent', 'N/A')}%")
                print(f"  内存: {status.get('memory_mb', 'N/A'):.1f}MB")
                print(f"  子进程: {status.get('num_children', 0)}")
        
        print("=" * 50 + "\n")
    
    def add_log(self, execution_id, log_entry):
        """添加日志到队列"""
        if execution_id not in self.execution_logs:
            self.execution_logs[execution_id] = []
        self.execution_logs[execution_id].append(log_entry)
    
    def get_logs(self, execution_id):
        """获取执行日志"""
        return self.execution_logs.get(execution_id, [])
    
    def pop_log(self, execution_id):
        """弹出一条日志"""
        if execution_id in self.execution_logs and self.execution_logs[execution_id]:
            return self.execution_logs[execution_id].pop(0)
        return None
    
    def clear_logs(self, execution_id):
        """清理日志"""
        if execution_id in self.execution_logs:
            del self.execution_logs[execution_id]
    
    def has_logs(self, execution_id):
        """检查是否有日志"""
        return execution_id in self.execution_logs and bool(self.execution_logs[execution_id])
    
    def stop_all_executions(self):
        """停止所有活跃的代码执行"""
        stopped_count = 0
        for execution_id, executor in list(self.active_executors.items()):
            if executor.is_running:
                try:
                    executor.stop_execution()
                    stopped_count += 1
                except Exception as e:
                    print(f"停止执行器 {execution_id} 时出错: {e}")
        
        # 清理已停止的执行器
        self.active_executors = {k: v for k, v in self.active_executors.items() if v.is_running}
        
        if stopped_count > 0:
            print(f"已停止 {stopped_count} 个正在运行的执行器")
        
        return stopped_count
    
    def stop_execution(self, execution_id):
        """停止指定的代码执行"""
        if execution_id in self.active_executors:
            executor = self.active_executors[execution_id]
            if executor.is_running:
                executor.stop_execution()
                return True
        return False
    
    def cleanup_finished_executors(self):
        """清理已完成的执行器"""
        finished_ids = []
        for execution_id, executor in self.active_executors.items():
            if not executor.is_running:
                finished_ids.append(execution_id)
        
        for execution_id in finished_ids:
            del self.active_executors[execution_id]


# 全局执行管理器实例
execution_manager = ExecutionManager()