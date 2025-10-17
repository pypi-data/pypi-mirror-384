import dataclasses
from tkinter import Widget, Frame
from tkinter.ttk import LabelFrame, Scrollbar, Frame, Button
from typing import Type, Any, Optional, Union, List, Literal, TypeVar

from pyguiadapterlite._messages import (
    MSG_MOVE_UP_BUTTON_TEXT,
    MSG_MOVE_DOWN_BUTTON_TEXT,
    MSG_REMOVE_ALL_BUTTON_TEXT,
    MSG_REMOVE_BUTTON_TEXT,
    MSG_EDIT_BUTTON_TEXT,
    MSG_REMOVE_CONFIRMATION,
    MSG_REMOVE_ALL_CONFIRMATION,
    MSG_NO_ITEMS_WARNING,
    MSG_NO_SELECTION_WARNING,
)
from pyguiadapterlite.components.listview import ListView
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    GetValueError,
    InvalidValue,
    SetValueError,
)
from pyguiadapterlite.utils import _error, show_warning, ask_yes_or_no


@dataclasses.dataclass(frozen=True)
class BaseStringListValue(BaseParameterWidgetConfig):
    default_value: List[str] = dataclasses.field(default_factory=list)
    content_title: str = ""
    select_mode: Literal["single", "multiple", "extended"] = "extended"
    scrollbar: Literal["horizontal", "vertical", "both", "none"] = "vertical"
    height: int = 0
    hide_label: bool = True
    double_click_to_edit: bool = True

    move_buttons: bool = True
    move_up_button_text: str = MSG_MOVE_UP_BUTTON_TEXT
    move_down_button_text: str = MSG_MOVE_DOWN_BUTTON_TEXT

    clear_button: bool = True
    cleat_button_text: str = MSG_REMOVE_ALL_BUTTON_TEXT

    remove_button: bool = True
    remove_button_text: str = MSG_REMOVE_BUTTON_TEXT

    edit_button: bool = True
    edit_button_text: str = MSG_EDIT_BUTTON_TEXT

    confirm_clear: bool = True
    clear_confirm_message: str = MSG_REMOVE_ALL_CONFIRMATION
    confirm_remove: bool = True
    remove_confirm_message: str = MSG_REMOVE_CONFIRMATION
    no_selection_message: str = MSG_NO_SELECTION_WARNING
    no_item_message: str = MSG_NO_ITEMS_WARNING

    @classmethod
    def target_widget_class(cls) -> Type["BaseStringListValueWidget"]:
        return BaseStringListValueWidget


