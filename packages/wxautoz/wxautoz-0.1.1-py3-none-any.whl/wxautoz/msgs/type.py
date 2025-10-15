from wxautoz.utils.tools import (
    get_file_dir,
)
from wxautoz.ui.component import (
    CMenuWnd,
    WeChatImage,
)
from wxautoz.utils.win32 import (
    ReadClipboardData,
    SetClipboardText,
)
from .base import *
from typing import (
    Union,
)
from pathlib import Path
import shutil
import re

class TextMessage(HumanMessage):
    type = 'text'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox"
        ):
        super().__init__(control, parent)

class QuoteMessage(HumanMessage):
    type = 'quote'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox",
        ):
        super().__init__(control, parent)
        self.content, self.quote_content = \
            re.findall(self._lang('re_引用消息'), self.content, re.DOTALL)[0]
        
class MediaMessage:

    def download(
            self, 
            dir_path: Union[str, Path] = None,
            timeout: int = 10
        ) -> Path:
        if dir_path is None:
            dir_path = WxParam.DEFAULT_SAVE_PATH
        if self.type == 'image':
            filename = f"wxauto_{self.type}_{time.strftime('%Y%m%d%H%M%S')}.png"
        elif self.type == 'video':
            filename = f"wxauto_{self.type}_{time.strftime('%Y%m%d%H%M%S')}.mp4"
        filepath = get_file_dir(dir_path) / filename

        self.click()

        t0 = time.time()
        while True:
            self.right_click()
            menu = CMenuWnd(self)
            if menu and menu.select('复制'):
                try:
                    clipboard_data = ReadClipboardData()
                    cpath = clipboard_data['15'][0]
                    break
                except:
                    pass
            else:
                menu.close()
            if time.time() - t0 > timeout:
                return WxResponse.failure(f'下载超时: {self.type}')
            time.sleep(0.1)

        shutil.copyfile(cpath, filepath)
        SetClipboardText('')
        if imagewnd := WeChatImage():
            imagewnd.close()
        return filepath

class ImageMessage(HumanMessage, MediaMessage):
    type = 'image'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox"
        ):
        super().__init__(control, parent)

class VideoMessage(HumanMessage, MediaMessage):
    type = 'video'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox"
        ):
        super().__init__(control, parent)

class VoiceMessage(HumanMessage):
    type = 'voice'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox"
        ):
        super().__init__(control, parent)

    def to_text(self):
        """语音转文字"""
        if self.control.GetProgenyControl(8, 4):
            return self.control.GetProgenyControl(8, 4).Name
        voicecontrol = self.control.ButtonControl(Name='')
        if not voicecontrol.Exists(0.5):
            return WxResponse.failure('语音转文字失败')
        self.right_click()
        menu = CMenuWnd(self.parent)
        menu.select('语音转文字')

        text = ''
        while True:
            if not self.control.Exists(0):
                return WxResponse.failure('消息已撤回')
            text_control = self.control.GetProgenyControl(8, 4)
            if text_control is not None:
                if text_control.Name == text:
                    return text
                text = text_control.Name
            time.sleep(0.1)

class FileMessage(HumanMessage):
    type = 'file'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox"
        ):
        super().__init__(control, parent)
        self.filename = control.TextControl().Name
        self.filesize = control.GetProgenyControl(10, control_type='TextControl').Name

    def download(
            self,
            dir_path: Union[str, Path] = None,
            force_click: bool = False,
            timeout: int = 10
        ) -> Path:
        """下载文件"""
        from wxautoz.ui.base import WXAUTO_BACKGROUND_MODE
        from wxautoz.logger import wxlog

        if dir_path is None:
            dir_path = WxParam.DEFAULT_SAVE_PATH
        filepath = get_file_dir(dir_path) / self.filename
        t0 = time.time()

        # 后台模式：临时显示窗口（最小化）
        temp_show_window = False
        if WXAUTO_BACKGROUND_MODE:
            import win32gui, win32con
            hwnd = self.root.control.NativeWindowHandle
            wxlog.debug("后台模式：临时最小化显示窗口以下载文件")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMINIMIZED)
            time.sleep(0.5)
            temp_show_window = True

        def open_file_menu():
            attempts = 0
            max_attempts = 5
            while attempts < max_attempts:
                attempts += 1
                self.roll_into_view()
                self.right_click()
                time.sleep(0.3)

                if menu := CMenuWnd(self.parent):
                    wxlog.debug(f"菜单打开成功，尝试次数: {attempts}")
                    return menu
                wxlog.debug(f"菜单打开失败，重试 {attempts}/{max_attempts}")
            wxlog.debug(f"打开菜单失败，已尝试 {max_attempts} 次")
            return None

        try:
            if force_click:
                self.click()
                time.sleep(0.5)

            while True:
                if time.time() - t0 > timeout:
                    return WxResponse.failure("文件下载超时")
                try:
                    if self.control.TextControl(Name=self._lang('接收中')).Exists(0):
                        wxlog.debug("文件正在接收中，等待...")
                        time.sleep(0.5)
                        continue

                    menu = open_file_menu()
                    if not menu:
                        wxlog.debug("无法打开菜单，超时失败")
                        return WxResponse.failure("无法打开文件菜单")

                    option_names = menu.option_names
                    wxlog.debug(f"菜单选项: {option_names}")

                    if (option := self._lang('复制')) in option_names:
                        wxlog.debug(f"选择菜单项: {option}")
                        menu.select(option)
                        time.sleep(0.5)

                        clipboard_data = ReadClipboardData()
                        if '15' in clipboard_data and clipboard_data['15']:
                            temp_filepath = Path(clipboard_data['15'][0])
                            wxlog.debug(f"从剪贴板获取文件路径: {temp_filepath}")
                            break
                        else:
                            wxlog.debug("剪贴板中没有文件路径")
                            time.sleep(0.5)
                            continue
                    else:
                        wxlog.debug(f"菜单中没有'复制'选项")
                        return WxResponse.failure("菜单中没有'复制'选项")
                except Exception as e:
                    wxlog.debug(f"下载过程出错: {e}")
                    time.sleep(0.5)

            # 复制文件到目标目录
            t0 = time.time()
            while True:
                if time.time() - t0 > 2:
                    return WxResponse.failure("文件复制超时")
                try:
                    shutil.copyfile(temp_filepath, filepath)
                    SetClipboardText('')
                    wxlog.debug(f"文件复制成功: {filepath}")
                    return filepath
                except Exception as e:
                    wxlog.debug(f"文件复制失败，重试: {e}")
                    time.sleep(0.1)

        finally:
            # 恢复隐藏窗口
            if temp_show_window:
                wxlog.debug("恢复隐藏窗口")
                import win32gui, win32con
                win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)


class OtherMessage(BaseMessage):
    type = 'other'
    
    def __init__(
            self, 
            control: uia.Control, 
            parent: "ChatBox",

        ):
        super().__init__(control, parent)