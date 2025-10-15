from __future__ import annotations
from wxautoz.ui.component import (
    CMenuWnd
)
from wxautoz.param import (
    WxParam, 
    WxResponse,
)
from wxautoz.languages import *
from wxautoz.utils import (
    SetClipboardText,
)
from wxautoz.logger import wxlog
from wxautoz.uiautomation import Control
from wxautoz.utils.tools import roll_into_view
from typing import (
    List,
    Union
)
import time
import re


class SessionBox:
    def __init__(self, control, parent):
        self.control: Control = control
        self.root = parent.root
        self.parent = parent
        self.top_control = control.GetTopLevelControl()
        self.init()

    def _lang(self, text: str) -> str:
        return WECHAT_SESSION_BOX.get(text, {WxParam.LANGUAGE: text}).get(WxParam.LANGUAGE)

    def init(self):
        self.searchbox = self.control.EditControl(Name=self._lang('搜索'))
        self.session_list =\
            self.control.ListControl(Name=self._lang('会话'), searchDepth=7)
        self.archived_session_list =\
            self.control.ListControl(Name=self._lang('折叠的群聊'), searchDepth=7)

    def get_session(self) -> List[SessionElement]:
        if self.session_list.Exists(0):
            return [
                SessionElement(i, self) 
                for i in self.session_list.GetChildren()
                if i.Name != self._lang('折叠置顶聊天')
                and not re.match(self._lang('re_置顶聊天'), i.Name)
            ]
        elif self.archived_session_list.Exists(0):
            return [SessionElement(i, self) for i in self.archived_session_list.GetChildren()]
        else:
            return []
    
    def roll_up(self, n: int=5):
        self.control.MiddleClick()
        self.control.WheelUp(wheelTimes=n)

    def roll_down(self, n: int=5):
        self.control.MiddleClick()
        self.control.WheelDown(wheelTimes=n)
    
    def switch_chat(
            self,
            keywords: str,
            exact: bool = False,
            force: bool = False,
            force_wait: Union[float, int] = 0.5
        ):
        wxlog.debug(f"切换聊天窗口: {keywords}, {exact}, {force}, {force_wait}")
        # 检查后台模式，如果启用后台模式则不显示窗口
        from wxautoz.ui.base import WXAUTO_BACKGROUND_MODE
        if not WXAUTO_BACKGROUND_MODE:
            self.root._show()

        # 第一步：检查当前可见的会话列表
        sessions = self.get_session()
        wxlog.debug(f"当前可见会话数量: {len(sessions)}")
        for session in sessions:
            if keywords == session.name and session.control.BoundingRectangle.height():
                wxlog.debug(f"在可见会话列表中找到: {keywords}")
                session.switch()
                time.sleep(0.5)
                return keywords

        # 后台模式：临时显示窗口进行搜索
        if WXAUTO_BACKGROUND_MODE:
            try:
                wxlog.debug("后台模式：临时显示窗口执行搜索")

                # 临时显示窗口（最小化方式，减少干扰）
                import win32gui
                import win32con
                hwnd = self.root.control.NativeWindowHandle
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWMINIMIZED)
                time.sleep(0.3)

                # 点击搜索框
                wxlog.debug("步骤1: 点击搜索框")
                self.searchbox.Click(move=False)
                time.sleep(0.3)

                # 清空搜索框
                wxlog.debug("步骤2: 清空搜索框")
                self.searchbox.SendKeys('{Ctrl}a', api=False, waitTime=0.1)
                self.searchbox.SendKeys('{DELETE}', api=False, waitTime=0.1)
                time.sleep(0.2)

                # 使用剪贴板粘贴
                wxlog.debug(f"步骤3: 输入关键词: {keywords}")
                SetClipboardText(keywords)
                self.searchbox.SendKeys('{Ctrl}v', api=False, waitTime=0.2)
                time.sleep(2.0)
                wxlog.debug("步骤3完成: 等待搜索结果")

            except Exception as e:
                wxlog.debug(f"搜索失败: {e}")
                import traceback
                wxlog.debug(traceback.format_exc())
        else:
            # 前台模式：使用剪贴板
            self.searchbox.RightClick()
            SetClipboardText(keywords)
            menu = CMenuWnd(self)
            menu.select('粘贴')
            time.sleep(0.3)

        search_result = self.control.ListControl(RegexName='.*?IDS_FAV_SEARCH_RESULT.*?')

        if force:
            time.sleep(force_wait)
            self.searchbox.SendKeys('{ENTER}', api=False, waitTime=0.1)
            time.sleep(0.5)
            # 关闭搜索框
            if WXAUTO_BACKGROUND_MODE:
                self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
            return ''

        t0 = time.time()
        matched = False  # 标记是否已匹配
        search_timeout = WxParam.SEARCH_CHAT_TIMEOUT if not WXAUTO_BACKGROUND_MODE else WxParam.SEARCH_CHAT_TIMEOUT * 2
        wxlog.debug(f"搜索超时时间: {search_timeout}秒")

        while time.time() - t0 < search_timeout and not matched:
            results = []
            # 等待搜索结果出现（后台模式下可能需要更长时间）
            if not search_result.Exists(maxSearchSeconds=3):
                wxlog.debug("搜索结果列表尚未出现，继续等待...")
                time.sleep(0.3)
                continue
            search_result_items = search_result.GetChildren()
            if not search_result_items:
                wxlog.debug("搜索结果列表为空，继续等待...")
                time.sleep(0.3)
                continue
            wxlog.debug(f"找到 {len(search_result_items)} 个搜索结果")
            highlight_who = re.sub(r'(\s+)', r'</em>\1<em>', keywords)
            for search_result_item in search_result_items:
                item_name = search_result_item.Name
                item_type = search_result_item.ControlTypeName

                # 记录每个结果项用于调试
                wxlog.debug(f"搜索结果项: {item_name} (类型: {item_type})")

                if (
                    search_result_item.ControlTypeName == 'PaneControl'
                    and search_result_item.TextControl(Name='聊天记录').Exists(0)
                ) or item_name == f'搜索 {keywords}':
                    wxlog.debug(f"遇到搜索分隔符，停止搜索")
                    matched = True
                    break
                elif (
                    search_result_item.ControlTypeName == 'ListItemControl'
                    and search_result_item.TextControl(Name=f"微信号: <em>{keywords}</em>").Exists(0)
                ):
                    wxlog.debug(f"{keywords} 匹配到微信号：{item_name}")
                    search_result_item.Click(move=False)
                    time.sleep(0.5)
                    # 关闭搜索框并隐藏窗口
                    if WXAUTO_BACKGROUND_MODE:
                        self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                        import win32gui, win32con
                        win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
                    return item_name
                elif (
                    search_result_item.ControlTypeName == 'ListItemControl'
                    and search_result_item.TextControl(Name=f"昵称: <em>{highlight_who}</em>").Exists(0)
                ):
                    wxlog.debug(f"{keywords} 匹配到昵称：{item_name}")
                    search_result_item.Click(move=False)
                    time.sleep(0.5)
                    # 关闭搜索框并隐藏窗口
                    if WXAUTO_BACKGROUND_MODE:
                        self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                        import win32gui, win32con
                        win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
                    return item_name
                elif (
                    search_result_item.ControlTypeName == 'ListItemControl'
                    and search_result_item.TextControl(Name=f"群聊名称: <em>{highlight_who}</em>").Exists(0)
                ):
                    wxlog.debug(f"{keywords} 匹配到群聊名称：{item_name}")
                    search_result_item.Click(move=False)
                    time.sleep(0.5)
                    # 关闭搜索框并隐藏窗口
                    if WXAUTO_BACKGROUND_MODE:
                        self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                        import win32gui, win32con
                        win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
                    return item_name
                elif (
                    search_result_item.ControlTypeName == 'ListItemControl'
                    and keywords == item_name
                ):
                    wxlog.debug(f"{keywords} 完整匹配")
                    search_result_item.Click(move=False)
                    time.sleep(0.5)
                    # 关闭搜索框并隐藏窗口
                    if WXAUTO_BACKGROUND_MODE:
                        self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                        import win32gui, win32con
                        win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
                    return keywords
                elif (
                    search_result_item.ControlTypeName == 'ListItemControl'
                    and keywords in item_name
                ):
                    wxlog.debug(f"{keywords} 部分匹配，添加到候选列表")
                    results.append(search_result_item)

        if exact:
            wxlog.debug(f"{keywords} 未精准匹配，返回None")
            if search_result.Exists(0):
                if WXAUTO_BACKGROUND_MODE:
                    self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                    import win32gui, win32con
                    win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
                else:
                    search_result.SendKeys('{Esc}')
            return None
        if results:
            wxlog.debug(f"{keywords} 匹配到 {len(results)} 个候选结果，点击第一个")
            results[0].Click(move=False)
            time.sleep(0.5)
            # 关闭搜索框并隐藏窗口
            if WXAUTO_BACKGROUND_MODE:
                self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                import win32gui, win32con
                win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
            return results[0].Name

        wxlog.debug(f"{keywords} 未找到任何匹配结果")
        if search_result.Exists(0):
            if WXAUTO_BACKGROUND_MODE:
                self.searchbox.SendKeys('{Esc}', api=False, waitTime=0.1)
                import win32gui, win32con
                win32gui.ShowWindow(self.root.control.NativeWindowHandle, win32con.SW_HIDE)
            else:
                search_result.SendKeys('{Esc}')
        return None


    def open_separate_window(self, name: str):
        wxlog.debug(f"打开独立窗口: {name}")
        sessions = self.get_session()
        for session in sessions:
            if session.name == name:
                wxlog.debug(f"找到会话: {name}")
                while session.control.BoundingRectangle.height():
                    try:
                        session.click()
                        session.double_click()
                    except:
                        pass
                    time.sleep(0.1)
                else:
                    return WxResponse.success(data={'nickname': name})
        wxlog.debug(f"未找到会话: {name}")
        return WxResponse.failure('未找到会话')
    
    def go_top(self):
        wxlog.debug("回到会话列表顶部")
        if self.archived_session_list.Exists(0):
            self.control.ButtonControl(Name=self._lang('返回')).Click()
            time.sleep(0.3)
        first_session_name = self.session_list.GetChildren()[0].Name
        while True:
            self.control.WheelUp(wheelTimes=3)
            time.sleep(0.1)
            if self.session_list.GetChildren()[0].Name == first_session_name:
                break
            else:
                first_session_name = self.session_list.GetChildren()[0].Name


