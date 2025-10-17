import dataclasses
from abc import abstractmethod
from inspect import isclass
from tkinter import Frame, Widget
from typing import Any, TypeVar, Type, Optional, Union

from pyguiadapterlite.utils import _warning


class SetValueError(Exception):
    def __init__(self, raw_value: Any, msg: Optional[str]):
        super().__init__(msg)
        self.raw_value = raw_value


class GetValueError(Exception):
    def __init__(self, raw_value: Any, msg: Optional[str]):
        super().__init__(msg)
        self.raw_value = raw_value


class InvalidValue(object):
    def __init__(
        self, raw_value: Any, msg: Optional[str] = None, exception: Any = None
    ):
        self.raw_value = raw_value
        self.msg = msg
        self.exception = exception


class ColorFlashEffect(object):
    def __init__(
        self,
        target_widget: Optional[Frame],
        default_flash_color="red",
        default_duration=1000,
        default_flash_count=3,
    ):
        self._target: Optional[Frame] = None
        self._default_flash_color = default_flash_color
        self._default_duration = default_duration
        self._default_flash_count = default_flash_count

        self._original_bg: Optional[str] = None
        self._flash_count = 0

        self.set_target(target_widget)

    def set_target(self, target: Optional[Widget]):
        self._target = target
        if not self._target:
            self._original_bg = None
            return
        self._original_bg = target.cget("background")

    def start(
        self,
        color: Optional[str] = None,
        duration: Optional[int] = None,
        count: Optional[int] = None,
    ):
        if not self._target:
            _warning("target widget is not set, this effect will not take effect")
            return
        color = color or self._default_flash_color
        duration = duration or self._default_duration
        count = count or self._default_flash_count
        self._flash_count = 0
        self._flash(color, duration, count)

    def _flash(self, color: str, duration: int, count: int):
        if self._flash_count < count * 2:
            if self._flash_count % 2 == 0:
                self._target.configure(background=color)
            else:
                self._target.configure(background=self._original_bg)

            self._flash_count += 1
            self._target.after(
                duration // (count * 2), self._flash, color, duration, count
            )
        else:
            self._target.configure(background=self._original_bg)


@dataclasses.dataclass(frozen=True)
class BaseParameterWidgetConfig(object):
    """值控件配置基类"""

    default_value: Any = None
    label: str = ""
    description: str = ""
    group: str = ""
    hide_label: bool = False

    # noinspection PyAbstractClass
    @classmethod
    @abstractmethod
    def target_widget_class(cls) -> Type["BaseParameterWidget"]:
        raise NotImplementedError()

    @classmethod
    def new(cls, **kwargs) -> "BaseParameterWidgetConfig":
        return cls(**kwargs)

    def serialize(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def deserialize(cls, json_obj: dict) -> "BaseParameterWidgetConfig":
        return cls.new(**json_obj)


_T = TypeVar("_T", bound=BaseParameterWidgetConfig)


class BaseParameterWidget(Frame):
    """所有参数控件（输入控件）类的基类"""

    ConfigClass: Type[BaseParameterWidgetConfig] = NotImplemented

    def __init__(self, parent: Widget, parameter_name: str, config: _T):
        super().__init__(parent)
        self._parameter_name = parameter_name
        self._config = config
        self._label = self._config.label or self._parameter_name
        self._description = self._config.description or ""

        self._color_flash_effect = ColorFlashEffect(self, "red", 800, 3)

    @property
    def parameter_name(self) -> str:
        return self._parameter_name

    @property
    def config(self) -> _T:
        return self._config

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def color_flash_effect(self) -> ColorFlashEffect:
        return self._color_flash_effect

    # noinspection PyAbstractClass
    @abstractmethod
    def get_value(self) -> Union[Any, InvalidValue]:
        """获取控件的值"""
        pass

    # noinspection PyAbstractClass
    @abstractmethod
    def set_value(self, value: Any) -> Union[Any, InvalidValue]:
        """设置控件的值"""
        pass

    # noinspection PyAbstractClass
    @abstractmethod
    def build(self) -> "BaseParameterWidget":
        pass

    @classmethod
    def new(
        cls,
        parent: Widget,
        parameter_name: str,
        config: _T,
    ):
        return cls(parent, parameter_name, config).build()

    def start_invalid_value_effect(self):
        self._color_flash_effect.start()

    @classmethod
    def on_post_process_config(
        cls,
        config: BaseParameterWidgetConfig,
        parameter_name: str,
        parameter_info: "ParameterInfo",
    ) -> BaseParameterWidgetConfig:
        _ = parameter_name, parameter_info  # unused
        return config


def is_parameter_widget_class(o: Any) -> bool:
    return o is not None and isclass(o) and issubclass(o, BaseParameterWidget)
