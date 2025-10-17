import dataclasses
from tkinter import Widget, Scale
from typing import Type, Any, Optional, Union

from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error

from pyguiadapterlite.types.floats.ttkscale import (
    ScaleFloatValue,
    FloatScale,
    ScaleFloatValueWidget,
)

DEFAULT_STEP = 0.5
DEFAULT_TICK_INTERVAL = 10
DEFAULT_DIGITS = 0


@dataclasses.dataclass(frozen=True)
class ScaleFloatValue2(ScaleFloatValue):
    step: float = DEFAULT_STEP
    digits: int = DEFAULT_DIGITS
    tick_interval: float = DEFAULT_TICK_INTERVAL

    def __post_init__(self):
        # 验证参数合理性
        super().__post_init__()
        if self.step <= 0:
            raise ValueError("step must be positive")

    @classmethod
    def target_widget_class(cls) -> Type["ScaleFloatValueWidget2"]:
        return ScaleFloatValueWidget2


class FloatScale2(Scale):
    def __init__(self, parent: "ScaleFloatValueWidget2", **kwargs):
        self._parent = parent
        config = parent.config

        # 设置Scale的范围和分辨率
        super().__init__(
            parent,
            from_=config.min_value,
            to=config.max_value,
            resolution=config.step,
            orient="horizontal",
            digits=config.digits,
            showvalue=config.show_value,
            tickinterval=config.tick_interval,
            **kwargs,
        )

        # 初始值
        self.set(config.default_value)

    @property
    def value(self) -> float:
        return FloatScale.get_(self.get)

    @value.setter
    def value(self, value: float) -> None:
        FloatScale.set_(value, self._parent.config, self.set)


class ScaleFloatValueWidget2(BaseParameterWidget):
    ConfigClass = ScaleFloatValue2

    def __init__(self, parent: Widget, parameter_name: str, config: ScaleFloatValue2):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_widget: Optional[FloatScale2] = None

    @property
    def config(self) -> ScaleFloatValue2:
        return super().config

    def get_value(self) -> Union[float, InvalidValue]:
        return ScaleFloatValueWidget.get_(self)

    def set_value(self, value: Any) -> Union[float, InvalidValue]:
        return ScaleFloatValueWidget.set_(self, value)

    def build(self) -> "ScaleFloatValueWidget2":
        if self._build_flag:
            return self

        # 创建滑块
        self._input_widget = FloatScale2(self)
        self._input_widget.pack(fill="x", expand=True, padx=1, pady=1)
        # 设置初始值
        self._input_widget.value = self._config.default_value
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
