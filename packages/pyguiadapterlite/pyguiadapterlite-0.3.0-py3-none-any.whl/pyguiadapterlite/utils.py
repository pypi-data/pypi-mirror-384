import ast
import inspect
import logging
import re
import sys
import traceback
import warnings
from tkinter import messagebox, Tk
from typing import Any, Optional, Tuple, Union, List, Set

from pyguiadapterlite._messages import (
    MSG_INFO_TITLE,
    MSG_WARNING_TITLE,
    MSG_ERROR_TITLE,
    MSG_QUESTION_TITLE,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

_logger = logging.getLogger("__main__")


def _info(msg: str):
    _logger.info(msg)


def _warning(msg: str):
    _logger.warning(msg)


def _fatal(msg: str):
    _logger.critical(msg)
    sys.exit(1)


def _error(msg: str):
    _logger.error(msg)


def _debug(msg: str):
    _logger.debug(msg)


def _exception(e: BaseException, msg: str = None):
    _logger.exception(f"{msg if msg else 'Exception raised'}: {str(e)}")


def show_information(
    message: str, title: str = MSG_INFO_TITLE, parent=None, **options
) -> Any:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.showinfo(title, message, **options)


def show_warning(
    message: str, title: str = MSG_WARNING_TITLE, parent=None, **options
) -> Any:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.showwarning(title, message, **options)


def show_error(
    message: str, title: str = MSG_ERROR_TITLE, parent=None, **options
) -> Any:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.showerror(title, message, **options)


def show_question(
    message: str, title: str = MSG_QUESTION_TITLE, parent=None, **options
) -> str:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.askquestion(title, message, **options)


def ask_yes_or_no(
    message: str, title: str = MSG_QUESTION_TITLE, parent=None, **options
) -> bool:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.askyesno(title, message, **options)


def ask_ok_or_cancel(
    message: str, title: str = MSG_QUESTION_TITLE, parent=None, **options
) -> bool:
    options = options or {}
    if parent:
        options["parent"] = parent
    return messagebox.askokcancel(title, message, **options)


# noinspection PyUnresolvedReferences
def enable_dpi_awareness(root: Optional[Tk] = None, scale_factor_divider: int = 100):
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
        if root:
            scale_factor_divider = abs(scale_factor_divider or 100)
            scale_factor = (
                windll.shcore.GetScaleFactorForDevice(0) / scale_factor_divider
            )
            root.tk.call("tk", "scaling", scale_factor)
    except BaseException as e:
        _exception(e, "failed to enable DPI awareness")


def print_traceback(e: BaseException):
    exc_type, exc_msg, exc_tb = get_exception_info(e)
    print(f"{exc_type}: {exc_msg}\n{exc_tb}")


def get_exception_info(e: BaseException) -> Tuple[str, str, str]:
    exc_type = type(e).__name__
    exc_msg = str(e)
    exc_tb = ""
    if hasattr(e, "__traceback__"):
        tb = e.__traceback__
        tb_list = traceback.format_tb(tb)
        exc_tb = "".join(tb_list)
    return exc_type, exc_msg, exc_tb


def _marks(marks: Union[str, List[str], Tuple[str], Set[str]]) -> Set[str]:
    if not isinstance(marks, (list, tuple, set, str)):
        raise TypeError(f"unsupported types for marks: {type(marks)}")
    if isinstance(marks, str):
        if marks.strip() == "":
            raise ValueError("marks must be a non-empty string")
        return {marks}

    if len(marks) <= 0:
        raise ValueError("at least one mark must be provided")

    tmp = set()
    for mark in marks:
        if not isinstance(mark, str):
            raise TypeError(f"a mark must be a string: {type(mark)}")
        if mark.strip() == "":
            raise ValueError("an empty-string mark found")
        tmp.add(mark)
    return tmp


def _block_pattern(
    start_marks: Union[str, List[str], Tuple[str], Set[str]],
    end_marks: Union[str, List[str], Tuple[str], Set[str]],
) -> str:
    start_marks = _marks(start_marks)
    end_marks = _marks(end_marks)

    start_mark_choices = "|".join(start_marks)
    end_mark_choices = "|".join(end_marks)
    pattern = (
        rf"^(\s*(?:{start_mark_choices})\s*(.*\n.+)^\s*(?:{end_mark_choices})\s*\n)"
    )
    return pattern


def remove_text_block(
    text: str,
    start_marks: Union[str, List[str], Tuple[str], Set[str]],
    end_marks: Union[str, List[str], Tuple[str], Set[str]],
) -> str:
    pattern = _block_pattern(start_marks, end_marks)
    result = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.UNICODE)
    if not result:
        return text
    return re.sub(
        pattern, repl="", string=text, flags=re.MULTILINE | re.DOTALL | re.UNICODE
    )


def extract_text_block(
    text: str,
    start_marks: Union[str, List[str], Tuple[str], Set[str]],
    end_marks: Union[str, List[str], Tuple[str], Set[str]],
) -> Optional[str]:
    pattern = _block_pattern(start_marks, end_marks)
    result = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.UNICODE)
    if result:
        return result.group(2)
    return None


def get_type_args(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        content = raw[1:-1].strip()
    elif raw.startswith("(") and raw.endswith(")"):
        content = raw[1:-1].strip()
    else:
        content = None

    if content is None:
        return raw.split(",")

    content = "[" + content + "]"
    try:
        args = ast.literal_eval(content)
    except BaseException as e:
        warnings.warn(f"unable to parse type args '{raw}': {e}")
        return []
    return args


def hashable(obj: Any) -> bool:
    try:
        hash(obj)
        return True
    except TypeError:
        return False


def is_subclass_of(cls: Any, base_cls: Any):
    if not inspect.isclass(cls) or not inspect.isclass(base_cls):
        return False
    return issubclass(cls, base_cls)


def get_contrast_color(hex_color: str) -> str:
    """根据背景色返回对比度较高的文字颜色"""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.5 else "#FFFFFF"
