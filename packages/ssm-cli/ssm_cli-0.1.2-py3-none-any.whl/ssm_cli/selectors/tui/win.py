import msvcrt

UP=b"\xe0H"
DOWN=b"\xe0P"
CTRL_C=b"\x03"
ENTER=b"\r"

def getch():
    """Blocking read of a single character from stdin (arrow keys supported)."""
    ch1 = msvcrt.getch()
    if ch1 == b"\xe0":  # Escape sequence (arrow keys)
        ch3 = msvcrt.getch()
        return ch1 + ch3
    else:
        return ch1

def get_direction():
    pass