from wxautoz import uiautomation as uia
from wxautoz.param import PROJECT_NAME
from wxautoz.logger import wxlog
from abc import ABC, abstractmethod
import win32gui
from typing import Union
import time

# 全局开关：控制是否显示窗口（用于完全后台模式）
# 默认启用后台模式，模仿 wxautox 的行为
WXAUTO_BACKGROUND_MODE = True

class BaseUIWnd(ABC):
    _ui_cls_name: str = None
    _ui_name: str = None
    control: uia.Control

    @abstractmethod
    def _lang(self, text: str):pass

    def __repr__(self):
        return f"<{PROJECT_NAME} - {self.__class__.__name__} at {hex(id(self))}>"

    def __eq__(self, other):
        return self.control == other.control

    def __bool__(self):
        return self.exists()

    def _show(self):
        """显示窗口（如果 WXAUTO_BACKGROUND_MODE=True，则不显示）"""
        global WXAUTO_BACKGROUND_MODE

        if WXAUTO_BACKGROUND_MODE:
            # 后台模式：不显示窗口
            wxlog.debug("后台模式：跳过窗口显示")
            return

        # 前台模式：正常显示窗口
        import traceback
        wxlog.debug("前台模式：显示窗口")
        wxlog.debug(f"调用栈:\n{''.join(traceback.format_stack()[-4:-1])}")

        if hasattr(self, 'HWND'):
            win32gui.ShowWindow(self.HWND, 1)
            win32gui.SetWindowPos(self.HWND, -1, 0, 0, 0, 0, 3)
            win32gui.SetWindowPos(self.HWND, -2, 0, 0, 0, 0, 3)
        self.control.SwitchToThisWindow()

    def close(self):
        try:
            self.control.SendKeys('{Esc}')
        except:
            pass

    def exists(self, wait=0):
        try:
            result = self.control.Exists(wait)
            return result
        except:
            return False

class BaseUISubWnd(BaseUIWnd):
    root: BaseUIWnd
    parent: None

    def _lang(self, text: str):
        if getattr(self, 'parent'):
            return self.parent._lang(text)
        else:
            return self.root._lang(text)


