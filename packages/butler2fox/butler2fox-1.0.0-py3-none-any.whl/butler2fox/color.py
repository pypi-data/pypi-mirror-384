import os

COLORED_OUTPUT = os.getenv("COLORED_OUTPUT", "").lower() not in ["false", "no", "0"]


class Color:
    """Output Colouring helper class.

    See: https://notes.burke.libbey.me/ansi-escape-codes/"""

    _ESC_CALL = "\033["
    """Function call escape sequence"""
    _ESC_SGR = "m"
    """Select Graphics Rendition function"""
    BOLD = 1
    """Style: bold"""
    UNDERLINE = 2
    """Style: underline"""
    ITALIC = 4
    """Style: italic"""
    BACKGROUND = 8
    """Style: background color"""
    BRIGHT = 16
    """Style: bright color"""

    # constructor with one argument
    def __init__(self, color: str):
        self.color = color

    # colorize function
    def __call__(
        self,
        txt: str,
        style: int = 0,
    ):
        if COLORED_OUTPUT:
            if style & Color.BACKGROUND:
                tens = "10" if style & Color.BRIGHT else "4"
            else:
                tens = "9" if style & Color.BRIGHT else "3"
            return (
                Color._ESC_CALL
                + ("1;" if style & Color.BOLD else "")
                + ("3;" if style & Color.ITALIC else "")
                + ("4;" if style & Color.UNDERLINE else "")
                + tens
                + self.color
                + Color._ESC_SGR
                + str(txt)
                + Color._ESC_CALL
                + "0"
                + Color._ESC_SGR
            )
        return txt


BLACK = Color("0")
RED = Color("1")
GREEN = Color("2")
YELLOW = Color("3")
BLUE = Color("4")
PURPLE = Color("5")
CYAN = Color("6")
WHITE = Color("7")
