import dataclasses
import inspect
from enum import Enum
from tkinter import Widget
from tkinter.ttk import LabelFrame
from typing import Type, Any, Union, Dict, Optional

from pyguiadapterlite.components.singlechoice import SingleChoiceBox
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidgetConfig,
    BaseParameterWidget,
    InvalidValue,
)
from pyguiadapterlite.core.fn import ParameterInfo
from pyguiadapterlite.utils import is_subclass_of


@dataclasses.dataclass(frozen=True)
class EnumValue(BaseParameterWidgetConfig):
    default_value: Union[Enum, str, None] = None
    columns: int = 1
    content_title: str = ""
    hide_label: bool = True

    enum_class: Optional[Type[Enum]] = None

    @classmethod
    def target_widget_class(cls) -> Type["EnumValuedWidget"]:
        return EnumValuedWidget


class EnumValuedWidget(BaseParameterWidget):

    ConfigClass = EnumValue

    def __init__(
        self,
        parent: Widget,
        parameter_name: str,
        config: EnumValue,
    ):
        self._is_built = False
        self._value_widget: Optional[SingleChoiceBox] = None
        self._frame: Optional[LabelFrame] = None
        self._choices: Dict[str, Any] = {}
        self._enum_class: Optional[Type[Enum]] = None

        super().__init__(parent, parameter_name, config)

    @property
    def config(self) -> EnumValue:
        return super().config

    def get_value(self) -> Union[Any, InvalidValue]:
        try:
            value = self._value_widget.current
        except Exception as e:
            value = InvalidValue(raw_value=None, exception=e)
        return value

    def set_value(self, value: Any) -> Union[Any, InvalidValue]:
        try:
            if value is not None and not isinstance(value, self._enum_class):
                raise ValueError(
                    f"value `{value}` is not an instance of {self._enum_class}"
                )

            ret = self._value_widget.select(value)
            if not ret:
                raise ValueError(f"value `{value}` not in choices")
        except Exception as e:
            return InvalidValue(raw_value=value, exception=e)
        return value

    def build(self) -> "BaseParameterWidget":
        if self._is_built:
            return self

        if not self.config.enum_class:
            raise ValueError("enum class not specified")

        all_enums = self.config.enum_class.__members__
        if not all_enums:
            raise ValueError("enum class has no members")

        self._frame = LabelFrame(self, text=self._config.content_title or self.label)
        self._frame.pack(fill="both", expand=True, padx=1, pady=1)

        choices = {str(name): value for name, value in all_enums.items()}
        self._choices = choices
        self._enum_class = self.config.enum_class
        self._value_widget = SingleChoiceBox(
            self._frame, columns=self.config.columns, choices=choices
        )

        self._value_widget.pack(fill="both", expand=True)
        self.color_flash_effect.set_target(self)
        self._is_built = True
        self.set_value(self.config.default_value)
        return self

    @classmethod
    def on_post_process_config(
        cls,
        config: EnumValue,
        parameter_name: str,
        parameter_info: "ParameterInfo",
    ) -> BaseParameterWidgetConfig:
        if inspect.isclass(config.enum_class) and issubclass(config.enum_class, Enum):
            return config
        assert inspect.isclass(parameter_info.type) and issubclass(
            parameter_info.type, Enum
        )
        return dataclasses.replace(config, enum_class=parameter_info.type)

    @classmethod
    def _enum_type_mapping_rule(
        cls, parameter_info: ParameterInfo
    ) -> Optional[Type["EnumValuedWidget"]]:
        if is_subclass_of(parameter_info.type, Enum):
            return cls
        return None
