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
    loose_choice_t,
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
    dir_t,
    string_list,
    str_list,
    path_list,
    file_list,
    files_t,
    dir_list,
    dirs_t,
    option_t,
    options_t,
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


BUILTIN_WIDGETS_MAP = {
    # built-in types
    TYPE_STR: StringValueWidget,
    TYPE_INT: IntValueWidget,
    TYPE_BOOL: BoolValueWidget,
    TYPE_FLOAT: FloatValueWidget,
    TYPING_LITERAL: SingleChoiceValueWidget,
    # extended types
    # bool types
    bool_t.__name__: BoolValueWidget2,
    # int types
    int_r.__name__: RangedIntValueWidget,
    int_s.__name__: ScaleIntValueWidget2,
    int_ss.__name__: ScaleIntValueWidget,
    # float types
    float_r.__name__: RangedFloatValueWidget,
    float_s.__name__: ScaleFloatValueWidget,
    float_ss.__name__: ScaleFloatValueWidget2,
    # str types
    text_t.__name__: TextValueWidget,
    # dir_t
    directory_t.__name__: DirectoryValueWidget,
    dir_t.__name__: DirectoryValueWidget,
    # file_t
    file_t.__name__: FileValueWidget,
    # color_t
    color_hex_t.__name__: HexColorValueWidget,
    color_t.__name__: HexColorValueWidget,
    # choices types
    choice_t.__name__: SingleChoiceValueWidget,
    option_t.__name__: SingleChoiceValueWidget,
    loose_choice_t.__name__: LooseChoiceValueWidget,
    choices_t.__name__: MultiChoiceValueWidget,
    options_t.__name__: MultiChoiceValueWidget,
    # list types
    # string list types
    string_list_t.__name__: StringListValueWidget,
    string_list.__name__: StringListValueWidget,
    str_list.__name__: StringListValueWidget,
    # path list types
    path_list_t.__name__: PathListValueWidget,
    path_list.__name__: PathListValueWidget,
    paths_t.__name__: PathListValueWidget,
    # file path list types
    file_list_t.__name__: FileListValueWidget,
    file_list.__name__: FileListValueWidget,
    files_t.__name__: FileListValueWidget,
    # directory path list types
    dir_list_t.__name__: DirectoryListValueWidget,
    dir_list.__name__: DirectoryListValueWidget,
    dirs_t.__name__: DirectoryListValueWidget,
}

# noinspection PyProtectedMember
BUILTIN_WIDGETS_MAPPING_RULES = [
    EnumValuedWidget._enum_type_mapping_rule,
    # DictEdit._dict_mapping_rule,
]
