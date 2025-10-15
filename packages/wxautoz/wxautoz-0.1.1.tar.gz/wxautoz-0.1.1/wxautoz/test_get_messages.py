# -*- coding: utf-8 -*-
"""
后台获取聊天记录测试
功能：后台获取"文件传输助手"的最近10条聊天记录
"""

import time
import win32gui
import win32con

print("=" * 80)
print(" 后台获取聊天记录测试")
print("=" * 80)

# 启用后台模式
import wxauto.ui.base as base
base.WXAUTO_BACKGROUND_MODE = True
print(f"\n✓ 后台模式已启用")

# 启用调试日志
from wxauto.logger import wxlog
wxlog.set_debug(True)
print(f"✓ 调试日志已启用")

# 初始化微信
print("\n正在初始化微信...")
from wxauto import WeChat
wx = WeChat()

# 隐藏窗口
hwnd = wx.core.control.NativeWindowHandle
win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
print("✓ 窗口已隐藏")

# 配置参数
target = "文件传输助手"  # 修改为你要查询的聊天对象
msg_count = 10

print("\n" + "=" * 80)
print(f" 获取 '{target}' 的最近 {msg_count} 条聊天记录")
print("=" * 80)

try:
    # 切换到目标聊天
    print(f"\n[1/3] 切换到 '{target}' 聊天窗口...")

    # 先检查是否已经在目标会话
    try:
        initial_chat_info = wx.core.chatbox.get_info()
        initial_chat = initial_chat_info.get('chat_name', '未知')
        if initial_chat == target:
            print(f"  ✓ 已在目标会话: {target}")
        else:
            print(f"  当前会话: {initial_chat}，需要切换...")
    except:
        pass

    # 尝试切换
    result = wx.ChatWith(target)
    print(f"  切换结果: {result if result else '(无返回值，可能失败)'}")
    time.sleep(4)  # 增加等待时间确保切换完成

    # 确保窗口仍然隐藏
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

    # 验证是否切换成功
    print(f"\n[2/3] 验证当前聊天窗口...")
    max_retries = 2
    retry_count = 0

    while retry_count < max_retries:
        try:
            chat_info = wx.core.chatbox.get_info()
            current_chat = chat_info.get('chat_name', '未知')
            print(f"  当前聊天: {current_chat}")
            print(f"  聊天类型: {chat_info.get('chat_type', '未知')}")

            if current_chat == target:
                print(f"  ✓ 成功切换到目标会话")
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"  ⚠ 警告: 当前聊天为 '{current_chat}'，不是目标 '{target}'")
                    print(f"  ⚠ 尝试第 {retry_count + 1} 次切换...")

                    # 尝试使用force模式
                    result = wx.ChatWith(target, force=True, force_wait=1.5)
                    print(f"  强制切换结果: {result if result else '(无返回值)'}")
                    time.sleep(4)
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                else:
                    print(f"  ✗ 切换失败，已尝试 {max_retries + 1} 次")
                    print(f"  ✗ 将获取 '{current_chat}' 的消息而不是 '{target}'")
                    print(f"  提示: 请确保联系人名称完全正确，或尝试先手动打开该会话")
        except Exception as e:
            print(f"  ⚠ 无法获取当前聊天信息: {e}")
            break

    # 获取聊天记录
    print(f"\n[3/3] 获取聊天记录...")
    all_msgs = wx.GetAllMessage()

    print(f"  共获取 {len(all_msgs)} 条记录")

    # 不过滤消息，而是在显示时跳过时间标记
    # 获取最近的 msg_count 条消息（包括时间标记）
    msgs = all_msgs[-msg_count:] if len(all_msgs) >= msg_count else all_msgs

    # 统计真实消息数量（不包括时间标记）
    real_msg_count = len([m for m in msgs if m.attr != 'time'])

    if msgs:
        print(f"\n✓ 成功获取 {real_msg_count} 条消息（{len(msgs) - real_msg_count} 个时间标记）\n")
        print("=" * 80)
        print(" 聊天记录")
        print("=" * 80)

        msg_num = 0  # 只计数真实消息
        last_time = None  # 记录最近的时间标记

        for idx, msg in enumerate(msgs, 1):
            # 如果是时间标记，记录下来但不显示
            if msg.attr == 'time':
                # TimeMessage有time属性（已解析的时间）和content属性（原始时间文本）
                last_time = getattr(msg, 'time', msg.content)
                continue

            msg_num += 1
            print(f"\n[消息 {msg_num}]")
            # 使用最近的时间标记作为消息时间
            display_time = last_time if last_time else '未知'
            print(f"  时间: {display_time}")
            print(f"  发送者: {msg.sender}")
            print(f"  类型: {msg.type}")

            # 根据消息类型显示内容
            if msg.type == 'text':
                content = msg.content if hasattr(msg, 'content') else str(msg)
                # 限制显示长度
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"  内容: {content}")
            elif msg.type == 'image':
                print(f"  内容: [图片消息]")
            elif msg.type == 'file':
                print(f"  内容: [文件消息]")
                if hasattr(msg, 'filename'):
                    print(f"  文件名: {msg.filename}")
            elif msg.type == 'voice':
                print(f"  内容: [语音消息]")
            elif msg.type == 'video':
                print(f"  内容: [视频消息]")
            elif msg.type == 'emoji':
                print(f"  内容: [表情消息]")
            elif msg.type == 'card':
                print(f"  内容: [名片消息]")
            elif msg.type == 'system':
                content = msg.content if hasattr(msg, 'content') else '[系统消息]'
                print(f"  内容: {content}")
            else:
                print(f"  内容: {msg.content}")

        print("\n" + "=" * 80)

    else:
        print("✗ 未获取到消息")

except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()

finally:
    # 确保窗口保持隐藏
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

print("\n" + "=" * 80)
print(" 测试完成")
print("=" * 80)


print("- 如果切换失败，请先在微信中手动打开该会话，再运行程序")
