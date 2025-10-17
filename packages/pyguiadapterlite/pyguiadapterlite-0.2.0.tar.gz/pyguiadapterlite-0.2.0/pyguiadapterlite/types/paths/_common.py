from tkinter import TclError

from pyguiadapterlite.components.textview import NAV_KEYS
from pyguiadapterlite.utils import _exception


def on_ctrl_c(source, event):
    _ = event
    try:
        source.event_generate("<<Copy>>")
    except TclError as e:
        _exception(e, "unable to generate copy event")
    return "break"


def block_keys(source, allow_backspace, event):
    """阻止文本编辑的按键"""
    # 允许导航键
    if event.keysym in NAV_KEYS:
        return ""
    # 允许退格键
    if allow_backspace and event.keysym == "BackSpace":
        return ""
    # 允许 Ctrl 组合键
    if event.state & 0x4:  # Ctrl 键被按下
        if event.keysym in ("c", "C"):  # Ctrl+C 复制
            return on_ctrl_c(source, event)
        return ""
    # 阻止其他所有按键
    return "break"
