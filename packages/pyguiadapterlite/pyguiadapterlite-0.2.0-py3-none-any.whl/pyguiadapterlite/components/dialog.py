import os
from tkinter import Toplevel, Tk, Widget, Frame, filedialog
from tkinter.ttk import Button, Entry, Label, Separator
from typing import Union, Any, Optional, List, Tuple, Literal

from pyguiadapterlite._messages import (
    MSG_DIALOG_BUTTON_OK,
    MSG_DIALOG_BUTTON_CANCEL,
    MSG_DIALOG_INPUT_PROMPT,
    MSG_PATH_DIALOG_FILE_BUTTON_TEXT,
    MSG_PATH_DIALOG_DIR_BUTTON_TEXT,
    MSG_FILE_FILTER_ALL,
    MSG_SELECT_FILE_DIALOG_TITLE,
    MSG_SELECT_DIR_DIALOG_TITLE,
)
from pyguiadapterlite.components.textview import TextView


class BaseDialog(object):
    def __init__(
        self,
        parent: Union[Toplevel, Tk, Widget],
        title: str,
        size: tuple = (300, 200),
        resizable: bool = False,
    ):
        self._parent = parent
        self._title = title
        self._size = size
        self._parent.update()

        self._dialog = Toplevel(self._parent)
        self._dialog.withdraw()
        self._dialog.title(self._title)
        self._dialog.geometry(f"{self._size[0]}x{self._size[1]}")
        self._dialog.resizable(resizable, resizable)
        self._dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)

        self._result: Any = None
        self._is_cancelled = False

        self.on_create_content_area(self._dialog)
        self.on_create_buttons(self._dialog)

        parent_window = parent
        if isinstance(parent, Widget):
            parent_window = parent.winfo_toplevel()

        # 将dialog移动到当前鼠标附近
        # x = parent_window.winfo_pointerx() - self._dialog.winfo_reqwidth() // 2
        # y = parent_window.winfo_pointery() - self._dialog.winfo_reqheight() // 2
        # dialog移动到父窗口中央
        x = (
            parent_window.winfo_rootx()
            + parent_window.winfo_width() // 2
            - self._dialog.winfo_reqwidth() // 2
        )
        y = (
            parent_window.winfo_rooty()
            + parent_window.winfo_height() // 2
            - self._dialog.winfo_reqheight() // 2
        )
        self._dialog.geometry(f"+{x}+{y}")
        self._dialog.deiconify()
        self._dialog.transient(parent_window)
        self._dialog.grab_set()
        self._dialog.wait_window()

    def on_create_content_area(self, dialog: Toplevel):
        raise NotImplementedError()

    def on_create_buttons(self, dialog: Toplevel):
        raise NotImplementedError()

    def is_cancelled(self):
        return self._is_cancelled

    @property
    def result(self) -> Any:
        return self._result

    def on_get_result(self) -> Any:
        raise NotImplementedError()

    def on_ok(self):
        self._result = self.on_get_result()
        self._is_cancelled = False
        self._dialog.destroy()

    def on_cancel(self):
        self._is_cancelled = True
        self._dialog.destroy()


class BaseSimpleDialog(BaseDialog):
    def __init__(
        self,
        parent: Union[Toplevel, Tk, Widget],
        title: str,
        size: tuple = (300, 200),
        resizable: bool = False,
        ok_text: str = MSG_DIALOG_BUTTON_OK,
        cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    ):
        self._ok_text = ok_text
        self._cancel_text = cancel_text
        self._content_area: Optional[Frame] = None
        self._buttons_area: Optional[Frame] = None
        self._ok_button: Optional[Button] = None
        self._cancel_button: Optional[Button] = None

        super().__init__(parent, title, size, resizable)

    def on_create_content_area(self, dialog: Toplevel):
        self._content_area = Frame(dialog)
        self._content_area.pack(fill="both", expand=True)
        self._content_area.pack(side="top", fill="both", expand=True)

    def on_create_buttons(self, dialog: Toplevel):
        self._buttons_area = Frame(dialog)
        self._buttons_area.pack(side="bottom", fill="x")
        self._cancel_button = Button(
            self._buttons_area, text=self._cancel_text, command=self.on_cancel
        )
        self._cancel_button.pack(side="right", padx=5, pady=5)

        self._ok_button = Button(
            self._buttons_area, text=self._ok_text, command=self.on_ok
        )
        self._ok_button.pack(side="right", padx=5, pady=5)


