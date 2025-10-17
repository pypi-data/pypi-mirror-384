import termios
import tty
import sys

UP="\x1b[A"
DOWN="\x1b[B"
CTRL_C="\x03"
ENTER="\r"

def getch():
    """Blocking read of a single character from stdin (arrow keys supported)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch1 = sys.stdin.read(1)
        if ch1 == "\x1b":  # Escape sequence (arrow keys)
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            return ch1 + ch2 + ch3
        else:
            return ch1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
