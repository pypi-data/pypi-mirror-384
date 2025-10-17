import re
from tkinter import (
    filedialog,
    Frame,
    Scrollbar,
    Text,
    Menu,
    SEL_FIRST,
    SEL_LAST,
    TclError,
    SEL,
    END,
    INSERT,
    messagebox,
)
from typing import Optional

from pyguiadapterlite._messages import (
    MSG_COPY,
    MSG_SELECT_ALL,
    MSG_CLEAR_OUTPUT,
    MSG_SCROLL_TO_TOP,
    MSG_SCROLL_TO_BOTTOM,
    MSG_SAVE_TO_FILE,
)
from pyguiadapterlite.utils import _warning


class TermView(Frame):

    colormap = {
        "black": "#000000",
        "red": "#FF0000",
        "green": "#00FF00",
        "yellow": "#FFFF00",
        "blue": "#0000FF",
        "magenta": "#FF00FF",
        "cyan": "#00FFFF",
        "white": "#FFFFFF",
        "bright_black": "#808080",
        "bright_red": "#FF6060",
        "bright_green": "#60FF60",
        "bright_yellow": "#FFFF60",
        "bright_blue": "#6060FF",
        "bright_magenta": "#FF60FF",
        "bright_cyan": "#60FFFF",
        "bright_white": "#FFFFFF",
    }

    def __init__(
        self,
        parent,
        background: str = "black",
        foreground: str = "white",
        select_background: str = "lightgray",
        font: tuple = ("Courier", 10),
        default_context_menu=False,
        colormap: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._background = background
        self._foreground = foreground
        self._select_background = select_background
        self._font = font
        self._default_context_menu = default_context_menu
        self._colormap = colormap or self.colormap.copy()

        # 创建文本区域和滚动条
        self._text_widget = Text(
            self,
            bg=background,
            fg=foreground,
            font=font,
            insertbackground=foreground,
            selectbackground=select_background,
            wrap="none",
            tabs=("1c", "2c", "3c", "4c"),
        )

        v_scrollbar = Scrollbar(
            self, orient="vertical", command=self._text_widget.yview
        )
        self._text_widget.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = Scrollbar(
            self, orient="horizontal", command=self._text_widget.xview
        )
        self._text_widget.configure(xscrollcommand=h_scrollbar.set)

        # 布局
        self._text_widget.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ANSI转义序列处理
        self.ansi_pattern = re.compile(r"\x1b\[([\d;]*)m")
        self.current_fg = foreground
        self.current_bg = background
        self.current_style = "normal"

        # 存储标签配置
        self._tag_configs = {}

        # 绑定事件
        self._text_widget.bind("<Key>", self._ignore_input)

        # 创建右键菜单
        if self._default_context_menu:
            self._create_context_menu()
            # 绑定右键点击事件
            self._text_widget.bind(
                "<Button-3>", self._show_context_menu
            )  # Windows/Linux
            self._text_widget.bind("<Button-2>", self._show_context_menu)  # Mac

        # 初始化标签
        self._init_tags()

    def _create_context_menu(self):
        """创建右键上下文菜单"""
        self.context_menu = Menu(self._text_widget, tearoff=0)

        # 添加菜单项
        self.context_menu.add_command(label=MSG_COPY, command=self.copy_selected_text)
        self.context_menu.add_command(label=MSG_SELECT_ALL, command=self.select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=MSG_CLEAR_OUTPUT, command=self.clear)
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label=MSG_SCROLL_TO_TOP, command=self.scroll_to_top
        )
        self.context_menu.add_command(
            label=MSG_SCROLL_TO_BOTTOM, command=self.scroll_to_bottom
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(label=MSG_SAVE_TO_FILE, command=self.save_to_file)

    def _show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selected_text(self, copy_to_clipboard=True) -> Optional[str]:
        """复制选中的文本"""
        try:
            # 获取选中的文本
            selected_text = self._text_widget.get(SEL_FIRST, SEL_LAST)
            if selected_text and copy_to_clipboard:
                self.clipboard_clear()
                self.clipboard_append(selected_text)
            return selected_text
        except TclError:
            _warning("no text selected")
            return None

    def select_all(self):
        """全选文本"""
        self._text_widget.tag_add(SEL, "1.0", END)
        self._text_widget.mark_set(INSERT, "1.0")
        self._text_widget.see(INSERT)

    def scroll_to_top(self):
        """滚动到顶部"""
        self._text_widget.see("1.0")

    def scroll_to_bottom(self):
        """滚动到底部"""
        self._text_widget.see(END)

    def save_to_file(self):
        """保存控制台内容到文件"""

        # 获取所有文本（去除ANSI转义序列）
        text_content = self._get_plain_text()

        # 选择保存文件
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title=MSG_SAVE_TO_FILE,
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(text_content)
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")

    def _get_plain_text(self):
        """获取纯文本内容（去除ANSI转义序列）"""
        text_content = self._text_widget.get("1.0", END)
        # 移除ANSI转义序列
        clean_text = re.sub(r"\x1b\[[\d;]*m", "", text_content)
        return clean_text

    def _init_tags(self):
        """初始化文本样式标签"""
        # 前景色标签
        for name, color in self._colormap.items():
            tag_name = f"fg_{name}"
            self._text_widget.tag_config(tag_name, foreground=color)
            self._tag_configs[tag_name] = {"foreground": color}

        # 背景色标签
        for name, color in self._colormap.items():
            tag_name = f"bg_{name}"
            self._text_widget.tag_config(tag_name, background=color)
            self._tag_configs[tag_name] = {"background": color}

        # 样式标签
        self._text_widget.tag_config(
            "bold", font=(self._font[0], self._font[1], "bold")
        )
        self._text_widget.tag_config(
            "italic", font=(self._font[0], self._font[1], "italic")
        )
        self._text_widget.tag_config("underline", underline=True)
        self._tag_configs["bold"] = {"font": (self._font[0], self._font[1], "bold")}
        self._tag_configs["italic"] = {"font": (self._font[0], self._font[1], "italic")}
        self._tag_configs["underline"] = {"underline": True}

    @staticmethod
    def _ignore_input(event):
        _ = event
        """忽略用户输入"""
        return "break"

    def _process_text(self, text):
        """处理文本和ANSI转义序列"""
        # 简单的ANSI转义序列处理
        parts = self.ansi_pattern.split(text)

        # 如果没有ANSI序列，直接输出
        if len(parts) == 1:
            self._text_widget.insert(END, text)
            self._text_widget.see(END)
            return

        # 处理包含ANSI序列的文本
        i = 0
        while i < len(parts):
            if i % 2 == 0:
                # 普通文本
                if parts[i]:
                    self._insert_with_current_style(parts[i])
            else:
                # ANSI序列
                self._handle_ansi_sequence(parts[i])
            i += 1

        self._text_widget.see(END)

    def _insert_with_current_style(self, text):
        """使用当前样式插入文本"""
        tags = []

        # 添加前景色标签
        if self.current_fg != self._foreground:
            fg_tag = f"fg_{self.current_fg}"
            if fg_tag in self._tag_configs:
                tags.append(fg_tag)

        # 添加背景色标签
        if self.current_bg != self._background:
            bg_tag = f"bg_{self.current_bg}"
            if bg_tag in self._tag_configs:
                tags.append(bg_tag)

        # 添加样式标签
        if self.current_style != "normal":
            if self.current_style in self._tag_configs:
                tags.append(self.current_style)

        # 插入文本
        if tags:
            self._text_widget.insert(END, text, tags)
        else:
            self._text_widget.insert(END, text)

    def _handle_ansi_sequence(self, sequence):
        """处理ANSI转义序列"""
        if not sequence:
            # 重置所有属性
            self.current_fg = self._foreground
            self.current_bg = self._background
            self.current_style = "normal"
            return

        codes = sequence.split(";")
        for code in codes:
            if not code:
                continue

            c = int(code)

            # 重置所有属性
            if c == 0:
                self.current_fg = self._foreground
                self.current_bg = self._background
                self.current_style = "normal"

            # 样式设置
            elif c == 1:
                self.current_style = "bold"
            elif c == 3:
                self.current_style = "italic"
            elif c == 4:
                self.current_style = "underline"
            elif c == 7:
                # 反色 - 交换前景色和背景色
                self.current_fg, self.current_bg = self.current_bg, self.current_fg

            # 前景色
            elif 30 <= c <= 37:
                colors = [
                    "black",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                ]
                self.current_fg = colors[c - 30]
            elif 90 <= c <= 97:
                colors = [
                    "bright_black",
                    "bright_red",
                    "bright_green",
                    "bright_yellow",
                    "bright_blue",
                    "bright_magenta",
                    "bright_cyan",
                    "bright_white",
                ]
                self.current_fg = colors[c - 90]

            # 背景色
            elif 40 <= c <= 47:
                colors = [
                    "black",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                ]
                self.current_bg = colors[c - 40]
            elif 100 <= c <= 107:
                colors = [
                    "bright_black",
                    "bright_red",
                    "bright_green",
                    "bright_yellow",
                    "bright_blue",
                    "bright_magenta",
                    "bright_cyan",
                    "bright_white",
                ]
                self.current_bg = colors[c - 100]

    def clear(self):
        """清空控制台"""
        self._text_widget.delete(1.0, END)

    def write(self, text):
        """向控制台输出文本，处理ANSI转义序列"""
        self._process_text(text)

    def write_line(self, text):
        """输出一行文本"""
        self.write(text + "\n")

    def set_text(self, text):
        """设置控制台文本"""
        self.clear()
        self.write(text)

    def write_after(self, text):
        """向控制台输出文本，处理ANSI转义序列"""
        self.after(0, self._process_text, text)

    def write_line_after(self, text):
        """输出一行文本"""
        self.write_after(text + "\n")

    def get_text(self):
        """获取控制台中的所有文本"""
        return self._text_widget.get(1.0, END)

    def set_text_after(self, text):
        """设置控制台文本"""
        self.clear()
        self.write_after(text)
