from tkinter import Widget, Toplevel, Frame, Label
from typing import Tuple, Optional, List, Literal


class ToolTip(object):
    def __init__(
        self,
        target_widget: Widget,
        text: str = "",
        delay: int = 500,
        x_offset: int = 15,
        y_offset: int = 10,
        background: str = "#ffffe0",
        foreground: str = "black",
        relief: Literal["flat", "raised", "sunken", "groove", "ridge"] = "solid",
        font: tuple = ("Arial", 10),
        wrap_length: Optional[int] = None,
    ):
        self._destroyed = False
        self._target_widget = target_widget
        self._text = text
        self._tooltip_window = None
        self._id = None
        self._x = 0
        self._y = 0

        self._x_offset = x_offset
        self._y_offset = y_offset
        self._background = background
        self._foreground = foreground
        self._relief = relief
        self._font = font
        self._delay = delay
        self._wrap_length = wrap_length

        self._target_widget.bind("<Enter>", self.on_enter)
        self._target_widget.bind("<Leave>", self.on_leave)
        self._target_widget.bind("<Motion>", self.on_motion)

    def on_enter(self, event):
        _ = event
        self.schedule()

    def on_leave(self, event):
        _ = event
        self.unschedule()
        self.hide()

    def on_motion(self, event):
        self._x = event.x_root
        self._y = event.y_root

    def schedule(self):
        self.unschedule()
        self._id = self._target_widget.after(self._delay, self.show)

    def unschedule(self):
        if self._id:
            self._target_widget.after_cancel(self._id)
            self._id = None

    def update_text(self, text: str):
        if self._destroyed:
            raise RuntimeError("ToolTip has already been destroyed")

        self._text = text
        if self._tooltip_window:
            self.unschedule()
            self.hide()
            self.show()

    def show(self):
        if self._destroyed:
            raise RuntimeError("ToolTip has already been destroyed")

        if self._tooltip_window or (not self._text.strip()):
            return
        wind = Toplevel(self._target_widget)
        # 设置无边框
        wind.wm_overrideredirect(True)
        # 根据目标控件的位置设置提示框位置
        x = self._x + self._x_offset
        y = self._y + self._y_offset
        wind.geometry(f"+{x}+{y}")
        # 设置样式
        wind.configure(background=self._background, relief=self._relief, borderwidth=1)
        wind.wm_attributes("-topmost", True)
        if not self._wrap_length:
            label = Label(
                wind,
                text=self._text,
                justify="left",
                background=self._background,
                foreground=self._foreground,
                relief=self._relief,
                borderwidth=0,
                font=self._font,
            )
        else:
            label = Label(
                wind,
                text=self._text,
                justify="left",
                background=self._background,
                foreground=self._foreground,
                relief=self._relief,
                borderwidth=0,
                font=self._font,
                wraplength=self._wrap_length,
            )

        label.pack(ipadx=1, ipady=1)
        self._tooltip_window = wind

    def hide(self):
        if self._destroyed:
            raise RuntimeError("ToolTip has already been destroyed")

        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None

    def destroy(self):
        if self._destroyed:
            raise RuntimeError("ToolTip has already been destroyed")
        self.unschedule()
        self.hide()
        self._target_widget.unbind("<Enter>")
        self._target_widget.unbind("<Leave>")
        self._target_widget.unbind("<Motion>")
        self._target_widget = None
        self._destroyed = True

    @classmethod
    def success(cls, target_widget: Widget, text: str, **kwargs) -> "ToolTip":
        kwargs = kwargs or {}
        kwargs.update(
            {
                "background": "#d4edda",
                "foreground": "#155724",
            }
        )
        return cls(target_widget, text, **kwargs)

    @classmethod
    def warning(cls, target_widget: Widget, text: str, **kwargs) -> "ToolTip":
        kwargs = kwargs or {}
        kwargs.update(
            {
                "background": "#fff3cd",
                "foreground": "#856404",
            }
        )
        return cls(target_widget, text, **kwargs)

    @classmethod
    def error(cls, target_widget: Widget, text: str, **kwargs) -> "ToolTip":
        kwargs = kwargs or {}
        kwargs.update(
            {
                "background": "#f8d7da",
                "foreground": "#721c24",
            }
        )
        return cls(target_widget, text, **kwargs)


