import dataclasses
from tkinter import Widget, Canvas, Scrollbar, Label, N, S, E, W, PhotoImage
from tkinter.ttk import Frame
from typing import Optional, Tuple, List, Dict, Any, Union

from pyguiadapterlite.assets import image_file
from pyguiadapterlite.components.tooltip import ToolTip
from pyguiadapterlite.components.valuewidget import (
    BaseParameterWidget,
    BaseParameterWidgetConfig,
    InvalidValue,
)
from pyguiadapterlite.core.fn import ParameterInfo

_DESCRIPTION_ICON_FILE = image_file("info.png")
_DESCRIPTION_ICON = None

STICKY_MAP = {
    "center": "",  # 居中，不填充
    "w": W,  # 左对齐，填充垂直方向
    "e": E,  # 右对齐，填充垂直方向
    "n": N,  # 上对齐，填充水平方向
    "s": S,  # 下对齐，填充水平方向
    "nw": N + W,  # 左上，不填充
    "ne": N + E,  # 右上，不填充
    "sw": S + W,  # 左下，不填充
    "se": S + E,  # 右下，不填充
    "ew": E + W,  # 左右填充（水平填充）
    "ns": N + S,  # 上下填充（垂直填充）
    "nsew": N + S + E + W,  # 全部填充
}

DEFAULT_STICKY = E + W
DEFAULT_SCROLLBAR_CURSOR = "fleur"


@dataclasses.dataclass(frozen=True)
class ColumnConfig(object):
    anchor: str = W
    width: Optional[int] = None
    weight: Optional[int] = None
    padding_x: Optional[int] = 1
    padding_y: Optional[int] = 1


