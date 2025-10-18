import dataclasses
from tkinter import Tk, Toplevel, TclError
from tkinter.ttk import Frame, PanedWindow, Label, Entry, Button
from typing import Any, Union, Optional, cast, Dict, List

from pyguiadapterlite._messages import (
    MSG_FUNC_SEL_WIN_TITLE,
    MSG_SEL_BUTTON_TEXT,
    MSG_FUNC_DOC_TITLE,
    MSG_FUNC_LIST_TITLE,
    MSG_NO_FUNC_DOC_STATUS,
    MSG_SEL_FUNC_FIRST,
    MSG_CURRENT_FUNC_STATUS,
)
from pyguiadapterlite.components.listview import ListView
from pyguiadapterlite.components.textview import TextView
from pyguiadapterlite.utils import show_warning, _info, _exception
from pyguiadapterlite.core.fn import FnInfo
from pyguiadapterlite.windows.basewindow import BaseWindow, BaseWindowConfig
from pyguiadapterlite.windows.fnexecwindow import FnExecuteWindow


@dataclasses.dataclass(frozen=True)
class FnSelectWindowConfig(BaseWindowConfig):
    title: str = MSG_FUNC_SEL_WIN_TITLE
    select_button_text: str = MSG_SEL_BUTTON_TEXT
    function_list_title: str = MSG_FUNC_LIST_TITLE
    document_view_title: str = MSG_FUNC_DOC_TITLE
    label_text_font: tuple = ("Arial", 10, "bold")
    document_font: tuple = ("Arial", 10, "bold")
    # no_match_status_text: str = "未找到匹配项"
    # no_match_document_text: str = "未找到匹配项"
    no_document_text: str = MSG_NO_FUNC_DOC_STATUS
    no_selection_status_text: str = MSG_SEL_FUNC_FIRST
    current_view_status_text: str = MSG_CURRENT_FUNC_STATUS


