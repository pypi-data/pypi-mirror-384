import dataclasses
from abc import abstractmethod
from typing import Callable, Any, Type, Dict, Optional, List

from pyguiadapterlite.windows.basewindow import BaseWindowConfig
from pyguiadapterlite.components.valuewidget import BaseParameterWidgetConfig


class ExecuteStateListener(object):
    def before_execute(self, fn_info: "FnInfo", arguments: Dict[str, Any]) -> None:
        pass

    def on_execute_start(self, fn_info: "FnInfo", arguments: Dict[str, Any]) -> None:
        pass

    def on_execute_finish(
        self,
        fn_info: "FnInfo",
        arguments: Dict[str, Any],
        return_value: Any,
        exception: Optional[BaseException],
    ) -> None:
        pass


# noinspection PyAbstractClass
class BaseFunctionExecutor(object):

    def __init__(self, listener: Optional[ExecuteStateListener] = None):
        self._listener = listener

    @property
    def listener(self) -> Optional[ExecuteStateListener]:
        return self._listener

    @abstractmethod
    def execute(self, fn_info: "FnInfo", arguments: Optional[Dict[str, Any]] = None):
        pass

    @property
    @abstractmethod
    def is_executing(self) -> bool:
        pass

    @abstractmethod
    def try_cancel(self):
        pass

    @property
    @abstractmethod
    def is_cancelled(self) -> bool:
        pass


@dataclasses.dataclass
class ParameterInfo(object):
    default_value: Any
    type: Type
    typename: str
    type_args: List[Any] = dataclasses.field(default_factory=list)
    description: str = None


@dataclasses.dataclass
class FnInfo(object):
    fn: Callable
    fn_name: Optional[str] = None
    display_name: Optional[str] = None
    document: Optional[str] = ""
    icon: Optional[str] = None
    parameter_configs: Dict[str, BaseParameterWidgetConfig] = dataclasses.field(
        default_factory=dict
    )
    cancelable: bool = False
    executor: Optional[Type[BaseFunctionExecutor]] = None
    capture_system_exit_exception: bool = True
    window_config: Optional[BaseWindowConfig] = None
    parameters_validator: Optional[
        Callable[[str, Dict[str, object]], Optional[Dict[str, str]]]
    ] = None
    parameter_infos: Dict[str, ParameterInfo] = dataclasses.field(default_factory=dict)

    def get_function_name(self) -> str:
        if self.fn_name:
            return self.fn_name
        return self.fn.__name__


class ParameterError(Exception):
    def __init__(self, parameter_name: str, message: str):
        self._parameter_name: str = parameter_name
        self._message: str = message
        super().__init__(message)

    @property
    def parameter_name(self) -> str:
        return self._parameter_name

    @property
    def message(self) -> str:
        return self._message
