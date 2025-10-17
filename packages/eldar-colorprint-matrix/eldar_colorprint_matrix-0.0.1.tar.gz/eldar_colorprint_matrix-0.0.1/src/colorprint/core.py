import sys

COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "reset": "\033[0m",
}

def print_color(text: str, color: str = "white", bold: bool = False, end: str = "\n"):
    color_code = COLORS.get(color.lower(), COLORS["white"])
    style = "\033[1m" if bold else ""
    sys.stdout.write(f"{style}{color_code}{text}{COLORS['reset']}{end}")
