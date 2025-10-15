# Pretty-CLI: Pretty Printing for the CLI

This package provides `PrettyCli`, a utility class for structured printing in the CLI. Simply use its `print()` and helper methods instead of the default `print()` and you're good to go!

The package is available in PyPi as `mff-pretty-cli`. You can install it with:
```sh
pip install mff-pretty-cli
```

Here is a full example of the available function calls:

```python
from pretty_cli import PrettyCli


cli = PrettyCli()

cli.main_title("my example file:\nAmazing")

cli.print("Hello, world!")
cli.print("你好！")

cli.big_divisor() # Divisors, titles, etc. add blank space above/under as needed.

cli.print("Let's print a dict:")
cli.blank() # Add a blank if the previous line is not blank already.
cli.blank()
cli.blank()
cli.print({ # Enforces nice alignment of dict contents.
    "foo": "bar",
    "nested": { "hi": "there" },
    "another one": { "how": "are you?", "fine": "thanks" },
})

cli.small_divisor()

cli.print("Some header styles:")
cli.chapter("a chapter")
cli.subchapter("a sub-chapter")
cli.section("a section")
cli.print("That's all, folks!")
```

And the produced output:

```
==================================================================
======================== MY EXAMPLE FILE: ========================
============================ AMAZING =============================
==================================================================

Hello, world!
你好！

================================

Let's print a dict:

foo:         bar
nested:
    hi:      there
another one:
    how:     are you?
    fine:    thanks

----------------

Some header styles:

================ A Chapter ================

-------- A Sub-Chapter --------

[A Section]

That's all, folks!
```

## Dataclass Support

By default, dataclasses are converted to dicts. This code:

```python
import math
from dataclasses import dataclass
from pretty_cli import PrettyCli


@dataclass
class MyData:
    some_int: int
    some_float: float
    some_string: str


cli = PrettyCli()

my_data = MyData(
    some_int=42,
    some_float=math.pi,
    some_string="Lorem ipsum dolor sit amet.",
)

cli.print(my_data)
```

Produces this output:

```
some_int:    42
some_float:  3.141592653589793
some_string: Lorem ipsum dolor sit amet.
```

## Replicating to File

Sometimes, we want to save a copy of the output to a log file. In Unix systems, one can use `tee`:

```sh
echo "Hi there" | tee hi.log
```

However, this is inconvenient in more complicated scenarios. For example, we might want to generate a timestamp within Python and use it for the file name, or we might want to strip color codes from the file output without using command-line tricks. `PrettyCli` has built-in support for replicating output to a file, with optional stripping of ANSI codes (on by default):

```python
cli = PrettyCli(log_file="path/to/file", strip_ansi=False) # strip_ansi defaults to True.
```
