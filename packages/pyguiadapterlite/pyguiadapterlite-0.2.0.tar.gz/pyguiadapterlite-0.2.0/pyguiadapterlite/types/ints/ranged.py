import dataclasses
from tkinter import Widget
from tkinter.ttk import Spinbox
from typing import Type, Any, Optional, Union

from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error

MAX_VALUE = 2**31 - 1
MIN_VALUE = -MAX_VALUE


@dataclasses.dataclass(frozen=True)
class RangedIntValue(BaseParameterWidgetConfig):
    default_value: int = 0
    min_value: int = MIN_VALUE
    max_value: int = MAX_VALUE
    step: int = 1
    wrap: bool = False

    @classmethod
    def target_widget_class(cls) -> Type["RangedIntValueWidget"]:
        return RangedIntValueWidget


class IntSpinbox(Spinbox):
    def __init__(self, parent: "RangedIntValueWidget", **kwargs):
        super().__init__(parent, **kwargs)
        self.config(
            from_=parent.config.min_value,
            to=parent.config.max_value,
            increment=parent.config.step,
            wrap=parent.config.wrap,
        )
        self._parent = parent

    @property
    def value(self) -> Union[int, InvalidValue]:
        current_value = self.get().strip()
        try:
            val = int(current_value)
        except BaseException as e:
            raise GetValueError(
                raw_value=current_value, msg=f"cannot convert to int"
            ) from e
        if val < self._parent.config.min_value or val > self._parent.config.max_value:
            raise GetValueError(
                raw_value=current_value,
                msg=f"out of range [{self._parent.config.min_value}, {self._parent.config.max_value}]",
            )
        return val

    @value.setter
    def value(self, value: int) -> Optional[InvalidValue]:
        raw_value = value
        try:
            value = int(raw_value)
        except BaseException as e:
            raise SetValueError(
                raw_value=raw_value, msg=f"cannot convert to int"
            ) from e
        if (
            value < self._parent.config.min_value
            or value > self._parent.config.max_value
        ):
            raise SetValueError(
                raw_value=raw_value,
                msg=f"out of range [{self._parent.config.min_value}, {self._parent.config.max_value}]",
            )
        self.set(str(value))


class RangedIntValueWidget(BaseParameterWidget):
    ConfigClass = RangedIntValue

    def __init__(self, parent: Widget, parameter_name: str, config: RangedIntValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_entry: Optional[IntSpinbox] = None

    @property
    def config(self) -> RangedIntValue:
        return self._config

    def get_value(self) -> Union[int, InvalidValue]:
        if not self._input_entry:
            raise RuntimeError("input widget not created yet")
        try:
            return self._input_entry.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[int, InvalidValue]:
        if not self._input_entry:
            raise RuntimeError("input widget not created yet")
        try:
            self._input_entry.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "RangedIntValueWidget":
        if self._build_flag:
            return self
        self._input_entry = IntSpinbox(self)
        self.color_flash_effect.set_target(self)
        # noinspection PyTypeChecker
        self._input_entry.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self._input_entry.value = self._config.default_value
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