class ScrollableListView(Frame):
    def __init__(
        self,
        parent: "BaseStringListBox",
        x_scrollbar: bool,
        y_scrollbar: bool,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._config: BaseStringListValue = parent.parent_config

        self._x_scrollbar: Optional[Scrollbar] = None
        self._y_scrollbar: Optional[Scrollbar] = None

        if x_scrollbar:
            self._x_scrollbar = Scrollbar(self, orient="horizontal")
            self._x_scrollbar.grid(row=1, column=0, sticky="ew")

        if y_scrollbar:
            self._y_scrollbar = Scrollbar(self, orient="vertical")
            self._y_scrollbar.grid(row=0, column=1, sticky="ns")

        self._parent = parent
        self._listview = ListView(self, **kwargs)
        self._listview.grid(row=0, column=0, sticky="nsew")
        if self._config.height:
            self._listview.config(height=self._config.height)

        if self._config.select_mode:
            self._listview.config(selectmode=self._config.select_mode)

        if self._x_scrollbar:
            self._listview.config(xscrollcommand=self._x_scrollbar.set)
            self._x_scrollbar.config(command=self._listview.xview)
        if self._y_scrollbar:
            self._listview.config(yscrollcommand=self._y_scrollbar.set)
            self._y_scrollbar.config(command=self._listview.yview)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._listview.set_double_click_handler(self._on_double_click)

    @property
    def real(self) -> ListView:
        return self._listview

    def _on_double_click(self, listview, index):
        _ = listview
        _ = index
        selection = self._listview.curselection()
        if not selection:
            return
        if not self._config.double_click_to_edit:
            return
        self._parent.on_edit(selection)


class BaseStringListBox(LabelFrame):
    def __init__(self, parent: "BaseStringListValueWidget", **kwargs):
        super().__init__(parent, **kwargs)

        self._button_frame: Optional[Frame] = None

        self._clear_button: Optional[Button] = None
        self._edit_button: Optional[Button] = None
        self._remove_button: Optional[Button] = None
        self._move_up_button: Optional[Button] = None
        self._move_down_button: Optional[Button] = None
        self._config: BaseStringListValue = parent.config

        self.config(text=self._config.content_title or parent.label)

        x_scrollbar = False
        y_scrollbar = False
        if parent.config.scrollbar == "horizontal":
            x_scrollbar = True
        elif parent.config.scrollbar == "vertical":
            y_scrollbar = True
        elif parent.config.scrollbar == "both":
            x_scrollbar = True
            y_scrollbar = True
        else:
            x_scrollbar = False
            y_scrollbar = False

        self._parent = parent
        self._listview = ScrollableListView(
            self, x_scrollbar=x_scrollbar, y_scrollbar=y_scrollbar, **kwargs
        )
        self._listview.pack(side="top", fill="both", expand=True)
        self._create_buttons()

    @property
    def parent_config(self) -> BaseStringListValue:
        return self._parent.config

    @property
    def buttons_area(self) -> Optional[Frame]:
        return self._button_frame

    @property
    def value(self) -> List[str]:
        return self._listview.real.items().copy()

    @value.setter
    def value(self, value: Any):
        try:
            list_value = list(value)
            self._listview.real.clear()
            self._listview.real.extend(list_value)
        except Exception as e:
            if not isinstance(e, SetValueError):
                raise SetValueError(
                    raw_value=value, msg=f"failed to set value: {str(e)}"
                ) from e
            raise

    def on_edit(self, indexes: List[int]):
        pass

    def on_remove_selected(self):
        selection = self._listview.real.curselection()
        if not selection and self._config.no_selection_message:
            show_warning(
                self._config.no_selection_message, parent=self.winfo_toplevel()
            )
            return
        if self._config.confirm_remove:
            reply = ask_yes_or_no(
                self._config.remove_confirm_message, parent=self.winfo_toplevel()
            )
            if not reply:
                return
        self._listview.real.remove_selected_items()

    def on_clear_all(self):
        if self._listview.real.size() <= 0 and self._config.no_item_message:
            show_warning(self._config.no_item_message, parent=self.winfo_toplevel())
            return
        if self._config.confirm_clear:
            reply = ask_yes_or_no(
                self._config.clear_confirm_message, parent=self.winfo_toplevel()
            )
            if not reply:
                return
        self._listview.real.clear()

    def on_move_up(self):
        selection = self._listview.real.curselection()
        if not selection and self._config.no_selection_message:
            show_warning(
                self._config.no_selection_message, parent=self.winfo_toplevel()
            )
            return
        self._listview.real.move_up()

    def on_move_down(self):
        selection = self._listview.real.curselection()
        if not selection and self._config.no_selection_message:
            show_warning(
                self._config.no_selection_message, parent=self.winfo_toplevel()
            )
            return
        self._listview.real.move_down()

    def _create_buttons(self):
        self._button_frame = Frame(self)
        self._button_frame.pack(fill="both", expand=True)

        if self._config.move_buttons:
            self._move_up_button = Button(
                self._button_frame,
                text=self._config.move_up_button_text,
                command=self.on_move_up,
            )
            self._move_up_button.pack(side="left", padx=2, pady=2)
            self._move_down_button = Button(
                self._button_frame,
                text=self._config.move_down_button_text,
                command=self.on_move_down,
            )
            self._move_down_button.pack(side="left", padx=2, pady=2)

        if self._config.clear_button:
            self._clear_button = Button(
                self._button_frame,
                text=self._config.cleat_button_text,
                command=self.on_clear_all,
            )
            self._clear_button.pack(side="right", padx=2, pady=2)

        if self._config.remove_button:
            self._remove_button = Button(
                self._button_frame,
                text=self._config.remove_button_text,
                command=self.on_remove_selected,
            )
            self._remove_button.pack(side="right", padx=2, pady=2)

        if self._config.edit_button:
            self._edit_button = Button(
                self._button_frame,
                text=self._config.edit_button_text,
                command=lambda: self.on_edit(self._listview.real.curselection()),
            )
            self._edit_button.pack(side="right", padx=2, pady=2)


W_ = TypeVar("W_", bound=BaseStringListBox)
T_ = TypeVar("T_", bound=BaseStringListValue)


class BaseStringListValueWidget(BaseParameterWidget):
    ConfigClass = T_

    def __init__(
        self,
        input_widget_type: Type[W_],
        parent: Widget,
        parameter_name: str,
        config: BaseStringListValue,
    ):
        super().__init__(parent, parameter_name, config)

        self._build_flag = False
        self._input_widget_type = input_widget_type
        self._input_widget: Optional[input_widget_type] = None

    @property
    def config(self) -> T_:
        return super().config

    def get_value(self) -> Union[str, List[str], InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            return self._input_widget.value
        except GetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def set_value(self, value: Any) -> Union[str, List[str], InvalidValue]:
        if not self._input_widget:
            raise RuntimeError("input widget not created yet")
        try:
            self._input_widget.value = value
            return value
        except SetValueError as e:
            self.on_parameter_error(self._parameter_name, e)
            return InvalidValue(raw_value=e.raw_value, exception=e)

    def build(self) -> "BaseStringListValueWidget":
        if self._build_flag:
            return self
        # 创建输入控件
        self._input_widget = self._input_widget_type(self)
        self._input_widget.pack(fill="both", expand=True, padx=1, pady=1)
        self._input_widget.value = self.config.default_value
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
