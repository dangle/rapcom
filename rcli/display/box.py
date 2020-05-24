import contextlib
import functools

from . import terminal
from .io import AppendIOBase
from .util import visible_len, remove_invisible_characters
from .style import Style, Reset


class BoxIO(AppendIOBase):
    def __init__(self, box_):
        super().__init__()
        self._box = box_
        self._style = Style.current()
        self._sep = remove_invisible_characters(self._box._get_sep())

    def write(self, s):
        super().write(f"{Style.current() if s != self._sep else ''}{s}")

    def update_line(self, s):
        current_style = Style.current()
        cleaned_s = remove_invisible_characters(s)
        if cleaned_s[:2] == self._sep[:2] and cleaned_s[-2:] == self._sep[-2:]:
            return f"{self._style}{s}{current_style}"
        left = " ".join(f"{box[1]}{box[0]._vertical}" for box in Box._stack)
        return functools.reduce(
            lambda r, b: self._get_right_append(r, b[0], *b[1]),
            zip(range(len(Box._stack) - 1, -1, -1), reversed(Box._stack)),
            f"{self._style}{left} {current_style}{s}{self._style}",
        ) + str(current_style)

    def _get_right_append(self, current, i, box_, style):
        num_spaces = (
            (box_._size or terminal.cols())
            - visible_len(current)
            - visible_len(box_._vertical)
            - i * 2
        )
        return f"{current}{style}{' ' * num_spaces}{box_._vertical}"


class Box:
    _depth = 0
    _stack = []

    def __init__(
        self,
        upper_left="\u250C",
        upper_right="\u2510",
        lower_left="\u2514",
        lower_right="\u2518",
        horizontal="\u2500",
        vertical="\u2502",
        sep_left="\u251C",
        sep_horizontal="\u2500",
        sep_right="\u2524",
        size=None,
    ):
        self._upper_left = upper_left
        self._upper_right = upper_right
        self._lower_left = lower_left
        self._lower_right = lower_right
        self._horizontal = horizontal
        self._vertical = vertical
        self._sep_left = sep_left
        self._sep_horizontal = sep_horizontal
        self._sep_right = sep_right
        self._size = size

    def top(self):
        print(
            self._line(
                self._horizontal,
                self._upper_left,
                self._upper_right + str(Reset()),
            ),
            flush=True,
        )

    def sep(self):
        print(self._get_sep(), sep="", flush=True)

    def bottom(self):
        print(
            self._line(
                self._horizontal,
                self._lower_left,
                self._lower_right + str(Reset()),
            ),
            flush=True,
        )

    def _set_size(self, size):
        self._size = size

    def _line(self, char, start, end):
        size = self._size or terminal.cols()
        width = size - 4 * (Box._depth - 1)
        return f"{start}{char * (width - 2)}{end}"

    def _create_buffer(self):
        return BoxIO(self)

    def _get_sep(self):
        return self._line(
            self._sep_horizontal, self._sep_left, self._sep_right
        )

    def __enter__(self):
        Box._depth += 1
        self.top()
        Box._stack.append((self, Style.current()))
        return self

    def __exit__(self, *args, **kwargs):
        Box._stack.pop()
        self.bottom()
        Box._depth -= 1

    @staticmethod
    def new_style(*args, **kwargs):
        @contextlib.contextmanager
        def inner(**kw):
            impl = Box(*args, **kwargs)
            if "size" in kw:
                impl._set_size(kw["size"])
            with impl, contextlib.redirect_stdout(impl._create_buffer()):
                yield impl

        return inner


Box.simple = Box.new_style()
Box.thick = Box.new_style(
    "\u250F",
    "\u2513",
    "\u2517",
    "\u251B",
    "\u2501",
    "\u2503",
    "\u2523",
    "\u2501",
    "\u252B",
)
Box.info = Box.new_style(
    "\u250F",
    "\u2513",
    "\u2517",
    "\u251B",
    "\u2501",
    "\u2503",
    "\u2520",
    "\u2500",
    "\u2528",
)
Box.ascii = Box.new_style("+", "+", "+", "+", "=", "|", "+", "-", "+")
Box.star = Box.new_style("*", "*", "*", "*", "*", "*", "*", "*", "*")
Box.double = Box.new_style(
    "\u2554",
    "\u2557",
    "\u255A",
    "\u255D",
    "\u2550",
    "\u2551",
    "\u2560",
    "\u2550",
    "\u2563",
)
Box.fancy = Box.new_style("\u2552", "\u2555", "\u2558", "\u255B", "\u2550")
Box.round = Box.new_style("\u256D", "\u256E", "\u2570", "\u256F")

box = Box.simple
