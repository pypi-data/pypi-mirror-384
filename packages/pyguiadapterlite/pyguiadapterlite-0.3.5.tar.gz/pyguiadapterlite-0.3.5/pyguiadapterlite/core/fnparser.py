import dataclasses
import inspect
import warnings
from collections import OrderedDict
from typing import Union, Any, Type, Dict, List, Tuple, Set, Callable, Optional

import docstring_parser
import tomlkit

from pyguiadapterlite import utils
from pyguiadapterlite.core.fn import FnInfo, ParameterInfo
from pyguiadapterlite.types.typenames import get_typename, get_type_args

PARAM_WIDGET_METADATA_START = ("@widgets", "@parameters", "@params")
PARAM_WIDGET_METADATA_END = "@end"


class _Unset(object):
    pass


UNSET = _Unset


class FnDocstring(object):

    def __init__(self, fn_docstring: str):
        self._fn_docstring: str = fn_docstring

        try:
            self._docstring = docstring_parser.parse(fn_docstring)
        except docstring_parser.ParseError:
            self._docstring = None

    def has_parameter(self, parameter_name: str) -> bool:
        if self._docstring is None:
            return False
        return self._find_parameter(parameter_name) is not None

    def get_short_description(self) -> Optional[str]:
        if self._docstring is None:
            return None
        return self._docstring.short_description

    def get_long_description(self) -> Optional[str]:
        if self._docstring is None:
            return None
        return self._docstring.long_description

    def get_parameter_description(self, parameter_name: str) -> Optional[str]:
        docstring_param = self._find_parameter(parameter_name)
        if docstring_param is None:
            return None
        return docstring_param.description.strip()

    def get_parameter_default_value(self, parameter_name: str) -> Optional[str]:
        docstring_param = self._find_parameter(parameter_name)
        if docstring_param is None:
            return None
        return docstring_param.default

    def get_parameter_typename(self, parameter_name: str) -> Optional[str]:
        docstring_param = self._find_parameter(parameter_name)
        if docstring_param is None:
            return None
        return docstring_param.type_name

    def _find_parameter(
        self, parameter_name: str
    ) -> Optional[docstring_parser.DocstringParam]:
        if self._docstring is None:
            return None
        for param in self._docstring.params:
            if param.arg_name == parameter_name:
                return param
        return None


@dataclasses.dataclass
class WidgetMeta(object):
    widget_class: Union[str, None, Type[_Unset]] = UNSET
    value_type: Union[str, None, Type[_Unset]] = UNSET
    default_value: Union[Any, Type[_Unset]] = UNSET
    label: Union[str, None, Type[_Unset]] = UNSET
    description: Union[str, None, Type[_Unset]] = UNSET
    custom_configs: Union[Dict[str, Any], Type[_Unset]] = UNSET

    def to_config_dict(self) -> Dict[str, Any]:
        config_dict = dataclasses.asdict(self)
        custom_configs = config_dict.pop("custom_configs", None)
        if not isinstance(custom_configs, dict):
            custom_configs = OrderedDict()
        config_dict.update(**custom_configs)
        config_dict = {k: v for k, v in config_dict.items() if v is not UNSET}
        return config_dict


