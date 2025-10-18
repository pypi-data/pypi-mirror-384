import dataclasses
from tkinter import BooleanVar
from typing import List, Union, Optional, Callable, ForwardRef

from pyguiadapterlite.utils import _error

BaseWindow_ = ForwardRef("BaseWindow")
Action_ = ForwardRef("Action")

ActionTriggeredCallback = Callable[[BaseWindow_, Action_], None]
ActionToggledCallback = Callable[[BaseWindow_, Action_, bool], None]


@dataclasses.dataclass
class Action(object):
    """该类用于创建动作（`Action`），在工具栏（`ToolBar`）中一个`Action`代表一个工具栏按钮，在菜单（`Menu`）中，一个`Action`代表一个菜单项。"""

    text: str
    """动作（`Action`）的描述性文本。"""

    on_triggered: Optional[ActionTriggeredCallback] = None
    """回调函数，在动作（`Action`）被触发时回调。"""

    enabled: bool = True
    """动作（`Action`）是否处于启用状态。"""

    checkable: bool = False
    """动作（`Action`）是否为**`可选中动作`**。`可选中动作`具有`选中`和`未选中`两种状态，在状态发生切换时，将触发`on_toggled`回调函数。"""

    initial_checked: bool = False
    """动作（`Action`）初始是否处于`选中`状态。"""

    shortcut: Optional[str] = None
    """动作（`Action`）的快捷键，例如：Control+o。"""

    data: Optional[object] = None
    """用户自定义数据。"""

    def bind_checked_var(self, checked_var: BooleanVar):
        setattr(self, "__checked__", checked_var)

    def is_checked(self) -> bool:
        if not self.checkable:
            return False
        checked_var = getattr(self, "__checked__", None)
        if isinstance(checked_var, BooleanVar):
            return checked_var.get()
        else:
            _error("checked variable not bind to action")
            return False

    def set_checked(self, checked: bool):
        if not self.checkable:
            return
        checked_var = getattr(self, "__checked__", None)
        if not checked_var:
            _error("checked variable not bind to action")
            return
        checked_var.set(checked)

    def get_exclusive_group_id(self) -> Optional[int]:
        if not self.checkable:
            return None
        return getattr(self, "__group_id__", None)

    def add_to_exclusive_group(self, group_id: int):
        if not self.checkable:
            return
        setattr(self, "__group_id__", group_id)


@dataclasses.dataclass(frozen=True)
class Separator(object):
    """代表了一个分割符，开发者可以用其来分割工具栏上和菜单栏上的动作（`Action`）"""

    pass


@dataclasses.dataclass(frozen=True)
class Menu(object):
    """该类用于配置窗口菜单栏上的菜单。"""

    title: str
    """菜单的标题。"""

    actions: List[Union[Action, Separator, "Menu"]]
    """菜单下的菜单项（`Action`）、分隔符（`Separator`）或子菜单（`Menu`）"""

    tear_off_enabled: bool = True
    """菜单可以被“撕下”。为`True`时，菜单将包含一个特殊的“撕下”项（通常显示为菜单顶部的虚线），当触发它时，会创建一个菜单的副本。这个“撕下”的副本
    会存在于一个单独的窗口中，并且包含与原始菜单相同的菜单项。"""

    exclusive: bool = False
    """是否将菜单下的菜单项（`Action`）添加到一个互斥组中。只有当前菜单下`checkable`属性为`True`的菜单项（`Action`）才会被添加的互斥组中。"""

    def remove_action(self, action: Union[str, Action, Separator, "Menu"]):
        if isinstance(action, str):
            for action_ in self.actions:
                if isinstance(action_, Action):
                    if action_.text == action:
                        action = action_
                        break
                if isinstance(action_, Menu):
                    if action_.title == action:
                        action = action_
                        break
            if action in self.actions:
                self.actions.remove(action)
            return
        if action in self.actions:
            self.actions.remove(action)
            return
