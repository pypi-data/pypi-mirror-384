# !/usr/bin/env python3

# Colour definitions for terminal output
# Author: Luxforge

class Colours:
    GRAY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    ORANGE = "\033[38;5;208m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    CYBERPURPLE = "\033[38;5;201m"  # Neon pink
    DEEP_MAGENTA = "\033[38;5;165m"  # Deep magenta
    BUBBLEGUM = "\033[38;5;213m"  # Bubblegum
    RASPBERRY = "\033[38;5;200m"  # Raspberry
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"

    @staticmethod
    def colour_text( text, colour: str = None, bold: bool = False, underline: bool = False, reverse: bool = False):
        # cast colour to upper to match class attributes
        if colour:
            colour = colour.upper()
        else:
            colour = "RESET"
        if not hasattr(Colours, colour) or colour == "RESET":
            colour = Colours.RESET
        else:
            colour = getattr(Colours, colour)
        styles = [colour]
        if bold:
            styles.append(Colours.BOLD)
        if underline:
            styles.append(Colours.UNDERLINE)
        if reverse:
            styles.append(Colours.REVERSE)
        return f"{''.join(styles)}{text}{Colours.RESET}"
    @staticmethod
    def test_all():
        for colour in ["GRAY", "RED", "GREEN", "YELLOW", "ORANGE", "BLUE", "CYAN", "MAGENTA"]:
            print(Colours.colour_text(f"This is {colour.lower()} text", colour))
        print(Colours.colour_text("This is bold text", bold=True))
        print(Colours.colour_text("This is underlined text", underline=True))
        print(Colours.colour_text("This is reversed text", reverse=True))
        print(Colours.colour_text("This is normal text")) 

    @staticmethod
    def style(colour: str = None, bold=False, underline=False, reverse=False):
        colour = colour.upper() if colour else "RESET"
        if not hasattr(Colours, colour) or colour == "RESET":
            colour_code = Colours.RESET
        else:
            colour_code = getattr(Colours, colour)
        styles = [colour_code]
        if bold: styles.append(Colours.BOLD)
        if underline: styles.append(Colours.UNDERLINE)
        if reverse: styles.append(Colours.REVERSE)
        return ''.join(styles)
    
if __name__ == "__main__":
    Colours.test_all()
    for code in [201, 200, 213, 165]:
        print(f"\033[38;5;{code}mCyberpunk Purple {code}\033[0m")