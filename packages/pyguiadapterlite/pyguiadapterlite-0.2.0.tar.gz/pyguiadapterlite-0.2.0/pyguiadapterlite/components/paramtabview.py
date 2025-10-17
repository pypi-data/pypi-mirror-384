from tkinter import Widget, Tk, Toplevel
from typing import Union, Generator, Tuple, Optional, Any, Dict

from pyguiadapterlite.components.scrollarea import (
    ParameterWidgetArea,
    ParameterNotFound,
)
from pyguiadapterlite.components.tabview import TabView, TabIdNotFoundError
from pyguiadapterlite.utils import _warning
from pyguiadapterlite.components.valuewidget import (
    InvalidValue,
    BaseParameterWidgetConfig,
)

DEFAULT_GROUP_NAME = "Main"


class ParameterGroupTabView(TabView):
    def __init__(
        self,
        parent: Union[Widget, Tk, Toplevel],
        default_group_name: str = DEFAULT_GROUP_NAME,
        **kwargs,
    ):
        self._default_group_name = default_group_name
        super().__init__(parent, **kwargs)

    def _create_parameter_group(self, group_name: str) -> ParameterWidgetArea:
        if not self.has_tab(group_name):
            group_tab = self.create_parameter_tab()
            self.add_tab(group_name, group_name, group_tab)
            return group_tab
        tab = self.get_tab(group_name)
        if not isinstance(tab, ParameterWidgetArea):
            raise ValueError(
                f"tab `{group_name}` already exists but is not a ParameterWidgetArea."
            )
        return tab

    def add_tab(self, tab_id: str, tab_name: str, content: Widget, **kwargs) -> None:
        if tab_id == self._default_group_name and (
            not isinstance(content, ParameterWidgetArea)
        ):
            raise ValueError(
                f"tab_id `{self._default_group_name}` is reserved for ParameterWidgetArea."
            )
        return super().add_tab(tab_id, tab_name, content, **kwargs)

    @property
    def parameter_groups(self) -> Generator[Tuple[str, ParameterWidgetArea], Any, None]:
        for tab_id, tab in self._tabs.items():
            if isinstance(tab, ParameterWidgetArea):
                yield tab_id, tab

    def get_parameter_group(self, group_name: str) -> Optional[ParameterWidgetArea]:
        if not self.has_tab(group_name):
            raise TabIdNotFoundError(f"tab `{group_name}` not found.")
        tab = self.get_tab(group_name)
        if not isinstance(tab, ParameterWidgetArea):
            raise ValueError(f"tab `{group_name}` is not a ParameterWidgetArea.")
        return tab

    def remove_parameter_group(self, group_name: str):
        if not self.has_tab(group_name):
            raise TabIdNotFoundError(f"tab `{group_name}` not found.")
        tab = self.get_tab(group_name)
        if not isinstance(tab, ParameterWidgetArea):
            raise ValueError(f"tab `{group_name}` is not a ParameterWidgetArea.")
        self.remove_tab(group_name, destroy_content=True)

    def get_parameter_values_of_group(
        self, group_name: str
    ) -> Optional[Dict[str, Any]]:
        if not self.has_tab(group_name):
            raise None
        tab = self.get_tab(group_name)
        if not isinstance(tab, ParameterWidgetArea):
            raise ValueError(f"tab `{group_name}` is not a ParameterWidgetArea.")
        return tab.get_parameter_values()

    def get_parameter_values(self) -> Dict[str, Union[Any, InvalidValue]]:
        values = {}
        for group_name, group in self.parameter_groups:
            group_values = group.get_parameter_values()
            if group_values:
                values.update(group_values)
        return values

    def update_parameter_values(
        self, values: Dict[str, Any], ignore_not_exist: bool = True
    ) -> Dict[str, Union[Any, InvalidValue]]:
        ret = {}
        for group_name, group in self.parameter_groups:
            group_values = group.update_parameter_values(
                values, ignore_not_exist=ignore_not_exist
            )
            if group_values:
                ret.update(group_values)
        return ret

    def find_parameter_group(
        self, parameter_name: str
    ) -> Optional[ParameterWidgetArea]:
        for group_name, group in self.parameter_groups:
            if group.has_parameter(parameter_name):
                return group
        return None

    def get_parameter_group_name(self, parameter_name: str) -> Optional[str]:
        for group_name, group in self.parameter_groups:
            if group.has_parameter(parameter_name):
                return group_name
        return None

    def has_parameter(self, parameter_name: str) -> bool:
        return bool(self.find_parameter_group(parameter_name))

    def show_error_effect(self, parameter_name: str):
        group = self.find_parameter_group(parameter_name)
        if not group:
            _warning(f"parameter `{parameter_name}` not found.")
            return
        self._notebook.select(group)
        parameter_widget = group.get_parameter_widget(parameter_name)
        if not parameter_widget:
            _warning(f"parameter widget for `{parameter_name}` not found.")
            return
        parameter_widget.start_invalid_value_effect()

    def add_parameter(self, parameter_name: str, config: BaseParameterWidgetConfig):
        group_name = config.group or self._default_group_name
        parameter_group = self._create_parameter_group(group_name)
        parameter_group.add_parameter(parameter_name, config)

    def remove_parameter(self, parameter_name: str):
        group = self.find_parameter_group(parameter_name)
        if not group:
            raise ParameterNotFound(f"parameter `{parameter_name}` not found.")
        group.remove_parameter(parameter_name)

    def clear_parameters(self):
        for group_name, group in self.parameter_groups:
            group.clear_parameters()

    def create_parameter_tab(self) -> ParameterWidgetArea:
        return ParameterWidgetArea(self._notebook)