class StringInputDialog(BaseSimpleDialog):
    def __init__(
        self,
        parent: Union[Toplevel, Tk, Widget],
        title: str,
        size: tuple = (300, 100),
        resizable: bool = False,
        ok_text: str = MSG_DIALOG_BUTTON_OK,
        cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
        label_text: str = MSG_DIALOG_INPUT_PROMPT,
        initial_value: str = "",
        echo_char: Optional[str] = None,
    ):
        self._label_text = label_text
        self._initial_value = initial_value
        self._echo_char = echo_char

        self._input_label: Optional[Label] = None
        self._input_entry: Optional[Entry] = None
        super().__init__(parent, title, size, resizable, ok_text, cancel_text)

    def on_get_result(self) -> str:
        return self._input_entry.get()

    def on_create_content_area(self, dialog: Toplevel):
        super().on_create_content_area(dialog)
        if self._label_text:
            self._input_label = Label(self._content_area, text=self._label_text)
            self._input_label.pack(side="top", fill="x", padx=5, pady=(5, 0))
        self._input_entry = Entry(self._content_area)
        self._input_entry.pack(side="bottom", fill="x", expand=True, padx=5, pady=2)
        self._input_entry.insert(0, self._initial_value)
        if self._echo_char is not None:
            self._input_entry.config(show=self._echo_char)


