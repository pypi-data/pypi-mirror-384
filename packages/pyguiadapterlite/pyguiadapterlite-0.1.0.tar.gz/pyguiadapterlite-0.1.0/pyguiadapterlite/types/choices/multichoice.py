import dataclasses
from tkinter import Widget
from tkinter.ttk import LabelFrame
from typing import Type, Any, Union, List, Dict, Optional, Iterable

from pyguiadapterlite.components.multiplechoice import MultipleChoiceBox
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidgetConfig,
    BaseParameterWidget,
    InvalidValue,
)
from pyguiadapterlite.core.fn import ParameterInfo


@dataclasses.dataclass(frozen=True)
class MultiChoiceValue(BaseParameterWidgetConfig):
    default_value: Iterable[Any] = dataclasses.field(default_factory=list)
    choices: Union[Dict[str, Any], Iterable[Any]] = dataclasses.field(
        default_factory=list
    )
    columns: int = 2
    content_title: str = ""
    hide_label: bool = True

    @classmethod
    def target_widget_class(cls) -> Type["MultiChoiceValueWidget"]:
        return MultiChoiceValueWidget


class MultiChoiceValueWidget(BaseParameterWidget):

    ConfigClass = MultiChoiceValue

    def __init__(
        self,
        parent: Widget,
        parameter_name: str,
        config: MultiChoiceValue,
    ):
        self._is_built = False
        self._value_widget: Optional[MultipleChoiceBox] = None
        self._frame: Optional[LabelFrame] = None
        super().__init__(parent, parameter_name, config)

    @property
    def config(self) -> MultiChoiceValue:
        return super().config

    def get_value(self) -> Union[List[Any], InvalidValue]:
        try:
            value = self._value_widget.current_values.copy()
        except Exception as e:
            value = InvalidValue(raw_value=None, exception=e)
        return value

    def set_value(self, value: List[Any]) -> Union[Any, InvalidValue]:
        try:
            self._value_widget.select(value.copy())
        except Exception as e:
            return InvalidValue(raw_value=value, exception=e)
        return value

    def build(self) -> "BaseParameterWidget":
        if self._is_built:
            return self
        if not self.config.choices:
            raise ValueError("no choices provided")

        self._frame = LabelFrame(self, text=self._config.content_title or self.label)
        self._frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._value_widget = MultipleChoiceBox(
            self._frame, columns=self.config.columns, choices=self.config.choices
        )
        self._value_widget.select(self.config.default_value)
        self._value_widget.pack(fill="both", expand=True)
        self.color_flash_effect.set_target(self)
        self._is_built = True
        return self

    @classmethod
    def on_post_process_config(
        cls,
        config: MultiChoiceValue,
        parameter_name: str,
        parameter_info: "ParameterInfo",
    ) -> BaseParameterWidgetConfig:
        if not config.choices:
            if (
                isinstance(config.default_value, (list, tuple, set, dict))
                and len(config.default_value) > 0
            ):
                if isinstance(config.default_value, dict):
                    choices = config.default_value.copy()
                else:
                    choices = list(config.default_value)
                config = dataclasses.replace(config, choices=choices, default_value=[])
        return config
