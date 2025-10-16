"""
集中管理可翻译的消息字符串
"""

from pyguiadapterlite.i18n import tr_

MSG_CLOSE_BUTTON_TEXT = tr_("Close")

MSG_WARNING_TITLE = tr_("Warning")
MSG_ERROR_TITLE = tr_("Error")
MSG_INFO_TITLE = tr_("Information")
MSG_QUESTION_TITLE = tr_("Question")
MSG_CRITICAL_TITLE = tr_("Critical")

MSG_NO_FUNC_DOC = tr_("No function documentation available.")

MSG_COPY = tr_("Copy")
MSG_CUT = tr_("Cut")
MSG_PASTE = tr_("Paste")
MSG_UNDO = tr_("Undo")
MSG_REDO = tr_("Redo")

MSG_BROWSE_BUTTON_TEXT = tr_("Browse")

MSG_SELECT_FILE_DIALOG_TITLE = tr_("Select File")
MSG_SAVE_FILE_DIALOG_TITLE = tr_("Save File")
MSG_SELECT_DIR_DIALOG_TITLE = tr_("Select Directory")
MSG_FILE_FILTER_ALL = tr_("All Files")

MSG_SELECT_ALL = tr_("Select All")
MSG_CLEAR_OUTPUT = tr_("Clear Output")
MSG_SCROLL_TO_TOP = tr_("Scroll to Top")
MSG_SCROLL_TO_BOTTOM = tr_("Scroll to Bottom")
MSG_SAVE_TO_FILE = tr_("Save to File")
MSG_ZOOMING = tr_("Zoom")
MSG_ZOOM_IN = tr_("Zoom In")
MSG_ZOOM_OUT = tr_("Zoom Out")
MSG_ZOOM_RESET = tr_("Zoom Reset")
MSG_NAVIGATION = tr_("Navigation")
MSG_NAV_TOP = tr_("Top")
MSG_NAV_BOTTOM = tr_("Bottom")
MSG_NAV_PAGE_UP = tr_("Page Up")
MSG_NAV_PAGE_DOWN = tr_("Page Down")
MSG_NAV_HINT = tr_("Arrow Keys/PageUp/PageDown")

MSG_FUNC_EXEC_WIN_TITLE = tr_("Function Execution")
MSG_FUNC_DOC_TAB_TITLE = tr_("Function Document")
MSG_FUNC_OUTPUT_TAB_TITLE = tr_("Function Output")
MSG_EXEC_BUTTON_TEXT = tr_("Execute")
MSG_CANCEL_BUTTON_TEXT = tr_("Cancel")

MSG_CLEAR_BUTTON_TEXT = tr_("Clear Output")
MSG_CLEAR_CHECKBOX_TEXT = tr_("clear output before execution")
MSG_FUNC_ERR_DIALOG_TITLE = tr_("Error")
MSG_FUNC_RET_DIALOG_TITLE = tr_("Result")
MSG_FUNC_EXECUTING = tr_("The function is executing, please wait...")
MSG_FUNC_NOT_EXECUTING = tr_("The function is not executing.")
MSG_FUNC_CANCELLABLE = tr_("The function is not cancellable.")
MSG_EXCEPTION_DURING_EXEC = tr_("An exception occurred during function execution:")
MSG_FUNC_RET_MSG = tr_("The function returned: {}")

MSG_FUNC_SEL_WIN_TITLE = tr_("Select Function")
MSG_SEL_BUTTON_TEXT = tr_("Select")
MSG_FUNC_LIST_TITLE = tr_("Function List")
MSG_FUNC_DOC_TITLE = tr_("Function Document")
MSG_NO_FUNC_DOC_STATUS = tr_("No documentation provided")
MSG_SEL_FUNC_FIRST = tr_("Select a function first!")
MSG_CURRENT_FUNC_STATUS = tr_("Current function: ")

MSG_PARAM_VALIDATION_WIN_TITLE = tr_("Validation Errors")
MSG_INVALID_PARAMS_GROUP_TITLE = tr_("Parameters")
MSG_INVALID_PARAMS_LABEL_TEXT = tr_("Please check the following parameters:")
MSG_INVALID_PARAM_DETAIL_GROUP_TITLE = tr_("Detail")
MSG_INVALID_PARAM_DETAIL_TEMPLATE = tr_("Parameter:\n  {}\nReason:\n  {}")