class SimpleHtmlToolTip(ToolTip):
    def __init__(
        self,
        target_widget: Widget,
        text: str = "",
        delay: int = 500,
        x_offset: int = 20,
        y_offset: int = 10,
        relief: Literal["flat", "raised", "sunken", "groove", "ridge"] = "solid",
        font: tuple = ("Arial", 10),
        wrap_length: Optional[int] = None,
    ):
        super().__init__(
            target_widget,
            text,
            delay,
            x_offset,
            y_offset,
            "#ffffe0",
            "black",
            relief,
            font,
            wrap_length,
        )

    @staticmethod
    def parse_html(text: str) -> List[Tuple[str, str]]:
        """简单的HTML样式解析"""
        lines = text.split("\n")
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("<b>") and line.endswith("</b>"):
                # 粗体文本
                content = line[3:-4]
                formatted_lines.append(("bold", content))
            elif line.startswith("<i>") and line.endswith("</i>"):
                # 斜体文本
                content = line[3:-4]
                formatted_lines.append(("italic", content))
            elif line.startswith("<u>") and line.endswith("</u>"):
                # 下划线文本
                content = line[3:-4]
                formatted_lines.append(("underline", content))
            elif line.startswith("<title>") and line.endswith("</title>"):
                # 标题
                content = line[7:-8]
                formatted_lines.append(("title", content))
            elif line == "<hr>":
                # 分隔线
                formatted_lines.append(("separator", ""))
            else:
                formatted_lines.append(("normal", line))
        return formatted_lines

    def show(self):
        if self._tooltip_window or (not self._text.strip()):
            return
        wind = Toplevel(self._target_widget)
        # 设置无边框
        wind.wm_overrideredirect(True)
        # 根据目标控件的位置设置提示框位置
        x = self._x + self._x_offset
        y = self._y + self._y_offset
        wind.geometry(f"+{x}+{y}")
        # 设置样式
        wind.configure(background="#ffffff", relief="solid", borderwidth=1)
        main_frame = Frame(wind, bg="#ffffff", padx=10, pady=8)
        main_frame.pack()
        formatted_content = self.parse_html(self._text)
        for style, content in formatted_content:
            if style == "separator":
                # 分隔线
                separator = Frame(main_frame, height=1, bg="#cccccc")
                separator.pack(fill="x", pady=3)
            elif style == "title":
                # 标题
                label = Label(
                    main_frame,
                    text=content,
                    bg="#ffffff",
                    fg="#2c3e50",
                    font=("Arial", 11, "bold"),
                    justify="left",
                )
                label.pack(anchor="w")
            elif style == "bold":
                # 粗体
                label = Label(
                    main_frame,
                    text=content,
                    bg="#ffffff",
                    fg="#34495e",
                    font=("Arial", 10, "bold"),
                    justify="left",
                )
                label.pack(anchor="w")
            elif style == "italic":
                # 斜体
                label = Label(
                    main_frame,
                    text=content,
                    bg="#ffffff",
                    fg="#34495e",
                    font=("Arial", 10, "italic"),
                    justify="left",
                )
                label.pack(anchor="w")
            elif style == "underline":
                # 下划线
                label = Label(
                    main_frame,
                    text=content,
                    bg="#ffffff",
                    fg="#34495e",
                    font=("Arial", 10, "underline"),
                    justify="left",
                )
                label.pack(anchor="w")
            else:
                # 普通文本
                label = Label(
                    main_frame,
                    text=content,
                    bg="#ffffff",
                    fg="#34495e",
                    font=("Arial", 10),
                    justify="left",
                )
                label.pack(anchor="w")
        self._tooltip_window = wind
