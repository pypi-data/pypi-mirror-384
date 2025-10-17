#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断并清理卡住的Python进程
"""

import psutil
import os
import sys
import time

def diagnose_and_kill():
    """诊断并强制终止相关进程"""
    
    current_pid = os.getpid()
    server_pids = []  # 服务器进程PID
    execution_pids = []  # 执行进程PID
    
    print("\n" + "="*60)
    print("诊断Python进程")
    print("="*60)
    
    try:
        # 查找所有Python进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status', 'create_time']):
            try:
                if proc.pid == current_pid:
                    continue
                    
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline)
                        status = proc.info.get('status', 'unknown')
                        
                        # 获取进程详细信息
                        try:
                            p = psutil.Process(proc.pid)
                            cpu = p.cpu_percent(interval=0.1)
                            mem_mb = p.memory_info().rss / 1024 / 1024
                            create_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                                       time.localtime(p.create_time()))
                        except:
                            cpu = 0
                            mem_mb = 0
                            create_time = 'unknown'
                        
                        # 判断进程类型
                        is_server = 'xgo_blockly' in cmdline_str or 'flask' in cmdline_str.lower()
                        is_execution = 'exec_' in cmdline_str and '.xgo-blockly' in cmdline_str
                        
                        if is_server:
                            server_pids.append(proc.pid)
                            print(f"\n[服务器进程] PID={proc.pid}")
                        elif is_execution:
                            execution_pids.append(proc.pid)
                            print(f"\n[执行进程] PID={proc.pid} ⚠️")
                        else:
                            print(f"\n[其他Python进程] PID={proc.pid}")
                        
                        print(f"  命令: {cmdline_str[:100]}")
                        print(f"  状态: {status}")
                        print(f"  CPU: {cpu:.1f}%")
                        print(f"  内存: {mem_mb:.1f}MB")
                        print(f"  创建时间: {create_time}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        print("\n" + "="*60)
        print(f"发现 {len(server_pids)} 个服务器进程")
        print(f"发现 {len(execution_pids)} 个执行进程")
        print("="*60)
        
        # 询问是否清理
        if execution_pids:
            print(f"\n⚠️  发现 {len(execution_pids)} 个执行进程可能卡住!")
            print(f"PID列表: {execution_pids}")
            
            choice = input("\n是否强制终止这些进程? (y/n): ").strip().lower()
            if choice == 'y':
                for pid in execution_pids:
                    try:
                        p = psutil.Process(pid)
                        print(f"正在终止 PID={pid}...")
                        
                        # 先终止子进程
                        children = p.children(recursive=True)
                        for child in children:
                            try:
                                child.kill()
                            except:
                                pass
                        
                        # 强制杀死主进程
                        p.kill()
                        p.wait(timeout=3)
                        print(f"✓ 已终止 PID={pid}")
                    except Exception as e:
                        print(f"✗ 终止 PID={pid} 失败: {e}")
                
                print("\n✓ 清理完成!")
            else:
                print("已取消清理")
        else:
            print("\n✓ 未发现需要清理的执行进程")
            
    except Exception as e:
        print(f"\n错误: {e}")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    diagnose_and_kill()