class FnParser(object):
    def __init__(
        self,
        widget_metadata_start: Union[
            str, List[str], Tuple[str], Set[str]
        ] = PARAM_WIDGET_METADATA_START,
        widget_metadata_end: Union[
            str, List[str], Tuple[str], Set[str]
        ] = PARAM_WIDGET_METADATA_END,
    ):
        self._widget_metadata_start: Union[str, List[str], Tuple[str], Set[str]] = (
            widget_metadata_start
        )
        self._widget_metadata_end: Union[str, List[str], Tuple[str], Set[str]] = (
            widget_metadata_end
        )

    def parse(
        self, fn: Callable, ignore_self_param: bool = True
    ) -> Tuple[str, Dict[str, ParameterInfo]]:
        if not inspect.ismethod(fn) and not inspect.isfunction(fn):
            raise ValueError("fn must be a function or method")

        doc = fn.__doc__ or ""
        fn_docstring_text = utils.remove_text_block(
            doc, self._widget_metadata_start, self._widget_metadata_end
        )
        fn_docstring = FnDocstring(fn_docstring_text)
        short_desc = fn_docstring.get_short_description() or ""
        long_desc = fn_docstring.get_long_description() or ""
        document = (short_desc + "\n\n" + long_desc).strip() or fn_docstring_text
        parameters = self._parse_fn_params(fn, fn_docstring, ignore_self_param)
        return document, parameters

    def parse_widget_configs(
        self, fn_info: FnInfo, params: Dict[str, ParameterInfo]
    ) -> Dict[str, Tuple[Optional[str], Optional[str], dict]]:
        # this method returns a dict of "parameter_name" -> (widget_class_name| None, value_type_name | None, widget_config)
        configs = OrderedDict()
        metas = self._parse_widget_meta(fn_info, params)
        for param_name, param_info in params.items():
            widget_config = OrderedDict(
                {
                    "default_value": param_info.default_value,
                    "label": param_name,
                    "description": param_info.description,
                }
            )

            if widget_config["default_value"] is UNSET:
                widget_config.pop("default_value")

            widget_class_name = None
            value_type_name = None
            meta = metas.get(param_name, None)
            if meta is not None:
                meta_config_dict = meta.to_config_dict()
                widget_class_name = meta_config_dict.pop("widget_class", None)
                value_type_name = meta_config_dict.pop("value_type", None)
                widget_config.update(**meta_config_dict)
            configs[param_name] = (widget_class_name, value_type_name, widget_config)
        return configs

    def _parse_widget_meta(
        self, fn_info: FnInfo, params: Dict[str, ParameterInfo]
    ) -> Dict[str, WidgetMeta]:
        fn = fn_info.fn
        meta_text = utils.extract_text_block(
            fn.__doc__ or "", self._widget_metadata_start, self._widget_metadata_end
        )
        if meta_text is None:
            return OrderedDict()
        meta_text = meta_text.strip()

        try:
            # metadata = tomli.loads(meta_text)
            metadata = tomlkit.parse(meta_text).unwrap()
            if not isinstance(metadata, dict):
                raise ValueError("invalid widget configs text")
        except Exception as e:
            warnings.warn(f"failed to parse widget configs in docstring: {e}")
            return OrderedDict()

        meta = OrderedDict()
        for param_name, widget_configs in metadata.items():
            if not isinstance(widget_configs, dict):
                continue

            param_info: Optional[ParameterInfo] = params.get(param_name, None)
            widget_config_meta = WidgetMeta()

            key_widget_class = "widget_class"
            conf_widget_class = widget_configs.pop(key_widget_class, None)
            if conf_widget_class:
                widget_config_meta.widget_class = conf_widget_class

            key_value_type = "__type__"
            conf_value_type = widget_configs.pop(key_value_type, None)
            if conf_value_type:
                widget_config_meta.value_type = conf_value_type

            key_default_value = "default_value"
            conf_default_value = widget_configs.pop(key_default_value, None)
            if conf_default_value is not None:
                widget_config_meta.default_value = conf_default_value
            elif param_info is not None:
                widget_config_meta.default_value = param_info.default_value
            else:
                widget_config_meta.default_value = UNSET

            key_label = "label"
            conf_label = widget_configs.pop(key_label, None)
            if conf_label is not None:
                widget_config_meta.label = str(conf_label)
            elif param_info is not None:
                widget_config_meta.label = param_name
            else:
                widget_config_meta.label = UNSET

            key_description = "description"
            conf_description = widget_configs.pop(key_description, None)
            if conf_description is not None:
                widget_config_meta.description = str(conf_description)
            elif param_info is not None:
                widget_config_meta.description = str(param_info.description or "")
            else:
                widget_config_meta.description = UNSET

            if len(widget_configs) > 0:
                widget_config_meta.custom_configs = {**widget_configs}

            meta[param_name] = widget_config_meta
        return meta

    def _parse_fn_params(
        self, fn: Callable, fn_docstring: FnDocstring, ignore_self_param: bool
    ) -> Dict[str, ParameterInfo]:
        params = OrderedDict()
        fn_signature = inspect.signature(fn)
        for param_name, param in fn_signature.parameters.items():
            if param_name in params:
                raise ValueError(f"duplicate parameter name: {param_name}")

            if ignore_self_param and param_name == "self":
                continue

            default_value = self._get_param_default_value(param, fn_docstring)

            typ, typename, type_args = self._get_param_type_info(
                param, default_value, fn_docstring
            )
            description = fn_docstring.get_parameter_description(param.name) or ""

            params[param_name] = ParameterInfo(
                type=typ,
                typename=typename,
                type_args=type_args,
                default_value=default_value,
                description=description,
            )
        return params

    def _get_param_type_info(
        self, param: inspect.Parameter, default_value: Any, fn_docstring: FnDocstring
    ) -> Tuple[Type, str, List[Any]]:
        param_typename = None
        param_type_args = None

        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            raise RuntimeError(
                f"positional only parameters are not supported: {param.name}"
            )
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            param_type = list
            param_type_args = []
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            param_type = dict
            param_type_args = []
        elif self._has_type_annotation(param):
            param_type = param.annotation
        else:
            _param_type_in_docstring = fn_docstring.get_parameter_typename(param.name)
            if _param_type_in_docstring is not None:
                param_typename = _param_type_in_docstring
                param_type = None
            else:
                param_type = self._guess_param_type(default_value)
            param_type_args = []

        if param_typename is None:
            param_typename = get_typename(param_type)

        if param_type_args is None:
            param_type_args = get_type_args(param_type)

        return param_type, param_typename, param_type_args

    @staticmethod
    def _get_param_default_value(
        param: inspect.Parameter, fn_docstring: FnDocstring
    ) -> Any:
        if param.default is UNSET:
            return UNSET

        if param.default is not inspect.Parameter.empty:
            return param.default

        default_value = fn_docstring.get_parameter_default_value(param.name)
        if default_value is not None:
            return default_value
        return UNSET

    @staticmethod
    def _guess_param_type(default_value: Any) -> Type:
        if default_value is None or default_value is UNSET:
            return Any
        if isinstance(default_value, type):
            return default_value
        return type(default_value)

    @staticmethod
    def _has_type_annotation(param: inspect.Parameter) -> bool:
        if (
            param.annotation is not None
            and param.annotation is not inspect.Parameter.empty
        ):
            return True
        return False
