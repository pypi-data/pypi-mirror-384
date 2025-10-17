from tkinter import Widget, Toplevel, Tk, TclError, Menu
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Frame, Label, Button
from typing import Union, Literal

from pyguiadapterlite._messages import (
    MSG_COPY,
    MSG_SELECT_ALL,
    MSG_ZOOM_IN,
    MSG_ZOOM_OUT,
    MSG_ZOOMING,
    MSG_ZOOM_RESET,
    MSG_NAVIGATION,
    MSG_NAV_TOP,
    MSG_NAV_BOTTOM,
    MSG_NAV_HINT,
    MSG_NAV_PAGE_UP,
    MSG_NAV_PAGE_DOWN,
    MSG_PASTE,
    MSG_CUT,
    MSG_UNDO,
    MSG_REDO,
)
from pyguiadapterlite.utils import _exception

NAV_KEYS = ("Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End")

ZOOM_KEYS = ("plus", "equal", "minus", "0")


class TextView(object):
    def __init__(
        self,
        parent: Union[Widget, Toplevel, Tk],
        font: tuple = ("Arial", 14),
        wrap: Literal["none", "char", "word"] = "word",
        background: str = None,
        foreground: str = None,
        default_menu: bool = True,
        editable: bool = False,
        **kwargs,
    ):
        self._context_menu = None
        self._parent = parent
        # 保存初始字体设置
        self._original_font = font
        self._current_font = font
        self._zoom_level = 0  # 缩放级别

        self._editable = editable

        self._text_widget = ScrolledText(self._parent, font=font, wrap=wrap, **kwargs)

        self.set_font(font)
        self.set_background(background)
        self.set_foreground(foreground)
        self.set_wrap(wrap)

        self._bind_keyboard_events()

        if default_menu:
            self.create_default_menu()

    def pack(self, **kwargs):
        self._text_widget.pack(**kwargs)

    def grid(self, **kwargs):
        self._text_widget.grid(**kwargs)

    def place(self, **kwargs):
        self._text_widget.place(**kwargs)

    @property
    def widget(self) -> ScrolledText:
        return self._text_widget

    def _bind_keyboard_events(self):
        """绑定键盘导航事件"""
        # 允许文本组件获得焦点
        self._text_widget.config(takefocus=1)

        # 方向键
        self._text_widget.bind("<Up>", self._on_arrow_key)
        self._text_widget.bind("<Down>", self._on_arrow_key)
        self._text_widget.bind("<Left>", self._on_arrow_key)
        self._text_widget.bind("<Right>", self._on_arrow_key)

        # PageUp 和 PageDown
        self._text_widget.bind("<Prior>", self._on_page_up)  # PageUp
        self._text_widget.bind("<Next>", self._on_page_down)  # PageDown

        # Home 和 End
        self._text_widget.bind("<Home>", self._on_home)
        self._text_widget.bind("<End>", self._on_end)

        # Ctrl+Home 和 Ctrl+End
        self._text_widget.bind("<Control-Home>", self._on_ctrl_home)
        self._text_widget.bind("<Control-End>", self._on_ctrl_end)

        # 阻止文本编辑的键盘事件
        if not self._editable:
            self._text_widget.bind("<Key>", self._block_editing_keys)
        else:
            # 在可编辑模式下还要绑定一些快捷键
            self._text_widget.config(undo=True)
            self._text_widget.bind("<Control-c>", self._on_ctrl_c)
            self._text_widget.bind("<Control-v>", self._on_ctrl_v)
            self._text_widget.bind("<Control-x>", self._on_ctrl_x)
            self._text_widget.bind("<Control-z>", self._on_ctrl_z)
            self._text_widget.bind("<Control-y>", self._on_ctrl_y)
            self._text_widget.bind("<Control-a>", self._on_ctrl_a)

    def _block_editing_keys(self, event):
        """阻止文本编辑的按键"""
        # 允许导航键
        if event.keysym in NAV_KEYS:
            return ""

        # 允许 Ctrl 组合键（用于缩放等）
        if event.state & 0x4:  # Ctrl 键被按下
            if event.keysym in ZOOM_KEYS:  # 缩放相关
                return ""
            if event.keysym in ("a", "A"):  # Ctrl+A 全选
                return self._on_ctrl_a(event)
            if event.keysym in ("c", "C"):  # Ctrl+C 复制
                return self._on_ctrl_c(event)
        # 阻止其他所有按键
        return "break"

    def _on_arrow_key(self, event):
        """处理方向键事件"""
        # 允许默认的滚动行为
        return

    def _on_page_up(self, event=None):
        _ = event
        """PageUp - 向上翻页"""
        self._text_widget.yview_scroll(-1, "pages")
        return "break"

    def _on_page_down(self, event=None):
        """PageDown - 向下翻页"""
        _ = event
        self._text_widget.yview_scroll(1, "pages")
        return "break"

    def _on_home(self, event):
        """Home - 移动到行首"""
        if event.state & 0x1:  # Shift 键被按下
            self._text_widget.tag_add("sel", "insert linestart", "insert")
        else:
            self._text_widget.mark_set("insert", "insert linestart")
        return "break"

    def _on_end(self, event):
        """End - 移动到行尾"""
        if event.state & 0x1:  # Shift 键被按下
            self._text_widget.tag_add("sel", "insert", "insert lineend")
        else:
            self._text_widget.mark_set("insert", "insert lineend")
        return "break"

    def _on_ctrl_home(self, event):
        """Ctrl+Home - 移动到文档开头"""
        _ = event
        self._text_widget.mark_set("insert", "1.0")
        self._text_widget.see("1.0")
        return "break"

    def _on_ctrl_end(self, event):
        """Ctrl+End - 移动到文档末尾"""
        _ = event
        self._text_widget.mark_set("insert", "end")
        self._text_widget.see("end")
        return "break"

    def _on_ctrl_a(self, event):
        """Ctrl+A - 全选"""
        _ = event
        self._text_widget.tag_add("sel", "1.0", "end")
        return "break"

    def _on_ctrl_c(self, event):
        """Ctrl+C - 复制"""
        _ = event
        try:
            self._text_widget.event_generate("<<Copy>>")
        except TclError as e:
            _exception(e, "unable to generate copy event")
        return "break"

    def _on_ctrl_v(self, event):
        """Ctrl+V - 粘贴"""
        _ = event
        try:
            self._text_widget.event_generate("<<Paste>>")
        except TclError as e:
            _exception(e, "unable to generate paste event")
        return "break"

    def _on_ctrl_x(self, event):
        """Ctrl+X - 剪切"""
        _ = event
        try:
            self._text_widget.event_generate("<<Cut>>")
        except TclError as e:
            _exception(e, "unable to generate cut event")
        return "break"

    def _on_ctrl_z(self, event):
        """Ctrl+Z - 撤销"""
        _ = event
        try:
            self._text_widget.edit_undo()
        except TclError as e:
            _exception(e, "cannot undo")
        return "break"

    def _on_ctrl_y(self, event):
        """Ctrl+Y - 重做"""
        _ = event
        try:
            self._text_widget.edit_redo()
        except TclError as e:
            _exception(e, "cannot redo")
        return "break"

    def set_text(self, text: str):
        self._text_widget.delete("1.0", "end")
        self._text_widget.insert("1.0", text)

    def append_text(self, text: str):
        self._text_widget.insert("end", text)

    def get_text(self) -> str:
        return self._text_widget.get("1.0", "end-1c")

    def set_font(self, font: tuple):
        if font:
            self._current_font = font
            self._text_widget.config(font=font)

    def set_background(self, color: str):
        if color:
            self._text_widget.config(bg=color)

    def set_foreground(self, color: str):
        if color:
            self._text_widget.config(fg=color)

    def set_wrap(self, wrap: Literal["none", "char", "word"]):
        self._text_widget.config(wrap=wrap)

    def clear(self):
        self._text_widget.delete("1.0", "end")

    def create_default_menu(self):
        """创建右键菜单"""
        self._context_menu = Menu(self._text_widget, tearoff=0)
        self._context_menu.add_command(label=MSG_COPY, command=self.copy)
        if self._editable:
            self._context_menu.add_command(
                label=MSG_CUT, command=lambda e=None: self._on_ctrl_x(e)
            )
            self._context_menu.add_command(
                label=MSG_PASTE, command=lambda e=None: self._on_ctrl_v(e)
            )
            self._context_menu.add_separator()
            self._context_menu.add_command(
                label=MSG_UNDO, command=lambda e=None: self._on_ctrl_z(e)
            )
            self._context_menu.add_command(
                label=MSG_REDO, command=lambda e=None: self._on_ctrl_y(e)
            )

        self._context_menu.add_separator()
        self._context_menu.add_command(label=MSG_SELECT_ALL, command=self.select_all)
        self._context_menu.add_separator()
        self._context_menu.add_command(label=MSG_ZOOM_IN, command=self.zoom_in)
        self._context_menu.add_command(label=MSG_ZOOM_OUT, command=self.zoom_out)
        self._context_menu.add_command(label=MSG_ZOOM_RESET, command=self.zoom_reset)
        self._context_menu.add_separator()
        self._context_menu.add_command(label=MSG_NAV_TOP, command=self.scroll_to_top)
        self._context_menu.add_command(
            label=MSG_NAV_BOTTOM, command=self.scroll_to_bottom
        )
        self._context_menu.add_command(label=MSG_NAV_PAGE_UP, command=self._on_page_up)
        self._context_menu.add_command(
            label=MSG_NAV_PAGE_DOWN, command=self._on_page_down
        )

        # 绑定右键事件
        self._text_widget.bind("<Button-3>", self.show_context_menu)  # 右键点击

    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def copy(self):
        """复制选中的文本"""
        try:
            self._text_widget.event_generate("<<Copy>>")
        except TclError as e:
            _exception(e, "unable to generate copy event")

    def select_all(self):
        """全选文本"""
        self._text_widget.tag_add("sel", "1.0", "end")

    def zoom_in(self):
        self._zoom_level += 1
        font_name = self._current_font[0]
        font_size = self._original_font[1] + self._zoom_level
        self.set_font((font_name, font_size))

    def zoom_out(self):
        self._zoom_level -= 1
        font_name = self._current_font[0]
        font_size = max(8, self._original_font[1] + self._zoom_level)
        self.set_font((font_name, font_size))

    def zoom_reset(self):
        self._zoom_level = 0
        self.set_font(self._original_font)

    def scroll_to_top(self):
        """滚动到顶部"""
        self._text_widget.see("1.0")

    def scroll_to_bottom(self):
        """滚动到底部"""
        self._text_widget.see("end")


