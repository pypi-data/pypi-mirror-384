from concurrent.futures import Future
from tkinter import messagebox, simpledialog
from typing import Any, Callable, Literal, Optional, Type, Tuple, List

from pyguiadapterlite._messages import (
    MSG_INFO_TITLE,
    MSG_WARNING_TITLE,
    MSG_CRITICAL_TITLE,
    MSG_QUESTION_TITLE,
    MSG_INPUT_DIALOG_TITLE,
    MSG_DIALOG_BUTTON_OK,
    MSG_DIALOG_BUTTON_CANCEL,
    MSG_DIALOG_INPUT_PROMPT,
    MSG_PATH_DIALOG_FILE_BUTTON_TEXT,
    MSG_SELECT_FILE_DIALOG_TITLE,
    MSG_PATH_DIALOG_DIR_BUTTON_TEXT,
    MSG_SELECT_DIR_DIALOG_TITLE,
    MSG_INPUT_PATH_PROMPT,
    MSG_INPUT_FILE_PROMPT,
    MSG_INPUT_DIR_PROMPT,
)
from pyguiadapterlite.components import toast
from pyguiadapterlite.components.dialog import (
    BaseDialog,
    StringInputDialog,
    PathInputDialog,
    TextViewDialog,
)
from pyguiadapterlite.core.ucontext import UContext
from pyguiadapterlite.windows.fnexecwindow import FnExecuteWindow


def is_cancel_requested() -> bool:
    if UContext.current_cancel_event() is not None:
        return UContext.current_cancel_event().is_set()
    return False


def uprint(*messages: Any, sep=" ", end="\n"):
    exec_window = UContext.current_execute_window()
    if not exec_window:
        print(*messages, sep=sep, end=end)
        return
    for message in messages:
        exec_window.output_view.write(f"{message}{sep}")
    if end:
        exec_window.output_view.write(end)


def _call_func(
    func: Callable[[FnExecuteWindow, list, dict], Any],
    window: FnExecuteWindow,
    future: Future,
    *args,
    **kwargs,
):
    try:
        future.set_result(func(window, *args, **kwargs))
    except Exception as e:
        future.set_exception(e)


def _run_ui_on_thread(
    func: Callable[[FnExecuteWindow, list, dict], Any], *args, **kwargs
) -> Any:
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    future = Future()
    exec_window.parent.after(0, _call_func, func, exec_window, future, args, kwargs)
    return future.result()


