import dataclasses
from tkinter import Widget
from typing import Type, Any, Optional, Union, Literal

from pyguiadapterlite.components.textview import TextView
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error


@dataclasses.dataclass(frozen=True)
class TextValue(BaseParameterWidgetConfig):
    default_value: str = ""
    wrap: Literal["none", "char", "word"] = "word"
    default_menu: bool = True
    font: tuple = ("Arial", 11)
    height: int = 8

    @classmethod
    def target_widget_class(cls) -> Type["TextValueWidget"]:
        return TextValueWidget


class TextEdit(TextView):
    def __init__(self, parent: "TextValueWidget", **kwargs):
        super().__init__(
            parent,
            editable=True,
            wrap=parent.config.wrap,
            height=parent.config.height,
            default_menu=parent.config.default_menu,
            font=parent.config.font,
            **kwargs,
        )

    @property
    def value(self) -> Union[str, InvalidValue]:
        return self.get_text()

    @value.setter
    def value(self, value: Any) -> Optional[InvalidValue]:
        self.set_text(str(value))


class TextValueWidget(BaseParameterWidget):
    ConfigClass = TextValue

    def __init__(self, parent: Widget, parameter_name: str, config: TextValue):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_widget: Optional[TextEdit] = None

    @property
    def config(self) -> TextValue:
        return super().config

    def get_value(self) -> Union[int, InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            return self._input_widget.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[int, InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            self._input_widget.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "TextValueWidget":
        if self._build_flag:
            return self
        self._input_widget = TextEdit(self)
        self.color_flash_effect.set_target(self)
        self._input_widget.pack(side="left", fill="x", expand=True, padx=1, pady=1)
        self._input_widget.value = self._config.default_value
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
