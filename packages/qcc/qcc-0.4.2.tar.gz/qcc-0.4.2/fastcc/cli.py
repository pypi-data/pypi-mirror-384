#!/usr/bin/env python3
"""FastCC CLI主程序"""

import sys
import subprocess
from typing import Optional
import click
from pathlib import Path

from .core.config import ConfigManager
from .utils.crypto import generate_master_key
from .utils.ui import select_from_list, print_status, print_header, show_loading, print_separator, confirm_action, safe_icon
from .providers.manager import ProvidersManager
from .providers.browser import (
    open_browser_and_wait, wait_for_input, confirm_continue,
    print_step, print_provider_info
)


# Windows 兼容的 print 函数
def safe_print(text: str):
    """安全地打印文本，自动替换 emoji 为 ASCII 符号"""
    # 替换所有常用 emoji
    emoji_map = {
        '🚀': safe_icon('🚀'),
        '✅': safe_icon('✅'),
        '❌': safe_icon('❌'),
        '⚠️': safe_icon('⚠️'),
        'ℹ️': safe_icon('ℹ️'),
        '⏳': safe_icon('⏳'),
        '⭐': safe_icon('⭐'),
        '🔄': safe_icon('🔄'),
        '💰': safe_icon('💰'),
        '📊': safe_icon('📊'),
        '🎯': safe_icon('🎯'),
        '💡': safe_icon('💡'),
        '🔧': safe_icon('🔧'),
        '📝': safe_icon('📝'),
        '🎉': safe_icon('🎉'),
        '📋': safe_icon('📋'),
        '👋': safe_icon('👋'),
        '⚙️': safe_icon('⚙️'),
        '🗑️': safe_icon('🗑️'),
        '⏱️': safe_icon('⏱️'),
        '🚫': safe_icon('🚫'),
        '❓': safe_icon('❓'),
        '🔥': safe_icon('🔥'),
        '⚡': safe_icon('⚡'),
        '🛡️': safe_icon('🛡️'),
        '👤': safe_icon('👤'),
        '🤖': safe_icon('🤖'),
    }

    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)

    # 在 Windows 上，尝试使用 errors='replace' 处理无法编码的字符
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果仍然出错，使用 ASCII 编码并替换无法编码的字符
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text)


@click.group(invoke_without_command=True)
@click.option('--smart', '-s', is_flag=True, help='智能启动模式（推荐）')
@click.pass_context
def cli(ctx, smart):
    """FastCC - 快速Claude配置管理工具

    \b
    本地开发测试：
      uvx --from . qcc              智能启动（推荐）
      uvx --from . qcc init         初始化配置
      uvx --from . qcc add <名称>   添加新配置
      uvx --from . qcc list         查看所有配置
      uvx --from . qcc use <名称>   使用指定配置
      uvx --from . qcc fc           厂商快速配置

    \b
    远程安装使用：
      uvx qcc                       智能启动（推荐）
      uvx qcc init                  初始化配置
      uvx qcc add <名称>            添加新配置
      uvx qcc list                  查看所有配置
      uvx qcc use <名称>            使用指定配置
      uvx qcc fc                    厂商快速配置
    """
    if ctx.invoked_subcommand is None:
        if smart:
            # 智能启动模式
            smart_launch()
        else:
            # 默认智能启动（用户友好）
            smart_launch()


def smart_launch():
    """智能快速启动Claude Code - nv fastcc的核心逻辑"""
    try:
        print_header("FastCC 智能启动")
        
        config_manager = ConfigManager()
        
        # 步骤1: 检查登录状态
        if not config_manager.user_id:
            print_status("首次使用，需要登录GitHub账户", "info")
            if not auto_initialize(config_manager):
                return
        
        # 步骤2: 初始化存储后端（如果需要）
        if not config_manager.storage_backend:
            print_status("初始化存储后端...", "loading")
            if not config_manager.initialize_storage_backend():
                print_status("存储后端初始化失败", "error")
                return
        
        # 步骤3: 同步配置
        show_loading("同步云端配置", 1.5)
        config_manager.sync_from_cloud()
        
        # 步骤4: 获取配置列表
        profiles = config_manager.list_profiles()
        if not profiles:
            print_status("暂无配置档案", "warning")
            print("请先添加配置: nv add <名称>")
            return
        
        # 步骤5: 智能选择配置
        selected_profile = smart_select_profile(config_manager, profiles)
        if not selected_profile:
            return
        
        # 步骤6: 应用配置并启动
        print_status(f"应用配置: {selected_profile.name}", "loading")
        if config_manager.apply_profile(selected_profile.name):
            launch_claude_code()
        else:
            print_status("配置应用失败", "error")
            
    except Exception as e:
        print_status(f"启动失败: {e}", "error")


def auto_initialize(config_manager: ConfigManager) -> bool:
    """自动初始化配置"""
    try:
        print_status("正在初始化GitHub认证...", "loading")
        
        if config_manager.initialize_storage_backend():
            # 尝试同步现有配置
            config_manager.sync_from_cloud()
            print_status("初始化完成！", "success")
            return True
        else:
            print_status("GitHub认证失败", "error")
            print("请检查网络连接或稍后重试")
            return False
            
    except Exception as e:
        print_status(f"初始化失败: {e}", "error")
        return False


def smart_select_profile(config_manager: ConfigManager, profiles) -> Optional:
    """智能选择配置档案"""
    try:
        # 获取默认配置
        default_profile = config_manager.get_default_profile()
        default_index = 0
        
        if default_profile:
            # 找到默认配置的索引
            for i, profile in enumerate(profiles):
                if profile.name == default_profile.name:
                    default_index = i
                    break
        
        # 构建选择列表
        profile_names = []
        for profile in profiles:
            desc = f" - {profile.description}" if profile.description else ""
            profile_names.append(f"{profile.name}{desc}")
        
        # 用户选择（3秒超时）
        selected_index = select_from_list(
            profile_names, 
            "选择配置档案", 
            timeout=3, 
            default_index=default_index
        )
        
        if selected_index >= 0:
            return profiles[selected_index]
        else:
            print_status("未选择配置", "warning")
            return None
            
    except Exception as e:
        print_status(f"选择配置失败: {e}", "error")
        return None


def quick_launch():
    """传统快速启动Claude Code"""
    try:
        config_manager = ConfigManager()
        
        # 检查是否已初始化
        if not config_manager.user_id:
            safe_print("🚀 欢迎使用FastCC！")
            print("首次使用需要初始化配置，请运行: nv init")
            print("或者使用: nv fastcc 进行智能启动")
            return
        
        # 尝试从云端同步配置
        if config_manager.storage_backend:
            config_manager.sync_from_cloud()
        
        profiles = config_manager.list_profiles()
        if not profiles:
            safe_print("📝 暂无配置档案，请使用 'nv add' 添加配置")
            return
        
        # 获取默认配置或让用户选择
        default_profile = config_manager.get_default_profile()
        
        if default_profile:
            # 使用默认配置
            safe_print(f"🚀 使用默认配置: {default_profile.name}")
            if config_manager.apply_profile(default_profile.name):
                launch_claude_code()
        else:
            # 显示配置列表让用户选择
            safe_print("📋 可用配置档案:")
            for i, profile in enumerate(profiles, 1):
                last_used = profile.last_used or "从未使用"
                if profile.last_used:
                    last_used = profile.last_used[:10]  # 只显示日期部分
                print(f"  {i}. {profile.name} - {profile.description} (最后使用: {last_used})")
            
            try:
                choice = input("\n请选择配置 (输入数字): ").strip()
                index = int(choice) - 1
                
                if 0 <= index < len(profiles):
                    selected_profile = profiles[index]
                    if config_manager.apply_profile(selected_profile.name):
                        launch_claude_code()
                else:
                    safe_print("❌ 无效选择")
            except (ValueError, KeyboardInterrupt):
                safe_print("❌ 操作取消")
                
    except Exception as e:
        safe_print(f"❌ 启动失败: {e}")


def launch_claude_code():
    """启动Claude Code"""
    try:
        safe_print("🚀 正在启动Claude Code...")
        
        # 检测操作系统，Windows需要shell=True
        import platform
        is_windows = platform.system() == 'Windows'
        
        # 尝试启动Claude Code
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, shell=is_windows)
        
        if result.returncode == 0:
            # Claude Code已安装，启动交互模式
            subprocess.run(['claude'], shell=is_windows)
        else:
            safe_print("❌ 未找到Claude Code，请先安装: https://claude.ai/code")
            
    except FileNotFoundError:
        safe_print("❌ 未找到Claude Code，请先安装: https://claude.ai/code")
    except KeyboardInterrupt:
        safe_print("\n👋 退出Claude Code")


@cli.command()
def init():
    """初始化FastCC配置"""
    try:
        safe_print("🔧 初始化FastCC...")
        
        config_manager = ConfigManager()
        
        # 初始化GitHub后端
        if config_manager.initialize_storage_backend():
            # 尝试从云端同步现有配置
            config_manager.sync_from_cloud()
            
            safe_print("✅ FastCC初始化完成！")
            print("现在可以使用以下命令：")
            print("  nv add <名称>     - 添加新配置")
            print("  nv list          - 查看所有配置")
            print("  nv               - 快速启动")
        else:
            safe_print("❌ 初始化失败")
            
    except Exception as e:
        safe_print(f"❌ 初始化失败: {e}")


