from tkinter import Widget
from tkinter.ttk import Notebook
from typing import Dict, Optional, List, Callable

from pyguiadapterlite.utils import _exception


class TabIdAlreadyExistsError(Exception):
    pass


class TabIdNotFoundError(Exception):
    pass


class TabView(object):
    def __init__(self, parent: Widget, **kwargs):
        self._tabs: Dict[str, Widget] = {}  # 存放tab_id和对应的内容控件
        # 创建内部的Notebook
        self._notebook = Notebook(parent, **kwargs)

    def pack(self, **kwargs):
        self._notebook.pack(**kwargs)

    def add_tab(self, tab_id: str, tab_name: str, content: Widget, **kwargs):
        if tab_id in self._tabs:
            raise TabIdAlreadyExistsError(f"tab id `{tab_id}` already exists")
        content.master = self._notebook
        # if content.master is None:
        #     content.configure(master=self._notebook)
        self._notebook.add(content, text=tab_name, **kwargs)
        self._tabs[tab_id] = content

    def remove_tab(self, tab_id: str, destroy_content: bool = True) -> None:
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs.pop(tab_id)
        self._notebook.forget(content)
        if destroy_content:
            content.destroy()

    def remove_tabs(self, tab_ids: List[str], destroy_content: bool = True):
        for tab_id in tab_ids:
            try:
                self.remove_tab(tab_id, destroy_content)
            except Exception as e:
                _exception(e, f"cannot remove tab `{tab_id}`")

    def clear(self, destroy_content: bool = True) -> None:
        # 移除所有tab
        for widget in self._tabs.values():
            try:
                self._notebook.forget(widget)
            except Exception as e:
                _exception(
                    e, f"an error occurred when invoking forget() on widget `{widget}`"
                )
            if destroy_content:
                widget.destroy()
        self._tabs.clear()

    def has_tab(self, tab_id: str) -> bool:
        return tab_id in self._tabs

    def get_tab(self, tab_id: str) -> Optional[Widget]:
        return self._tabs.get(tab_id, None)

    def set_current_tab(self, tab_id: str):
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs[tab_id]
        self._notebook.select(content)

    def tab_count(self) -> int:
        return len(self._tabs)

    def rename_tab(self, tab_id: str, new_name: str):
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs[tab_id]
        self._notebook.tab(content, text=new_name)

    def get_tab_name(self, tab_id: str) -> str:
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs[tab_id]
        return self._notebook.tab(content, option="text")

    def enable_tab(self, tab_id: str):
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs[tab_id]
        self._notebook.tab(content, state="normal")

    def disable_tab(self, tab_id: str):
        if tab_id not in self._tabs:
            raise TabIdNotFoundError(f"tab  id `{tab_id}` not found")
        content = self._tabs[tab_id]
        self._notebook.tab(content, state="disabled")

    def bind_tab_changed_event(self, handler: Callable):
        self._notebook.bind("<<NotebookTabChanged>>", handler)

    def __contains__(self, tab_id: str) -> bool:
        """支持使用 'in' 操作符检查tab是否存在"""
        return self.has_tab(tab_id)

    def __len__(self) -> int:
        """支持使用 len() 获取tab数量"""
        return self.tab_count()

    def __getitem__(self, tab_id: str) -> Widget:
        """支持使用 tab_view[tab_id] 获取tab内容"""
        content = self.get_tab(tab_id)
        if content is None:
            raise KeyError(f"tab with tab id '{tab_id}' not found")
        return content
