class bool_t(int):
    pass


class text_t(str):
    pass


class int_r(int):
    pass


class int_s(int):
    pass


class int_ss(int):
    pass


class float_r(float):
    pass


class float_s(float):
    pass


class float_ss(float):
    pass


class file_t(str):
    pass


class dir_t(str):
    pass


# directory_t = dir_t
class directory_t(dir_t):
    pass


class choice_t(object):
    pass


class option_t(choice_t):
    pass


# loose_choices_t = choice_t
class loose_choice_t(choice_t):
    pass


class choices_t(list):
    pass


class options_t(choices_t):
    pass


class color_hex_t(str):
    pass


class color_t(color_hex_t):
    pass


class string_list_t(list):
    pass


class str_list(string_list_t):
    pass


class string_list(string_list_t):
    pass


class path_list_t(list):
    pass


class path_list(path_list_t):
    pass


class paths_t(path_list_t):
    pass


class dir_list_t(list):
    pass


class dirs_t(dir_list_t):
    pass


class dir_list(dir_list_t):
    pass


class file_list_t(list):
    pass


class file_list(file_list_t):
    pass


class files_t(file_list_t):
    pass
