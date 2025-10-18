from tkinter import Widget
from tkinter.ttk import Frame, Combobox, Button
from typing import List, Literal, Optional, Iterable

from pyguiadapterlite.utils import _warning


class ComboBox(Frame):
    def __init__(
        self,
        parent: Widget,
        choices: Iterable[str],
        default_value: Optional[str] = None,
        readonly: bool = False,
        add_user_input: bool = False,
        justify: Literal["left", "center", "right"] = "left",
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._add_user_input = add_user_input

        self._choices: List[str] = []
        for choice in choices:
            if choice in self._choices:
                _warning(f"duplicate choice found: {choice}")
                continue
            self._choices.append(choice)

        if not self._choices:
            raise ValueError("choices cannot be empty")

        self._combo: Combobox = Combobox(
            self,
            values=self._choices,
            state="readonly" if readonly else "normal",
            justify=justify,
        )
        self._combo.pack(fill="both", expand=True)
        if default_value is None:
            self._combo.current(0)
        else:
            self.current_value = default_value

        # self._combo.bind("<FocusOut>", self._on_focus_out)
        self._combo.bind("<Return>", self._on_enter)

    @property
    def current_value(self) -> str:
        return self._combo.get()

    @current_value.setter
    def current_value(self, value: str):
        if value not in self._choices:
            _warning(f"choice not found: {value}")
        if self._add_user_input and value not in self._choices:
            self.add_choice(value)
        self._combo.set(value)

    def has_choice(self, choice: str) -> bool:
        return choice in self._choices

    def add_choice(self, choice: str):
        if choice in self._choices:
            _warning(f"choice already exists: {choice}")
            return
        self._choices.append(choice)
        self._combo["values"] = self._choices

    def remove_choice(self, choice: str):
        if choice not in self._choices:
            _warning(f"choice not found: {choice}")
            return
        self._choices.remove(choice)
        self._combo["values"] = self._choices

    def _on_enter(self, event):
        _ = event
        if not self._add_user_input:
            return
        value = self._combo.get()
        if value in self._choices:
            return
        self.add_choice(value)