class SessionElement:
    def __init__(
            self, 
            control: Control, 
            parent: SessionBox
        ):
        self.root = parent.root
        self.parent = parent
        self.control = control
        info_controls = [i for i in self.control.GetProgenyControl(3).GetChildren() if i.ControlTypeName=='TextControl']
        self.name = info_controls[0].Name
        self.time = info_controls[-1].Name
        self.content = (
            temp_control.Name 
            if (temp_control := control.GetProgenyControl(4, -1, control_type='TextControl')) 
            else None
        )
        self.ismute = (
            True
            if control.GetProgenyControl(4, 1, control_type='PaneControl')
            else False
        )
        self.isnew = (new_tag_control := control.GetProgenyControl(2, 2)) is not None
        self.new_count = 0
        if self.isnew:
            if new_tag_name := (new_tag_control.Name):
                try:
                    self.new_count = int(new_tag_name)
                    self.ismute = False
                except ValueError:
                    self.new_count = 999
            else:
                new_text = re.findall(self._lang('re_条数'), str(self.content))
                if new_text:
                    try:
                        self.new_count = int(re.findall('\d+', new_text[0])[0])
                    except ValueError:
                        self.new_count = 999
                    self.content = self.content[len(new_text[0])+1:]
                else: 
                    self.new_count = 1
                    

        self.info = {
            'name': self.name,
            'time': self.time,
            'content': self.content,
            'isnew': self.isnew,
            'new_count': self.new_count,
            'ismute': self.ismute
        }

    def _lang(self, text: str) -> str:
        return self.parent._lang(text)
    
    def roll_into_view(self):
        from wxautoz.ui.base import WXAUTO_BACKGROUND_MODE
        if not WXAUTO_BACKGROUND_MODE:
            self.root._show()
        roll_into_view(self.control.GetParentControl(), self.control)


    def _click(self, right: bool=False, double: bool=False):
        from wxautoz.ui.base import WXAUTO_BACKGROUND_MODE
        self.roll_into_view()
        if right:
            if WXAUTO_BACKGROUND_MODE:
                self.control.RightClick(move=False)
            else:
                self.control.RightClick()
        elif double:
            if WXAUTO_BACKGROUND_MODE:
                self.control.DoubleClick(move=False)
            else:
                self.control.DoubleClick()
        else:
            if WXAUTO_BACKGROUND_MODE:
                self.control.Click(move=False)
            else:
                self.control.Click()

    def click(self):
        self._click()

    def right_click(self):
        self._click(right=True)

    def double_click(self):
        self._click(double=True)

    def switch(self):
        self.click()