# -*- coding: utf-8 -*-
"""
Win32 后台点击实现
模仿 wxautox 的 Win32.click_by_bbox 方法
"""

import win32gui
import win32con
import win32api
import time


class Win32BackgroundClick:
    """Windows API 后台点击"""

    def __init__(self, hwnd):
        """
        Args:
            hwnd: 窗口句柄
        """
        self.hwnd = hwnd

    def click_by_bbox(self, bbox, xbias=None, ybias=None, pos='center', activate=False):
        """
        通过边界框后台点击

        Args:
            bbox: 边界框对象，有 left, top, right, bottom 属性
            xbias: X 偏移
            ybias: Y 偏移
            pos: 点击位置 ('center', 'topleft', etc.)
            activate: 是否激活窗口
        """
        # 计算点击位置
        if pos == 'center':
            x = (bbox.left + bbox.right) // 2
            y = (bbox.top + bbox.bottom) // 2
        elif pos == 'topleft':
            x = bbox.left
            y = bbox.top
        else:
            x = (bbox.left + bbox.right) // 2
            y = (bbox.top + bbox.bottom) // 2

        # 应用偏移
        if xbias is not None:
            if xbias < 0:
                x = bbox.right + xbias
            else:
                x = bbox.left + xbias

        if ybias is not None:
            if ybias < 0:
                y = bbox.bottom + ybias
            else:
                y = bbox.top + ybias

        # 激活窗口（如果需要）
        if activate:
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.1)

        # 将屏幕坐标转换为客户区坐标
        client_x, client_y = win32gui.ScreenToClient(self.hwnd, (x, y))

        # 构造 lParam (低16位=x, 高16位=y)
        lParam = win32api.MAKELONG(client_x, client_y)

        # 发送鼠标消息（后台）
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        time.sleep(0.05)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)

        return (x, y)


# 测试函数
def test_background_click():
    """测试后台点击"""
    print("=" * 80)
    print(" Win32 后台点击测试")
    print("=" * 80)

    import pyautogui
    from wxautoz import WeChat

    # 记录初始鼠标位置
    initial_pos = pyautogui.position()
    print(f"\n初始鼠标位置: {initial_pos}")

    # 初始化微信
    wx = WeChat()
    hwnd = wx.core.control.NativeWindowHandle

    print(f"微信窗口句柄: {hwnd}")

    # 创建后台点击器
    win32_click = Win32BackgroundClick(hwnd)

    # 获取搜索框
    searchbox = wx.core.sessionbox.searchbox
    bbox = searchbox.BoundingRectangle

    print(f"\n搜索框位置: ({bbox.left}, {bbox.top}, {bbox.right}, {bbox.bottom})")

    # 后台点击搜索框
    print("正在后台点击搜索框...")
    win32_click.click_by_bbox(bbox, activate=False)

    time.sleep(1)

    # 检查鼠标位置
    final_pos = pyautogui.position()
    print(f"最终鼠标位置: {final_pos}")

    dx = abs(final_pos[0] - initial_pos[0])
    dy = abs(final_pos[1] - initial_pos[1])

    if dx <= 2 and dy <= 2:
        print(f"\n✓ 成功！鼠标未移动（{dx}, {dy}）")
    else:
        print(f"\n✗ 失败！鼠标移动了 ({dx}, {dy}) 像素")


if __name__ == "__main__":
    test_background_click()
