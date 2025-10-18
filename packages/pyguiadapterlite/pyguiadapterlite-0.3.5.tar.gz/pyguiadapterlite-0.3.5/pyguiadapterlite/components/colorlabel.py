from tkinter import Label, Widget, colorchooser
from typing import Optional, Literal

from pyguiadapterlite.utils import get_contrast_color


class ColorLabel(Label):
    def __init__(
        self,
        parent: Widget,
        initial_color: str = "#FFFFFF",
        color_picker: bool = True,
        color_picker_title: str = "",
        show_color_code: bool = True,
        font: tuple = ("Arial", 12, "bold"),
        width: Optional[int] = None,
        height: Optional[int] = 2,
        borderwidth: int = 1,
        relief: Optional[
            Literal["raised", "sunken", "flat", "ridge", "solid", "groove"]
        ] = "sunken",
        **kwargs,
    ):
        self._initial_color = initial_color
        self._color_picker = color_picker
        self._color_picker_title = color_picker_title
        self._show_color_code = show_color_code

        super().__init__(
            parent,
            font=font,
            bg=initial_color,
            fg=get_contrast_color(initial_color),
            justify="center",
            height=height,
            width=width,
            borderwidth=borderwidth,
            relief=relief,
            **kwargs,
        )
        self._update_display()

        self.bind("<Button-1>", self._pick_color)

    @property
    def current_color(self) -> str:
        return self.cget("bg")

    @current_color.setter
    def current_color(self, color: str):
        self.config(bg=color)
        self._update_display()

    def _update_display(self):
        current_color = self.cget("bg")
        if self._show_color_code:
            self.config(
                text=f"#{current_color[1:]}", fg=get_contrast_color(current_color)
            )

    def _pick_color(self, event):
        color_code = colorchooser.askcolor(
            parent=self,
            initialcolor=self.current_color,
            title=self._color_picker_title,
        )
        if color_code[0] is None:
            return
        self.current_color = color_code[1]


if __name__ == "__main__":
    from tkinter import Tk

    root = Tk()
    color_label = ColorLabel(
        root,
        initial_color="#FF0000",
        color_picker=True,
        show_color_code=True,
    )
    color_label.pack()
    root.mainloop()
