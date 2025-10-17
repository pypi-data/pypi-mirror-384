import dataclasses
import os
from tkinter import Widget, Frame, filedialog
from tkinter.ttk import Entry, Button
from typing import Type, Any, Optional, Union, List

from pyguiadapterlite._messages import (
    MSG_BROWSE_BUTTON_TEXT,
    MSG_SELECT_DIR_DIALOG_TITLE,
)
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.types.paths._common import block_keys
from pyguiadapterlite.utils import _error


@dataclasses.dataclass(frozen=True)
class DirectoryValue(BaseParameterWidgetConfig):
    default_value: str = ""
    start_dir: str = ""
    dialog_title: str = MSG_SELECT_DIR_DIALOG_TITLE
    select_button_text: str = MSG_BROWSE_BUTTON_TEXT
    normalize_path: bool = False
    absolutize_path: bool = False
    readonly: bool = False
    allow_backspace: bool = False

    def __post_init__(self):
        pass

    @classmethod
    def target_widget_class(cls) -> Type["DirectoryValueWidget"]:
        return DirectoryValueWidget


class FileSelectBox(Frame):
    def __init__(self, parent: "DirectoryValueWidget", **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent

        # 创建文件路径输入框
        self._entry = Entry(self)
        # 创建浏览按钮
        self._browse_button = Button(
            self, text=self._parent.config.select_button_text, command=self._browse_dir
        )

        # 布局组件
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._browse_button.pack(side="right")

        if self._parent.config.readonly:
            self.set_readonly()

    def set_readonly(self):
        self._entry.bind("<Key>", self._on_key)

    def _on_key(self, event):
        return block_keys(self._entry, self._parent.config.allow_backspace, event)

    def _browse_dir(self):
        config = self._parent.config

        try:
            file_path = filedialog.askdirectory(
                initialdir=config.start_dir, title=config.dialog_title
            )
            file_path = self._norm(file_path)
            if file_path:
                self._entry.delete(0, "end")
                self._entry.insert(0, file_path)
        except Exception as e:
            _error(f"error in directory dialog: {e}")

    def _norm(self, path: str):
        path = path.strip()
        if not path:
            return ""
        if self._parent.config.normalize_path:
            path = os.path.normpath(path)
        if self._parent.config.absolutize_path:
            path = os.path.abspath(path)
        return path

    @property
    def value(self) -> str:
        return self._norm(self._entry.get())

    @value.setter
    def value(self, value: Any):
        try:
            file_path = self._norm(str(value))
            self._entry.delete(0, "end")
            self._entry.insert(0, file_path)
        except Exception as e:
            if not isinstance(e, SetValueError):
                raise SetValueError(
                    raw_value=value, msg=f"failed to set directory value: {str(e)}"
                ) from e
            raise


class DirectoryValueWidget(BaseParameterWidget):
    ConfigClass = DirectoryValue

    def __init__(self, parent: Widget, parameter_name: str, config: DirectoryValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_widget: Optional[FileSelectBox] = None

    @property
    def config(self) -> DirectoryValue:
        return super().config

    def get_value(self) -> Union[str, List[str], InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            return self._input_widget.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[str, List[str], InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            self._input_widget.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "DirectoryValueWidget":
        if self._build_flag:
            return self

        # 创建输入控件
        self._input_widget = FileSelectBox(self)
        self._input_widget.pack(fill="both", expand=True, padx=1, pady=1)
        self._input_widget.value = self.config.default_value
        # 设置无效值效果目标
        self.color_flash_effect.set_target(self)
        self._build_flag = True
        return self

    def on_parameter_error(self, parameter_name: str, error: Any) -> None:
        if parameter_name == self._parameter_name:
            if isinstance(error, GetValueError):
                _error(
                    f"failed to get value from widget of parameter `{parameter_name}`: {error}"
                )
                self.start_invalid_value_effect()
                return
