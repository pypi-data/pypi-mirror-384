import dataclasses
from tkinter import Widget, Frame, IntVar
from tkinter.ttk import Radiobutton, Checkbutton
from typing import Type, Any, Optional, Union, Literal

from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error


@dataclasses.dataclass(frozen=True)
class BoolValue2(BaseParameterWidgetConfig):
    default_value: bool = False
    hint_text: str = ""
    hide_label: bool = True

    @classmethod
    def target_widget_class(cls) -> Type["BoolValueWidget2"]:
        return BoolValueWidget2


class BoolBox2(Frame):
    def __init__(self, parent: "BoolValueWidget2", **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self._value_var = IntVar(value=1 if parent.config.default_value else 0)
        # 创建单选按钮
        self._checkbox = Checkbutton(self, variable=self._value_var)
        hint_text = (
            self._parent.config.hint_text
            or self._parent.label
            or self._parent.config.description.strip()
        )
        self._checkbox.config(text=hint_text)
        self._checkbox.pack(fill="both", expand=True, padx=1, pady=1)

    @property
    def value(self) -> bool:
        return bool(self._value_var.get())

    @value.setter
    def value(self, value: Any):
        bool_value = bool(value)
        # 设置值
        self._value_var.set(1 if bool_value else 0)


class BoolValueWidget2(BaseParameterWidget):
    ConfigClass = BoolValue2

    def __init__(self, parent: Widget, parameter_name: str, config: BoolValue2):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_widget: Optional[BoolBox2] = None

    @property
    def config(self) -> BoolValue2:
        return super().config

    def get_value(self) -> Union[bool, InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            return self._input_widget.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[bool, InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            self._input_widget.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "BoolValueWidget2":
        if self._build_flag:
            return self
        # 创建输入控件
        self._input_widget = BoolBox2(self)
        self._input_widget.pack(fill="both", expand=True, padx=1, pady=1)
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