class FnSelectWindow(BaseWindow):

    def __init__(
        self,
        parent: Union[Tk, Toplevel],
        function_list: List[FnInfo],
        config: Optional[FnSelectWindowConfig] = None,
    ):

        config = config or FnSelectWindowConfig()

        self._doc_view: Optional[TextView] = None
        self._status_bar: Optional[Label] = None
        self._right_frame: Optional[Frame] = None
        self._main_pane: Optional[PanedWindow] = None
        self._search_entry: Optional[Entry] = None
        self._listview: Optional[ListView] = None
        self._left_frame: Optional[Frame] = None
        # self._search_var: StringVar = StringVar()

        self._function_list: Dict[int, FnInfo] = {}
        self._execute_window_root: Optional[Toplevel] = None
        self._execute_window: Optional[FnSelectWindow] = None

        super().__init__(parent, config)

        self._fill_listview(function_list)
        self._listview.selection_set(0)
        self._on_select(None)

    @property
    def config(self) -> FnSelectWindowConfig:
        return cast(FnSelectWindowConfig, super().config)

    def create_main_area(self) -> Any:
        self._main_pane = PanedWindow(self._parent, orient="horizontal")
        self._main_pane.pack(fill="both", expand=True)

    def create_left_area(self) -> Any:
        # 创建左侧框架 - 列表区域
        self._left_frame = Frame(self._main_pane)
        self._main_pane.add(self._left_frame, weight=1)
        # 设置左侧列表面板
        self._setup_left_panel()

    def _fill_listview(self, function_list: List[FnInfo]):
        """初始化函数列表"""
        self._listview.clear()
        for index, fn_info in enumerate(function_list):
            self._function_list[index] = fn_info
            self._listview.append(
                fn_info.display_name.strip() or fn_info.get_function_name()
            )

    def _setup_left_panel(self):
        """设置左侧列表面板"""
        # 添加标题
        list_label = Label(
            self._left_frame,
            text=self.config.function_list_title,
            font=self.config.label_text_font,
        )
        list_label.pack(pady=(0, 5))

        # 添加搜索框
        # self._setup_search_entry()

        # 创建列表框
        self._listview = ListView(self._left_frame)
        self._listview.pack(fill="both", padx=(2, 0), expand=True)
        # 绑定列表选择事件
        self._listview.set_selection_mode("single")
        self._listview.set_double_click_handler(self._on_list_item_double_click)
        self._listview.bind("<<ListboxSelect>>", self._on_select)

        # 添加按钮
        button_frame = Frame(self._left_frame)
        button_frame.pack(pady=(5, 5))
        select_button = Button(
            button_frame,
            text=self.config.select_button_text,
            command=self._on_select_button_clicked,
        )
        select_button.pack(fill="x")

    # def _setup_search_entry(self):
    #     """设置搜索功能"""
    #     search_frame = Frame(self._left_frame)
    #     search_frame.pack(fill="x", pady=(5, 5))
    #
    #     search_label = Label(search_frame, text=self.config.search_entry_title)
    #     search_label.pack(side="left", padx=(0, 5))
    #
    #     self._search_entry = Entry(search_frame, textvariable=self._search_var)
    #     self._search_entry.pack(side="left", fill="x", expand=True)
    #     # 绑定搜索事件
    #     self._search_var.trace("w", self._on_search)

    def create_right_area(self) -> Any:
        self._right_frame = Frame(self._main_pane)
        self._main_pane.add(self._right_frame, weight=2)
        self._setup_right_panel()

    def _setup_right_panel(self):
        """设置右侧文档面板"""
        # 添加标题
        doc_label = Label(
            self._right_frame,
            text=self.config.document_view_title,
            font=self.config.label_text_font,
        )
        doc_label.pack(pady=(0, 5))

        # 创建文档显示区域
        doc_frame = Frame(self._right_frame)
        doc_frame.pack(fill="both", expand=True)

        # 创建文档显示控件
        self._doc_view = TextView(
            doc_frame, font=self.config.document_font, wrap="word"
        )
        self._doc_view.pack(side="left", fill="both", expand=True)

        # 添加状态栏
        self._status_bar = Label(
            self._right_frame,
            text=self.config.no_selection_status_text,
            relief="sunken",
            anchor="w",
        )
        self._status_bar.pack(fill="x", pady=(5, 0))

    def _on_select(self, event):
        _ = event
        """处理列表选择事件"""
        selection = self._listview.curselection()
        if selection:
            index = selection[0]
            info = self._function_list.get(index)
            assert isinstance(info, FnInfo)
            if not info:
                return
            # 更新文档显示
            self._update_document(info)
            # 更新状态栏
            self._status_bar.config(
                text=f"{self.config.current_view_status_text}{info.get_function_name()}"
            )

    # def _on_search(self, *args):
    #     _ = args
    #     """处理搜索事件"""
    #     search_term = self._search_var.get().lower()
    #     if not search_term.strip():
    #         self._fill_listview(list(self._function_list.values()))
    #         return
    #     print("搜索词:", search_term)
    #     # 清空列表
    #     self._listview.clear()
    #     # 根据搜索词过滤并重新填充列表
    #     result = []
    #     for index, fn_info in self._function_list.items():
    #         if (
    #             search_term in fn_info.display_name.lower()
    #             or search_term in fn_info.fn_name.lower()
    #         ):
    #             print("匹配项:", fn_info.display_name, fn_info.fn_name)
    #             result.append(fn_info)
    #     print("搜索结果:", result)
    #     self._fill_listview(result)
    #     # 如果有匹配项，选中第一个
    #     if self._listview.size() > 0:
    #         self._listview.selection_set(0)
    #         self._on_select(None)
    #     else:
    #         self._doc_view.set_text(self.config.no_match_document_text)
    #         self._status_bar.config(text=self.config.no_match_status_text)

    def _on_select_button_clicked(self):
        selection = self._listview.curselection()
        if not selection:
            show_warning(MSG_SEL_FUNC_FIRST, parent=self._parent)
            return
        index = selection[0]
        info = self._function_list.get(index)
        assert isinstance(info, FnInfo)
        # print("选择的函数:", info.get_function_name())
        self._execute_window_root = Toplevel(self._parent)
        self._execute_window_root.withdraw()
        self._execute_window = FnExecuteWindow(self._execute_window_root, info)
        self._execute_window_root.transient(self._parent)
        self._execute_window_root.grab_set()
        self._execute_window.move_to_center()
        self._execute_window_root.deiconify()
        _info(f"creating an execute window and wait for it to close(fn={info.fn_name})")
        self._parent.wait_window(self._execute_window_root)
        try:
            self._execute_window_root.destroy()
        except TclError as e:
            _exception(e, "error when destroying execute window root")
        self._execute_window_root = None
        self._execute_window = None

    def _on_list_item_double_click(self, listview: ListView, index: int):
        _ = listview, index
        self._on_select_button_clicked()

    def _update_document(self, fn_info: FnInfo):
        if not fn_info.document.strip():
            self._doc_view.set_text(self.config.no_document_text)
        else:
            self._doc_view.set_text(fn_info.document)
