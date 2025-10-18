"""浏览器跳转和等待工具"""

import webbrowser
import time
import sys
from typing import Optional


def open_browser_and_wait(url: str, message: str = None) -> bool:
    """打开浏览器并等待用户操作"""
    try:
        print(f"🌐 正在打开浏览器...")
        print(f"📎 URL: {url}")
        
        # 打开浏览器
        success = webbrowser.open(url)
        
        if not success:
            print("[X] 无法自动打开浏览器")
            print(f"[L] 请手动复制以下链接到浏览器:")
            print(f"   {url}")
        else:
            print("[OK] 浏览器已打开")
        
        if message:
            print(f"[?] {message}")
        
        return True
        
    except Exception as e:
        print(f"[X] 打开浏览器失败: {e}")
        print(f"[L] 请手动访问: {url}")
        return False


def wait_for_input(prompt: str = "请按回车键继续...") -> str:
    """等待用户输入"""
    try:
        return input(f"\n{prompt}")
    except KeyboardInterrupt:
        print("\n[X] 操作取消")
        return ""
    except EOFError:
        return ""


def confirm_continue(message: str = "是否继续？") -> bool:
    """确认是否继续"""
    while True:
        try:
            response = input(f"\n{message} (y/n): ").strip().lower()
            if response in ['y', 'yes', '是', '确认']:
                return True
            elif response in ['n', 'no', '否', '取消']:
                return False
            else:
                print("请输入 y/yes/是 或 n/no/否")
        except (KeyboardInterrupt, EOFError):
            print("\n[X] 操作取消")
            return False


def show_loading_dots(message: str, duration: float = 2.0):
    """显示加载动画"""
    print(f"{message}", end="", flush=True)
    
    for i in range(int(duration * 2)):
        print(".", end="", flush=True)
        time.sleep(0.5)
    
    print(" 完成")


def print_step(step_num: int, total_steps: int, message: str):
    """打印步骤信息"""
    print(f"\n[L] 步骤 {step_num}/{total_steps}: {message}")


def print_provider_info(provider):
    """打印厂商信息"""
    print(f"[#] 厂商信息:")
    print(f"   名称: {provider.name}")
    print(f"   描述: {provider.description}")
    print(f"   API地址: {provider.base_url}")
    if provider.docs_url:
        print(f"   文档: {provider.docs_url}")
    if provider.api_key_help:
        print(f"   [?] API Key获取: {provider.api_key_help}")