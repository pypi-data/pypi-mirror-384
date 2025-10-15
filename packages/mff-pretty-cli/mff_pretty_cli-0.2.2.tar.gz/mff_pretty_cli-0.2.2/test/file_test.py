#!/bin/env -S python3 -u


from pathlib import Path
from pretty_cli import PrettyCli


ANSI_RESET   = "\u001b[0m"
ANSI_RED     = "\u001b[31m"
ANSI_GREEN   = "\u001b[32m"
ANSI_YELLOW  = "\u001b[33m"


def print_color_example(cli: PrettyCli) -> None:
    cli.main_title("my example file:\nAmazing")
    cli.print("Hello, world!")
    cli.print(f"{ANSI_YELLOW}你好！{ANSI_RESET}")
    cli.big_divisor() # Divisors, titles, etc. add blank space above/under as needed.
    cli.print(f"Let's print a green dict:{ANSI_GREEN}")
    cli.blank() # Add a blank if the previous line is not blank already.
    cli.blank()
    cli.blank()
    cli.print({ # Enforces nice alignment of dict contents.
        "foo": "bar",
        "nested": { "hi": "there" },
        "another one": { "how": "are you?", "fine": "thanks" },
    })
    cli.print(f"{ANSI_RESET}Done.")
    cli.small_divisor()
    cli.print(f"Some {ANSI_RED}HEADER{ANSI_RESET} styles:")
    cli.chapter("a chapter")
    cli.subchapter("a sub-chapter")
    cli.section("a section")
    cli.print("That's all, folks!")


def main():
    # Test we're running from the top-level
    assert Path(".gitignore").is_file()
    assert Path("pretty_cli").is_dir()

    scratch = Path("scratch")
    if not scratch.is_dir():
        scratch.mkdir(parents=False, exist_ok=False)

    cli_strip = PrettyCli(log_file=scratch / "file_test.log")
    cli_preserve = PrettyCli(log_file=scratch / "file_test_color.log", strip_ansi=False)

    print("[ Stripping Color ]")
    print_color_example(cli_strip)
    print()
    print("[ Preserving Color ]")
    print_color_example(cli_preserve)


if __name__ == "__main__":
    main()