class NColumnScrollableArea(Frame):
    def __init__(
        self,
        parent: Widget,
        n_columns: int,
        column_configs: Optional[Tuple[ColumnConfig, ...]] = None,
        scrollbar_cursor: str = DEFAULT_SCROLLBAR_CURSOR,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self._n_columns = n_columns
        self._scrollbar_cursor = scrollbar_cursor
        self._rows: List[List[Widget]] = []

        # 创建默认列配置
        if column_configs is None:
            column_configs = tuple(ColumnConfig() for _ in range(n_columns))

        if len(column_configs) != n_columns:
            raise ValueError(
                f"column_configs length ({len(column_configs)}) must match n_columns ({n_columns})"
            )

        self._column_configs = column_configs

        self._canvas: Optional[Canvas] = None
        self._inner_frame: Optional[Frame] = None
        self._canvas_window: Optional[int] = None

        # 创建滚动框架
        self._create_scrollable_area()

    def _create_scrollable_area(self):
        """创建可滚动区域"""
        # 创建垂直滚动条
        v_scrollbar = Scrollbar(self, orient="vertical", cursor=self._scrollbar_cursor)
        v_scrollbar.pack(side="right", fill="y")

        # 创建画布
        self._canvas = Canvas(
            self, yscrollcommand=v_scrollbar.set, highlightthickness=0
        )
        self._canvas.pack(side="left", fill="both", expand=True)

        # 配置滚动条
        v_scrollbar.config(command=self._canvas.yview)

        # 创建内部框架（用于放置内容）
        self._inner_frame = Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_frame, anchor="nw", tags="inner_frame"
        )

        # 绑定事件
        self._inner_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # 创建列配置
        self._create_column_config()

    def _create_column_config(self):
        """创建列配置"""
        for i, config in enumerate(self._column_configs):
            # 设置列的权重，让列可以扩展
            weight = 0
            if config.weight:
                weight = 1
            self._inner_frame.grid_columnconfigure(i, weight=weight)

    def _on_frame_configure(self, event):
        _ = event
        """当内部框架大小改变时，更新画布的滚动区域"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """当画布大小改变时，调整内部框架的宽度"""
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def add_row(self, widgets: Tuple[Widget, ...], **kwargs):
        """添加一行"""
        if len(widgets) > self._n_columns:
            raise ValueError(
                f"too many widgets for a row({len(widgets) > self._n_columns})"
            )

        row_index = len(self._rows)
        row_widgets = []

        for col_index, (widget, config) in enumerate(
            zip(widgets, self._column_configs)
        ):
            # 将anchor转换为sticky参数
            sticky = STICKY_MAP.get(
                config.anchor.lower(), DEFAULT_STICKY
            )  # 默认水平填充

            # 配置widget在网格中的位置，使用sticky让widget填满单元格
            if config.padding_x is None:
                px = 0
            else:
                px = config.padding_x

            if config.padding_y is None:
                py = 0
            else:
                py = config.padding_y
            widget.grid(
                row=row_index,
                column=col_index,
                sticky=sticky,
                padx=px,
                pady=py,
                **kwargs,
            )

            # 如果指定了宽度，设置列的最小宽度
            if config.width is not None:
                self._inner_frame.grid_columnconfigure(col_index, minsize=config.width)

            row_widgets.append(widget)

        self._rows.append(row_widgets)
        self._update_scroll_area()

    def remove_row(self, row_index: int):
        """移除指定行"""
        if 0 <= row_index < len(self._rows):
            # 销毁该行的所有widget
            for widget in self._rows[row_index]:
                widget.destroy()

            # 从列表中移除
            self._rows.pop(row_index)

            # 重新排列剩余的行
            self._rearrange_rows()
            self._update_scroll_area()
        else:
            raise IndexError(f"row_index {row_index} out of range")

    def clear(self):
        """清除所有行"""
        for row_widgets in self._rows:
            for widget in row_widgets:
                widget.destroy()
        self._rows.clear()
        self._update_scroll_area()

    def row_count(self) -> int:
        """返回行数"""
        return len(self._rows)

    def column_count(self) -> int:
        """返回列数"""
        return self._n_columns

    def get_row(self, row_index: int) -> Tuple[Widget, ...]:
        """获取指定行的所有widget"""
        if 0 <= row_index < len(self._rows):
            return tuple(self._rows[row_index])
        raise IndexError(f"row_index {row_index} out of range")

    def widget_at(self, row_index: int, column_index: int) -> Widget:
        """获取指定位置的widget"""
        if 0 <= row_index < len(self._rows) and 0 <= column_index < self._n_columns:
            return self._rows[row_index][column_index]
        raise IndexError(f"position ({row_index}, {column_index}) out of range")

    def rows(self) -> Tuple[Tuple[Widget, ...], ...]:
        """返回所有行"""
        return tuple(tuple(row) for row in self._rows)

    def select_columns(self, *column_indices: int) -> Tuple[Tuple[Widget, ...], ...]:
        if not column_indices:
            raise ValueError("At least one column index must be specified")
        if min(column_indices) < 0:
            raise ValueError(f"column index {min(column_indices)} out of range")

        if max(column_indices) >= self._n_columns:
            raise ValueError(f"column index {max(column_indices)} out of range")
        return tuple(
            tuple(row[col_index] for col_index in column_indices) for row in self._rows
        )

    def select_column(self, column_index: int) -> Tuple[Widget, ...]:
        if column_index < 0:
            raise ValueError(f"column index {column_index} out of range")
        if column_index >= self._n_columns:
            raise ValueError(f"column index {column_index} out of range")
        return tuple(row[column_index] for row in self._rows)

    def scroll_to_top(self):
        """滚动到顶部"""
        self._canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """滚动到底部"""
        self._canvas.yview_moveto(1)

    def _update_scroll_area(self):
        """更新滚动区域"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _rearrange_rows(self):
        """重新排列所有行"""
        for row_index, row_widgets in enumerate(self._rows):
            for col_index, widget in enumerate(row_widgets):
                config = self._column_configs[col_index]
                sticky = STICKY_MAP.get(
                    config.anchor.lower(), DEFAULT_STICKY
                )  # 默认水平填充
                widget.grid(
                    row=row_index, column=col_index, sticky=sticky, padx=1, pady=1
                )


#######################################################################################
# 注意：
# ParameterWidgetArea继承自NColumnScrollableArea类，用于管理多个BaseParameterWidget。
# 不要使用基类提供的增删改查方法，而是使用ParameterWidgetArea提供的接口方法来管理参数控件。
#######################################################################################


class ParameterAlreadyExists(Exception):
    pass


class ParameterNotFound(Exception):
    pass