MSG_DIALOG_BUTTON_OK = tr_("OK")
MSG_DIALOG_BUTTON_CANCEL = tr_("Cancel")
MSG_DIALOG_INPUT_PROMPT = tr_("Input:")
MSG_INPUT_DIALOG_TITLE = tr_("Input")
MSG_INPUT_FILE_PROMPT = tr_("Select a file:")
MSG_INPUT_DIR_PROMPT = tr_("Select a directory:")
MSG_INPUT_PATH_PROMPT = tr_("Select a path:")


MSG_PATH_DIALOG_FILE_BUTTON_TEXT = tr_("File")
MSG_PATH_DIALOG_DIR_BUTTON_TEXT = tr_("Folder")

MSG_ADD_ITEM_DIALOG_TITLE = tr_("Add Item")
MSG_ADD_ITEM_DIALOG_LABEL_TEXT = tr_("Add a new item:")
MSG_EDIT_ITEM_DIALOG_TITLE = tr_("Edit Item")
MSG_EDIT_ITEM_DIALOG_LABEL_TEXT = tr_("Edit the item:")
MSG_DUPLICATE_ITEMS_WARNING = tr_("An item with the same value already exists!")
MSG_MULTIPLE_SELECTION_WARNING = tr_("Please select only one item!")
MSG_EMPTY_STRING_WARNING = tr_("The string to be added cannot be empty!")

MSG_MOVE_UP_BUTTON_TEXT = tr_("↑")
MSG_MOVE_DOWN_BUTTON_TEXT = tr_("↓")
MSG_REMOVE_BUTTON_TEXT = tr_("Remove")
MSG_REMOVE_ALL_BUTTON_TEXT = tr_("Clear")
MSG_EDIT_BUTTON_TEXT = tr_("Edit")
MSG_ADD_BUTTON_TEXT = tr_("Add")
MSG_REMOVE_CONFIRMATION = tr_("Are you sure to remove selected items from the list?")
MSG_REMOVE_ALL_CONFIRMATION = tr_("Are you sure to remove all items from the list?")
MSG_NO_ITEMS_WARNING = tr_("There are no items in the list!")
MSG_NO_SELECTION_WARNING = tr_("No item is selected!")

MSG_ADD_FILE_BUTTON_TEXT = tr_("File")
MSG_ADD_DIR_BUTTON_TEXT = tr_("Folder")
MSG_EDIT_PATH_DIALOG_TITLE = tr_("Edit Path")
MSG_EDIT_PATH_DIALOG_LABEL_TEXT = tr_("Edit the path:")
MSG_ADD_PATH_DIALOG_TITLE = tr_("Add Path")
MSG_ADD_PATH_DIALOG_LABEL_TEXT = tr_("Add a new path:")
MSG_EMPTY_PATH_WARNING = tr_("The path cannot be empty!")
MSG_DUPLICATE_PATH_WARNING = tr_("The path has already been added to the list!")
MSG_NO_PATHS_WARNING = tr_("There are no paths in the list!")
MSG_NO_PATHS_SELECTED_WARNING = tr_("No path is selected!")
MSG_REMOVE_PATH_CONFIRMATION = tr_(
    "Are you sure to remove the selected path from the list?"
)
MSG_REMOVE_ALL_PATHS_CONFIRMATION = tr_(
    "Are you sure to remove all paths from the list?"
)

MSG_PARAMS_SERIALIZATION_FAILED = tr_("Failed to serialize parameters!")
MSG_SAVE_PARAMS_FAILED = tr_("Failed to save parameters to file!")
MSG_SAVE_PARAMS_SUCCESS = tr_("Parameters saved successfully!")
MSG_LOAD_PARAMS_FAILED = tr_("Failed to load parameters from file!")
MSG_PARAMS_DESERIALIZATION_FAILED = tr_("Failed to deserialize parameters!")
MSG_SET_PARAMS_FAILED = tr_("Failed to set parameters!")
MSG_INVALID_PARAMS_FOUND = tr_("Invalid parameters found!")
MSG_LOAD_FILE_DIALOG_TITLE = tr_("Load File")
MSG_LOAD_PARAMS_SUCCESS = tr_("Parameters loaded successfully!")
MSG_INVALID_PARAMS_NOT_APPLIED = tr_(
    "The following parameters are invalid and will not be applied:"
)
