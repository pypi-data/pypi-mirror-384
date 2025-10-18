import dataclasses
import platform
from collections import OrderedDict
from tkinter import Tk
from typing import Callable, Optional, Dict, Union, Tuple, Type, List

from pyguiadapterlite.components.menus import Menu, Separator
from pyguiadapterlite.core.fn import FnInfo, ParameterInfo, BaseFunctionExecutor
from pyguiadapterlite.windows.fnexecwindow import FnExecuteWindowConfig, FnExecuteWindow
from pyguiadapterlite.core.fnparser import FnParser
from pyguiadapterlite.windows.fnselectwindow import FnSelectWindowConfig, FnSelectWindow
from pyguiadapterlite.core.registry import ParameterWidgetFactory
from pyguiadapterlite.core.threaded import ThreadedExecutor
from pyguiadapterlite.core.ucontext import UContext
from pyguiadapterlite.utils import (
    _error,
    enable_dpi_awareness,
    _warning,
    _info,
)
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidgetConfig,
    BaseParameterWidget,
    is_parameter_widget_class,
)


class GUIAdapter(object):
    def __init__(self, *, hdpi_mode: bool = False, scale_factor_divisor: int = 100):
        self._hdpi_mode = hdpi_mode
        self._scale_factor_divisor = scale_factor_divisor
        self._functions: Dict[Callable, FnInfo] = {}
        self._fn_parser = FnParser()
        self._select_window: Optional[FnSelectWindow] = None
        self._execute_window: Optional[FnExecuteWindow] = None

    def add(
        self,
        fn: Callable,
        display_name: Optional[str] = None,
        icon: Optional[str] = None,
        document: Optional[str] = None,
        cancelable: bool = False,
        *,
        widget_configs: Optional[
            Dict[str, Union[BaseParameterWidgetConfig, dict]]
        ] = None,
        window_config: Optional[FnExecuteWindowConfig] = None,
        window_menus: Optional[List[Union[Menu, Separator]]] = None,
        parameters_validator: Optional[
            Callable[[str, Dict[str, object]], Optional[Dict[str, str]]]
        ] = None,
        capture_system_exit_exception: bool = True,
        function_executor_class: Type[BaseFunctionExecutor] = ThreadedExecutor,
        ignore_self_parameter: bool = True,
        enable_progressbar: bool = False,
        enable_progress_label: bool = False,
    ) -> None:
        doc, params = self._fn_parser.parse(fn, ignore_self_param=ignore_self_parameter)

        if window_config is None:
            window_config = FnExecuteWindowConfig(
                menus=window_menus,
                enable_progressbar=enable_progressbar,
                enable_progress_label=enable_progress_label,
            )
        else:
            if window_menus is not None:
                window_config = dataclasses.replace(window_config, menus=window_menus)

        fn_info = FnInfo(
            fn=fn,
            fn_name=fn.__name__,
            display_name=display_name or fn.__name__,
            icon=icon,
            document=document or doc,
            cancelable=cancelable,
            capture_system_exit_exception=capture_system_exit_exception,
            window_config=window_config,
            executor=function_executor_class,
            parameters_validator=parameters_validator,
            parameter_infos=params,
        )
        user_widget_configs = widget_configs or {}
        parsed_widget_configs = self._fn_parser.parse_widget_configs(fn_info, params)
        final_widget_configs: Dict[str, BaseParameterWidgetConfig] = (
            self._merge_widget_configs(
                parameters=params,
                parsed_configs=parsed_widget_configs,
                user_configs=user_widget_configs,
            )
        )
        fn_info.parameter_configs = final_widget_configs
        self._functions[fn] = fn_info

    def remove(self, fn: Callable) -> None:
        if fn in self._functions:
            del self._functions[fn]

    def exists(self, fn: Callable) -> bool:
        return fn in self._functions

    # 这个方法会启动一个mainloop，这意味着这是一个阻塞方法
    # 该方法将一直阻塞到根窗口关闭
    def run(
        self,
        *,
        show_select_window: bool = False,
        select_window_config: Optional[FnSelectWindowConfig] = None,
        select_window_menus: Optional[List[Union[Menu, Separator]]] = None,
    ) -> None:
        if len(self._functions) == 0:
            raise SystemExit("A least one function must be added before running.")

        if len(self._functions) > 1:
            show_select_window = True

        UContext.reset()
        root = Tk()
        root.withdraw()
        if self._hdpi_mode:
            if platform.system() == "Windows":
                _info(
                    "try to enable dpi awareness of current process to support high-DPI mode on Windows."
                )
                enable_dpi_awareness(root, self._scale_factor_divisor)
            else:
                _warning("high-DPI mode is not supported on this platform.")
        UContext.app_started(root)
        if show_select_window:
            if select_window_config is None:
                select_window_config = FnSelectWindowConfig(menus=select_window_menus)
            else:
                if select_window_menus is not None:
                    select_window_config = dataclasses.replace(
                        select_window_config, menus=select_window_menus
                    )
            self._show_select_window(select_window_config)
        else:
            self._show_execute_window(list(self._functions.values())[0])
        root.deiconify()
        root.mainloop()
        self._select_window = None
        self._execute_window = None
        UContext.app_quit()

    def _show_select_window(
        self, select_window_config: Optional[FnSelectWindowConfig]
    ) -> None:
        self._select_window = FnSelectWindow(
            parent=UContext.app_instance(),
            function_list=list(self._functions.values()),
            config=select_window_config,
        )
        self._select_window.move_to_center()

    def _show_execute_window(self, fn_info: FnInfo) -> None:
        self._execute_window = FnExecuteWindow(
            parent=UContext.app_instance(), fn_info=fn_info
        )
        self._execute_window.move_to_center()

    def _merge_widget_configs(
        self,
        parameters: Dict[str, ParameterInfo],
        parsed_configs: Dict[str, Tuple[Optional[str], Optional[str], dict]],
        user_configs: Dict[str, Union[BaseParameterWidgetConfig, dict]],
    ) -> Dict[str, BaseParameterWidgetConfig]:
        final_widget_configs: Dict[str, BaseParameterWidgetConfig] = OrderedDict()
        for param_name, (
            parsed_widget_class_name,
            parsed_value_type_name,
            parsed_widget_config,
        ) in parsed_configs.items():
            assert isinstance(parsed_widget_class_name, (str, type(None)))
            assert isinstance(parsed_widget_config, dict)
            param_info = parameters.get(param_name, None)
            assert param_info is not None

            user_config = user_configs.get(param_name, None)

            if user_config is None:
                parsed_widget_class = self._get_widget_class_v2(
                    widget_class_name=parsed_widget_class_name,
                    value_type_name=parsed_value_type_name,
                    param_info=param_info,
                    default_value=None,
                )
                widget_class = parsed_widget_class
                if not is_parameter_widget_class(widget_class):
                    _error(
                        f"unable to find widget class for parameter `{param_name}` for parsed widget configs."
                    )
                    print("parsed widget configs:")
                    print(parsed_widget_config)
                    raise ValueError(
                        f"unable to find widget class for parameter `{param_name}`"
                    )

                widget_config = widget_class.ConfigClass.new(
                    **self._remove_undefined_fields(
                        widget_class.ConfigClass, parsed_widget_config
                    )
                )
                final_widget_configs[param_name] = widget_config

            elif isinstance(user_config, dict):
                parsed_widget_class = self._get_widget_class_v2(
                    widget_class_name=parsed_widget_class_name,
                    value_type_name=parsed_value_type_name,
                    param_info=param_info,
                    default_value=None,
                )
                conf_widget_class_name = user_config.pop("widget_class", None)
                conf_value_type_name = user_config.pop("__type__", None)
                user_widget_class = self._get_widget_class_v2(
                    widget_class_name=conf_widget_class_name,
                    value_type_name=conf_value_type_name,
                    param_info=param_info,
                    default_value=user_config.get("default_value", None),
                )
                widget_class = user_widget_class or parsed_widget_class
                if not is_parameter_widget_class(widget_class):
                    _error(
                        f"unable to find widget class for parameter `{param_name}` for parsed widget configs and user-provided configs."
                    )
                    print("parsed widget configs:")
                    print(parsed_widget_config)
                    print("user-provided configs:")
                    print(user_config)
                    raise ValueError(
                        f"unable to find widget class for parameter `{param_name}`"
                    )

                # override parsed config with user config
                tmp = self._remove_undefined_fields(
                    widget_class.ConfigClass, {**parsed_widget_config, **user_config}
                )
                widget_config = widget_class.ConfigClass.new(**tmp)
                final_widget_configs[param_name] = widget_config
            elif isinstance(user_config, BaseParameterWidgetConfig):
                # when user_config is a BaseParameterWidgetConfig instance
                final_widget_configs[param_name] = user_config
            else:
                raise ValueError(f"unsupported user_config type: {type(user_config)}")
        return final_widget_configs

    @staticmethod
    def _get_widget_class(
        widget_class_name: Optional[str], param_info: ParameterInfo
    ) -> Optional[Type[BaseParameterWidget]]:
        if widget_class_name is not None:
            widget_class_name = widget_class_name.strip()
        if widget_class_name:
            return ParameterWidgetFactory.find_by_widget_class_name(widget_class_name)
        widget_class = ParameterWidgetFactory.find_by_typename(param_info.typename)
        if is_parameter_widget_class(widget_class):
            return widget_class
        return ParameterWidgetFactory.find_by_rule(param_info)

    @staticmethod
    def _get_widget_class_v2(
        widget_class_name: Optional[str],
        value_type_name: Optional[str],
        param_info: Optional[ParameterInfo],
        default_value: object,
    ):
        if widget_class_name:
            widget_class_name = widget_class_name.strip()
            if widget_class_name:
                return ParameterWidgetFactory.find_by_widget_class_name(
                    widget_class_name
                )
        if value_type_name:
            value_type_name = value_type_name.strip()
            if value_type_name:
                return ParameterWidgetFactory.find_by_typename(value_type_name)

        if param_info:
            widget_class = ParameterWidgetFactory.find_by_typename(param_info.typename)
            if is_parameter_widget_class(widget_class):
                return widget_class

        if default_value is not None:
            value_type = type(default_value)
            widget_class = ParameterWidgetFactory.find_by_typename(value_type.__name__)
            if is_parameter_widget_class(widget_class):
                return widget_class

        return ParameterWidgetFactory.find_by_rule(param_info)

    @staticmethod
    def _remove_undefined_fields(
        widget_config_class: Type[BaseParameterWidgetConfig], config_dict: dict
    ):
        defined_fields = set(
            field.name for field in dataclasses.fields(widget_config_class)
        )
        return {k: v for k, v in config_dict.items() if k in defined_fields}
