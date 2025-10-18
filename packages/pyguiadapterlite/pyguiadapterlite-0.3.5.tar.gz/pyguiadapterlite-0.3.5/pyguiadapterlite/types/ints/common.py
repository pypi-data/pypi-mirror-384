import dataclasses

from tkinter import Widget, END
from tkinter.ttk import Entry
from typing import Type, Any, Optional, Union

from pyguiadapterlite.utils import _error, _exception
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)


@dataclasses.dataclass(frozen=True)
class IntValue(BaseParameterWidgetConfig):
    default_value: int = 0
    auto_correct: bool = False

    @classmethod
    def target_widget_class(cls) -> Type["IntValueWidget"]:
        return IntValueWidget


class IntEntry(Entry):
    def __init__(self, parent: "IntValueWidget", **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
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
        if value == "" or value == "-":
            return True
        # noinspection PyBroadException
        try:
            int(value)
            return True
        except BaseException as e:
            return False

    def on_focus_out(self, event):
        _ = event
        try:
            int(self.get().strip())
        except BaseException as e:
            self._parent.start_invalid_value_effect()
            _exception(e, "invalid int value")
            if self._parent.config.auto_correct:
                self.delete(0, END)
                self.insert(END, str(self._parent.config.default_value))

    @property
    def value(self) -> Union[int, InvalidValue]:
        current_value = self.get().strip()
        try:
            return int(self.get().strip())
        except BaseException as e:
            raise GetValueError(
                raw_value=current_value, msg=f"invalid int value `{current_value}`"
            ) from e

    @value.setter
    def value(self, value: int) -> Optional[InvalidValue]:
        raw_value = value
        try:
            value = int(raw_value)
            self.delete(0, END)
            self.insert(END, str(value))
        except BaseException as e:
            raise SetValueError(
                raw_value=raw_value, msg=f"invalid int value `{value}`"
            ) from e


class IntValueWidget(BaseParameterWidget):
    ConfigClass = IntValue

    def __init__(self, parent: Widget, parameter_name: str, config: IntValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_entry: Optional[IntEntry] = None

    @property
    def config(self) -> IntValue:
        return super().config

    def get_value(self) -> Union[int, InvalidValue]:
        if not self._input_entry:
            raise RuntimeError("input entry not created yet")
        try:
            return self._input_entry.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[int, InvalidValue]:
        if not self._input_entry:
            raise RuntimeError("input entry not created yet")
        try:
            self._input_entry.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "IntValueWidget":
        if self._build_flag:
            return self
        self._input_entry = IntEntry(self)
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
