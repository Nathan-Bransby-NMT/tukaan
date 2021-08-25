import re
from typing import Any, Callable, List, Literal, Tuple, Union

from ._platform import Platform
from .utils import TukaanError

# This module can't use anything that relies on get_tcl_interp,
# so it has its own each of those, which isn't a good thing :(


def updated(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        self.tcl_call(None, "update", "idletasks")
        result = func(self, *args, **kwargs)
        self.tcl_call(None, "update", "idletasks")
        return result

    return wrapper


def update_before(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        self.tcl_call(None, "update", "idletasks")
        return func(self, *args, **kwargs)

    return wrapper


def update_after(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        self.tcl_call(None, "update", "idletasks")
        return result

    return wrapper


# FIXME: the name 'windowmanager' is dumb because
# this class contains not only wm stuff, but all the other methods and properties
# needed for App and Window objects
class WindowManager:
    tcl_call: Callable
    wm_path: str
    tcl_path: str

    def maximize(self):
        if self.tcl_call(None, "tk", "windowingsystem") == "win32":
            self.tcl_call(None, "wm", "state", self.wm_path, "zoomed")
        else:
            self.tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", True)

    def restore(self):
        if self.tcl_call(None, "tk", "windowingsystem") == "win32":
            self.tcl_call(None, "wm", "state", self.wm_path, "normal")
        else:
            self.tcl_call(None, "wm", "attributes", self.wm_path, "-zoomed", False)

    def iconify(self):
        self.tcl_call(None, "wm", "iconify", self.wm_path)

    def deiconify(self):
        self.tcl_call(None, "wm", "deiconify", self.wm_path)

    @property
    def fullscreen(self):
        return self.tcl_call(bool, "wm", "attributes", self.wm_path, "-fullscreen")

    @fullscreen.setter
    def fullscreen(self, is_fullscreen):
        # todo: bind f11
        self.tcl_call(
            None, "wm", "attributes", self.wm_path, "-fullscreen", is_fullscreen
        )

    @property  # type: ignore
    @update_before
    def size(self) -> tuple:
        return tuple(
            map(
                int,
                re.split(r"x|\+", self.tcl_call(str, "wm", "geometry", self.wm_path))[
                    :2
                ],
            )
        )

    @size.setter  # type: ignore
    @update_after
    def size(self, size: Union[Tuple, List, int]) -> None:
        if isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        elif isinstance(size, int):
            width = height = size
        width, height = tuple(
            map(
                lambda a: self.tcl_call(int, "winfo", "pixels", ".", a),
                (width, height),
            )
        )
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"{width}x{height}")

    @property  # type: ignore
    @update_before
    def position(self) -> Tuple:
        return tuple(
            map(
                int,
                re.split(r"x|\+", self.tcl_call(str, "wm", "geometry", self.wm_path))[
                    2:
                ],
            )
        )

    @position.setter  # type: ignore
    @update_after
    def position(
        self,
        position: Union[
            int,
            Tuple,
            List,
            Union[
                Literal["center"],
                Literal["top-left"],
                Literal["top-right"],
                Literal["bottom-left"],
                Literal["bottom-right"],
            ],
        ],
    ):
        if position in {
            "center",
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
        }:
            if position == "center":
                x = int(
                    (self.tcl_call(int, "winfo", "screenwidth", self.wm_path) / 2)
                    - (self.width / 2)
                )
                y = int(
                    (self.tcl_call(int, "winfo", "screenheight", self.wm_path) / 2)
                    - (self.height / 2)
                )
            elif position == "top-left":
                x = y = 0
            elif position == "top-right":
                x = int(
                    self.tcl_call(int, "winfo", "screenwidth", self.wm_path)
                    - self.width
                )
                y = 0
            elif position == "bottom-left":
                x = 0
                y = int(
                    self.tcl_call(int, "winfo", "screenheight", self.wm_path)
                    - self.height
                )
            elif position == "bottom-right":
                x = int(
                    self.tcl_call(int, "winfo", "screenwidth", self.wm_path)
                    - self.width
                )
                y = int(
                    self.tcl_call(int, "winfo", "screenheight", self.wm_path)
                    - self.height
                )
        elif isinstance(position, (tuple, list)) and len(position) > 1:
            x, y = position
        elif isinstance(position, int):
            x = y = position
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"+{x}+{y}")

    @property  # type: ignore
    def bbox(self):
        # TODO: bottom border hack

        window_border_width = self.x - self.position[0]
        title_bar_height = self.root_y - self.position[1]

        x1 = self.position[0]
        y1 = self.root_y - title_bar_height
        x2 = self.root_x + self.width + window_border_width
        y2 = self.y + self.height

        return (x1, y1, x2, y2)

    @property  # type: ignore
    @update_before
    def x(self):
        return self.tcl_call(int, "winfo", "x", self.wm_path)

    @x.setter  # type: ignore
    @update_after
    def x(self, x):
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"{x}x{self.y}")

    @property  # type: ignore
    @update_before
    def y(self):
        return self.tcl_call(int, "winfo", "y", self.wm_path)

    @y.setter  # type: ignore
    @update_after
    def y(self, y):
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"{self.x}x{y}")

    @property  # type: ignore
    @update_before
    def root_x(self):
        return self.tcl_call(int, "winfo", "rootx", self.wm_path)

    @property  # type: ignore
    @update_before
    def root_y(self):
        return self.tcl_call(int, "winfo", "rooty", self.wm_path)

    @property  # type: ignore
    @update_before
    def width(self):
        return self.tcl_call(int, "winfo", "width", self.wm_path)

    @width.setter  # type: ignore
    @update_after
    def width(self, width):
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"{width}x{self.height}")

    @property  # type: ignore
    @update_before
    def height(self):
        return self.tcl_call(int, "winfo", "height", self.wm_path)

    @height.setter  # type: ignore
    @update_after
    def height(self, height):
        self.tcl_call(None, "wm", "geometry", self.wm_path, f"{self.width}x{height}")

    @property  # type: ignore
    @update_before
    def minsize(self):
        return self.tcl_call(None, "wm", "minsize", self.wm_path)

    @minsize.setter  # type: ignore
    @update_after
    def minsize(self, size):
        if isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        else:
            width = height = size
        self.tcl_call(None, "wm", "minsize", self.wm_path, width, height)

    @property  # type: ignore
    @update_before
    def maxsize(self):
        return self.tcl_call(None, "wm", "maxsize", self.wm_path)

    @maxsize.setter  # type: ignore
    @update_after
    def maxsize(self, size):
        if isinstance(size, (tuple, list)) and len(size) > 1:
            width, height = size
        else:
            width = height = size
        self.tcl_call(None, "wm", "maxsize", self.wm_path, width, height)

    @property
    def title(self) -> str:
        return self.tcl_call(None, "wm", "title", self.wm_path, None)

    @title.setter
    def title(self, new_title: str = None):
        self.tcl_call(None, "wm", "title", self.wm_path, new_title)

    @property
    def topmost(self) -> bool:
        return self.tcl_call(bool, "wm", "attributes", self.wm_path, "-topmost")

    @topmost.setter
    def topmost(self, istopmost: bool = False):
        self.tcl_call(None, "wm", "attributes", self.wm_path, "-topmost", istopmost)

    @property
    def transparency(self) -> Union[int, float]:
        return self.tcl_call(float, "wm", "attributes", self.wm_path, "-alpha")

    @transparency.setter
    def transparency(self, alpha: Union[int, float] = False):
        self.tcl_call(None, "tkwait", "visibility", self.wm_path)
        self.tcl_call(None, "wm", "attributes", self.wm_path, "-alpha", alpha)

    @property
    def resizable(self):
        return self._resizable

    @resizable.setter
    def resizable(
        self,
        direction: Union[
            Literal["none"], Literal["horizontal"], Literal["vertical"], Literal["both"]
        ],
    ):
        resize_dict = {
            "none": (False, False),
            "horizontal": (True, False),
            "vertical": (False, True),
            "both": (True, True),
        }
        try:
            width, height = resize_dict[direction]
        except KeyError:
            raise TukaanError(
                f"invalid resizable value: {direction!r}. Allowed values: 'none', 'horizontal' 'vertical', 'both'"
            )
        self._resizable = direction
        self.tcl_call(None, "wm", "resizable", self.wm_path, width, height)

    @property
    def user_last_active(self):
        return self.tcl_call(int, "tk", "inactive") / 1000

    @property
    def scaling(self):
        self.tcl_call(int, "tk", "scaling", "-displayof", self.wm_path)

    @scaling.setter
    def scaling(self, factor):
        self.tcl_call(None, "tk", "scaling", "-displayof", self.wm_path, factor)

    def _get_theme_aliases(self):
        # available_themes will use this
        theme_dict = {"clam": "clam", "legacy": "default", "native": "clam"}

        if Platform.windowing_system == "win32":
            theme_dict["native"] = "vista"
        elif Platform.windowing_system == "aqua":
            theme_dict["native"] = "aqua"

        return theme_dict

    @property
    def theme(self):
        theme_dict = {"clam": "clam", "default": "legacy"}

        if Platform.windowing_system == "win32":
            theme_dict["vista"] = "native"
        elif Platform.windowing_system == "aqua":
            theme_dict["aqua"] = "native"

        result = self.tcl_call(str, "ttk::style", "theme", "use")
        return theme_dict[result]

    @theme.setter
    def theme(self, theme):
        self.tcl_call(
            None, "ttk::style", "theme", "use", self._get_theme_aliases()[theme]
        )