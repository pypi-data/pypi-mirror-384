import dataclasses
from pathlib import Path
from tkinter import Menu as TkMenu, BooleanVar
from tkinter import Tk, Toplevel
from typing import Tuple, Optional, Any, Union, List, Dict

from pyguiadapterlite.components.menus import Menu, Separator, Action
from pyguiadapterlite.utils import _warning, _exception, _error


class ParameterGroupNameNotAvailableError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class BaseWindowConfig(object):
    title: str = ""
    icon: Optional[str] = None
    size: Tuple[int, int] = (800, 605)
    position: Tuple[Optional[int], Optional[int]] = (None, None)
    always_on_top: bool = False
    menus: Optional[List[Union[Menu, Separator]]] = None


class BaseWindow(object):
    def __init__(self, parent: Union[Tk, Toplevel], config: BaseWindowConfig):
        self._parent = parent
        self._config = config
        size = config.size
        position = config.position
        self._parent.geometry(
            f"{size[0]}x{size[1]}{f'+{position[0]}+{position[1]}' if position[0] and position[1] else ''}"
        )
        self._parent.title(config.title)
        icon = config.icon
        if icon:
            icon = Path(icon)
            if not icon.is_file():
                _warning(f"icon file `{icon}` not found, using default icon.")
            else:
                self._parent.iconbitmap(icon.as_posix())

        self._menu_bar: Optional[TkMenu] = None
        self._exclusive_groups: Dict[int, List[Action]] = {}

        self.create_main_area()
        self.create_left_area()
        self.create_right_area()
        self.create_bottom_area()
        self.create_main_menu()
        self.create_status_bar()

        self._parent.protocol("WM_DELETE_WINDOW", self.on_close)
        self.set_always_on_top(config.always_on_top)

    @property
    def parent(self) -> Union[Tk, Toplevel]:
        return self._parent

    @property
    def config(self) -> BaseWindowConfig:
        return self._config

    @property
    def menus(self) -> List[Menu]:
        return [menu for menu in self._config.menus if isinstance(menu, Menu)]

    def create_main_area(self) -> Any:
        pass

    def create_bottom_area(self) -> Any:
        pass

    def create_left_area(self) -> Any:
        pass

    def create_right_area(self) -> Any:
        pass

    def create_status_bar(self):
        pass

    def create_main_menu(self) -> None:
        if not self._config.menus:
            return
        # 创建主菜单栏
        menu_bar = TkMenu(self._parent)
        # 遍历菜单配置并创建菜单
        for menu_item in self._config.menus:
            if isinstance(menu_item, Separator):
                # 在菜单栏中添加分隔符（如果有需要的话）
                # 注意：在顶层菜单栏中通常不直接添加分隔符，所以这里跳过
                continue
            elif isinstance(menu_item, Menu):
                # 创建子菜单
                submenu = self._create_submenu(menu_bar, menu_item)
                # 将子菜单添加到菜单栏
                menu_bar.add_cascade(label=menu_item.title, menu=submenu)
        # 将菜单栏设置到窗口
        self._parent.config(menu=menu_bar)
        self._menu_bar = menu_bar

    def _create_submenu(self, parent_menu: TkMenu, menu_config: Menu) -> TkMenu:
        """
        创建子菜单（递归处理嵌套菜单）
        """
        # 创建菜单，设置 tearoff 属性
        menu = TkMenu(parent_menu, tearoff=1 if menu_config.tear_off_enabled else 0)
        for i, action in enumerate(menu_config.actions):
            if isinstance(action, Separator):
                menu.add_separator()
            elif isinstance(action, Menu):
                # 递归创建子菜单
                submenu = self._create_submenu(menu, action)
                menu.add_cascade(label=action.title, menu=submenu)
            elif isinstance(action, Action):
                self._add_action(action, menu_config, menu)
            else:
                raise ValueError(f"unknown menu item type: {type(action)}")
        return menu

    def _add_action(self, action: Action, menu_config: Menu, menu: TkMenu):
        # 添加动作菜单项
        # 创建菜单项命令
        command = lambda action_=action: self._handle_action_triggered(action_)
        # 根据动作类型创建不同的菜单项
        if menu_config.exclusive and action.checkable:
            # 排他复选框
            self._create_checkable_menu(menu, action, command=command)
            exclusive_group_id = id(menu_config)
            exclusive_group = self._exclusive_groups.get(exclusive_group_id, None)
            if exclusive_group is None:
                self._exclusive_groups[exclusive_group_id] = [action]
            else:
                exclusive_group.append(action)
            action.add_to_exclusive_group(exclusive_group_id)
            self._handle_exclusive_group_changed(action)
        elif action.checkable:
            # 普通复选框
            self._create_checkable_menu(menu, action, command=command)
        else:
            # 普通菜单项
            menu.add_command(label=action.text, command=command)
        # 设置快捷键
        if action.shortcut:
            shortcut = action.shortcut.strip().replace("Ctrl", "Control")
            # 绑定快捷键到窗口
            self._bind_shortcut(shortcut, command)
        # 设置启用状态
        if not action.enabled:
            menu.entryconfig(menu.index("end"), state="disabled")

    @staticmethod
    def _create_checkable_menu(menu: TkMenu, item: Action, command):
        # 回退到普通复选框
        action_checked_var = BooleanVar()
        action_checked_var.set(item.initial_checked)
        menu.add_checkbutton(
            label=item.text,
            command=command,
            variable=action_checked_var,
        )
        item.bind_checked_var(action_checked_var)

    def _handle_action_triggered(self, action: Action) -> None:
        """
        处理动作触发
        """
        if not action.on_triggered:
            return
        try:
            action.on_triggered(self, action)
            self._handle_exclusive_group_changed(action)
        except Exception as e:
            _exception(e, f"error executing action '{action.text}'")

    def _handle_exclusive_group_changed(self, action: Action) -> None:
        if not action.checkable:
            return
        exclusive_group_id = action.get_exclusive_group_id()
        if exclusive_group_id is None:
            return
        exclusive_group = self._exclusive_groups.get(exclusive_group_id, None)
        if exclusive_group is None:
            _error(
                f"exclusive group with id '{exclusive_group_id}'  not found for action '{action.text}'"
            )
            return
        action_checked = action.is_checked()
        for other_action in exclusive_group:
            if other_action is action:
                continue
            if action_checked:
                other_action.set_checked(False)

    def _bind_shortcut(self, shortcut: str, command) -> None:
        """
        绑定快捷键
        """
        try:
            # 简单的快捷键绑定实现
            # 实际实现可能需要更复杂的快捷键解析
            self._parent.bind(f"<{shortcut}>", lambda event: command())
        except Exception as e:
            _exception(e, f"failed to bind shortcut '{shortcut}'")

    def move_to_center(self):
        """
        将窗口居中显示（自动获取窗口尺寸）
        """
        self.hide()
        # 更新窗口以确保获取正确的尺寸
        self._parent.update()

        # 获取窗口尺寸
        width = self._parent.winfo_width()
        height = self._parent.winfo_height()

        # 获取屏幕尺寸
        screen_width = self._parent.winfo_screenwidth()
        screen_height = self._parent.winfo_screenheight()

        # 计算位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # 设置位置
        self._parent.geometry(f"+{x}+{y}")
        self.show()

    def hide(self):
        self._parent.withdraw()

    def show(self):
        self._parent.deiconify()

    def set_always_on_top(self, on: bool):
        self._parent.wm_attributes("-topmost", on)

    def on_close(self):
        if self._parent:
            self._parent.destroy()
            self._parent = None