@cli.command()
@click.argument('name')
@click.option('--description', '-d', default="", help='配置描述')
def add(name, description):
    """添加新的配置档案"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            safe_print("❌ 请先运行 'nv init' 初始化配置")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                safe_print("❌ 存储后端初始化失败")
                return

        # 从云端同步最新配置，避免名称冲突
        config_manager.sync_from_cloud()

        print(f"➕ 添加配置档案: {name}")

        # 获取用户输入
        base_url = input("请输入 ANTHROPIC_BASE_URL: ").strip()
        if not base_url:
            safe_print("❌ BASE_URL 不能为空")
            return
        
        api_key = input("请输入 ANTHROPIC_API_KEY: ").strip()
        if not api_key:
            safe_print("❌ API_KEY 不能为空")
            return
        
        if not description:
            description = input("请输入配置描述 (可选): ").strip()
        
        # 确认信息
        safe_print(f"\n📋 配置信息:")
        print(f"  名称: {name}")
        print(f"  描述: {description or '无'}")
        print(f"  BASE_URL: {base_url}")
        print(f"  API_KEY: {api_key[:10]}...{api_key[-4:]}")
        
        confirm = input("\n确认添加? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', '是']:
            if config_manager.add_profile(name, description, base_url, api_key):
                safe_print("✅ 配置添加成功！")
            else:
                safe_print("❌ 配置添加失败")
        else:
            safe_print("❌ 操作取消")
            
    except KeyboardInterrupt:
        safe_print("\n❌ 操作取消")
    except Exception as e:
        safe_print(f"❌ 添加配置失败: {e}")


@cli.command()
def list():
    """列出所有配置档案"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            safe_print("❌ 请先运行 'nv init' 初始化配置")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                safe_print("❌ 存储后端初始化失败")
                return
        
        # 从云端同步最新配置
        if config_manager.storage_backend:
            config_manager.sync_from_cloud()
        
        profiles = config_manager.list_profiles()
        default_name = config_manager.settings.get('default_profile')
        
        if not profiles:
            safe_print("📝 暂无配置档案")
            print("使用 'nv add <名称>' 添加新配置")
            return
        
        safe_print("📋 配置档案列表:")
        for profile in profiles:
            is_default = safe_icon("⭐") if profile.name == default_name else "  "
            last_used = profile.last_used or "从未使用"
            if profile.last_used:
                last_used = profile.last_used[:16].replace('T', ' ')

            safe_print(f"{is_default} {profile.name}")
            safe_print(f"     描述: {profile.description or '无'}")
            safe_print(f"     BASE_URL: {profile.base_url}")
            safe_print(f"     最后使用: {last_used}")
            safe_print("")

    except Exception as e:
        safe_print(f"❌ 列出配置失败: {e}")


@cli.command()
@click.argument('name', required=False)
def use(name):
    """使用指定配置启动Claude Code"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                print_status("存储后端初始化失败", "error")
                return
        
        # 从云端同步最新配置
        config_manager.sync_from_cloud()
        
        profiles = config_manager.list_profiles()
        if not profiles:
            print_status("暂无配置档案", "warning")
            print("请先添加配置: uvx qcc add <名称>（本地测试: uvx --from . qcc add <名称>）")
            return
        
        # 如果提供了名称参数，直接使用
        if name:
            profile = config_manager.get_profile(name)
            if not profile:
                print_status(f"配置档案 '{name}' 不存在", "error")
                return
            
            print_status(f"使用配置: {name}", "loading")
            if config_manager.apply_profile(name):
                launch_claude_code()
            return
        
        # 交互式选择配置
        print_header("选择配置启动 Claude Code")
        
        # 获取默认配置用于排序
        default_profile = config_manager.get_default_profile()
        default_index = 0
        
        if default_profile:
            for i, profile in enumerate(profiles):
                if profile.name == default_profile.name:
                    default_index = i
                    break
        
        # 构建选择列表，包含详细信息
        profile_names = []
        for profile in profiles:
            desc = f" - {profile.description}" if profile.description else ""
            last_used = profile.last_used or "从未使用"
            if profile.last_used:
                last_used = profile.last_used[:10]
            is_default = " [默认]" if default_profile and profile.name == default_profile.name else ""
            profile_names.append(f"{profile.name}{desc}{is_default} (最后使用: {last_used})")
        
        # 用户选择
        selected_index = select_from_list(
            profile_names,
            "选择配置档案启动 Claude Code",
            timeout=5,
            default_index=default_index
        )
        
        if selected_index >= 0:
            selected_profile = profiles[selected_index]
            print_status(f"使用配置: {selected_profile.name}", "loading")
            if config_manager.apply_profile(selected_profile.name):
                launch_claude_code()
        else:
            print_status("操作取消", "warning")
        
    except Exception as e:
        print_status(f"使用配置失败: {e}", "error")


@cli.command()
@click.argument('name', required=False)
def default(name):
    """设置默认配置档案"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                print_status("存储后端初始化失败", "error")
                return
        
        # 从云端同步最新配置
        config_manager.sync_from_cloud()
        
        profiles = config_manager.list_profiles()
        if not profiles:
            print_status("暂无配置档案", "warning")
            print("请先添加配置: uvx qcc add <名称>（本地测试: uvx --from . qcc add <名称>）")
            return
        
        # 如果提供了名称参数，直接使用
        if name:
            if config_manager.get_profile(name):
                config_manager.set_default_profile(name)
                print_status(f"已设置默认配置: {name}", "success")
            else:
                print_status(f"配置档案 '{name}' 不存在", "error")
            return
        
        # 交互式选择
        print_header("设置默认配置档案")
        
        # 获取当前默认配置
        current_default = config_manager.get_default_profile()
        default_index = 0
        
        if current_default:
            for i, profile in enumerate(profiles):
                if profile.name == current_default.name:
                    default_index = i
                    break
        
        # 构建选择列表
        profile_names = []
        for profile in profiles:
            desc = f" - {profile.description}" if profile.description else ""
            is_current_default = " [当前默认]" if current_default and profile.name == current_default.name else ""
            profile_names.append(f"{profile.name}{desc}{is_current_default}")
        
        # 用户选择
        selected_index = select_from_list(
            profile_names,
            "选择要设置为默认的配置档案",
            timeout=10,
            default_index=default_index
        )
        
        if selected_index >= 0:
            selected_profile = profiles[selected_index]
            config_manager.set_default_profile(selected_profile.name)
            print_status(f"已设置默认配置: {selected_profile.name}", "success")
        else:
            print_status("操作取消", "warning")
        
    except Exception as e:
        print_status(f"设置默认配置失败: {e}", "error")


