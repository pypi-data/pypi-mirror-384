"""
This package provides `PrettyCli`, a utility class for structured printing in the CLI.
"""

import re
from os import PathLike
from dataclasses import asdict, is_dataclass
from typing import Any, List, Optional


ANSI_REGEX = re.compile("\u001b\\[[^A-Za-z]*[A-Za-z]")


class PrettyCli:
    """
    Simple opinionated pretty-printing for the terminal, with an option to copy the output to file.

        Use `cli.print()` for basic printing; `cli.blank()` for ensuring separation between elements, and `cli.main_title()`, `cli.chapter()`, `cli.subchapter()`, `cli.section()` for different header styles.
        Includes `cli.big_separator()` and `cli.small_separator()` for dividing lines.

        Parameters
        ----------
        log_file: PathLike, default=None
            If set to a valid path, everything printed to stdout will also be printed to the file (similar to using tee).

        strip_ansi: bool, default=True
            If `log_file` is set, indicates wether ANSI escape codes (e.g., terminal color codes) should be removed before printing to file.
    """

    def __init__(self, log_file: Optional[PathLike] = None, strip_ansi: bool = True):
        self.previous_line_blank = True # Used to decide if whitespace should be added above.
        self.indent = " " * 4

        if log_file is not None:
            self.log_file = log_file
            self._log_file_handle = open(log_file, mode="w", encoding="utf-8", buffering=1)
            self.strip_ansi = strip_ansi
        else:
            self.log_file = None
            self._log_file_handle = None

    def __del__(self):
        if self._log_file_handle is not None:
            self._log_file_handle.close()

    def _print(self, text: str, end: Optional[str] = None) -> None:
            print(text, end=end)
            if self._log_file_handle is not None:
                if self.strip_ansi:
                    text = ANSI_REGEX.sub("", text)
                print(text, end=end, file=self._log_file_handle)

    def blank(self) -> None:
        """
        Add a blank line, IF the previous line was not blank as well.
        """
        if not self.previous_line_blank:
            self._print("")
            self.previous_line_blank = True

    def print(self, obj: Any, *, end: Optional[str] = None) -> None:
        """
        Base block for CLI pretty-printing.

        * Manages state for blank lines.
        * For dicts: calls self.print_dict()
        * For others: casts to str and strips trailing whitespace.
        * end keyword is NOT respected for dicts. Otherwise works like print().
        """
        if isinstance(obj, dict): # Pretty-print dicts.
            self._print_dict(obj)
            self.blank()
        elif is_dataclass(obj) and not isinstance(obj, type): # Treat dataclass objects as dicts.
            self._print_dict(asdict(obj))
            self.blank()
        else: # Default behavior: stringify the object and print it.
            text = str(obj).rstrip()
            self._print(text, end)
            self.previous_line_blank = False

    def main_title(self, text: str) -> None:
        """
        Use this to make a title at the beginning of the run.

        * Strips whitespace and casts to uppercase.
        * Encases in a big box.
        """
        side_padding : int =  24
        lines : List[str] = [line.strip().upper() for line in text.strip().split("\n")]

        max_len : int = 0
        for line in lines:
            max_len = max(max_len, len(line))

        cap_line = "=" * (max_len + 2 * (side_padding + 1))

        self.blank()
        self.print(cap_line)
        for line in lines:
            overflow = len(cap_line) - len(line) - 2
            left_pad = "=" * (overflow // 2)
            right_pad = "=" * (overflow - len(left_pad))
            self.print(f"{left_pad} {line} {right_pad}")
        self.print(cap_line)
        self.blank()

    def chapter(self, text: str) -> None:
        """
        Use this to separate major parts in the script.

        * Strips whitespace and capitalizes.
        * Adds = to the sides.
        """
        capitalized = text.strip().title()
        side_padding = "=" * 16
        line = f"{side_padding} {capitalized} {side_padding}"

        self.blank()
        self.print(line)
        self.blank()

    def subchapter(self, text: str) -> None:
        """
        Use this if you need a division bigger than a section but smaller than a chapter.

        * Strips whitespace and capitalizes.
        * Adds - to the sides.
        """
        capitalized = text.strip().title()
        side_padding = "-" * 8
        line = f"{side_padding} {capitalized} {side_padding}"

        self.blank()
        self.print(line)
        self.blank()

    def section(self, text: str) -> None:
        """
        Use this to separate minor parts in the script.

        * Strips whitespace and capitalizes.
        * Encases in [].
        """
        capitalized = text.strip().title()

        self.blank()
        self.print(f"[{capitalized}]")
        self.blank()

    def big_divisor(self) -> None:
        """
        Adds a horizontal line (32 '=') surrounded by blanks.
        """
        self.blank()
        self.print("=" * 32)
        self.blank()

    def small_divisor(self) -> None:
        """
        Adds a horizontal line (16 '-') surrounded by blanks.
        """
        self.blank()
        self.print("-" * 16)
        self.blank()

    def _size_dict(self, d: dict, depth: int) -> int:
        """
        Used internally to align all values when pretty-printing a dict.
        """
        prefix = self.indent * depth

        max_len = 0
        for (key, value) in d.items():
            key_len = len(str(key)) + len(prefix) + 2
            max_len = max(max_len, key_len)

            if type(value) is dict:
                child_len = self._size_dict(value, depth + 1)
                max_len = max(max_len, child_len)

        return max_len

    def _print_dict(self, d: dict, depth: int = 0, max_len: Optional[int] = None) -> None:
        """
        Used internally to pretty-print dicts.

        * Prints one "Key: Value" pair per line.
        * Prints sub-dicts hierarchically, with indenting.
        * Pre-calculates the space taken by all printed keys (including sub-dicts) and left-aligns all values to the same column.
        """
        prefix = self.indent * depth
        if max_len is None:
            max_len = self._size_dict(d, depth)

        for (key, value) in d.items():
            if type(value) is dict:
                self.print(f"{prefix}{key}:")
                self._print_dict(value, depth + 1, max_len)
            else:
                self.print(f"{prefix}{key}:".ljust(max_len) + f"{value}")