class PathInputDialog(BaseSimpleDialog):
    def __init__(
        self,
        parent: Union[Toplevel, Tk, Widget],
        title: str,
        size: tuple = (420, 130),
        resizable: bool = False,
        file_button_text: Optional[str] = MSG_PATH_DIALOG_FILE_BUTTON_TEXT,
        file_types: List[Tuple[str, str]] = None,
        file_dialog_title: str = MSG_SELECT_FILE_DIALOG_TITLE,
        file_dialog_action: Literal["open", "save"] = "open",
        dir_button_text: Optional[str] = MSG_PATH_DIALOG_DIR_BUTTON_TEXT,
        dir_dialog_title: str = MSG_SELECT_DIR_DIALOG_TITLE,
        start_dir: str = "",
        ok_text: str = MSG_DIALOG_BUTTON_OK,
        cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
        label_text: str = MSG_DIALOG_INPUT_PROMPT,
        initial_value: str = "",
    ):
        self._label_text = label_text
        self._initial_value = initial_value

        self._file_button_text = file_button_text or ""
        self._file_types = file_types or [(MSG_FILE_FILTER_ALL, "*")]
        self._file_dialog_title = file_dialog_title
        self._file_dialog_action = file_dialog_action
        self._dir_button_text = dir_button_text or ""
        self._dir_dialog_title = dir_dialog_title
        self._start_dir = start_dir

        self._input_label: Optional[Label] = None
        self._input_entry: Optional[Entry] = None
        self._file_button: Optional[Button] = None
        self._dir_button: Optional[Button] = None

        if not self._file_button_text and not self._dir_button_text:
            raise ValueError(
                "At least one of file_button_text and dir_button_text should be provided."
            )

        super().__init__(parent, title, size, resizable, ok_text, cancel_text)

    def on_get_result(self) -> str:
        return self._input_entry.get()

    def on_create_content_area(self, dialog: Toplevel):
        super().on_create_content_area(dialog)
        if self._label_text:
            self._input_label = Label(self._content_area, text=self._label_text)
            self._input_label.pack(side="top", fill="x", padx=5, pady=(5, 0))

        self._input_entry = Entry(self._content_area)
        self._input_entry.pack(side="left", fill="x", expand=True, padx=5, pady=2)
        self._input_entry.insert(0, self._initial_value)

    def on_create_buttons(self, dialog: Toplevel):
        super().on_create_buttons(dialog)

        if self._file_button_text:
            self._file_button = Button(
                self._buttons_area,
                text=self._file_button_text,
                command=self._select_file,
            )
            self._file_button.pack(side="left", padx=5, pady=5)

        if self._dir_button_text:
            self._dir_button = Button(
                self._buttons_area,
                text=self._dir_button_text,
                command=self._select_dir,
            )
            self._dir_button.pack(side="left", padx=5, pady=5)

        separator = Separator(self._buttons_area, orient="vertical")
        separator.pack(side="right", fill="y", padx=5, pady=5)

    def _select_file(self):
        """打开文件选择对话框并将选择的文件路径设置到输入框中"""
        # 确定初始目录
        initial_dir = self._start_dir
        if not initial_dir and self._input_entry.get():
            # 如果已有路径，使用其所在目录
            entry_path = self._input_entry.get()
            if os.path.exists(entry_path):
                if os.path.isfile(entry_path):
                    initial_dir = os.path.dirname(entry_path)
                else:
                    initial_dir = entry_path

        # 根据对话框动作选择不同的文件对话框
        if self._file_dialog_action == "open":
            file_path = filedialog.askopenfilename(
                parent=self._dialog,
                title=self._file_dialog_title,
                initialdir=initial_dir,
                filetypes=self._file_types,
            )
        else:  # "save"
            file_path = filedialog.asksaveasfilename(
                parent=self._dialog,
                title=self._file_dialog_title,
                initialdir=initial_dir,
                filetypes=self._file_types,
                defaultextension=self._get_default_extension(),
            )

        # 如果用户选择了文件（没有取消）
        if file_path:
            # 清空输入框并插入新路径
            self._input_entry.delete(0, "end")
            self._input_entry.insert(0, file_path)

    def _select_dir(self):
        """打开目录选择对话框并将选择的目录路径设置到输入框中"""
        # 确定初始目录
        initial_dir = self._start_dir
        if not initial_dir and self._input_entry.get():
            # 如果已有路径，使用其所在目录
            entry_path = self._input_entry.get()
            if os.path.exists(entry_path):
                if os.path.isfile(entry_path):
                    initial_dir = os.path.dirname(entry_path)
                else:
                    initial_dir = entry_path
        # 打开目录选择对话框
        dir_path = filedialog.askdirectory(
            parent=self._dialog, title=self._dir_dialog_title, initialdir=initial_dir
        )
        # 如果用户选择了目录（没有取消）
        if dir_path:
            # 清空输入框并插入新路径
            self._input_entry.delete(0, "end")
            self._input_entry.insert(0, dir_path)

    def _get_default_extension(self) -> str:
        """获取默认的文件扩展名"""
        if self._file_types and len(self._file_types) > 0:
            # 获取第一个文件类型的模式
            first_pattern = self._file_types[0][1]
            if first_pattern != "*":
                # 从模式中提取扩展名，如 "*.txt" -> ".txt"
                if "*." in first_pattern:
                    return first_pattern.split("*.")[-1]
        return ""


class TextViewDialog(BaseSimpleDialog):

    def __init__(
        self,
        parent: Union[Toplevel, Tk, Widget],
        title: str = "",
        size: tuple = (500, 400),
        resizable: bool = True,
        ok_text: str = MSG_DIALOG_BUTTON_OK,
        cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
        text: str = "",
        textview_height: int = 18,
        editable: bool = True,
        default_menu: bool = True,
        wrap: Literal["none", "char", "word"] = "word",
        font: tuple = ("Arial", 10),
        label_text: str = "",
    ):
        self._initial_text: str = text
        self._editable = editable
        self._default_menu = default_menu
        self._wrap = wrap
        self._font = font
        self._textview_height = textview_height
        self._label_text = label_text

        self._textview: Optional[TextView] = None

        super().__init__(parent, title, size, resizable, ok_text, cancel_text)

    def on_create_content_area(self, dialog: Toplevel):
        self._content_area = Frame(dialog)
        self._content_area.pack(fill="both", expand=True)

        label = Label(self._content_area, text=self._label_text)
        label.pack(side="top", fill="x", padx=5, pady=(5, 0))

        self._textview = TextView(
            self._content_area,
            editable=self._editable,
            default_menu=self._default_menu,
            wrap=self._wrap,
            font=self._font,
            height=self._textview_height,
        )
        self._textview.set_text(self._initial_text)
        self._textview.pack(fill="x", expand=False, padx=5, pady=2)

    def on_get_result(self) -> Any:
        return self._textview.get_text()
