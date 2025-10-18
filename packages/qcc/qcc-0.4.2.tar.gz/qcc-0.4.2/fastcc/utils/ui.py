"""用户界面工具模块"""

import sys
import time
import select
import threading
import asyncio
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.live import Live
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import FormattedText


# Windows emoji 兼容性检测
def _supports_emoji() -> bool:
    """检测当前终端是否支持 emoji"""
    if not sys.platform.startswith('win'):
        return True

    # Windows 10+ 的新终端（Windows Terminal）支持 emoji
    # 检查 WT_SESSION 环境变量
    import os
    if os.environ.get('WT_SESSION'):
        return True

    # 检查是否在 VSCode 集成终端中
    if os.environ.get('TERM_PROGRAM') == 'vscode':
        return True

    # 默认 Windows 控制台不支持 emoji
    return False


# 图标映射：emoji -> ASCII 回退
_ICON_MAP = {
    "🚀": "[>>]",
    "✅": "[OK]",
    "❌": "[X]",
    "⚠️": "[!]",
    "ℹ️": "[i]",
    "⏳": "[...]",
    "⭐": "*",
    "🔄": "[~]",
    "💰": "[$]",
    "📊": "[#]",
    "🎯": "[*]",
    "💡": "[?]",
    "🔧": "[+]",
    "📝": "[=]",
    "🎉": "[!]",
    "📋": "[L]",
    "👋": "[>]",
    "⚙️": "[*]",
    "🗑️": "[D]",
    "⏱️": "[T]",
    "🚫": "[B]",
    "❓": "[?]",
    "🔥": "[F]",
    "⚡": "[Z]",
    "🛡️": "[S]",
    "👤": "[U]",
    "🤖": "[R]",
}


def safe_icon(emoji: str) -> str:
    """安全地返回图标，在不支持 emoji 的终端上回退到 ASCII"""
    if _supports_emoji():
        return emoji
    return _ICON_MAP.get(emoji, emoji)


def prompt_with_timeout(message: str, timeout: int = 3, default: str = "") -> str:
    """带超时的用户输入提示
    
    Args:
        message: 提示信息
        timeout: 超时时间（秒）
        default: 默认值
        
    Returns:
        用户输入或默认值
    """
    print(message, end='', flush=True)
    
    # Windows系统使用threading实现超时
    if sys.platform.startswith('win'):
        result = []
        
        def get_input():
            try:
                result.append(input())
            except EOFError:
                result.append('')
        
        # 启动输入线程
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # 倒计时显示
        for remaining in range(timeout, 0, -1):
            if input_thread.is_alive():
                print(f'\r{message[:-2]}，{remaining}秒后自动选择): ', end='', flush=True)
                time.sleep(1)
            else:
                break
        
        # 等待输入线程完成或超时
        input_thread.join(timeout=0.1)
        
        if result:
            print()  # 换行
            return result[0].strip()
        else:
            timeout_icon = "[TIMEOUT]" if sys.platform.startswith('win') else "⏰"
            print(f"\n{timeout_icon} {timeout}秒超时，使用默认选择: {default}")
            return default
    
    # Unix系统使用select实现超时
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    
    if ready:
        return sys.stdin.readline().strip()
    else:
        timeout_icon = "[TIMEOUT]" if sys.platform.startswith('win') else "⏰"
        print(f"\n{timeout_icon} {timeout}秒超时，使用默认选择: {default}")
        return default


def select_from_list(items: List[str], prompt: str = "请选择", 
                    timeout: int = 3, default_index: int = 0) -> int:
    """从列表中选择项目，支持箭头键导航和超时自动选择
    
    Args:
        items: 选择项列表
        prompt: 提示信息
        timeout: 超时时间（秒）
        default_index: 默认选择的索引
        
    Returns:
        选择的索引，-1表示取消
    """
    if not items:
        return -1
    
    # 确保默认索引有效
    if not (0 <= default_index < len(items)):
        default_index = 0
    
    # 使用rich终端UI进行选择
    try:
        return _interactive_select(items, prompt, timeout, default_index)
    except Exception as e:
        # 如果新UI失败，回退到原来的实现
        print(f"{safe_icon('⚠️')} 终端UI启动失败，使用简化模式: {e}")
        return _fallback_select(items, prompt, timeout, default_index)


