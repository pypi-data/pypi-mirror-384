from datetime import datetime, date, time
from typing import Union

from pyguiadapterlite.types import (
    StringValueWidget,
    TextValueWidget,
    FloatValueWidget,
    RangedFloatValueWidget,
    ScaleFloatValueWidget2,
    ScaleIntValueWidget2,
    ScaleFloatValueWidget,
    BoolValueWidget,
    FileValueWidget,
    BoolValueWidget2,
    DirectoryValueWidget,
    StringListValueWidget,
    FileListValueWidget,
    DirectoryListValueWidget,
    PathListValueWidget,
    SingleChoiceValueWidget,
    LooseChoiceValueWidget,
    MultiChoiceValueWidget,
    HexColorValueWidget,
)
from pyguiadapterlite.types.choices.enumchoice import EnumValuedWidget
from pyguiadapterlite.types.extendtypes import (
    text_t,
    int_r,
    int_s,
    float_r,
    directory_t,
    file_t,
    choice_t,
    choices_t,
    color_hex_t,
    string_list_t,
    color_t,
    path_list_t,
    file_list_t,
    dir_list_t,
    paths_t,
    float_s,
    int_ss,
    float_ss,
    bool_t,
)
from pyguiadapterlite.types.ints.common import IntValueWidget
from pyguiadapterlite.types.ints.ranged import RangedIntValueWidget
from pyguiadapterlite.types.ints.scale import ScaleIntValueWidget
from pyguiadapterlite.types.typenames import (
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_STR,
    TYPE_BOOL,
    TYPING_LITERAL,
)

PyLiteralType = Union[bool, int, float, bytes, str, list, tuple, dict, set, type(None)]


TYPE_BOOL_T = bool_t.__name__
TYPE_TEXT = text_t.__name__
TYPE_INT_R = int_r.__name__
TYPE_INT_S = int_s.__name__
TYPE_INT_SS = int_ss.__name__
TYPE_FLOAT_R = float_r.__name__
TYPE_FLOAT_S = float_s.__name__
TYPE_FLOAT_SS = float_ss.__name__
TYPE_DIR_T = directory_t.__name__
TYPE_FILE_T = file_t.__name__
TYPE_PY_LITERAL = str(PyLiteralType)
TYPE_CHOICE_T = choice_t.__name__
TYPE_CHOICES_T = choices_t.__name__
TYPE_DATETIME = datetime.__name__
TYPE_DATE = date.__name__
TYPE_TIME = time.__name__
TYPE_COLOR_HEX = color_hex_t.__name__
# noinspection SpellCheckingInspection
TYPE_COLOR_T = color_t.__name__
TYPE_STRING_LIST_T = string_list_t.__name__
TYPE_PATH_LIST_T = path_list_t.__name__
TYPE_FILE_LIST_T = file_list_t.__name__
TYPE_DIR_LIST_T = dir_list_t.__name__
TYPE_PATHS_T = paths_t.__name__

BUILTIN_WIDGETS_MAP = {
    TYPE_STR: StringValueWidget,
    TYPE_TEXT: TextValueWidget,
    TYPE_INT: IntValueWidget,
    TYPE_BOOL: BoolValueWidget,
    TYPE_BOOL_T: BoolValueWidget2,
    TYPE_INT_R: RangedIntValueWidget,
    TYPE_INT_S: ScaleIntValueWidget2,
    TYPE_INT_SS: ScaleIntValueWidget,
    TYPE_FLOAT: FloatValueWidget,
    TYPE_FLOAT_R: RangedFloatValueWidget,
    TYPE_FLOAT_S: ScaleFloatValueWidget2,
    TYPE_FLOAT_SS: ScaleFloatValueWidget,
    TYPE_DIR_T: DirectoryValueWidget,
    TYPE_FILE_T: FileValueWidget,
    # TYPE_JSON_OBJ_T: JsonEdit,
    # TYPE_ANY: PyLiteralEdit,
    # TYPING_ANY: PyLiteralEdit,
    # TYPE_PY_LITERAL: PyLiteralEdit,
    # TYPING_UNION: PyLiteralEdit,
    # TYPE_OBJECT: PyLiteralEdit,
    # TYPE_DICT: DictEdit,
    # TYPING_DICT: DictEdit,
    # TYPE_MAPPING: DictEdit,
    # TYPE_MUTABLE_MAPPING: DictEdit,
    # TYPING_TYPED_DICT: DictEdit,
    # TYPE_LIST: ListEdit,
    # TYPING_LIST: ListEdit,
    # TYPE_TUPLE: TupleEdit,
    # TYPING_TUPLE: TupleEdit,
    # TYPE_SET: SetEdit,
    # TYPING_SET: SetEdit,
    # TYPE_MUTABLE_SET: SetEdit,
    TYPING_LITERAL: SingleChoiceValueWidget,
    TYPE_CHOICE_T: LooseChoiceValueWidget,
    TYPE_CHOICES_T: MultiChoiceValueWidget,
    # TYPE_SLIDER_INT_T: Slider,
    # TYPE_DIAL_INT_T: Dial,
    # TYPE_DATETIME: DateTimeEdit,
    # TYPE_DATE: DateEdit,
    # TYPE_TIME: TimeEdit,
    # TYPE_COLOR_TUPLE: ColorTuplePicker,
    TYPE_COLOR_HEX: HexColorValueWidget,
    # TYPE_QCOLOR: ColorPicker,
    # TYPE_COLOR_T: ColorPicker,
    # TYPE_KEY_SEQUENCE_T: KeySequenceEdit,
    TYPE_STRING_LIST_T: StringListValueWidget,
    # TYPE_PLAIN_DICT_T: PlainDictEdit,
    TYPE_PATH_LIST_T: PathListValueWidget,
    TYPE_FILE_LIST_T: FileListValueWidget,
    TYPE_DIR_LIST_T: DirectoryListValueWidget,
    # TYPE_FONT_T: FontSelect,
    # TYPE_INT_QUANTITY: IntQuantityBox,
    # TYPE_FLOAT_QUANTITY: FloatQuantityBox,
    # TYPE_STRING_DICT_T: StringDictEdit,
    # TYPE_PATHS_T: PathsEditor,
}

# noinspection PyProtectedMember
BUILTIN_WIDGETS_MAPPING_RULES = [
    EnumValuedWidget._enum_type_mapping_rule,
    # DictEdit._dict_mapping_rule,
]
