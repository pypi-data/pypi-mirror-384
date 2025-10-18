from tkinter import Widget, StringVar
from tkinter.ttk import Frame, Radiobutton
from typing import Dict, Any, List, Union, Optional


# class ChoiceByIndex(object):
#     def __init__(self, index: int):
#         self.index = index
#
#     @classmethod
#     def first(cls):
#         return cls(0)
#
#     @classmethod
#     def last(cls):
#         return cls(-1)
#
#     @classmethod
#     def of(cls, index: int):
#         return cls(index)


FIRST_CHOICE = None
LAST_CHOICE = object()


class SingleChoiceBox(Frame):
    def __init__(
        self,
        parent: Widget,
        choices: Union[Dict[str, Any], List[Any]],
        columns: int = 2,
        default_choice: Any = FIRST_CHOICE,
        **kwargs,
    ):
        # 当choices为字典时，key代表选项显示的文本, value代表该选项的实际值
        # 如: {'男': 1, '女': 2, '保密': 3}, 将显示为: 男、女、保密
        # 选择'男'时，返回1, 选择'女'时，返回2, 选择'保密'时，返回3.
        # 当choices为列表时，其将转换为字典，key和value相同.
        # 如: ['男', '女', '保密'],将被转换为: {'男': '男', '女': '女', '保密': '保密'}.

        super().__init__(parent, **kwargs)

        self._choices_dict = (
            choices.copy()
            if isinstance(choices, dict)
            else {str(val): val for val in choices}
        )

        if not self._choices_dict:
            raise ValueError("choices cannot be empty")

        self._var = StringVar()
        if columns < 1:
            columns = 1
        self._columns: int = columns
        self._radiobuttons: Dict[str, Radiobutton] = {}
        self._setup_widgets()

        self.select(default_choice)

    def _setup_widgets(self):
        row = 0
        col = 0
        for label, value in self._choices_dict.items():
            rb = Radiobutton(self, text=label, variable=self._var, value=label)
            rb.grid(row=row, column=col, sticky="w")
            rb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            self._radiobuttons[label] = rb

            col += 1
            if col >= self._columns:
                col = 0
                row += 1

    @property
    def current(self) -> Any:
        for rb in self._radiobuttons.values():
            if rb.instate(["selected"]):
                label = rb.cget("text")
                return self._choices_dict.get(label, None)
        return None

    @property
    def current_label(self) -> Optional[str]:
        for rb in self._radiobuttons.values():
            if rb.instate(["selected"]):
                return rb.cget("text")
        return None

    def select(self, value: Any) -> bool:
        if value is FIRST_CHOICE:
            return self.select_by_label(list(self._choices_dict.keys())[0])
        elif value is LAST_CHOICE:
            return self.select_by_label(list(self._choices_dict.keys())[-1])
        else:
            return self.select_by_label(self._find_label_by_value(value))

    def select_by_label(self, label: str):
        if label is None:
            return False
        rb = self._radiobuttons.get(label, None)
        if not rb:
            return False
        if not rb.instate(["selected"]):
            rb.invoke()
        return True

    def _find_label_by_value(self, value: Any) -> Optional[str]:
        for label, val in self._choices_dict.items():
            if val == value:
                return label
        return None
