# wxautoz

基于 [wxauto](https://github.com/cluic/wxauto) 的增强版本，添加了后台调度功能。

## ✨ 新增功能

### 后台读取聊天记录

**最新更新 (2025.10.13)**: 成功实现后台阅读聊天记录功能

- ✅ 无需前台显示窗口即可读取消息
- ✅ 支持多种消息类型（文本、图片、文件、语音等）
- ⚠️ **限制**: 必须是近期打开过的窗口

## 🚀 快速开始

### 安装

```bash
pip install wxautoz
```

### 使用示例

运行后台读取聊天记录测试程序:

```bash
python test_get_messages.py
```

### 代码示例

```python
import wxauto.ui.base as base
from wxauto import WeChat

# 启用后台模式
base.WXAUTO_BACKGROUND_MODE = True

# 初始化微信
wx = WeChat()

# 切换到目标聊天
wx.ChatWith("文件传输助手")

# 获取聊天记录
messages = wx.GetAllMessage()
```

## 📝 功能说明

### 后台模式

后台模式允许在不显示微信窗口的情况下执行操作，适用于:

- 自动化消息监控
- 定时任务处理
- 消息数据收集

### 限制说明

当前版本需要目标聊天窗口在近期被打开过。如果切换失败，请先在微信中手动打开该会话。

## 🔗 相关链接

- 原始项目: [wxauto](https://github.com/cluic/wxauto)
---

## 🧩 Acknowledgement

This project is built upon the excellent open-source work [wxauto](https://github.com/cluic/wxauto)  
by **cluic**, licensed under the MIT License.

The cPilot team has made major improvements and extensions, including  
enhanced WeChat automation capabilities, improved reliability, and additional developer tools.

---

## 📜 License

This project is released under the **MIT License**.

- Original work © 2021 cluic  
- Modified work © 2025 cPilot  

You are free to use, modify, and distribute this software,  
provided that proper attribution to both authors is preserved.

For full license text, please see the [LICENSE](./LICENSE) file.
