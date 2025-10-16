import dataclasses
import os
from tkinter import Widget
from tkinter.ttk import Button
from typing import Type, Optional, Literal, List, Tuple

from pyguiadapterlite._messages import (
    MSG_MULTIPLE_SELECTION_WARNING,
    MSG_ADD_FILE_BUTTON_TEXT,
    MSG_ADD_DIR_BUTTON_TEXT,
    MSG_ADD_BUTTON_TEXT,
    MSG_SELECT_DIR_DIALOG_TITLE,
    MSG_SELECT_FILE_DIALOG_TITLE,
    MSG_EDIT_PATH_DIALOG_TITLE,
    MSG_EDIT_PATH_DIALOG_LABEL_TEXT,
    MSG_ADD_PATH_DIALOG_TITLE,
    MSG_ADD_PATH_DIALOG_LABEL_TEXT,
    MSG_EMPTY_PATH_WARNING,
    MSG_DUPLICATE_PATH_WARNING,
    MSG_REMOVE_PATH_CONFIRMATION,
    MSG_REMOVE_ALL_PATHS_CONFIRMATION,
    MSG_NO_PATHS_WARNING,
    MSG_NO_PATHS_SELECTED_WARNING,
)
from pyguiadapterlite.components.dialog import PathInputDialog
from pyguiadapterlite.types.lists._common import (
    BaseStringListValue,
    BaseStringListValueWidget,
    BaseStringListBox,
)
from pyguiadapterlite.utils import show_warning


@dataclasses.dataclass(frozen=True)
class PathListValue(BaseStringListValue):

    add_button_text: str = MSG_ADD_BUTTON_TEXT
    add_file_button_text: Optional[str] = MSG_ADD_FILE_BUTTON_TEXT
    add_dir_button_text: Optional[str] = MSG_ADD_DIR_BUTTON_TEXT

    add_method: Literal["append", "prepend"] = "append"

    start_dir: str = ""
    normalize_path: bool = True
    absolutize_path: bool = True
    filters: List[Tuple[str, str]] = dataclasses.field(default_factory=list)
    file_dialog_action: Literal["open", "save"] = "open"
    file_dialog_title: str = MSG_SELECT_FILE_DIALOG_TITLE
    dir_dialog_title: str = MSG_SELECT_DIR_DIALOG_TITLE

    strip: bool = True

    accept_empty: bool = False
    empty_path_message: str = MSG_EMPTY_PATH_WARNING

    accept_duplicates: bool = False
    duplicate_message: str = MSG_DUPLICATE_PATH_WARNING

    multi_selection_message: str = MSG_MULTIPLE_SELECTION_WARNING

    add_path_dialog_title: str = MSG_ADD_PATH_DIALOG_TITLE
    add_path_dialog_label_text: str = MSG_ADD_PATH_DIALOG_LABEL_TEXT
    edit_path_dialog_title: str = MSG_EDIT_PATH_DIALOG_TITLE
    edit_path_dialog_label_text: str = MSG_EDIT_PATH_DIALOG_LABEL_TEXT

    no_item_message: str = MSG_NO_PATHS_WARNING
    no_selection_message: str = MSG_NO_PATHS_SELECTED_WARNING
    remove_confirm_message: str = MSG_REMOVE_PATH_CONFIRMATION
    clear_confirm_message: str = MSG_REMOVE_ALL_PATHS_CONFIRMATION

    @classmethod
    def target_widget_class(cls) -> Type["PathListValueWidget"]:
        return PathListValueWidget


class PathListBox(BaseStringListBox):
    def __init__(self, parent: "PathListValueWidget", **kwargs):
        self._add_file_button: Optional[Button] = None
        self._add_dir_button: Optional[Button] = None

        self._config: PathListValue = parent.config

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
        dialog = PathInputDialog(
            self,
            title=self._config.edit_path_dialog_title,
            label_text=self._config.edit_path_dialog_label_text,
            initial_value=str(current_value),
            file_button_text=self._config.add_file_button_text,
            dir_button_text=self._config.add_dir_button_text,
            file_dialog_action=self._config.file_dialog_action,
            file_dialog_title=self._config.file_dialog_title,
            dir_dialog_title=self._config.dir_dialog_title,
            start_dir=self._config.start_dir,
            file_types=self._config.filters,
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
            show_warning(self._config.empty_path_message, parent=self.winfo_toplevel())
            return None

        value = self._normpath(value)

        if not self._config.accept_duplicates and self._listview.real.contains(value):
            show_warning(self._config.duplicate_message, parent=self.winfo_toplevel())
            return None

        return value

    def _on_add_item(self):
        input_dialog = PathInputDialog(
            self,
            title=self._config.add_path_dialog_title,
            label_text=self._config.add_path_dialog_label_text,
            initial_value="",
            file_button_text=self._config.add_file_button_text,
            dir_button_text=self._config.add_dir_button_text,
            file_dialog_action=self._config.file_dialog_action,
            file_dialog_title=self._config.file_dialog_title,
            dir_dialog_title=self._config.dir_dialog_title,
            start_dir=self._config.start_dir,
            file_types=self._config.filters,
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
        self._add_file_button = Button(
            self.buttons_area,
            text=self._config.add_button_text,
            command=self._on_add_item,
        )
        self._add_file_button.pack(side="right", padx=2, pady=2)

    def _normpath(self, path: str):
        if self._config.normalize_path:
            path = os.path.normpath(path)
        if self._config.absolutize_path:
            path = os.path.abspath(path)
        return path


class PathListValueWidget(BaseStringListValueWidget):
    ConfigClass = PathListValue

    def __init__(
        self,
        parent: Widget,
        parameter_name: str,
        config: PathListValue,
    ):

        if not (config.add_file_button_text or config.add_dir_button_text):
            raise RuntimeError(
                "config.add_file_button_text and config.add_dir_button_text cannot both be None or empty"
            )

        super().__init__(PathListBox, parent, parameter_name, config)

    @property
    def config(self) -> PathListValue:
        return self._config


@dataclasses.dataclass(frozen=True)
class FileListValue(PathListValue):
    pass

    @classmethod
    def target_widget_class(cls) -> Type["FileListValueWidget"]:
        return FileListValueWidget


class FileListValueWidget(PathListValueWidget):
    ConfigClass = FileListValue

    def __init__(self, parent: Widget, parameter_name: str, config: FileListValue):
        if config.add_dir_button_text:
            config = dataclasses.replace(config, add_dir_button_text=None)
        super().__init__(parent, parameter_name, config)


@dataclasses.dataclass(frozen=True)
class DirectoryListValue(PathListValue):
    pass

    @classmethod
    def target_widget_class(cls) -> Type["DirectoryListValueWidget"]:
        return DirectoryListValueWidget


class DirectoryListValueWidget(PathListValueWidget):
    ConfigClass = DirectoryListValue

    def __init__(self, parent: Widget, parameter_name: str, config: DirectoryListValue):
        if config.add_file_button_text:
            config = dataclasses.replace(config, add_file_button_text=None)
        super().__init__(parent, parameter_name, config)