def is_progressbar_enabled() -> bool:
    def _func(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return window.is_progressbar_enabled()

    return _run_ui_on_thread(_func)


def is_progress_label_enabled() -> bool:
    def _func(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return window.is_progress_label_enabled()

    return _run_ui_on_thread(_func)


def show_progressbar():
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    exec_window.parent.after(0, exec_window.show_progressbar)


def hide_progressbar():
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    exec_window.parent.after(0, exec_window.hide_progressbar)


def start_progressbar(
    total: int,
    mode: Literal["determinate", "indeterminate"] = "determinate",
    initial_value: int = 0,
    initial_msg: Optional[str] = "",
):
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    exec_window.parent.after(
        0, exec_window.start_progressbar, total, mode, initial_value, initial_msg
    )


def update_progressbar(value: int, msg: Optional[str] = None):
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    exec_window.parent.after(0, exec_window.update_progressbar, value, msg)


def stop_progressbar(hide_after_stop: bool = True):
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")
    exec_window.parent.after(0, exec_window.stop_progressbar, hide_after_stop)


def show_toast(
    message: str,
    duration: int = 3000,
    position: Literal["top", "bottom", "center"] = "top",
    background: str = "#323232",
    foreground: str = "#FFFFFF",
    font: tuple = ("Arial", 10),
    pad_x: int = 20,
    pad_y: int = 20,
    alpha: float = 0.0,
):
    exec_window = UContext.current_execute_window()
    if not exec_window:
        raise RuntimeError("fn execute_window is not set")

    def _show_toast(window: FnExecuteWindow):
        t = toast.Toast(window.parent)
        t.show_toast(
            message=message,
            duration=duration,
            position=position,
            background=background,
            foreground=foreground,
            font=font,
            pad_x=pad_x,
            pad_y=pad_y,
            alpha=alpha,
        )

    exec_window.parent.after(0, _show_toast, exec_window)


def show_info_messagebox(
    message: str, title: str = MSG_INFO_TITLE, **messagebox_kwargs
) -> str:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.showinfo(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )
        return ret

    return _run_ui_on_thread(_call)


def show_warning_messagebox(
    message: str, title: str = MSG_WARNING_TITLE, **messagebox_kwargs
) -> str:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.showwarning(
            title=title,
            message=message,
            parent=window.parent,
            **messagebox_kwargs,
        )
        return ret

    return _run_ui_on_thread(_call)


def show_critical_messagebox(
    message: str, title: str = MSG_CRITICAL_TITLE, **messagebox_kwargs
) -> str:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.showerror(
            title=title,
            message=message,
            parent=window.parent,
            **messagebox_kwargs,
        )
        return ret

    return _run_ui_on_thread(_call)


show_error_messagebox = show_critical_messagebox


def show_question_messagebox(
    message: str,
    title: str = MSG_QUESTION_TITLE,
    **messagebox_kwargs,
) -> str:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return messagebox.askquestion(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )

    return _run_ui_on_thread(_call)


def show_ok_cancel_messagebox(
    message: str,
    title: str = MSG_QUESTION_TITLE,
    **messagebox_kwargs,
) -> bool:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.askokcancel(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )
        return ret

    return _run_ui_on_thread(_call)


def show_retry_cancel_messagebox(
    message: str,
    title: str = MSG_QUESTION_TITLE,
    **messagebox_kwargs,
) -> Literal["ok", "retry", "cancel"]:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.askretrycancel(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )
        return ret

    return _run_ui_on_thread(_call)


def show_yes_no_cancel_messagebox(
    message: str,
    title: str = MSG_QUESTION_TITLE,
    **messagebox_kwargs,
) -> Optional[bool]:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.askyesnocancel(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )
        return ret

    return _run_ui_on_thread(_call)


def show_yes_no_messagebox(
    message: str,
    title: str = MSG_QUESTION_TITLE,
    **messagebox_kwargs,
) -> bool:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        ret = messagebox.askyesno(
            title=title, message=message, parent=window.parent, **messagebox_kwargs
        )
        return ret

    return _run_ui_on_thread(_call)


def get_string_input(
    prompt: str, title: str = MSG_INPUT_DIALOG_TITLE, **dialog_kwargs
) -> Optional[str]:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return simpledialog.askstring(
            title=title, prompt=prompt, parent=window.parent, **dialog_kwargs
        )

    return _run_ui_on_thread(_call)


def get_int_input(
    prompt: str, title: str = MSG_INPUT_DIALOG_TITLE, **dialog_kwargs
) -> Optional[int]:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return simpledialog.askinteger(
            title=title, prompt=prompt, parent=window.parent, **dialog_kwargs
        )

    return _run_ui_on_thread(_call)


def get_float_input(
    prompt: str, title: str = MSG_INPUT_DIALOG_TITLE, **dialog_kwargs
) -> Optional[float]:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        return simpledialog.askfloat(
            title=title, prompt=prompt, parent=window.parent, **dialog_kwargs
        )

    return _run_ui_on_thread(_call)


def show_custom_dialog(
    dialog_class: Type[BaseDialog], title: str, **dialog_kwargs
) -> Any:
    def _call(window: FnExecuteWindow, *args, **kwargs):
        _ = args, kwargs  # unused
        dialog = dialog_class(title=title, parent=window.parent, **dialog_kwargs)
        if dialog.is_cancelled():
            return None
        return dialog.result

    return _run_ui_on_thread(_call)


def get_string_input2(
    title: str = MSG_INPUT_DIALOG_TITLE,
    size: tuple = (300, 100),
    resizable: bool = False,
    ok_text: str = MSG_DIALOG_BUTTON_OK,
    cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    label_text: str = MSG_DIALOG_INPUT_PROMPT,
    initial_value: str = "",
    echo_char: Optional[str] = None,
):
    return show_custom_dialog(
        dialog_class=StringInputDialog,
        title=title,
        size=size,
        resizable=resizable,
        ok_text=ok_text,
        cancel_text=cancel_text,
        label_text=label_text,
        initial_value=initial_value,
        echo_char=echo_char,
    )


def get_path_input(
    title: str = MSG_INPUT_DIALOG_TITLE,
    size: tuple = (420, 130),
    resizable: bool = False,
    file_button_text: Optional[str] = MSG_PATH_DIALOG_FILE_BUTTON_TEXT,
    file_types: List[Tuple[str, str]] = None,
    file_dialog_title: str = MSG_SELECT_FILE_DIALOG_TITLE,
    file_dialog_action: Literal["open", "save"] = "open",
    dir_button_text: Optional[str] = MSG_PATH_DIALOG_DIR_BUTTON_TEXT,
    dir_dialog_title: str = MSG_SELECT_DIR_DIALOG_TITLE,
    start_dir: str = "",
    ok_text: str = MSG_DIALOG_BUTTON_OK,
    cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    label_text: str = MSG_INPUT_PATH_PROMPT,
    initial_value: str = "",
):
    return show_custom_dialog(
        dialog_class=PathInputDialog,
        title=title,
        size=size,
        resizable=resizable,
        file_button_text=file_button_text,
        file_types=file_types,
        file_dialog_title=file_dialog_title,
        file_dialog_action=file_dialog_action,
        dir_button_text=dir_button_text,
        dir_dialog_title=dir_dialog_title,
        start_dir=start_dir,
        ok_text=ok_text,
        cancel_text=cancel_text,
        label_text=label_text,
        initial_value=initial_value,
    )


def get_file_path_input(
    title: str = MSG_INPUT_DIALOG_TITLE,
    size: tuple = (420, 130),
    resizable: bool = False,
    file_button_text: Optional[str] = MSG_PATH_DIALOG_FILE_BUTTON_TEXT,
    file_types: List[Tuple[str, str]] = None,
    file_dialog_title: str = MSG_SELECT_FILE_DIALOG_TITLE,
    file_dialog_action: Literal["open", "save"] = "open",
    start_dir: str = "",
    ok_text: str = MSG_DIALOG_BUTTON_OK,
    cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    label_text: str = MSG_INPUT_FILE_PROMPT,
    initial_value: str = "",
):
    return show_custom_dialog(
        dialog_class=PathInputDialog,
        title=title,
        size=size,
        resizable=resizable,
        file_button_text=file_button_text,
        file_types=file_types,
        file_dialog_title=file_dialog_title,
        file_dialog_action=file_dialog_action,
        dir_button_text=None,
        dir_dialog_title="",
        start_dir=start_dir,
        ok_text=ok_text,
        cancel_text=cancel_text,
        label_text=label_text,
        initial_value=initial_value,
    )


def get_dir_path_input(
    title: str = MSG_INPUT_DIALOG_TITLE,
    size: tuple = (420, 130),
    resizable: bool = False,
    dir_button_text: Optional[str] = MSG_PATH_DIALOG_DIR_BUTTON_TEXT,
    dir_dialog_title: str = MSG_SELECT_DIR_DIALOG_TITLE,
    start_dir: str = "",
    ok_text: str = MSG_DIALOG_BUTTON_OK,
    cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    label_text: str = MSG_INPUT_DIR_PROMPT,
    initial_value: str = "",
):
    return show_custom_dialog(
        dialog_class=PathInputDialog,
        title=title,
        size=size,
        resizable=resizable,
        file_button_text=None,
        file_types="",
        file_dialog_title="",
        file_dialog_action="open",
        dir_button_text=dir_button_text,
        dir_dialog_title=dir_dialog_title,
        start_dir=start_dir,
        ok_text=ok_text,
        cancel_text=cancel_text,
        label_text=label_text,
        initial_value=initial_value,
    )


def get_text_input(
    title: str = MSG_INPUT_DIALOG_TITLE,
    size: tuple = (500, 400),
    resizable: bool = True,
    ok_text: str = MSG_DIALOG_BUTTON_OK,
    cancel_text: str = MSG_DIALOG_BUTTON_CANCEL,
    label_text: str = MSG_DIALOG_INPUT_PROMPT,
    initial_value: str = "",
    textview_height: int = 20,
    default_menu: bool = True,
    wrap: Literal["none", "char", "word"] = "word",
    font: tuple = ("Arial", 10),
):
    return show_custom_dialog(
        TextViewDialog,
        title=title,
        size=size,
        resizable=resizable,
        ok_text=ok_text,
        cancel_text=cancel_text,
        default_menu=default_menu,
        wrap=wrap,
        font=font,
        text=initial_value,
        textview_height=textview_height,
        label_text=label_text,
    )


# 定义别名
is_function_cancelled = is_cancel_requested
