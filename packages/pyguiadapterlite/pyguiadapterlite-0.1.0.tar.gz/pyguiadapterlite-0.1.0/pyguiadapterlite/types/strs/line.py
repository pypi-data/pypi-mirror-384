import dataclasses

from tkinter import Widget, END
from tkinter.ttk import Entry
from typing import Type, Any, Optional, Union, Literal

from pyguiadapterlite.utils import _error
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)


@dataclasses.dataclass(frozen=True)
class StringValue(BaseParameterWidgetConfig):
    default_value: str = ""
    echo_char: str = ""
    justify: Literal["left", "center", "right"] = "left"

    @classmethod
    def target_widget_class(cls) -> Type["StringValueWidget"]:
        return StringValueWidget


class StringEntry(Entry):
    def __init__(self, parent: "StringValueWidget", **kwargs):
        super().__init__(parent, **kwargs)
        self.config(show=parent.config.echo_char, justify=parent.config.justify)

    @property
    def value(self) -> Union[str, InvalidValue]:
        return self.get()

    @value.setter
    def value(self, value: Any) -> Optional[InvalidValue]:
        self.delete(0, END)
        self.insert(END, str(value))


class StringValueWidget(BaseParameterWidget):
    ConfigClass = StringValue

    def __init__(self, parent: Widget, parameter_name: str, config: StringValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_entry: Optional[StringEntry] = None

    @property
    def config(self) -> StringValue:
        return super().config

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

    def build(self) -> "StringValueWidget":
        if self._build_flag:
            return self
        self._build_flag = True
        self._input_entry = StringEntry(self)
        self.color_flash_effect.set_target(self)
        # noinspection PyTypeChecker
        self._input_entry.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        self._input_entry.value = self._config.default_value

        return self

    def on_parameter_error(self, parameter_name: str, error: Any) -> None:
        if parameter_name == self._parameter_name:
            if isinstance(error, GetValueError):
                _error(
                    f"failed to get value from widget of parameter `{parameter_name}`: {error}"
                )
                self.start_invalid_value_effect()
                return
