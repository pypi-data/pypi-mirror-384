import dataclasses
from tkinter import Widget, END
from tkinter.ttk import Spinbox
from typing import Type, Any, Optional, Union, Literal

from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error, _exception

MAX_VALUE = 2.0**31 - 1
MIN_VALUE = -MAX_VALUE
DEFAULT_VALUE = 0.00
DEFAULT_STEP = 0.1
DEFAULT_DECIMALS = 2
MAX_DECIMALS = 10


@dataclasses.dataclass(frozen=True)
class RangedFloatValue(BaseParameterWidgetConfig):
    default_value: float = DEFAULT_VALUE
    min_value: float = MIN_VALUE
    max_value: float = MAX_VALUE
    step: float = DEFAULT_STEP
    decimals: int = DEFAULT_DECIMALS
    auto_correct: bool = False
    correct_to: Literal["default", "min", "max", "nearest"] = "nearest"

    def __post_init__(self):
        # 验证参数合理性
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        if self.step <= 0:
            raise ValueError("step must be positive")
        if not (self.min_value <= self.default_value <= self.max_value):
            raise ValueError("default_value must be between min_value and max_value")
        if not (0 <= self.decimals <= MAX_DECIMALS):
            raise ValueError("decimals must be between 0 and 10")

    @classmethod
    def target_widget_class(cls) -> Type["RangedFloatValueWidget"]:
        return RangedFloatValueWidget


class FloatSpinbox(Spinbox):
    def __init__(self, parent: "RangedFloatValueWidget", **kwargs):
        self._parent = parent
        config = parent.config

        # 设置Spinbox的范围和步长
        super().__init__(
            parent,
            from_=config.min_value,
            to=config.max_value,
            increment=config.step,
            format=f"%.{config.decimals}f",
            **kwargs,
        )

        self._validate_command = self.register(self.validate_input)
        self.configure(
            validate="key",
            validatecommand=(self._validate_command, "%P"),
        )
        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Return>", self.on_focus_out)

    @staticmethod
    def validate_input(value: str) -> bool:
        value = value.strip()
        if value == "" or value == "-" or value == "." or value == "-.":
            return True
        # noinspection PyBroadException
        try:
            float(value)
        except BaseException:
            return False
        return True

    def on_focus_out(self, event):
        _ = event
        current_value = self.get().strip()
        config = self._parent.config
        float_value = None
        try:
            float_value = float(current_value)
            # 检查是否在范围内
            if not (config.min_value <= float_value <= config.max_value):
                raise ValueError("out of range")
        except BaseException as e:
            _exception(e, "invalid float value")
            self._parent.start_invalid_value_effect()
            if config.auto_correct:
                self.set_value(self._corrected_value(float_value))

    @property
    def value(self) -> Union[float, InvalidValue]:
        current_value = self.get().strip()
        config = self._parent.config

        try:
            float_value = float(current_value)
            # 检查是否在范围内
            if config.min_value <= float_value <= config.max_value:
                return float_value
            else:
                raise GetValueError(
                    raw_value=current_value,
                    msg=f"out of range [{config.min_value}, {config.max_value}]",
                )
        except BaseException as e:
            raise GetValueError(
                raw_value=current_value, msg=f"invalid float value `{current_value}`"
            ) from e

    def set_value(self, value: float) -> None:
        """设置Spinbox的值"""
        config = self._parent.config

        try:
            float_value = float(value)
            # 检查是否在范围内
            if not (config.min_value <= float_value <= config.max_value):
                raise SetValueError(
                    raw_value=value,
                    msg=f"out of range [{config.min_value}, {config.max_value}]",
                )

            # 删除当前内容并插入新值
            self.delete(0, END)
            self.insert(END, str(float_value))

        except BaseException as e:
            raise SetValueError(
                raw_value=value, msg=f"invalid float value `{value}`"
            ) from e

    def _corrected_value(self, value: Optional[float]) -> float:
        config = self._parent.config
        if config.correct_to == "default":
            return config.default_value
        elif config.correct_to == "min":
            return config.min_value
        elif config.correct_to == "max":
            return config.max_value
        else:
            if value is None:
                return config.default_value
            # 取最近的合法值
            if value < config.min_value:
                return config.min_value
            elif value > config.max_value:
                return config.max_value
            else:
                return config.default_value


class RangedFloatValueWidget(BaseParameterWidget):
    ConfigClass = RangedFloatValue

    def __init__(self, parent: Widget, parameter_name: str, config: RangedFloatValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._spinbox: Optional[FloatSpinbox] = None

    @property
    def config(self) -> RangedFloatValue:
        return super().config

    def get_value(self) -> Union[float, InvalidValue]:
        if not self._spinbox:
            raise RuntimeError("spinbox not created yet")
        try:
            return self._spinbox.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[float, InvalidValue]:
        if not self._spinbox:
            raise RuntimeError("spinbox not created yet")
        try:
            self._spinbox.set_value(value)
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "RangedFloatValueWidget":
        if self._build_flag:
            return self
        self._spinbox = FloatSpinbox(self)
        self.color_flash_effect.set_target(self)
        # noinspection PyTypeChecker
        self._spinbox.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self._spinbox.set_value(self._config.default_value)
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