class ParameterWidgetArea(NColumnScrollableArea):

    def __init__(
        self,
        parent: Optional[Widget],
        label_anchor: str = E + W,
        parameter_anchor: str = E + W,
        parameter_infos: Optional[Dict[str, ParameterInfo]] = None,
        **kwargs,
    ):
        self._tooltips: Dict[str, ToolTip] = {}
        self._parameter_infos = parameter_infos or {}

        super().__init__(
            parent,
            n_columns=3,
            column_configs=(
                ColumnConfig(anchor=label_anchor, weight=0),
                ColumnConfig(anchor=parameter_anchor, weight=1),
                ColumnConfig(anchor=E + W, weight=0),
            ),
            **kwargs,
        )

    def _create_parameter_widgets(
        self, parameter_name: str, config: BaseParameterWidgetConfig
    ) -> Tuple[Label, BaseParameterWidget, Label]:
        cls = config.target_widget_class()

        # 某些类的些控件可能需在实例化前对config进行一些处理
        # 因此需调用on_post_process_config()类方法
        parameter_info = self._parameter_infos.get(parameter_name, None)
        config = cls.on_post_process_config(
            config,
            parameter_name,
            parameter_info,
        )

        input_widget = cls.new(
            parent=self._inner_frame, parameter_name=parameter_name, config=config
        )
        param_name_label = Label(self._inner_frame, text=input_widget.label)
        if config.description:
            global _DESCRIPTION_ICON
            if _DESCRIPTION_ICON is None:
                _DESCRIPTION_ICON = PhotoImage(file=_DESCRIPTION_ICON_FILE)
            description_label = Label(
                self._inner_frame,
                # borderwidth=1,
                relief="flat",
                takefocus=False,
                # bg="lightyellow",
                image=_DESCRIPTION_ICON,
            )
            tooltip = ToolTip(description_label, input_widget.description)
            self._tooltips[parameter_name] = tooltip
        else:
            description_label = Label(self._inner_frame)

        return param_name_label, input_widget, description_label

    def has_parameter(self, parameter_name: str) -> bool:
        for w in self.select_column(1):
            w: BaseParameterWidget
            if w.parameter_name == parameter_name:
                return True
        return False

    def add_parameter(self, parameter_name: str, config: BaseParameterWidgetConfig):
        if not parameter_name.strip():
            raise ValueError("parameter_name cannot be empty")

        if self.has_parameter(parameter_name):
            raise ParameterAlreadyExists(f"parameter {parameter_name} already exists")

        param_name_label, input_widget, description_label = (
            self._create_parameter_widgets(parameter_name, config)
        )
        self.add_row((param_name_label, input_widget, description_label))
        if config.hide_label:
            param_name_label.grid_remove()

    def remove_parameter(self, parameter_name: str):
        for index in range(self.row_count()):
            widget = self.get_row(index)[1]
            assert isinstance(widget, BaseParameterWidget)
            if widget.parameter_name == parameter_name:
                if widget.parameter_name in self._tooltips:
                    self._tooltips[widget.parameter_name].destroy()
                    del self._tooltips[widget.parameter_name]
                self.remove_row(index)
                return
        raise ParameterNotFound(f"parameter {parameter_name} not found")

    def clear_parameters(self):
        for tooltip in self._tooltips.values():
            tooltip.destroy()
        self._tooltips.clear()
        self.clear()

    def get_parameter_widget(
        self, parameter_name: str
    ) -> Optional[BaseParameterWidget]:
        for w in self.select_column(1):
            w: BaseParameterWidget
            if w.parameter_name == parameter_name:
                return w
        return None

    def get_parameter_value(self, parameter_name: str) -> Union[Any, InvalidValue]:
        widget = self.get_parameter_widget(parameter_name)
        if widget is None:
            raise ParameterNotFound(f"parameter {parameter_name} not found")
        return widget.get_value()

    def get_parameter_values(self) -> Dict[str, Union[Any, InvalidValue]]:
        widgets: Tuple[BaseParameterWidget, ...] = self.select_column(1)
        return {w.parameter_name: w.get_value() for w in widgets}

    def set_parameter_value(
        self, parameter_name: str, value: Any
    ) -> Union[Any, InvalidValue]:
        widget = self.get_parameter_widget(parameter_name)
        if widget is None:
            raise ParameterNotFound(f"parameter {parameter_name} not found")
        return widget.set_value(value)

    def update_parameter_values(
        self, parameter_values: Dict[str, Any], ignore_not_exist: bool = False
    ) -> Dict[str, Union[Any, InvalidValue]]:
        ret = {}
        for parameter_name, value in parameter_values.items():
            widget = self.get_parameter_widget(parameter_name)
            if not widget:
                if ignore_not_exist:
                    continue
                raise ParameterNotFound(f"parameter {parameter_name} not found")
            else:
                ret_value = widget.set_value(value)
                ret[parameter_name] = ret_value
        return ret
