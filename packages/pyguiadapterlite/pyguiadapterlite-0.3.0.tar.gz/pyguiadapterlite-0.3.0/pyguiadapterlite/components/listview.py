from tkinter import Listbox, Widget, Tk, Toplevel, END, Event
from typing import Any, Callable, Optional, List, Union


class ListView(Listbox):
    def __init__(self, parent: Union[Widget, Tk, Toplevel], **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self._click_handler: Optional[Callable[[ListView, int], None]] = None
        self._double_click_handler: Optional[Callable[[ListView, int], None]] = None
        self._right_click_handler: Optional[Callable[[ListView], None]] = None

        self.bind("<Button-1>", self._on_click)
        self.bind("<Double-Button-1>", self._on_double_click)
        self.bind("<Button-3>", self._on_right_click)

    def set_click_handler(self, handler: Callable[["ListView", int], None]) -> None:
        self._click_handler = handler

    def set_double_click_handler(
        self, handler: Callable[["ListView", int], None]
    ) -> None:
        self._double_click_handler = handler

    def set_right_click_handler(
        self, handler: Callable[["ListView", int], None]
    ) -> None:
        self._right_click_handler = handler

    def enable_click_event(self, enabled: bool = True) -> None:
        if enabled:
            self.bind("<Button-1>", self._on_click)
        else:
            self.unbind("<Button-1>")

    def enable_double_click_event(self, enabled: bool = True) -> None:
        if enabled:
            self.bind("<Double-Button-1>", self._on_double_click)
        else:
            self.unbind("<Double-Button-1>")

    def enable_right_click_event(self, enabled: bool = True) -> None:
        if enabled:
            self.bind("<Button-3>", self._on_right_click)
        else:
            self.unbind("<Button-3>")

    def append(self, item: str) -> None:
        """在列表末尾添加一个元素"""
        self.insert(END, item)

    def extend(self, items: List[str]) -> None:
        """在列表末尾批量添加元素"""
        for item in items:
            self.append(item)

    def prepend(self, item: str) -> None:
        """在列表开头添加一个元素"""
        self.insert(0, item)

    def items(self) -> List[str]:
        """返回当前列表中的所有元素"""
        return list(self.get(0, END))

    def index_of(self, item: str) -> int:
        """返回指定元素的索引"""
        for i in range(self.size()):
            if self.get(i) == item:
                return i
        return -1

    def remove(self, item: str) -> None:
        """从列表中删除一个元素"""
        for i in range(self.size()):
            if self.get(i) == item:
                self.delete(i)
                return

    def pop(self, index: int = -1) -> str:
        if index < 0 and index != -1:
            raise IndexError("index out of range")
        if index >= self.size():
            raise IndexError("index out of range")
        if index == -1:
            item = self.get(END)
            self.delete(END)
        else:
            item = self.get(index)
            self.delete(index)
        return item

    def clear(self) -> None:
        """清除当前列表中的所有元素"""
        self.delete(0, END)

    def set(self, index: int, new_item: str):
        """设置指定索引处的元素"""
        if not self._is_valid_index(index):
            raise IndexError(f"invalid index: {index}")
        self.delete(index)
        self.insert(index, new_item)

    def sort(self, key=None, reverse=False):
        items = self.items()
        items.sort(key=key, reverse=reverse)
        self.clear()
        self.extend(items)

    def reverse(self):
        items = self.items()
        items.reverse()
        self.clear()
        self.extend(items)

    def move(self, from_index: int, to_index: int):
        if not self._is_valid_index(from_index):
            raise IndexError(f"invalid from_index: {from_index}")
        if not self._is_valid_index(to_index):
            raise IndexError(f"invalid to_index: {to_index}")
        from_item = self.get(from_index)
        self.delete(from_index)
        self.insert(to_index, from_item)

    def selected_items(self) -> List[str]:
        """返回当前选中的元素"""
        return [self.get(i) for i in self.curselection()]

    def remove_selected_items(self) -> None:
        """删除当前选中的元素"""
        selected_indices = self.curselection()
        if not selected_indices:
            return
        for i in selected_indices[::-1]:
            self.delete(i)

    def selected_count(self) -> int:
        """返回当前选中的元素数量"""
        return len(self.curselection())

    def select_none(self) -> None:
        """清除当前选中的元素"""
        self.selection_clear(0, END)

    def select_all(self) -> None:
        """选中所有元素"""
        self.selection_set(0, END)

    def set_selection_mode(self, mode: str):
        self.config(selectmode=mode)

    def get_selection_mode(self) -> str:
        return self.cget("selectmode")

    def move_up(self):
        """将选中的元素向上移动"""
        """上移选中的项目"""
        selected_indices = self.curselection()
        if not selected_indices:
            return

        # 检查是否可以移动（第一个项目不能上移）
        if 0 in selected_indices:
            return

        # 从前往后移动（避免索引冲突）
        for i in selected_indices:
            if i > 0:
                # 获取项目内容
                current_item = self.get(i)
                prev_item = self.get(i - 1)

                # 交换位置
                self.delete(i - 1, i)  # 删除这两个位置
                self.insert(i - 1, current_item)
                self.insert(i, prev_item)

        # 重新选择移动后的项目
        new_selection = [i - 1 for i in selected_indices]
        self.selection_clear(0, END)
        for i in new_selection:
            self.selection_set(i)

    def move_down(self):
        """将选中的元素向下移动"""
        selected_indices = self.curselection()
        if not selected_indices:
            return

        # 检查是否可以移动（最后一个项目不能下移）
        last_index = self.size() - 1
        if last_index in selected_indices:
            return

        # 从后往前移动（避免索引冲突）
        for i in selected_indices[::-1]:
            if i < last_index:
                # 获取项目内容
                current_item = self.get(i)
                next_item = self.get(i + 1)

                # 交换位置
                self.delete(i, i + 1)  # 删除这两个位置
                self.insert(i, next_item)
                self.insert(i + 1, current_item)

        # 重新选择移动后的项目
        new_selection = [i + 1 for i in selected_indices]
        self.selection_clear(0, END)
        for i in new_selection:
            self.selection_set(i)

    def contains(self, item: str) -> bool:
        """判断列表中是否包含指定元素"""
        return item in self

    def _is_valid_index(self, index: int) -> bool:
        if index < 0 or index >= self.size():
            return False
        return True

    def _on_click(self, event: Event) -> None:
        if not self._click_handler:
            return
        index = self.nearest(event.y)
        self._click_handler(self, index)

    def _on_double_click(self, event: Event) -> None:
        if not self._double_click_handler:
            return
        index = self.nearest(event.y)
        self._double_click_handler(self, index)

    def _on_right_click(self, event: Event) -> None:
        _ = event
        if not self._right_click_handler:
            return
        self._right_click_handler(self)

    def __contains__(self, item: str) -> bool:
        for i in range(self.size()):
            if self.get(i) == item:
                return True
        return False