class SimpleTextViewer(Toplevel):
    def __init__(
        self,
        parent=None,
        title="文本查看器",
        width=850,
        height=600,
        font: tuple = ("Arial", 14),
        wrap: Literal["none", "char", "word"] = "word",
        background: str = None,
        foreground: str = None,
        default_menu: bool = True,
        show_control_panel: bool = True,
        **kwargs,
    ):
        super().__init__(parent)

        self._parent = parent
        self.title(title)
        self.geometry(f"{width}x{height}")

        # 设置窗口图标（如果有父窗口）
        if parent:
            try:
                self.iconbitmap(parent.wm_iconbitmap())
            except Exception as e:
                _exception(e, "unable to set iconbitmap")

        # 设置窗口属性
        self.resizable(True, True)

        # 创建文本视图
        self._text_view = TextView(
            self,
            font=font,
            wrap=wrap,
            background=background,
            foreground=foreground,
            default_menu=default_menu,
            **kwargs,
        )
        self._text_view.pack(fill="both", padx=10, pady=10, expand=True)

        # 创建控制面板（可选）
        self._control_panel = None
        if show_control_panel:
            self._create_control_panel()

        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _create_control_panel(self):
        """创建控制面板"""
        control_frame = Frame(self)
        control_frame.pack(fill="x", padx=10, pady=5)

        # 缩放控制
        Label(control_frame, text=MSG_ZOOMING).pack(side="left", padx=5)

        zoom_in_btn = Button(
            control_frame, text=MSG_ZOOM_IN, command=self._text_view.zoom_in
        )
        zoom_in_btn.pack(side="left", padx=2)

        zoom_out_btn = Button(
            control_frame, text=MSG_ZOOM_OUT, command=self._text_view.zoom_out
        )
        zoom_out_btn.pack(side="left", padx=2)

        zoom_reset_btn = Button(
            control_frame, text=MSG_ZOOM_RESET, command=self._text_view.zoom_reset
        )
        zoom_reset_btn.pack(side="left", padx=2)

        # 导航控制
        Label(control_frame, text=MSG_NAVIGATION).pack(side="left", padx=(20, 5))

        top_btn = Button(
            control_frame, text=MSG_NAV_TOP, command=self._text_view.scroll_to_top
        )
        top_btn.pack(side="left", padx=2)

        bottom_btn = Button(
            control_frame, text=MSG_NAV_BOTTOM, command=self._text_view.scroll_to_bottom
        )
        bottom_btn.pack(side="left", padx=2)

        # 状态信息
        self.status_label = Label(control_frame, text=MSG_NAV_HINT)
        self.status_label.pack(side="right", padx=10)
        self._control_panel = control_frame

    @property
    def text_view(self) -> TextView:
        return self._text_view

    def set_text(self, text: str):
        """设置文本内容"""
        self._text_view.set_text(text)

    def clear(self):
        """清空文本"""
        self._text_view.clear()

    def get_text(self) -> str:
        """获取文本内容"""
        return self._text_view.get_text()

    def destroy(self):
        """销毁窗口"""
        super().destroy()
        self._parent = None
        self._text_view = None
        self._control_panel = None

    def show(self):
        """显示窗口（非模态）"""
        self.deiconify()
        self.lift()
        self.focus_force()
        # 如果有父窗口，设置为 transient
        if self._parent:
            self.transient(self._parent)

    def show_modal(self):
        """显示模态窗口"""
        self.show()
        self.grab_set()
        if self._parent:
            self.wait_window(self)

    def set_title(self, title: str):
        """设置窗口标题"""
        self.title(title)

    def set_icon(self, icon_path: str):
        """设置窗口图标"""
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            _exception(e, "unable to set iconbitmap")
