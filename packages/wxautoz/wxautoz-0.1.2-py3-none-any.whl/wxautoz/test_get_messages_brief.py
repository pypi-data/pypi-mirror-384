# -*- coding: utf-8 -*-
"""
后台获取聊天记录测试
功能：后台获取"文件传输助手"的最近10条聊天记录
"""

import time
import win32gui
import win32con
import ui.base as base
from wxautoz import WeChat

base.WXAUTO_BACKGROUND_MODE = True
wx = WeChat()
hwnd = wx.core.control.NativeWindowHandle
win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
# 根据当前窗口是否前置来切换前后台模式
contact_name = "文件传输助手"  # 修改为你要查询的聊天对象
count = 10

try:
    result = wx.ChatWith(contact_name)
    time.sleep(0.1)
    message = wx.GetAllMessage()
    if message:
        recent_messages = message[-count:] if len(message) > count else message
        print(f"Recent messages from '{contact_name}': {recent_messages}")
        print(message[-1].info)
        for msg in reversed(message):
            print(msg)

except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()