@cli.command()
@click.argument('name', required=False)
def remove(name):
    """删除配置档案"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                print_status("存储后端初始化失败", "error")
                return
        
        # 从云端同步最新配置
        config_manager.sync_from_cloud()
        
        profiles = config_manager.list_profiles()
        if not profiles:
            print_status("暂无配置档案", "warning")
            return
        
        # 如果提供了名称参数，直接删除
        if name:
            profile = config_manager.get_profile(name)
            if not profile:
                print_status(f"配置档案 '{name}' 不存在", "error")
                return
            
            print_status(f"即将删除配置档案: {name}", "warning")
            print(f"   描述: {profile.description}")
            print(f"   BASE_URL: {profile.base_url}")
            
            if confirm_action("确认删除？", default=False):
                config_manager.remove_profile(name)
                print_status(f"配置档案 '{name}' 已删除", "success")
            else:
                print_status("操作取消", "info")
            return
        
        # 交互式选择要删除的配置
        print_header("删除配置档案")
        
        # 构建选择列表，包含详细信息
        profile_names = []
        for profile in profiles:
            desc = f" - {profile.description}" if profile.description else ""
            last_used = profile.last_used or "从未使用"
            if profile.last_used:
                last_used = profile.last_used[:10]
            profile_names.append(f"{profile.name}{desc} (最后使用: {last_used})")
        
        # 用户选择
        selected_index = select_from_list(
            profile_names,
            "选择要删除的配置档案",
            timeout=15,
            default_index=0
        )
        
        if selected_index >= 0:
            selected_profile = profiles[selected_index]
            
            # 显示详细信息并确认
            print_separator()
            print_status(f"即将删除配置档案: {selected_profile.name}", "warning")
            print(f"   描述: {selected_profile.description or '无'}")
            print(f"   BASE_URL: {selected_profile.base_url}")
            print(f"   最后使用: {selected_profile.last_used or '从未使用'}")
            
            if confirm_action("确认删除？此操作不可恢复", default=False):
                config_manager.remove_profile(selected_profile.name)
                print_status(f"配置档案 '{selected_profile.name}' 已删除", "success")
            else:
                print_status("操作取消", "info")
        else:
            print_status("操作取消", "warning")
            
    except KeyboardInterrupt:
        print_status("操作取消", "warning")
    except Exception as e:
        safe_print(f"❌ 删除配置失败: {e}")


@cli.command()
def sync():
    """手动同步配置"""
    try:
        config_manager = ConfigManager()
        
        if not config_manager.user_id:
            safe_print("❌ 请先运行 'nv init' 初始化配置")
            return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                safe_print("❌ 存储后端初始化失败")
                return
        
        safe_print("🔄 同步配置...")
        
        # 从云端同步
        if config_manager.sync_from_cloud():
            # 同步到云端
            config_manager.sync_to_cloud()
        
    except Exception as e:
        safe_print(f"❌ 同步失败: {e}")


@cli.command()
def fastcc():
    """智能快速启动Claude Code（推荐使用）"""
    smart_launch()


@cli.command()
def config():
    """配置FastCC设置"""
    try:
        config_manager = ConfigManager()
        
        safe_print("⚙️  FastCC配置管理")
        print("1. 更改同步方式")
        print("2. 查看当前配置")
        print("3. 返回")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == "1":
            safe_print("\n🔄 重新选择同步方式...")
            if config_manager.initialize_storage_backend(force_choose=True):
                safe_print("✅ 同步方式已更新")
            else:
                safe_print("❌ 更新失败")
        
        elif choice == "2":
            backend_type = config_manager.settings.get('storage_backend_type', '未设置')
            backend_name_map = {
                'github': 'GitHub跨平台同步',
                'cloud': '本地云盘同步', 
                'local': '仅本地存储'
            }
            backend_name = backend_name_map.get(backend_type, backend_type)
            
            safe_print(f"\n📋 当前配置:")
            print(f"  同步方式: {backend_name}")
            print(f"  用户ID: {config_manager.user_id or '未设置'}")
            print(f"  配置档案数: {len(config_manager.profiles)}")
            print(f"  默认档案: {config_manager.settings.get('default_profile', '未设置')}")
            print(f"  自动同步: {'开启' if config_manager.settings.get('auto_sync') else '关闭'}")
        
        elif choice == "3":
            return
        else:
            safe_print("❌ 无效选择")
            
    except KeyboardInterrupt:
        safe_print("\n❌ 操作取消")
    except Exception as e:
        safe_print(f"❌ 配置失败: {e}")


@cli.command()
def uninstall():
    """卸载FastCC本地配置"""
    try:
        safe_print("🗑️  FastCC本地配置卸载")
        print("")
        safe_print("⚠️  此操作将删除：")
        print("   - 所有本地配置文件 (~/.fastcc/)")
        print("   - Claude设置文件 (~/.claude/settings.json)")
        print("")
        safe_print("✅ 保留内容：")
        print("   - 云端配置数据（其他设备仍可使用）")
        print("   - FastCC程序本身")
        print("")
        
        # 双重确认
        confirm1 = input("确认卸载本地配置？(输入 'yes' 确认): ").strip()
        if confirm1.lower() != 'yes':
            safe_print("❌ 操作取消")
            return
        
        print("")
        confirm2 = input("最后确认：真的要删除所有本地配置吗？(输入 'DELETE' 确认): ").strip()
        if confirm2 != 'DELETE':
            safe_print("❌ 操作取消")
            return
        
        print("")
        safe_print("🔄 正在卸载本地配置...")
        
        config_manager = ConfigManager()
        if config_manager.uninstall_local():
            print("")
            safe_print("🎉 FastCC本地配置卸载完成！")
            print("")
            safe_print("💡 后续操作：")
            print("   - 重新使用：运行 'nv init' 重新初始化")
            print("   - 完全移除：使用包管理器卸载 FastCC")
        else:
            safe_print("❌ 卸载过程中出现错误")
            
    except KeyboardInterrupt:
        safe_print("\n❌ 操作取消")
    except Exception as e:
        safe_print(f"❌ 卸载失败: {e}")


@cli.command()
def status():
    """显示FastCC状态"""
    try:
        config_manager = ConfigManager()
        
        safe_print("📊 FastCC状态:")
        print(f"  用户ID: {config_manager.user_id or '未初始化'}")
        print(f"  存储后端: {config_manager.storage_backend.backend_name if config_manager.storage_backend else '未配置'}")
        print(f"  配置档案数量: {len(config_manager.profiles)}")
        print(f"  默认配置: {config_manager.settings.get('default_profile', '未设置')}")
        print(f"  自动同步: {'开启' if config_manager.settings.get('auto_sync') else '关闭'}")
        print(f"  加密存储: {'开启' if config_manager.settings.get('encryption_enabled') else '关闭'}")
        
        # 检查Claude Code状态
        try:
            import platform
            is_windows = platform.system() == 'Windows'
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True, shell=is_windows)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  Claude Code: {version}")
            else:
                print("  Claude Code: 未安装")
        except FileNotFoundError:
            print("  Claude Code: 未安装")
            
    except Exception as e:
        safe_print(f"❌ 获取状态失败: {e}")


@cli.command()
def fc():
    """厂商快速配置 (Fast Config)"""
    try:
        print_header("厂商快速配置")
        
        # 检查是否已初始化，如果未初始化则自动初始化
        config_manager = ConfigManager()
        if not config_manager.user_id:
            safe_print("🔧 首次使用，正在初始化配置...")
            if not auto_initialize(config_manager):
                safe_print("❌ 初始化失败，请手动运行 'uvx qcc init'（本地测试: uvx --from . qcc init）")
                return
        
        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                safe_print("❌ 存储后端初始化失败")
                return
        
        # 获取厂商配置
        providers_manager = ProvidersManager()
        if not providers_manager.fetch_providers():
            safe_print("❌ 无法获取厂商配置，请检查网络连接")
            return
        
        providers = providers_manager.get_providers()
        if not providers:
            safe_print("❌ 暂无可用厂商配置")
            return
        
        # 步骤1: 选择厂商
        print_step(1, 5, "选择 AI 厂商")
        safe_print("📋 可用厂商:")
        for i, provider in enumerate(providers, 1):
            print(f"  {i}. {provider}")
        
        try:
            choice = input("\n请选择厂商 (输入数字): ").strip()
            provider_index = int(choice) - 1
            
            if not (0 <= provider_index < len(providers)):
                safe_print("❌ 无效选择")
                return
                
            selected_provider = providers[provider_index]
            
        except (ValueError, KeyboardInterrupt):
            safe_print("❌ 操作取消")
            return
        
        # 步骤2: 显示厂商信息并直接打开注册页面
        print_step(2, 5, "注册或登录厂商账户")
        print_provider_info(selected_provider)
        
        print(f"\n🌐 正在打开 {selected_provider.name} 注册/登录页面...")
        
        # 直接打开浏览器
        open_browser_and_wait(
            selected_provider.signup_url,
            f"请在浏览器中完成 {selected_provider.name} 的注册或登录"
        )
        
        # 步骤3: 等待用户获取API Key
        print_step(3, 5, "获取 API Key")
        safe_print(f"💡 {selected_provider.api_key_help}")
        wait_for_input("完成注册/登录后，请按回车键继续...")
        
        # 输入API Key
        while True:
            try:
                api_key = input(f"\n请输入 {selected_provider.name} 的 API Key: ").strip()
                if not api_key:
                    safe_print("❌ API Key 不能为空")
                    continue
                
                # 验证API Key格式
                if not providers_manager.validate_api_key(selected_provider, api_key):
                    safe_print("⚠️  API Key 格式可能不正确，但将继续使用")
                
                break
                
            except KeyboardInterrupt:
                safe_print("\n❌ 操作取消")
                return
        
        # 步骤4: 确认Base URL
        print_step(4, 5, "确认 API 地址")
        print(f"默认 API 地址: {selected_provider.base_url}")
        
        use_default = input("是否使用默认地址？(Y/n): ").strip().lower()
        if use_default in ['n', 'no', '否']:
            while True:
                custom_base_url = input("请输入自定义 API 地址: ").strip()
                if providers_manager.validate_base_url(custom_base_url):
                    base_url = custom_base_url
                    break
                else:
                    safe_print("❌ 无效的 URL 格式")
        else:
            base_url = selected_provider.base_url
        
        # 步骤5: 输入配置信息
        print_step(5, 5, "创建配置档案")
        
        while True:
            config_name = input("请输入配置名称: ").strip()
            if not config_name:
                safe_print("❌ 配置名称不能为空")
                continue
            
            # 检查是否已存在
            if config_manager.get_profile(config_name):
                safe_print(f"❌ 配置 '{config_name}' 已存在，请使用其他名称")
                continue
            
            break
        
        description = input("请输入配置描述 (可选): ").strip()
        if not description:
            description = f"{selected_provider.name} 配置"
        
        # 确认配置信息
        safe_print(f"\n📋 配置信息确认:")
        print(f"  厂商: {selected_provider.name}")
        print(f"  名称: {config_name}")
        print(f"  描述: {description}")
        print(f"  API地址: {base_url}")
        print(f"  API Key: {api_key[:10]}...{api_key[-4:]}")
        
        if not confirm_continue("确认创建配置？"):
            safe_print("❌ 操作取消")
            return
        
        # 创建配置
        if config_manager.add_profile(config_name, description, base_url, api_key):
            safe_print("✅ 配置创建成功！")
            
            # 询问是否立即使用
            if confirm_continue("是否立即使用此配置启动 Claude Code？"):
                if config_manager.apply_profile(config_name):
                    launch_claude_code()
            else:
                safe_print(f"💡 稍后可使用 'uvx qcc use {config_name}' 启动此配置（本地测试: uvx --from . qcc use {config_name}）")
        else:
            safe_print("❌ 配置创建失败")
            
    except KeyboardInterrupt:
        safe_print("\n❌ 操作取消")
    except Exception as e:
        safe_print(f"❌ 厂商配置失败: {e}")


# ========== Proxy 命令组（新增） ==========

@cli.group()
def proxy():
    """代理服务管理命令"""
    pass


@proxy.command('start')
@click.option('--host', default='127.0.0.1', help='监听地址')
@click.option('--port', default=7860, help='监听端口')
@click.option('--cluster', default=None, help='集群配置名称')
def proxy_start(host, port, cluster):
    """启动代理服务器"""
    try:
        import asyncio
        import logging
        from .proxy.server import ProxyServer
        from .proxy.load_balancer import LoadBalancer
        from .proxy.health_monitor import HealthMonitor
        from .proxy.failover_manager import FailoverManager
        from .proxy.failure_queue import FailureQueue
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager
        from pathlib import Path

        print_header("QCC 代理服务器")

        # 配置日志系统
        log_file = Path.home() / '.qcc' / 'proxy.log'
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("代理服务器日志系统已初始化")

        # 初始化配置管理器
        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        # 如果指定了集群配置，则加载该集群的 endpoints
        if cluster:
            cluster_profile = config_manager.get_profile(cluster)
            if not cluster_profile:
                print_status(f"集群配置 '{cluster}' 不存在", "error")
                safe_print("💡 使用 'uvx qcc endpoint add' 创建集群配置")
                return

            if not hasattr(cluster_profile, 'endpoints') or not cluster_profile.endpoints:
                print_status(f"集群配置 '{cluster}' 没有 endpoints", "error")
                safe_print("💡 使用 'uvx qcc endpoint add' 添加 endpoints")
                return

            print_status(f"使用集群配置: {cluster}", "success")
            print(f"加载 {len(cluster_profile.endpoints)} 个 endpoint")
            print()

            # 显示 endpoints 列表
            for i, ep in enumerate(cluster_profile.endpoints, 1):
                priority_label = "主节点" if ep.priority == 1 else "副节点" if ep.priority == 2 else "其他"
                print(f"  {i}. [{priority_label}] {ep.base_url}")
            print()
        else:
            # 检查是否有配置
            profiles = config_manager.list_profiles()
            if not profiles:
                print_status("暂无配置档案", "warning")
                print("请先添加配置: uvx qcc add <名称>（本地测试: uvx --from . qcc add <名称>）")
                return

        # 初始化负载均衡器 - 使用主备优先级策略
        load_balancer = LoadBalancer(strategy="priority_failover")

        # 初始化优先级管理器
        priority_manager = PriorityManager(config_manager=config_manager)

        # 初始化健康监控器
        health_monitor = HealthMonitor(
            check_interval=60,  # 每 60 秒检查一次
            enable_weight_adjustment=True,  # 启用动态权重调整
            min_checks_before_adjustment=3  # 至少 3 次检查后才调整权重
        )

        # 初始化故障转移管理器
        failover_manager = FailoverManager(
            config_manager=config_manager,
            priority_manager=priority_manager,
            health_monitor=health_monitor,
            check_interval=30  # 每 30 秒检查一次
        )

        # 初始化对话检查器（用于失败队列验证）
        from .proxy.conversational_checker import ConversationalHealthChecker
        conversational_checker = ConversationalHealthChecker()

        # 初始化失败队列
        failure_queue = FailureQueue(
            config_manager=config_manager,
            conversational_checker=conversational_checker
        )

        # 初始化代理服务器
        server = ProxyServer(
            host=host,
            port=port,
            config_manager=config_manager,
            load_balancer=load_balancer,
            priority_manager=priority_manager,
            failover_manager=failover_manager,
            health_monitor=health_monitor,
            failure_queue=failure_queue,
            cluster_name=cluster  # 传递集群配置名称
        )

        # 运行服务器
        print(f"正在启动代理服务器 {host}:{port}...")
        print(f"")
        safe_print(f"💡 使用方法:")
        print(f"   1. 设置环境变量:")
        print(f"      export ANTHROPIC_BASE_URL=http://{host}:{port}")
        print(f"      export ANTHROPIC_API_KEY=proxy-managed")
        print(f"")
        print(f"   2. 启动 Claude Code:")
        print(f"      claude")
        print(f"")
        print(f"按 Ctrl+C 停止服务器")
        print(f"")

        asyncio.run(server.start())

    except KeyboardInterrupt:
        print("\n收到停止信号")
    except Exception as e:
        print_status(f"启动代理服务器失败: {e}", "error")
        import traceback
        traceback.print_exc()


@proxy.command('status')
def proxy_status():
    """查看代理服务器状态"""
    try:
        from .proxy.server import ProxyServer
        from datetime import datetime

        print_header("QCC 代理服务器状态")

        server_info = ProxyServer.get_running_server()

        if not server_info:
            print_status("代理服务器未运行", "info")
            return

        # 显示服务器信息
        pid = server_info['pid']
        host = server_info['host']
        port = server_info['port']
        start_time = server_info['start_time']

        # 计算运行时间
        start_dt = datetime.fromisoformat(start_time)
        uptime_seconds = (datetime.now() - start_dt).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)

        print_status(f"代理服务器正在运行", "success")
        print()
        safe_print(f"📊 服务器信息:")
        print(f"  进程 ID: {pid}")
        print(f"  监听地址: http://{host}:{port}")
        print(f"  启动时间: {start_time[:19].replace('T', ' ')}")
        print(f"  运行时长: {hours}小时 {minutes}分钟 {seconds}秒")
        print()
        safe_print("💡 停止服务器: uvx qcc proxy stop")

    except Exception as e:
        print_status(f"查看状态失败: {e}", "error")


@proxy.command('stop')
def proxy_stop():
    """停止代理服务器"""
    try:
        from .proxy.server import ProxyServer
        import time

        print_header("QCC 代理服务器")

        server_info = ProxyServer.get_running_server()

        if not server_info:
            print_status("代理服务器未运行", "info")
            return

        pid = server_info['pid']
        host = server_info['host']
        port = server_info['port']

        print(f"正在停止代理服务器 (PID: {pid}, {host}:{port})...")

        if ProxyServer.stop_running_server():
            # 等待进程停止
            time.sleep(1)

            # 再次检查是否已停止
            if not ProxyServer.get_running_server():
                print_status("代理服务器已停止", "success")
            else:
                print_status("代理服务器可能未完全停止，请检查进程状态", "warning")
        else:
            print_status("停止代理服务器失败", "error")

    except Exception as e:
        print_status(f"停止代理服务器失败: {e}", "error")
        import traceback
        traceback.print_exc()


@proxy.command('use')
@click.argument('cluster_name')
@click.option('--host', default='127.0.0.1', help='代理服务器地址')
@click.option('--port', default=7860, help='代理服务器端口')
def proxy_use(cluster_name, host, port):
    """配置 Claude Code 使用代理服务器访问集群

    \b
    示例:
        uvx qcc proxy use test                    # 配置使用 test 集群
        uvx qcc proxy use test --port 8080        # 使用自定义端口
    """
    try:
        import json
        from pathlib import Path
        from .core.config import ConfigManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        # 检查集群配置是否存在
        cluster_profile = config_manager.get_profile(cluster_name)
        if not cluster_profile:
            print_status(f"集群配置 '{cluster_name}' 不存在", "error")
            safe_print("💡 使用 'uvx qcc endpoint add' 创建集群配置")
            return

        if not hasattr(cluster_profile, 'endpoints') or not cluster_profile.endpoints:
            print_status(f"配置 '{cluster_name}' 不是集群配置（无 endpoints）", "error")
            safe_print("💡 使用 'uvx qcc endpoint add' 创建集群配置")
            return

        print_header(f"配置 Claude Code 使用代理访问集群: {cluster_name}")

        # 设置 Claude Code 环境变量指向代理服务器
        claude_config_dir = Path.home() / ".claude"
        claude_config_dir.mkdir(exist_ok=True)
        claude_config_file = claude_config_dir / "settings.json"

        # 读取现有配置
        if claude_config_file.exists():
            with open(claude_config_file, 'r') as f:
                claude_config = json.load(f)
        else:
            claude_config = {"env": {}, "permissions": {"allow": [], "deny": []}}

        if "env" not in claude_config:
            claude_config["env"] = {}

        # 设置指向代理服务器（使用占位符 API Key，代理会替换为实际的 Key）
        proxy_url = f"http://{host}:{port}"
        claude_config["env"]["ANTHROPIC_BASE_URL"] = proxy_url
        claude_config["env"]["ANTHROPIC_API_KEY"] = "proxy-managed"
        claude_config["env"]["ANTHROPIC_AUTH_TOKEN"] = "proxy-managed"
        claude_config["apiKeyHelper"] = "echo 'proxy-managed'"

        # 写入配置
        with open(claude_config_file, 'w') as f:
            json.dump(claude_config, f, indent=2, ensure_ascii=False)

        claude_config_file.chmod(0o600)

        print_status("Claude Code 配置已更新", "success")
        print()
        print(f"集群配置 '{cluster_name}':")
        print(f"  代理地址: {proxy_url}")
        print(f"  Endpoints: {len(cluster_profile.endpoints)} 个")
        print()

        for i, ep in enumerate(cluster_profile.endpoints, 1):
            priority_label = "主节点" if ep.priority == 1 else "副节点" if ep.priority == 2 else "其他"
            print(f"  {i}. [{priority_label}] {ep.base_url}")

        print()
        print_separator()
        safe_print("💡 使用步骤:")
        print("   1. 启动代理服务器:")
        print(f"      uvx qcc proxy start --cluster {cluster_name}")
        print()
        print("   2. 启动 Claude Code:")
        print("      claude")
        print()
        safe_print("🔍 查看状态:")
        print("   - 代理状态: uvx qcc proxy status")
        print("   - 健康检查: uvx qcc health status")
        print("   - 查看日志: uvx qcc proxy logs -f")
        print()
        safe_print("⚠️  注意: 必须先启动代理服务器，Claude Code 才能正常工作！")

    except Exception as e:
        print_status(f"配置失败: {e}", "error")
        import traceback
        traceback.print_exc()


@proxy.command('logs')
@click.option('--lines', '-n', default=50, type=int, help='显示行数')
@click.option('--follow', '-f', is_flag=True, help='实时跟踪日志')
def proxy_logs(lines, follow):
    """查看代理服务器日志

    \b
    示例:
        uvx qcc proxy logs              # 查看最近 50 行日志
        uvx qcc proxy logs -n 100       # 查看最近 100 行日志
        uvx qcc proxy logs -f           # 实时跟踪日志
    """
    try:
        from pathlib import Path

        print_header("QCC 代理服务器日志")

        log_file = Path.home() / '.qcc' / 'proxy.log'

        if not log_file.exists():
            print_status("日志文件不存在", "warning")
            safe_print("💡 启动代理服务器后会自动创建日志文件")
            return

        if follow:
            # 实时跟踪日志
            print("实时跟踪日志 (按 Ctrl+C 退出)...")
            print()

            import subprocess
            try:
                subprocess.run(['tail', '-f', str(log_file)])
            except KeyboardInterrupt:
                print("\n日志跟踪已停止")
        else:
            # 显示最近 N 行
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                display_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            for line in display_lines:
                print(line, end='')

            print()
            print(f"\n显示最近 {len(display_lines)} 行日志")
            safe_print("💡 使用 -f 选项实时跟踪日志: uvx qcc proxy logs -f")

    except Exception as e:
        print_status(f"查看日志失败: {e}", "error")


# ========== Health 命令组（新增） ==========

@cli.group()
def health():
    """健康检测管理命令"""
    pass


@health.command('test')
@click.argument('endpoint_id', required=False)
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def health_test(endpoint_id, verbose):
    """执行对话测试

    \b
    示例:
        uvx qcc health test                  # 测试所有 endpoint
        uvx qcc health test endpoint-1       # 测试指定 endpoint
        uvx qcc health test -v               # 显示详细信息
    """
    try:
        import asyncio
        from .proxy.conversational_checker import ConversationalHealthChecker
        from .proxy.health_check_models import HealthCheckResult
        from .core.config import ConfigManager

        print_header("对话式健康测试")

        # 初始化
        checker = ConversationalHealthChecker()
        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        # 获取所有配置的 endpoints
        endpoints = config_manager.get_all_endpoints()

        if endpoint_id:
            endpoints = [ep for ep in endpoints if ep.id == endpoint_id]

        if not endpoints:
            print_status("没有可测试的 endpoint", "warning")
            safe_print("💡 提示: 使用 'uvx qcc endpoint add <config-name>' 添加 endpoint")
            return

        print(f"🔍 测试 {len(endpoints)} 个 endpoint...\n")

        # 执行测试
        async def run_tests():
            return await checker.check_all_endpoints(endpoints)

        results = asyncio.run(run_tests())

        # 显示结果
        success_count = 0
        for check in results:
            result_icon = {
                HealthCheckResult.SUCCESS: '✅',
                HealthCheckResult.FAILURE: '❌',
                HealthCheckResult.TIMEOUT: '⏱️',
                HealthCheckResult.RATE_LIMITED: '🚫',
            }.get(check.result, '❓')

            print(f"{result_icon} {check.endpoint_id}")
            print(f"   测试消息: {check.test_message}")

            if check.result == HealthCheckResult.SUCCESS:
                success_count += 1
                print(f"   响应时间: {check.response_time_ms:.0f}ms")
                print(f"   响应内容: {check.response_content[:50]}...")
                print(f"   质量评分: {check.response_score:.0f}/100")
                print(f"   响应有效: {'是' if check.response_valid else '否'}")

                if verbose:
                    print(f"   完整响应: {check.response_content}")
                    print(f"   使用 Token: {check.tokens_used}")
                    print(f"   使用模型: {check.model_used}")
            else:
                print(f"   错误: {check.error_message}")

            print()

        # 显示汇总
        print_separator()
        safe_print(f"📊 测试汇总: {success_count}/{len(results)} 成功")

    except Exception as e:
        print_status(f"测试失败: {e}", "error")
        import traceback
        traceback.print_exc()


@health.command('metrics')
@click.argument('endpoint_id', required=False)
def health_metrics(endpoint_id):
    """查看性能指标

    \b
    示例:
        uvx qcc health metrics               # 查看所有 endpoint 指标
        uvx qcc health metrics endpoint-1    # 查看指定 endpoint 指标
    """
    try:
        from pathlib import Path
        import json

        print_header("性能指标")

        # 尝试加载持久化的指标数据
        metrics_file = Path.home() / '.qcc' / 'health_metrics.json'

        if not metrics_file.exists():
            print_status("暂无性能指标数据", "warning")
            safe_print("💡 提示:")
            print("   1. 使用 'uvx qcc proxy start' 启动代理服务器")
            print("   2. 代理服务器会自动收集性能指标")
            print("   3. 然后可以使用此命令查看指标")
            return

        with open(metrics_file, 'r') as f:
            all_metrics = json.load(f)

        if not all_metrics:
            print_status("暂无性能数据", "warning")
            return

        if endpoint_id:
            metrics = all_metrics.get(endpoint_id)
            if not metrics:
                print_status(f"没有 '{endpoint_id}' 的性能数据", "warning")
                return

            _print_detailed_metrics(metrics)
        else:
            for ep_id, metrics in all_metrics.items():
                _print_summary_metrics(metrics)

    except Exception as e:
        print_status(f"查看指标失败: {e}", "error")
        import traceback
        traceback.print_exc()


def _print_detailed_metrics(metrics):
    """打印详细指标"""
    print_separator()
    print(f"Endpoint: {metrics['endpoint_id']}")
    print()

    safe_print("📊 检查统计:")
    print(f"  总检查次数: {metrics['total_checks']}")
    print(f"  成功次数: {metrics['successful_checks']}")
    print(f"  失败次数: {metrics['failed_checks']}")
    print(f"  超时次数: {metrics.get('timeout_checks', 0)}")
    print(f"  限流次数: {metrics.get('rate_limited_checks', 0)}")
    print()

    print("📈 性能指标:")
    print(f"  成功率: {metrics['success_rate']:.1f}%")
    print(f"  近期成功率: {metrics['recent_success_rate']:.1f}%")
    print(f"  平均响应时间: {metrics['avg_response_time']:.0f}ms")
    print(f"  P95 响应时间: {metrics['p95_response_time']:.0f}ms")
    print(f"  稳定性评分: {metrics['stability_score']:.1f}/100")
    print()

    safe_print("🔄 连续状态:")
    print(f"  连续成功: {metrics['consecutive_successes']} 次")
    print(f"  连续失败: {metrics['consecutive_failures']} 次")
    print()

    print(f"⏰ 最后更新: {metrics['last_update']}")


def _print_summary_metrics(metrics):
    """打印简要指标"""
    success_rate = metrics.get('recent_success_rate', 0)
    status_icon = '✅' if success_rate > 80 else '⚠️' if success_rate > 50 else '❌'

    print(f"\n{status_icon} {metrics['endpoint_id']}")
    print(f"   成功率: {success_rate:.1f}% | "
          f"响应: {metrics.get('avg_response_time', 0):.0f}ms | "
          f"稳定性: {metrics.get('stability_score', 0):.0f}/100")


@health.command('check')
def health_check():
    """立即执行健康检查（需要代理服务器运行）

    \b
    示例:
        uvx qcc health check
    """
    try:
        from .proxy.server import ProxyServer

        print_header("执行健康检查")

        # 检查代理服务器是否运行
        server_info = ProxyServer.get_running_server()

        if not server_info:
            print_status("代理服务器未运行", "error")
            safe_print("💡 使用 'uvx qcc proxy start' 启动代理服务器")
            return

        print_status("触发健康检查...", "loading")
        safe_print("💡 健康检查将在后台执行，请稍后使用 'uvx qcc health metrics' 查看结果")

    except Exception as e:
        print_status(f"执行健康检查失败: {e}", "error")


@health.command('status')
def health_status():
    """查看所有 endpoint 的健康状态

    \b
    示例:
        uvx qcc health status
    """
    try:
        from pathlib import Path
        import json
        from datetime import datetime

        print_header("Endpoint 健康状态")

        # 加载指标数据
        metrics_file = Path.home() / '.qcc' / 'health_metrics.json'

        if not metrics_file.exists():
            print_status("暂无健康状态数据", "warning")
            safe_print("💡 启动代理服务器后会自动收集健康数据")
            return

        with open(metrics_file, 'r') as f:
            all_metrics = json.load(f)

        if not all_metrics:
            print_status("暂无健康数据", "warning")
            return

        # 显示健康状态汇总
        healthy_count = 0
        unhealthy_count = 0
        unknown_count = 0

        for ep_id, metrics in all_metrics.items():
            success_rate = metrics.get('recent_success_rate', 0)

            if success_rate >= 80:
                status = "健康"
                icon = "✅"
                healthy_count += 1
            elif success_rate >= 50:
                status = "警告"
                icon = "⚠️"
                unhealthy_count += 1
            else:
                status = "不健康"
                icon = "❌"
                unhealthy_count += 1

            consecutive_failures = metrics.get('consecutive_failures', 0)
            last_update = metrics.get('last_update', '')

            print(f"\n{icon} {ep_id} - {status}")
            print(f"   成功率: {success_rate:.1f}%")
            print(f"   平均响应: {metrics.get('avg_response_time', 0):.0f}ms")
            print(f"   连续失败: {consecutive_failures} 次")
            if last_update:
                print(f"   最后检查: {last_update[:19].replace('T', ' ')}")

        # 显示汇总
        print_separator()
        total = healthy_count + unhealthy_count + unknown_count
        safe_print(f"📊 汇总: {total} 个 endpoint")
        safe_print(f"   ✅ 健康: {healthy_count}")
        safe_print(f"   ⚠️  警告/不健康: {unhealthy_count}")

    except Exception as e:
        print_status(f"查看状态失败: {e}", "error")


@health.command('history')
@click.argument('endpoint_id')
@click.option('--limit', '-n', type=int, default=20, help='显示数量')
def health_history(endpoint_id, limit):
    """查看 endpoint 的健康检查历史

    \b
    示例:
        uvx qcc health history endpoint-1
        uvx qcc health history endpoint-1 -n 50
    """
    try:
        from pathlib import Path
        import json

        print_header(f"健康检查历史: {endpoint_id}")

        # 加载历史数据
        history_file = Path.home() / '.qcc' / 'health_history.json'

        if not history_file.exists():
            print_status("暂无历史数据", "warning")
            return

        with open(history_file, 'r') as f:
            all_history = json.load(f)

        history = all_history.get(endpoint_id, [])

        if not history:
            print_status(f"没有 '{endpoint_id}' 的历史数据", "warning")
            return

        # 显示最近的历史记录
        recent_history = history[-limit:] if len(history) > limit else history

        for record in recent_history:
            timestamp = record.get('timestamp', '')[:19].replace('T', ' ')
            result = record.get('result', 'UNKNOWN')
            response_time = record.get('response_time_ms', 0)

            icon = {
                'SUCCESS': '✅',
                'FAILURE': '❌',
                'TIMEOUT': '⏱️',
                'RATE_LIMITED': '🚫',
            }.get(result, '❓')

            print(f"{icon} {timestamp} - {result}")
            if result == 'SUCCESS':
                print(f"   响应时间: {response_time:.0f}ms")
                print(f"   质量评分: {record.get('response_score', 0):.0f}/100")
            else:
                print(f"   错误: {record.get('error_message', '未知错误')}")

        print()
        print(f"显示最近 {len(recent_history)} 条记录（共 {len(history)} 条）")

    except Exception as e:
        print_status(f"查看历史失败: {e}", "error")


@health.command('config')
@click.option('--interval', type=int, help='检查间隔（秒）')
@click.option('--enable-weight-adjustment', is_flag=True, help='启用权重调整')
@click.option('--disable-weight-adjustment', is_flag=True, help='禁用权重调整')
@click.option('--min-checks', type=int, help='调整权重前的最少检查次数')
def health_config(interval, enable_weight_adjustment, disable_weight_adjustment, min_checks):
    """配置健康检测参数

    \b
    示例:
        uvx qcc health config --interval 60
        uvx qcc health config --enable-weight-adjustment
        uvx qcc health config --min-checks 5
    """
    try:
        from pathlib import Path
        import json

        print_header("健康检测配置")

        # 加载现有配置
        config_dir = Path.home() / '.qcc'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'health_config.json'

        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {
                'check_interval': 60,
                'enable_weight_adjustment': True,
                'min_checks_before_adjustment': 3
            }

        # 更新配置
        updated = False

        if interval is not None:
            config['check_interval'] = interval
            updated = True

        if enable_weight_adjustment:
            config['enable_weight_adjustment'] = True
            updated = True

        if disable_weight_adjustment:
            config['enable_weight_adjustment'] = False
            updated = True

        if min_checks is not None:
            config['min_checks_before_adjustment'] = min_checks
            updated = True

        if not updated:
            # 只显示当前配置
            print("当前配置:")
            print(f"  检查间隔: {config['check_interval']} 秒")
            print(f"  权重调整: {'启用' if config['enable_weight_adjustment'] else '禁用'}")
            print(f"  最少检查次数: {config['min_checks_before_adjustment']}")
            print()
            safe_print("💡 使用选项修改配置，例如: uvx qcc health config --interval 120")
            return

        # 保存配置
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print_status("配置已更新", "success")
        print()
        print("当前配置:")
        print(f"  检查间隔: {config['check_interval']} 秒")
        print(f"  权重调整: {'启用' if config['enable_weight_adjustment'] else '禁用'}")
        print(f"  最少检查次数: {config['min_checks_before_adjustment']}")
        print()
        safe_print("💡 重启代理服务器以应用新配置")

    except Exception as e:
        print_status(f"配置失败: {e}", "error")


def _start_cluster_and_claude(cluster_name: str, host: str, port: int, config_manager):
    """启动集群代理服务器和 Claude Code

    Args:
        cluster_name: 集群配置名称
        host: 代理服务器监听地址
        port: 代理服务器监听端口
        config_manager: 配置管理器实例
    """
    import subprocess
    import time
    import json
    from pathlib import Path

    try:
        # 应用集群配置到 Claude Code 环境变量
        print_status(f"应用集群配置: {cluster_name}", "loading")

        # 设置环境变量指向代理服务器
        claude_config_dir = Path.home() / ".claude"
        claude_config_dir.mkdir(exist_ok=True)
        claude_config_file = claude_config_dir / "settings.json"

        # 读取现有配置
        if claude_config_file.exists():
            with open(claude_config_file, 'r') as f:
                claude_config = json.load(f)
        else:
            claude_config = {"env": {}, "permissions": {"allow": [], "deny": []}}

        if "env" not in claude_config:
            claude_config["env"] = {}

        # 设置指向代理服务器
        proxy_url = f"http://{host}:{port}"
        claude_config["env"]["ANTHROPIC_BASE_URL"] = proxy_url
        claude_config["env"]["ANTHROPIC_API_KEY"] = "proxy-managed"
        claude_config["env"]["ANTHROPIC_AUTH_TOKEN"] = "proxy-managed"
        claude_config["apiKeyHelper"] = "echo 'proxy-managed'"

        # 写入配置
        with open(claude_config_file, 'w') as f:
            json.dump(claude_config, f, indent=2, ensure_ascii=False)

        claude_config_file.chmod(0o600)
        print_status("Claude Code 配置已更新", "success")

        # 启动代理服务器（后台运行）
        print()
        print_status("启动代理服务器...", "loading")

        # 检查是否已有代理服务器运行
        from .proxy.server import ProxyServer
        server_info = ProxyServer.get_running_server()

        if server_info:
            print_status(f"检测到代理服务器已运行 (PID: {server_info['pid']})", "warning")
            if not confirm_action("是否停止现有服务器并重新启动？", default=True):
                print_status("保持现有服务器运行", "info")
            else:
                ProxyServer.stop_running_server()
                time.sleep(1)
                server_info = None

        if not server_info:
            # 启动新的代理服务器（后台）
            python_path = sys.executable
            script_args = [
                python_path, '-m', 'fastcc.cli',
                'proxy', 'start',
                '--host', host,
                '--port', str(port),
                '--cluster', cluster_name  # 传递集群配置名称
            ]

            # 后台启动
            log_file = Path.home() / '.qcc' / 'proxy.log'
            log_file.parent.mkdir(exist_ok=True)

            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    script_args,
                    stdout=log,
                    stderr=log,
                    start_new_session=True  # 分离进程
                )

            # 等待服务器启动
            time.sleep(2)
            print_status(f"代理服务器已启动: {proxy_url} (PID: {process.pid})", "success")
            print(f"   日志文件: {log_file}")

        # 启动 Claude Code
        print()
        print_status("启动 Claude Code...", "loading")
        time.sleep(1)

        print()
        print_separator()
        safe_print("✅ 集群配置已激活！")
        print()
        safe_print(f"📊 集群状态:")
        print(f"   配置: {cluster_name}")
        print(f"   代理: {proxy_url}")
        print(f"   Endpoints: 已加载")
        print()
        safe_print("💡 使用方法:")
        print("   1. Claude Code 将通过代理服务器访问所有 endpoints")
        print("   2. 代理服务器会自动进行负载均衡和故障转移")
        print("   3. 查看代理状态: uvx qcc proxy status")
        print("   4. 查看健康状态: uvx qcc health status")
        print()

        # 启动 Claude Code
        try:
            import platform
            is_windows = platform.system() == 'Windows'

            result = subprocess.run(['claude', '--version'],
                                  capture_output=True, text=True, shell=is_windows)

            if result.returncode == 0:
                safe_print("🚀 正在启动 Claude Code...")
                subprocess.run(['claude'], shell=is_windows)
            else:
                print_status("未找到 Claude Code，请先安装", "warning")
                print("   下载地址: https://claude.ai/code")
        except FileNotFoundError:
            print_status("未找到 Claude Code，请先安装", "warning")
            print("   下载地址: https://claude.ai/code")

    except KeyboardInterrupt:
        safe_print("\n👋 退出 Claude Code")
    except Exception as e:
        print_status(f"启动失败: {e}", "error")
        import traceback
        traceback.print_exc()


# ========== Endpoint 命令组（新增） ==========

@cli.group()
def endpoint():
    """Endpoint 管理命令"""
    pass


@endpoint.command('add')
@click.argument('cluster_name')
@click.option('--host', default='127.0.0.1', help='代理服务器监听地址')
@click.option('--port', default=7860, help='代理服务器监听端口')
@click.option('--no-auto-start', is_flag=True, default=True, help='不自动启动代理服务器和 Claude Code（默认）')
@click.option('--auto-start', is_flag=True, help='创建后立即启动代理服务器和 Claude Code')
def endpoint_add(cluster_name, host, port, no_auto_start, auto_start):
    """创建 Endpoint 集群配置

    \b
    示例:
        uvx qcc endpoint add production                # 创建集群（默认不启动）
        uvx qcc endpoint add production --auto-start   # 创建并立即启动
    """
    # 如果指定了 --auto-start，则覆盖默认的 no_auto_start
    if auto_start:
        no_auto_start = False
    try:
        from .core.config import ConfigManager, ConfigProfile
        from .core.endpoint import Endpoint

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        # 确保存储后端已初始化
        if not config_manager.storage_backend:
            if not config_manager.initialize_storage_backend():
                print_status("存储后端初始化失败", "error")
                return

        # 从云端同步最新配置
        config_manager.sync_from_cloud()

        # 检查集群配置是否已存在
        if config_manager.get_profile(cluster_name):
            print_status(f"配置 '{cluster_name}' 已存在", "error")
            safe_print(f"💡 使用其他名称或删除现有配置: uvx qcc remove {cluster_name}（本地测试: uvx --from . qcc remove {cluster_name}）")
            return

        print_header(f"创建 Endpoint 集群配置: {cluster_name}")

        # 获取所有现有配置
        profiles = config_manager.list_profiles()
        if not profiles:
            print_status("暂无可用配置", "warning")
            safe_print("💡 请先添加配置: uvx qcc add <名称>（本地测试: uvx --from . qcc add <名称>）")
            return

        # 步骤 1: 选择主节点
        print_step(1, 2, "选择主节点（优先级高，优先使用）")
        print("可用配置:")
        for i, p in enumerate(profiles, 1):
            print(f"  {i}. {p.name} - {p.description or '无描述'}")

        print()
        primary_input = input("请选择主节点 (多选用逗号分隔，如: 1,2,4): ").strip()
        if not primary_input:
            print_status("未选择主节点，操作取消", "warning")
            return

        try:
            primary_indices = [int(x.strip()) - 1 for x in primary_input.split(',')]
            primary_profiles = []
            for idx in primary_indices:
                if 0 <= idx < len(profiles):
                    primary_profiles.append(profiles[idx])
                else:
                    print_status(f"无效的选择: {idx + 1}", "error")
                    return
        except ValueError:
            print_status("输入格式错误", "error")
            return

        # 步骤 2: 选择副节点
        print()
        print_step(2, 2, "选择副节点（故障转移，主节点失败时使用）")

        # 过滤掉已选为主节点的配置
        primary_names = {p.name for p in primary_profiles}
        available_profiles = [p for p in profiles if p.name not in primary_names]

        if available_profiles:
            print("剩余配置:")
            for i, p in enumerate(available_profiles, 1):
                print(f"  {i}. {p.name} - {p.description or '无描述'}")
            print()
            secondary_input = input("请选择副节点 (多选用逗号分隔，或直接回车跳过): ").strip()

            secondary_profiles = []
            if secondary_input:
                try:
                    secondary_indices = [int(x.strip()) - 1 for x in secondary_input.split(',')]
                    for idx in secondary_indices:
                        if 0 <= idx < len(available_profiles):
                            secondary_profiles.append(available_profiles[idx])
                        else:
                            print_status(f"无效的选择: {idx + 1}", "error")
                            return
                except ValueError:
                    print_status("输入格式错误", "error")
                    return
        else:
            print_status("无剩余配置可选", "info")
            secondary_profiles = []

        # 创建集群配置
        print()
        print_separator()

        # 创建 endpoints 列表
        endpoints = []

        # 添加主节点 (priority=1)
        for profile in primary_profiles:
            endpoint = Endpoint.from_profile(profile, weight=100, priority=1)
            endpoints.append(endpoint)

        # 添加副节点 (priority=2)
        for profile in secondary_profiles:
            endpoint = Endpoint.from_profile(profile, weight=100, priority=2)
            endpoints.append(endpoint)

        # 创建新的配置档案
        description = f"Endpoint 集群 - {len(primary_profiles)} 主节点"
        if secondary_profiles:
            description += f" + {len(secondary_profiles)} 副节点"

        # 使用第一个主节点的信息作为默认值（向后兼容）
        first_endpoint = endpoints[0]
        cluster_profile = ConfigProfile(
            name=cluster_name,
            description=description,
            base_url=first_endpoint.base_url,
            api_key=first_endpoint.api_key,
            endpoints=endpoints,
            priority="primary",
            enabled=True
        )

        # 保存配置
        config_manager.profiles[cluster_name] = cluster_profile
        config_manager.save_profiles()

        # 显示创建结果
        print_status("集群配置创建成功！", "success")
        print()
        print(f"集群配置 '{cluster_name}':")
        print(f"  主节点: {', '.join(p.name for p in primary_profiles)}")
        if secondary_profiles:
            print(f"  副节点: {', '.join(p.name for p in secondary_profiles)}")
        print(f"  总计: {len(endpoints)} 个 endpoint")
        print()

        # 显示 endpoint 详情
        for i, ep in enumerate(endpoints, 1):
            priority_label = "主节点" if ep.priority == 1 else "副节点"
            print(f"{i}. [{priority_label}] {ep.display_info()}")

        print()

        # 询问是否立即启动
        if no_auto_start:
            safe_print("💡 稍后可使用以下命令启动:")
            print(f"   uvx qcc proxy start --cluster {cluster_name}")
            return

        if not confirm_action("是否立即启动代理服务器和 Claude Code？", default=True):
            print_status("配置已保存", "info")
            safe_print("💡 稍后可使用以下命令启动:")
            print(f"   uvx qcc proxy start --cluster {cluster_name}")
            return

        # 启动代理服务器和 Claude Code
        print()
        print_separator()
        _start_cluster_and_claude(cluster_name, host, port, config_manager)

    except KeyboardInterrupt:
        print_status("\n操作取消", "warning")
    except Exception as e:
        print_status(f"创建集群配置失败: {e}", "error")
        import traceback
        traceback.print_exc()


@endpoint.command('list')
@click.argument('config_name')
def endpoint_list(config_name):
    """列出配置的所有 endpoint

    \b
    示例:
        uvx qcc endpoint list production
    """
    try:
        from .core.config import ConfigManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        profile = config_manager.get_profile(config_name)
        if not profile:
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        print_header(f"配置 '{config_name}' 的 Endpoints")

        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            print_status("该配置暂无 endpoint", "warning")
            safe_print("💡 使用 'uvx qcc endpoint add' 添加 endpoint")
            return

        print(f"共 {len(profile.endpoints)} 个 endpoint:\n")

        for i, ep in enumerate(profile.endpoints, 1):
            print(f"{i}. {ep.display_info()}")
            print()

    except Exception as e:
        print_status(f"列出 Endpoint 失败: {e}", "error")


@endpoint.command('remove')
@click.argument('config_name')
@click.argument('endpoint_id')
def endpoint_remove(config_name, endpoint_id):
    """删除指定的 endpoint

    \b
    示例:
        uvx qcc endpoint remove production abc12345
    """
    try:
        from .core.config import ConfigManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        profile = config_manager.get_profile(config_name)
        if not profile:
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            print_status("该配置暂无 endpoint", "warning")
            return

        # 查找并删除
        found = False
        for ep in profile.endpoints:
            if ep.id == endpoint_id:
                if confirm_action(f"确认删除 endpoint '{ep.id}'?", default=False):
                    profile.endpoints.remove(ep)
                    config_manager.save_profiles()
                    print_status(f"Endpoint '{endpoint_id}' 已删除", "success")
                else:
                    print_status("操作取消", "info")
                found = True
                break

        if not found:
            print_status(f"Endpoint '{endpoint_id}' 不存在", "error")

    except KeyboardInterrupt:
        print_status("\n操作取消", "warning")
    except Exception as e:
        print_status(f"删除 Endpoint 失败: {e}", "error")


# ========== Priority 命令组（新增） ==========

@cli.group()
def priority():
    """优先级管理命令"""
    pass


@priority.command('set')
@click.argument('profile_name')
@click.argument('level', type=click.Choice(['primary', 'secondary', 'fallback']))
def priority_set(profile_name, level):
    """设置配置的优先级

    \b
    示例:
        uvx qcc priority set production primary      # 设置为主配置
        uvx qcc priority set backup secondary        # 设置为次配置
        uvx qcc priority set emergency fallback      # 设置为兜底配置
    """
    try:
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager, PriorityLevel

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        # 初始化 PriorityManager
        priority_manager = PriorityManager(config_manager=config_manager)

        # 设置优先级
        level_enum = PriorityLevel(level)
        if priority_manager.set_priority(profile_name, level_enum):
            print_status(f"已设置 '{profile_name}' 为 {level} 配置", "success")
        else:
            print_status("设置失败", "error")

    except Exception as e:
        print_status(f"设置优先级失败: {e}", "error")


@priority.command('list')
def priority_list():
    """查看优先级配置

    \b
    示例:
        uvx qcc priority list
    """
    try:
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        priority_manager = PriorityManager(config_manager=config_manager)

        print_header("优先级配置")

        priority_list = priority_manager.get_priority_list()

        for item in priority_list:
            level = item['level']
            profile = item['profile'] or '未设置'
            active = ' [活跃]' if item['active'] else ''

            level_icon = {
                'primary': '🔥',
                'secondary': '⚡',
                'fallback': '🛡️'
            }.get(level, '❓')

            print(f"{level_icon} {level.upper():<10} {profile}{active}")

        print()

        # 显示策略配置
        policy = priority_manager.get_policy()
        print("策略配置:")
        print(f"  自动故障转移: {'✓' if policy['auto_failover'] else '✗'}")
        print(f"  自动恢复: {'✓' if policy['auto_recovery'] else '✗'}")
        print(f"  故障阈值: {policy['failure_threshold']} 次")
        print(f"  冷却期: {policy['cooldown_period']} 秒")

    except Exception as e:
        print_status(f"查看优先级失败: {e}", "error")


@priority.command('switch')
@click.argument('profile_name')
def priority_switch(profile_name):
    """手动切换到指定配置

    \b
    示例:
        uvx qcc priority switch backup
    """
    try:
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        priority_manager = PriorityManager(config_manager=config_manager)

        if priority_manager.switch_to(profile_name, reason="Manual switch"):
            print_status(f"已切换到配置: {profile_name}", "success")
        else:
            print_status("切换失败", "error")

    except Exception as e:
        print_status(f"切换配置失败: {e}", "error")


@priority.command('history')
@click.option('--limit', '-n', type=int, default=10, help='显示数量')
def priority_history(limit):
    """查看切换历史

    \b
    示例:
        uvx qcc priority history
        uvx qcc priority history -n 20
    """
    try:
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        priority_manager = PriorityManager(config_manager=config_manager)

        print_header("切换历史")

        history = priority_manager.get_history(limit=limit)

        if not history:
            print_status("暂无切换历史", "info")
            return

        for record in history:
            timestamp = record['timestamp'][:19].replace('T', ' ')
            from_prof = record['from'] or '(无)'
            to_prof = record['to']
            reason = record['reason']
            switch_type = record['type']

            type_icon = {
                'manual': '👤',
                'failover': '🔄',
                'auto': '🤖'
            }.get(switch_type, '❓')

            print(f"{type_icon} {timestamp}")
            print(f"   {from_prof} → {to_prof}")
            print(f"   原因: {reason}")
            print()

    except Exception as e:
        print_status(f"查看历史失败: {e}", "error")


@priority.command('policy')
@click.option('--auto-failover', is_flag=True, help='启用自动故障转移')
@click.option('--no-auto-failover', is_flag=True, help='禁用自动故障转移')
@click.option('--auto-recovery', is_flag=True, help='启用自动恢复')
@click.option('--no-auto-recovery', is_flag=True, help='禁用自动恢复')
@click.option('--failure-threshold', type=int, help='故障阈值')
@click.option('--cooldown', type=int, help='冷却期（秒）')
def priority_policy(auto_failover, no_auto_failover, auto_recovery,
                   no_auto_recovery, failure_threshold, cooldown):
    """配置故障转移策略

    \b
    示例:
        uvx qcc priority policy --auto-failover --auto-recovery
        uvx qcc priority policy --failure-threshold 3 --cooldown 300
    """
    try:
        from .core.config import ConfigManager
        from .core.priority_manager import PriorityManager

        config_manager = ConfigManager()

        if not config_manager.user_id:
            print_status("请先运行 'uvx qcc init' 初始化配置（本地测试: uvx --from . qcc init）", "error")
            return

        priority_manager = PriorityManager(config_manager=config_manager)

        # 处理参数
        kwargs = {}

        if auto_failover:
            kwargs['auto_failover'] = True
        elif no_auto_failover:
            kwargs['auto_failover'] = False

        if auto_recovery:
            kwargs['auto_recovery'] = True
        elif no_auto_recovery:
            kwargs['auto_recovery'] = False

        if failure_threshold is not None:
            kwargs['failure_threshold'] = failure_threshold

        if cooldown is not None:
            kwargs['cooldown_period'] = cooldown

        if not kwargs:
            print_status("请指定至少一个配置选项", "warning")
            return

        # 更新策略
        priority_manager.set_policy(**kwargs)
        print_status("故障转移策略已更新", "success")

        # 显示当前策略
        policy = priority_manager.get_policy()
        print("\n当前策略:")
        print(f"  自动故障转移: {'✓' if policy['auto_failover'] else '✗'}")
        print(f"  自动恢复: {'✓' if policy['auto_recovery'] else '✗'}")
        print(f"  故障阈值: {policy['failure_threshold']} 次")
        print(f"  冷却期: {policy['cooldown_period']} 秒")

    except Exception as e:
        print_status(f"配置策略失败: {e}", "error")


# ========== Queue 命令组（新增） ==========

@cli.group()
def queue():
    """失败队列管理命令"""
    pass


@queue.command('status')
def queue_status():
    """查看队列状态"""
    try:
        from pathlib import Path
        import json

        print_header("失败队列状态")

        # 加载队列数据
        queue_file = Path.home() / '.qcc' / 'failure_queue.json'

        if not queue_file.exists():
            print_status("失败队列为空", "info")
            safe_print("💡 队列中的请求会在代理服务器运行时自动重试")
            return

        with open(queue_file, 'r') as f:
            data = json.load(f)

        stats = data.get('stats', {})
        queue_items = data.get('queue', [])

        # 显示统计信息
        safe_print("📊 统计信息:")
        print(f"  队列大小: {len(queue_items)}")
        print(f"  总入队数: {stats.get('total_enqueued', 0)}")
        print(f"  总重试数: {stats.get('total_retried', 0)}")
        print(f"  成功数: {stats.get('total_success', 0)}")
        print(f"  失败数: {stats.get('total_failed', 0)}")
        print()

        # 显示队列项状态分布
        pending = sum(1 for item in queue_items if item.get('status') == 'pending')
        safe_print(f"📋 队列状态:")
        print(f"  待重试: {pending} 个")
        print()

        updated_at = data.get('updated_at', '')
        if updated_at:
            print(f"⏰ 最后更新: {updated_at[:19].replace('T', ' ')}")

        print()
        safe_print("💡 使用 'uvx qcc queue list' 查看详细列表")

    except Exception as e:
        print_status(f"查看队列状态失败: {e}", "error")


@queue.command('list')
@click.option('--limit', '-n', type=int, default=20, help='显示数量')
def queue_list(limit):
    """列出队列中的请求

    \b
    示例:
        uvx qcc queue list
        uvx qcc queue list -n 50
    """
    try:
        from pathlib import Path
        import json

        print_header("失败队列列表")

        # 加载队列数据
        queue_file = Path.home() / '.qcc' / 'failure_queue.json'

        if not queue_file.exists():
            print_status("失败队列为空", "info")
            return

        with open(queue_file, 'r') as f:
            data = json.load(f)

        queue_items = data.get('queue', [])

        if not queue_items:
            print_status("失败队列为空", "info")
            return

        # 显示队列项
        display_items = queue_items[-limit:] if len(queue_items) > limit else queue_items

        for item in display_items:
            request_id = item.get('request_id', 'unknown')
            status = item.get('status', 'unknown')
            retry_count = item.get('retry_count', 0)
            reason = item.get('reason', '未知原因')
            enqueued_at = item.get('enqueued_at', '')[:19].replace('T', ' ')
            next_retry_at = item.get('next_retry_at', '')[:19].replace('T', ' ')

            status_icon = {
                'pending': '⏳',
                'success': '✅',
                'failed': '❌'
            }.get(status, '❓')

            print(f"{status_icon} {request_id}")
            print(f"   状态: {status}")
            print(f"   重试次数: {retry_count}")
            print(f"   失败原因: {reason}")
            print(f"   入队时间: {enqueued_at}")
            if status == 'pending' and next_retry_at:
                print(f"   下次重试: {next_retry_at}")
            print()

        print(f"显示 {len(display_items)} 个请求（共 {len(queue_items)} 个）")
        print()
        safe_print("💡 使用 'uvx qcc queue retry <request-id>' 手动重试")

    except Exception as e:
        print_status(f"列出队列失败: {e}", "error")


@queue.command('retry')
@click.argument('request_id')
def queue_retry(request_id):
    """手动重试指定请求

    \b
    示例:
        uvx qcc queue retry retry-123
    """
    try:
        print_header("手动重试请求")

        # 这个功能需要代理服务器运行
        from .proxy.server import ProxyServer

        server_info = ProxyServer.get_running_server()

        if not server_info:
            print_status("代理服务器未运行", "error")
            safe_print("💡 手动重试需要代理服务器运行")
            print("   使用 'uvx qcc proxy start' 启动代理服务器")
            return

        print_status(f"触发重试请求: {request_id}", "loading")
        safe_print("💡 重试将在后台执行，请稍后使用 'uvx qcc queue status' 查看结果")

    except Exception as e:
        print_status(f"重试失败: {e}", "error")


@queue.command('retry-all')
def queue_retry_all():
    """重试所有待处理的请求

    \b
    示例:
        uvx qcc queue retry-all
    """
    try:
        print_header("重试所有请求")

        # 这个功能需要代理服务器运行
        from .proxy.server import ProxyServer

        server_info = ProxyServer.get_running_server()

        if not server_info:
            print_status("代理服务器未运行", "error")
            safe_print("💡 批量重试需要代理服务器运行")
            print("   使用 'uvx qcc proxy start' 启动代理服务器")
            return

        if not confirm_action("确认重试所有待处理的请求？", default=False):
            print_status("操作取消", "info")
            return

        print_status("触发批量重试...", "loading")
        safe_print("💡 重试将在后台执行，请稍后使用 'uvx qcc queue status' 查看结果")

    except KeyboardInterrupt:
        print_status("\n操作取消", "warning")
    except Exception as e:
        print_status(f"批量重试失败: {e}", "error")


@queue.command('clear')
def queue_clear():
    """清空失败队列"""
    try:
        from pathlib import Path
        import json

        print_header("清空失败队列")

        # 加载队列数据检查是否为空
        queue_file = Path.home() / '.qcc' / 'failure_queue.json'

        if not queue_file.exists():
            print_status("失败队列已经为空", "info")
            return

        with open(queue_file, 'r') as f:
            data = json.load(f)

        queue_items = data.get('queue', [])

        if not queue_items:
            print_status("失败队列已经为空", "info")
            return

        print(f"当前队列中有 {len(queue_items)} 个请求")

        if not confirm_action("确认清空失败队列？此操作不可恢复", default=False):
            print_status("操作取消", "info")
            return

        # 清空队列
        data['queue'] = []
        data['stats']['queue_size'] = 0
        data['updated_at'] = datetime.now().isoformat()

        with open(queue_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print_status("失败队列已清空", "success")

    except KeyboardInterrupt:
        print_status("\n操作取消", "warning")
    except Exception as e:
        print_status(f"清空队列失败: {e}", "error")


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        safe_print("\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        safe_print(f"❌ 程序错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()