import dataclasses
from tkinter import Widget
from tkinter.ttk import LabelFrame
from typing import Type, Any, Union, List, Dict, Optional

from pyguiadapterlite.components.singlechoice import SingleChoiceBox
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidgetConfig,
    BaseParameterWidget,
    InvalidValue,
)
from pyguiadapterlite.core.fn import ParameterInfo


@dataclasses.dataclass(frozen=True)
class SingleChoiceValue(BaseParameterWidgetConfig):
    default_value: Any = None
    choices: Union[List[Any], Dict[str, Any]] = dataclasses.field(default_factory=list)
    columns: int = 1
    content_title: str = ""
    hide_label: bool = True

    @classmethod
    def target_widget_class(cls) -> Type["SingleChoiceValueWidget"]:
        return SingleChoiceValueWidget


class SingleChoiceValueWidget(BaseParameterWidget):

    ConfigClass = SingleChoiceValue

    def __init__(
        self,
        parent: Widget,
        parameter_name: str,
        config: SingleChoiceValue,
    ):
        self._is_built = False
        self._value_widget: Optional[SingleChoiceBox] = None
        self._frame: Optional[LabelFrame] = None
        super().__init__(parent, parameter_name, config)

    @property
    def config(self) -> SingleChoiceValue:
        return super().config

    def get_value(self) -> Union[Any, InvalidValue]:
        try:
            value = self._value_widget.current
        except Exception as e:
            value = InvalidValue(raw_value=None, exception=e)
        return value

    def set_value(self, value: Any) -> Union[Any, InvalidValue]:
        try:
            ret = self._value_widget.select(value)
            if not ret:
                raise ValueError(f"value `{value}` not in choices")
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

        self._value_widget = SingleChoiceBox(
            self._frame, columns=self.config.columns, choices=self.config.choices
        )
        ret = self._value_widget.select(self.config.default_value)
        if not ret:
            raise ValueError(
                f"default value {self.config.default_value} not in choices"
            )
        self._value_widget.pack(fill="both", expand=True)
        self.color_flash_effect.set_target(self)
        self._is_built = True
        return self

    @classmethod
    def on_post_process_config(
        cls,
        config: SingleChoiceValue,
        parameter_name: str,
        parameter_info: "ParameterInfo",
    ) -> BaseParameterWidgetConfig:
        if not config.choices and len(parameter_info.type_args) > 0:
            return dataclasses.replace(config, choices=parameter_info.type_args.copy())
        return config
