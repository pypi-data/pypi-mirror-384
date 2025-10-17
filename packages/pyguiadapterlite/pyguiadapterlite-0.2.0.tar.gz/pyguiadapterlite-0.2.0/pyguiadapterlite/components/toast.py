from tkinter import Widget, Toplevel, Label, Tk
from typing import Literal, Union


class Toast:
    def __init__(self, parent: Union[Widget, Tk, Toplevel]):
        self.parent = parent

    def show_toast(
        self,
        message: str,
        duration: int = 3000,
        position: Literal["top", "bottom", "center"] = "top",
        background: str = "#323232",
        foreground: str = "#FFFFFF",
        font: tuple = ("Arial", 10),
        pad_x: int = 20,
        pad_y: int = 20,
        alpha: float = 0.0,
    ):
        """显示Toast消息"""
        # 创建顶层窗口

        if isinstance(self.parent, Widget):
            parent = self.parent.winfo_toplevel()
        else:
            parent = self.parent
        toast_window = Toplevel(parent)
        toast_window.overrideredirect(True)  # 无边框
        toast_window.attributes("-alpha", alpha)  # 初始透明
        toast_window.attributes("-topmost", True)  # 置顶

        # 设置样式
        toast_window.configure(background=background)

        # 创建消息标签
        label = Label(
            toast_window,
            text=message,
            fg=foreground,
            bg=background,
            font=font,
            padx=pad_x,
            pady=pad_y,
        )
        label.pack()

        # 计算位置
        self._set_position(toast_window, position)
        # 淡入动画
        self._fade_in(toast_window, duration)

    def _set_position(self, window: Toplevel, position: str):
        """设置Toast位置"""
        position = position.lower().strip()

        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        if position == "top":
            x = parent_x + (parent_width - width) // 2
            y = parent_y + 50
        elif position == "bottom":
            x = parent_x + (parent_width - width) // 2
            y = parent_y + parent_height - height - 50
        elif position == "center":
            x = parent_x + (parent_width - width) // 2
            y = parent_y + (parent_height - height) // 2
        else:
            x = parent_x + (parent_width - width) // 2
            y = parent_y + 50

        window.geometry(f"+{x}+{y}")

    def _fade_in(self, window, duration):
        """淡入动画"""

        def fade(alpha):
            if alpha < 1.0:
                alpha += 0.1
                window.attributes("-alpha", alpha)
                window.after(30, lambda: fade(alpha))
            else:
                # 显示完成后开始淡出
                window.after(duration, lambda: self._fade_out(window))

        fade(0.1)

    @staticmethod
    def _fade_out(window):
        """淡出动画"""

        def fade(alpha):
            if alpha > 0:
                alpha -= 0.1
                window.attributes("-alpha", alpha)
                window.after(30, lambda: fade(alpha))
            else:
                window.destroy()

        fade(1.0)
