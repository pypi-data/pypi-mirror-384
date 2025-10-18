from tkinter import IntVar
from tkinter.ttk import Frame, Checkbutton
from typing import Dict, Any, List, Union, Iterable

_CB_OFF = object()


class MultipleChoiceBox(Frame):
    def __init__(
        self,
        parent,
        choices: Union[Dict[str, Any], Iterable[Any]],
        columns: int = 2,
        default_choices: List[Any] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        if default_choices is None:
            default_choices = []

        self._choices_dict = (
            choices.copy()
            if isinstance(choices, dict)
            else {str(val): val for val in choices}
        )
        self._states: Dict[str, IntVar] = {
            label: IntVar(value=0) for label in self._choices_dict
        }

        if not self._choices_dict:
            raise ValueError("choices cannot be empty")

        if columns < 1:
            columns = 1
        self._columns: int = columns
        self._checkboxes: Dict[str, Checkbutton] = {}
        self._setup_widgets()
        self.unselect_all()

        self.select(default_choices)

    def _setup_widgets(self):
        row = 0
        col = 0
        for label, value in self._choices_dict.items():
            cb = Checkbutton(
                self, text=label, variable=self._states[label], onvalue=1, offvalue=0
            )
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
            self._checkboxes[label] = cb

            col += 1
            if col >= self._columns:
                col = 0
                row += 1

    @property
    def current_values(self) -> List[Any]:
        checked_values = []
        for label, var in self._states.items():
            if var.get() == 1:
                checked_values.append(self._choices_dict[label])
        return checked_values

    @property
    def current_labels(self) -> List[str]:
        checked_labels = []
        for label, var in self._states.items():
            if var.get() == 1:
                checked_labels.append(label)
        return checked_labels

    def select(self, values: Iterable[Any]) -> List[Any]:
        unknown_values = []
        for val in values:
            labels = self._find_labes_by_value(val)
            if not labels:
                unknown_values.append(val)
                continue
            for label in labels:
                var = self._states[label]
                if var.get() == 0:
                    var.set(1)
        return unknown_values

    def unselect(self, values: Iterable[Any]) -> List[Any]:
        unknown_values = []
        for val in values:
            labels = self._find_labes_by_value(val)
            if not labels:
                unknown_values.append(val)
                continue
            for label in labels:
                var = self._states[label]
                if var.get() == 1:
                    var.set(0)
        return unknown_values

    def select_by_label(self, labels: Iterable[str]) -> List[str]:
        unknown_values = []
        for label in labels:
            var = self._states.get(label, None)
            if var is None:
                unknown_values.append(label)
                continue
            if var.get() == 0:
                var.set(1)
        return unknown_values

    def unselect_by_label(self, labels: Iterable[str]) -> List[str]:
        unknown_values = []
        for label in labels:
            var = self._states.get(label, None)
            if var is None:
                unknown_values.append(label)
                continue
            if var.get() == 1:
                var.set(0)
        return unknown_values

    def select_all(self):
        for var in self._states.values():
            var.set(1)

    def unselect_all(self):
        for var in self._states.values():
            var.set(0)

    def reverse_selection(self):
        for var in self._states.values():
            if var.get() == 1:
                var.set(0)
            else:
                var.set(1)

    def _find_labes_by_value(self, value: Any) -> List[str]:
        labels = []
        for label, val in self._choices_dict.items():
            if val == value:
                labels.append(label)
        return labels
