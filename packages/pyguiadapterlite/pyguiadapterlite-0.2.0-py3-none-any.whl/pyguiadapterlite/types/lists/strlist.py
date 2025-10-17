import dataclasses
from tkinter import Widget
from tkinter.ttk import Button
from typing import Type, Optional, Literal, List

from pyguiadapterlite._messages import (
    MSG_ADD_ITEM_DIALOG_TITLE,
    MSG_EDIT_ITEM_DIALOG_TITLE,
    MSG_ADD_ITEM_DIALOG_LABEL_TEXT,
    MSG_EDIT_ITEM_DIALOG_LABEL_TEXT,
    MSG_DUPLICATE_ITEMS_WARNING,
    MSG_EMPTY_STRING_WARNING,
    MSG_MULTIPLE_SELECTION_WARNING,
    MSG_ADD_BUTTON_TEXT,
)
from pyguiadapterlite.components.dialog import StringInputDialog
from pyguiadapterlite.types.lists._common import (
    BaseStringListValue,
    BaseStringListValueWidget,
    BaseStringListBox,
)
from pyguiadapterlite.utils import show_warning


@dataclasses.dataclass(frozen=True)
class StringListValue(BaseStringListValue):

    add_button: bool = True
    add_button_text: str = MSG_ADD_BUTTON_TEXT
    add_method: Literal["append", "prepend"] = "append"

    strip: bool = False

    accept_empty: bool = True
    empty_string_message: str = MSG_EMPTY_STRING_WARNING

    accept_duplicates: bool = True
    duplicate_message: str = MSG_DUPLICATE_ITEMS_WARNING

    multi_selection_message: str = MSG_MULTIPLE_SELECTION_WARNING

    add_item_dialog_title: str = MSG_ADD_ITEM_DIALOG_TITLE
    add_item_dialog_label_text: str = MSG_ADD_ITEM_DIALOG_LABEL_TEXT
    edit_item_dialog_title: str = MSG_EDIT_ITEM_DIALOG_TITLE
    edit_item_dialog_label_text: str = MSG_EDIT_ITEM_DIALOG_LABEL_TEXT

    @classmethod
    def target_widget_class(cls) -> Type["StringListValueWidget"]:
        return StringListValueWidget


class StringListBox(BaseStringListBox):
    def __init__(self, parent: "StringListValueWidget", **kwargs):
        self._add_button: Optional[Button] = None
        self._config: StringListValue = parent.config

        super().__init__(parent, **kwargs)

    def on_edit(self, indexes: List[int]):
        if not indexes:
            show_warning(
                self._config.no_selection_message, parent=self.winfo_toplevel()
            )
            return
        if len(indexes) > 1:
            show_warning(
                self._config.multi_selection_message, parent=self.winfo_toplevel()
            )
            return
        index = indexes[0]
        current_value = self._listview.real.get(index)
        dialog = StringInputDialog(
            self,
            title=self._config.edit_item_dialog_title,
            label_text=self._config.edit_item_dialog_label_text,
            initial_value=str(current_value),
        )
        if dialog.is_cancelled():
            return
        new_value = dialog.result
        if new_value == current_value:
            return
        new_value = self._process_input(new_value)
        if new_value is None:
            return
        self._listview.real.set(index, new_value)

    def _process_input(self, input_str: str) -> Optional[str]:
        value = str(input_str)
        if self._config.strip:
            value = value.strip()

        if not self._config.accept_empty and value.strip() == "":
            show_warning(
                self._config.empty_string_message, parent=self.winfo_toplevel()
            )
            return None

        if not self._config.accept_duplicates and self._listview.real.contains(value):
            show_warning(self._config.duplicate_message, parent=self.winfo_toplevel())
            return None

        return value

    def _on_add_item(self):
        input_dialog = StringInputDialog(
            self,
            title=self._config.add_item_dialog_title,
            label_text=self._config.add_item_dialog_label_text,
        )
        if input_dialog.is_cancelled():
            return
        value = input_dialog.result
        if value is None:
            return

        value = self._process_input(value)
        if value is None:
            return

        if self._config.add_method == "append":
            self._listview.real.append(value)
        else:
            self._listview.real.prepend(value)

    def _create_buttons(self):
        super()._create_buttons()
        if self._config.add_button:
            self._add_button = Button(
                self.buttons_area,
                text=self._config.add_button_text,
                command=self._on_add_item,
            )
            self._add_button.pack(side="right", padx=2, pady=2)


class StringListValueWidget(BaseStringListValueWidget):
    ConfigClass = StringListValue

    def __init__(
        self,
        parent: Widget,
        parameter_name: str,
        config: StringListValue,
    ):
        super().__init__(StringListBox, parent, parameter_name, config)

    @property
    def config(self) -> StringListValue:
        return self._config
