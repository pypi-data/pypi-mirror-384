import dataclasses
from tkinter import Toplevel
from tkinter.ttk import LabelFrame, Label
from typing import Any, Optional, cast, Dict, Tuple, Callable

from pyguiadapterlite._messages import (
    MSG_PARAM_VALIDATION_WIN_TITLE,
    MSG_INVALID_PARAMS_LABEL_TEXT,
    MSG_INVALID_PARAMS_GROUP_TITLE,
    MSG_INVALID_PARAM_DETAIL_GROUP_TITLE,
    MSG_INVALID_PARAM_DETAIL_TEMPLATE,
)
from pyguiadapterlite.windows.basewindow import BaseWindow, BaseWindowConfig
from pyguiadapterlite.components.listview import ListView
from pyguiadapterlite.components.textview import TextView


@dataclasses.dataclass(frozen=True)
class ParameterValidationWindowConfig(BaseWindowConfig):
    title: str = MSG_PARAM_VALIDATION_WIN_TITLE
    invalid_params_group_title: str = MSG_INVALID_PARAM_DETAIL_GROUP_TITLE
    invalid_params_label_text: str = MSG_INVALID_PARAMS_LABEL_TEXT
    description_group_title: str = MSG_INVALID_PARAMS_GROUP_TITLE
    invalid_param_detail_template: str = MSG_INVALID_PARAM_DETAIL_TEMPLATE
    size: tuple = (400, 450)
    font: tuple = ("Arial", 11)
    bell: bool = True


class ParameterValidationWindow(BaseWindow):
    def __init__(
        self,
        parent: Toplevel,
        invalid_params: Dict[str, Tuple[str, str]],
        config: Optional[ParameterValidationWindowConfig] = None,
    ):
        config = config or ParameterValidationWindowConfig()

        self._top_frame: Optional[LabelFrame] = None
        self._listview: Optional[ListView] = None
        self._bottom_frame: Optional[LabelFrame] = None
        self._doc_view: Optional[TextView] = None
        self._invalid_params_label: Optional[Label] = None

        self._on_close_handler: Optional[Callable[[], None]] = None
        self._item_click_handler: Optional[Callable[[str], None]] = None

        self._invalid_params: Dict[int, Tuple[str, str, str]] = {}

        super().__init__(parent, config)

        self._fill_listview(invalid_params)
        self._listview.selection_set(0)
        self._on_select(None)
        if self.config.bell:
            self._parent.bell()

    @property
    def config(self) -> ParameterValidationWindowConfig:
        return cast(ParameterValidationWindowConfig, super().config)

    def create_main_area(self) -> Any:
        config = self.config
        self._top_frame = LabelFrame(
            self._parent, text=config.invalid_params_group_title
        )
        self._invalid_params_label = Label(
            self._top_frame, text=config.invalid_params_label_text
        )
        self._invalid_params_label.pack(fill="x", padx=5, pady=5)
        self._listview = ListView(self._top_frame, selectmode="single")
        self._listview.pack(fill="both", expand=True, padx=5, pady=5)
        self._listview.bind("<<ListboxSelect>>", self._on_select)
        self._listview.set_click_handler(self._on_list_item_click)
        self._top_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def create_bottom_area(self) -> Any:
        self._bottom_frame = LabelFrame(
            self._parent, text=self.config.description_group_title
        )
        self._bottom_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._doc_view = TextView(self._bottom_frame, font=self.config.font)
        self._doc_view.pack(fill="both", expand=True, padx=5, pady=5)

    def set_item_clicked_handler(self, handler: Callable[[str], None]):
        self._item_click_handler = handler

    def set_on_close_handler(self, handler: Callable[[], None]):
        self._on_close_handler = handler

    def on_close(self):
        super().on_close()
        if self._on_close_handler:
            self._on_close_handler()

    def _on_list_item_click(self, listview: ListView, index: int):
        """处理列表项点击事件"""
        _ = listview
        if not self._item_click_handler:
            return
        if index < 0 or index >= len(self._invalid_params):
            return
        fn_name, _, _ = self._invalid_params.get(index)
        self._item_click_handler(fn_name)

    def _fill_listview(self, raw: Dict[str, Tuple[str, str]]):
        """初始化函数列表"""
        self._listview.clear()
        for index, data in enumerate(raw.items()):
            (parameter_name, (label, validation_msg)) = data
            self._invalid_params[index] = (parameter_name, label, validation_msg)
            self._listview.append(label or parameter_name)

    def _on_select(self, event):
        _ = event
        """处理列表选择事件"""
        selection = self._listview.curselection()
        if selection:
            index = selection[0]
            param_name, display_name, validation_msg = self._invalid_params.get(index)
            # 更新文档显示
            self._update_document(param_name, validation_msg)

    def _update_document(self, param_name: str, validation_msg: str):
        self._doc_view.clear()
        self._doc_view.set_text(
            self.config.invalid_param_detail_template.format(param_name, validation_msg)
        )