def _interactive_select(items: List[str], prompt: str, timeout: int, default_index: int) -> int:
    """使用prompt_toolkit的交互式选择器"""
    
    class SelectionState:
        def __init__(self):
            self.current_index = default_index
            self.countdown_active = True
            self.countdown_remaining = timeout
            self.result = None
            self.cancelled = False
    
    state = SelectionState()
    console = Console()
    
    # 创建键绑定
    bindings = KeyBindings()
    
    @bindings.add('up')
    def move_up(event):
        state.countdown_active = False
        state.current_index = (state.current_index - 1) % len(items)
        
    @bindings.add('down')
    def move_down(event):
        state.countdown_active = False
        state.current_index = (state.current_index + 1) % len(items)
        
    @bindings.add('enter')
    def accept(event):
        state.result = state.current_index
        event.app.exit()
        
    @bindings.add('c-c')
    def cancel(event):
        state.cancelled = True
        event.app.exit()
        
    @bindings.add('escape')
    def escape(event):
        state.cancelled = True
        event.app.exit()
    
    # 数字键选择
    for i in range(min(9, len(items))):
        @bindings.add(str(i + 1))
        def select_number(event, index=i):
            state.countdown_active = False
            state.current_index = index
            state.result = index
            event.app.exit()
    
    def get_formatted_content():
        """获取格式化的显示内容"""
        lines = []
        
        # 添加提示
        lines.append(("class:prompt", f"\n{prompt}:\n"))
        
        # 添加选项列表
        for i, item in enumerate(items):
            if i == state.current_index:
                marker = safe_icon("⭐") if not sys.platform.startswith('win') else ">"
                lines.append(("class:selected", f"{marker} {i + 1}. {item}\n"))
            else:
                lines.append(("", f"  {i + 1}. {item}\n"))
        
        # 添加操作提示
        lines.append(("class:help", "\n"))
        
        if state.countdown_active and state.countdown_remaining > 0:
            default_item = items[default_index] if 0 <= default_index < len(items) else "无"
            lines.append(("class:countdown", f"⏰ {state.countdown_remaining}秒后自动选择: {default_item}\n"))
            lines.append(("class:help", "使用 ↑↓ 键选择，Enter 确认，Ctrl+C 取消"))
        else:
            lines.append(("class:help", "使用 ↑↓ 键选择，Enter 确认，Ctrl+C 取消"))
        
        return FormattedText(lines)
    
    # 创建布局
    control = FormattedTextControl(get_formatted_content)
    window = Window(control, height=len(items) + 6)
    layout = Layout(HSplit([window]))
    
    # 创建应用
    app = Application(
        layout=layout,
        key_bindings=bindings,
        full_screen=False,
        mouse_support=False,
    )
    
    # 启动倒计时线程
    def countdown_thread():
        while state.countdown_active and state.countdown_remaining > 0 and state.result is None:
            time.sleep(1)
            if state.countdown_active:
                state.countdown_remaining -= 1
                try:
                    app.invalidate()  # 刷新显示
                except:
                    break
        
        # 倒计时结束，自动选择默认项
        if state.countdown_active and state.result is None and not state.cancelled:
            state.result = default_index
            try:
                app.exit()
            except:
                pass
    
    timer_thread = threading.Thread(target=countdown_thread, daemon=True)
    timer_thread.start()
    
    # 运行应用
    try:
        app.run()
    except KeyboardInterrupt:
        state.cancelled = True
    
    if state.cancelled:
        return -1
    
    return state.result if state.result is not None else default_index


def _fallback_select(items: List[str], prompt: str, timeout: int, default_index: int) -> int:
    """回退到简单的选择实现"""
    console = Console()
    
    # 显示选择列表
    console.print(f"\n{prompt}:")
    for i, item in enumerate(items):
        marker = safe_icon("⭐") if i == default_index else "  "
        console.print(f"{marker} {i + 1}. {item}")
    
    # 显示提示信息
    default_display = items[default_index] if 0 <= default_index < len(items) else "无"
    message = f"\n请选择 (1-{len(items)}, 回车选择默认: {default_display}, {timeout}秒后自动选择): "
    
    try:
        user_input = prompt_with_timeout(message, timeout, str(default_index + 1))
        
        if not user_input.strip():
            return default_index
        
        try:
            choice = int(user_input.strip())
            if 1 <= choice <= len(items):
                return choice - 1
            else:
                console.print(f"{safe_icon('❌')} 无效选择: {choice}")
                return -1
        except ValueError:
            console.print(f"{safe_icon('❌')} 无效输入: {user_input}")
            return -1

    except KeyboardInterrupt:
        console.print(f"\n{safe_icon('❌')} 操作取消")
        return -1


def show_loading(message: str, duration: float = 1.0):
    """显示加载动画"""
    console = Console()
    
    # 使用rich的spinner功能
    try:
        from rich.spinner import Spinner
        from rich.text import Text
        
        with Live(console=console, refresh_per_second=10) as live:
            frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            end_time = time.time() + duration
            
            i = 0
            while time.time() < end_time:
                frame = frames[i % len(frames)]
                text = Text()
                text.append(frame, style="cyan")
                text.append(f" {message}")
                live.update(text)
                time.sleep(0.1)
                i += 1
        
        console.print(f'{safe_icon("✅")} {message}完成', style="green")
    except ImportError:
        # 回退到原来的实现
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end_time = time.time() + duration

        i = 0
        while time.time() < end_time:
            frame = frames[i % len(frames)]
            print(f'\r{frame} {message}', end='', flush=True)
            time.sleep(0.1)
            i += 1

        print(f'\r{safe_icon("✅")} {message}完成')


def confirm_action(message: str, default: bool = False) -> bool:
    """确认操作"""
    console = Console()
    default_text = "Y/n" if default else "y/N"
    
    try:
        response = console.input(f"{message} ({default_text}): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n{safe_icon('❌')} 操作取消")
        return False
    
    if not response:
        return default
    
    return response in ['y', 'yes', '是', 'true', '1']


def print_status(message: str, status: str = "info"):
    """打印状态信息"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "loading": "⏳"
    }

    icon = safe_icon(icons.get(status, "ℹ️"))

    # 使用普通 print 避免 Windows Console 编码问题
    try:
        print(f"{icon} {message}")
    except UnicodeEncodeError:
        # 如果仍然失败，使用 ASCII 安全的输出
        safe_text = f"{icon} {message}".encode('ascii', errors='replace').decode('ascii')
        print(safe_text)


def print_header(title: str):
    """打印标题头"""
    # 使用普通 print 避免 Windows Console 编码问题
    try:
        print(f"\n{'=' * 50}")
        print(f"{safe_icon('🚀')} {title}")
        print(f"{'=' * 50}")
    except UnicodeEncodeError:
        # 如果仍然失败，使用 ASCII 安全的输出
        icon = safe_icon('🚀')
        safe_text = f"{icon} {title}".encode('ascii', errors='replace').decode('ascii')
        print(f"\n{'=' * 50}")
        print(safe_text)
        print(f"{'=' * 50}")


def print_separator():
    """打印分隔线"""
    console = Console()
    console.print("-" * 50, style="dim")