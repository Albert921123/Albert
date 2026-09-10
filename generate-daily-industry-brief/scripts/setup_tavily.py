#!/usr/bin/env python3
"""One-time, user-mediated Tavily activation for the daily brief skill.

The helper opens Tavily's account page, explains why a key is needed, accepts
the key through a masked local field when possible, tests it, and only then
saves it for the current Windows user.  It never prints, returns, or writes the
key into the skill package, HTML, retrieval ledger, or command line.
"""

from __future__ import print_function

import argparse
import os
import sys
import webbrowser

from py36_compat import configure_utf8_stdio


TAVILY_URL = "https://app.tavily.com/"
PROMPT = """\
当前 Agent 没有可用的网页检索路径，无法完成本期资讯的实时核验。

现在将打开 Tavily 的注册/登录页面，作为本次检索的备用通道。Tavily
目前提供每月免费额度；仅在已确认 Agent 自带搜索、可控浏览器、官网
列表/公开接口等路径均不可用时使用。

完成后请在 Tavily 后台进入 API Keys，创建一个新的 API Key 并复制。
该 Key 只保存在当前用户的本地环境中，不会写入 HTML、日报、台账、
技能包、GitHub 或聊天内容。随后在本地遮蔽输入框中粘贴它；系统会先
做一次无害测试，测试失败不会保存。\
"""


def emit(status, message):
    print("TAVILY_SETUP_STATUS=" + status)
    print(message)


def wait_for_registration(no_browser):
    print(PROMPT)
    if not no_browser:
        try:
            webbrowser.open(TAVILY_URL, new=2)
        except Exception:
            print("无法自动打开浏览器，请访问：" + TAVILY_URL)


def prompt_key_gui():
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog
    except Exception:
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(
            "知讯日报：启用 Tavily 备用检索",
            "当前 Agent 没有可用的网页检索路径。浏览器已打开 Tavily。\n\n"
            "请注册或登录，在 API Keys 中创建并复制 Key；完成后点“确定”。\n"
            "Key 仅用于本机检索，不会写入日报、HTML 或技能包。",
            parent=root,
        )
        value = simpledialog.askstring(
            "粘贴 Tavily API Key",
            "请粘贴以 tvly- 开头的 Tavily API Key：",
            show="*",
            parent=root,
        )
        root.destroy()
        return value
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        return None


def prompt_key_terminal():
    try:
        import getpass
        if sys.stdin.isatty():
            input("完成注册并复制 Key 后，按 Enter 打开本地安全输入：")
            return getpass.getpass("粘贴 Tavily API Key（输入不会显示）： ")
    except Exception:
        pass
    return None


def verify_key(value, query):
    os.environ["TAVILY_API_KEY"] = value
    try:
        from search_api_bridge import search_tavily
        result = search_tavily(query, 1, 0)
        return bool(result)
    except Exception:
        return False


def save_windows_user_environment(value):
    if os.name != "nt":
        return False
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
        try:
            winreg.SetValueEx(key, "TAVILY_API_KEY", 0, winreg.REG_SZ, value)
        finally:
            winreg.CloseKey(key)
        return True
    except Exception:
        return False


def main(argv=None):
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Open Tavily and securely activate its daily-brief fallback.")
    parser.add_argument("--reason", default="A/B/C 检索路径均不可用", help="Displayed reason only; never include a secret.")
    parser.add_argument("--test-query", default="住房城乡建设部 信息公开", help="Harmless query used to test the key.")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    try:
        from search_api_bridge import stored_tavily_key
        existing = stored_tavily_key()
    except Exception:
        existing = os.environ.get("TAVILY_API_KEY", "").strip()
    if existing:
        if verify_key(existing, args.test_query):
            emit("already-working", "已检测到可用 Tavily Key；无需重新登录。")
            return 0
        os.environ.pop("TAVILY_API_KEY", None)

    print("触发原因：" + args.reason)
    wait_for_registration(args.no_browser)
    value = prompt_key_gui() or prompt_key_terminal()
    value = (value or "").strip()
    if not value:
        emit("needs-user-input", "未获得 Key；请继续使用其它检索路径，或在具备安全输入能力的宿主中重新运行本脚本。")
        return 3
    if not value.startswith("tvly-"):
        emit("invalid-key", "输入的 Key 格式不正确，未保存。")
        return 2
    if not verify_key(value, args.test_query):
        emit("verification-failed", "Tavily 未返回可用结果，Key 未保存；请检查 API Keys 页面中的 Key 与账号额度。")
        return 4
    if save_windows_user_environment(value):
        emit("working", "Tavily 测试成功，已保存到当前 Windows 用户环境；后续日报会自动作为兜底路径调用。")
        return 0
    emit("working-session-only", "Tavily 测试成功，但当前系统不支持通用本地保存；请由宿主安全密钥库保存为 TAVILY_API_KEY。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
