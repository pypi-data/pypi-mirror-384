import dataclasses
from tkinter import Widget, Label, Frame
from tkinter import ttk
from typing import Type, Any, Optional, Union

from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error

MIN_VALUE = 0.0
MAX_VALUE = 100.0
DEFAULT_VALUE = 0.0
DEFAULT_DIGITS = 5
MAX_DIGITS = 10


@dataclasses.dataclass(frozen=True)
class ScaleFloatValue(BaseParameterWidgetConfig):
    default_value: float = DEFAULT_VALUE
    min_value: float = MIN_VALUE
    max_value: float = MAX_VALUE
    digits: int = DEFAULT_DIGITS
    show_value: bool = True
    cursor: str = "hand2"

    def __post_init__(self):
        # 验证参数合理性
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        if not (self.min_value <= self.default_value <= self.max_value):
            raise ValueError("default_value must be between min_value and max_value")
        if self.digits != 0:
            if self.digits < 0 or self.digits > MAX_DIGITS:
                raise ValueError(f"digits must be between 0 and {MAX_DIGITS}")

    @classmethod
    def target_widget_class(cls) -> Type["ScaleFloatValueWidget"]:
        return ScaleFloatValueWidget


class FloatScale(ttk.Scale):
    def __init__(self, parent: Frame, value_widget: "ScaleFloatValueWidget", **kwargs):
        self._parent = parent
        config = value_widget.config
        self._value_widget = value_widget

        # 设置ttk.Scale的范围和步长
        super().__init__(
            parent,
            from_=config.min_value,
            to=config.max_value,
            orient="horizontal",
            cursor=config.cursor,
            **kwargs,
        )
        # 初始值
        self.set(config.default_value)

    @staticmethod
    def set_(value, config, setter):
        try:
            float_value = float(value)
            # 检查是否在范围内
            if not (config.min_value <= float_value <= config.max_value):
                raise SetValueError(
                    raw_value=value,
                    msg=f"out of range [{config.min_value}, {config.max_value}]",
                )
            setter(float_value)
        except BaseException as e:
            raise SetValueError(
                raw_value=value, msg=f"invalid float value `{value}`"
            ) from e

    @staticmethod
    def get_(getter) -> float:
        try:
            return float(getter())
        except BaseException as e:
            current_value = getter()
            raise GetValueError(
                raw_value=current_value, msg=f"invalid float value `{current_value}`"
            ) from e

    @property
    def value(self) -> float:
        return self.get_(self.get)

    @value.setter
    def value(self, value: float) -> None:
        self.set_(value, self._value_widget.config, self.set)


class ScaleFloatValueWidget(BaseParameterWidget):
    ConfigClass = ScaleFloatValue

    def __init__(self, parent: Widget, parameter_name: str, config: ScaleFloatValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._frame: Optional[Frame] = None
        self._input_widget: Optional[FloatScale] = None
        self._value_label: Optional[Label] = None

    @property
    def config(self) -> ScaleFloatValue:
        return super().config

    @staticmethod
    def get_(widget):
        if not widget._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            return widget._input_widget.value
        except GetValueError as e:
            widget.on_parameter_error(widget._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    @staticmethod
    def set_(widget, value):
        if not widget._input_widget:
            raise RuntimeError("scale not created yet")
        try:
            widget._input_widget.value = value
            return value
        except SetValueError as e:
            widget.on_parameter_error(widget._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def get_value(self) -> Union[float, InvalidValue]:
        return self.get_(self)

    def set_value(self, value: Any) -> Union[float, InvalidValue]:
        return self.set_(self, value)

    def build(self) -> "ScaleFloatValueWidget":
        if self._build_flag:
            return self
        self._frame = Frame(self)
        self._frame.pack(fill="both", expand=True, padx=1, pady=1)
        self._input_widget = FloatScale(
            self._frame, value_widget=self, command=self.on_value_changed
        )
        self._input_widget.pack(side="left", fill="both", expand=True)
        self._input_widget.value = self._config.default_value
        if self._config.show_value:
            self._value_label = Label(self._frame, justify="center", anchor="center")
            self._value_label.pack(side="right", fill="x", expand=False)
            self.on_value_changed(None)
        self.color_flash_effect.set_target(self)
        # noinspection PyTypeChecker
        self._build_flag = True
        return self

    def _format_value(self, value: float) -> str:
        """格式化显示的值，根据digits参数控制小数位数"""
        format_str = f"{{:.{self.config.digits or 2}f}}"
        return format_str.format(value)

    def on_value_changed(self, value: Optional[str]) -> None:
        """当滑块值变化时更新显示标签"""
        if self._value_label:
            formatted_value = self._format_value(float(self._input_widget.value))
            self._value_label.config(text=formatted_value)

    def on_parameter_error(self, parameter_name: str, error: Any) -> None:
        if parameter_name == self._parameter_name:
            if isinstance(error, GetValueError):
                _error(
                    f"failed to get value from widget of parameter `{parameter_name}`: {error}"
                )
                self.start_invalid_value_effect()
                return
