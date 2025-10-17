# /#! /usr/bin/env python3

# keyhandler.py
# Author: Luxforge
# Utility to handle keypresses in the terminal

from foundry.logger.logger import logger

class KeyHandler:
    """
    Handle keypresses in the terminal, including special keys.
    """

    mapping = {
        # UNIX special keys
        '\x1b[A': 'UP',
        '\x1b[B': 'DOWN',
        '\x1b[C': 'RIGHT',
        '\x1b[D': 'LEFT',
        '\n': 'ENTER',
        '\r': 'ENTER',
        '\x08': 'BACKSPACE',
        '\x7f': 'BACKSPACE',
        '\x1b': 'ESC',
        ' ': 'SPACE',
        'TAB': 'TAB',

        # Windows special keys
        b'\xe0H': 'UP',
        b'\xe0P': 'DOWN',
        b'\xe0K': 'LEFT',
        b'\xe0M': 'RIGHT',
        b'\r': 'ENTER',
        b'\n': 'ENTER',
        b'\x08': 'BACKSPACE',
        b'\x1b': 'ESC',
        b' ': 'SPACE',
        b'\t': 'TAB',

        # Unicode glyphs
        '↑': 'UP',
        '↓': 'DOWN',
        '←': 'LEFT',
        '→': 'RIGHT',
        '⏎': 'ENTER',
        '⎋': 'ESC',
        '⌫': 'BACKSPACE'
    }

    def __init__(self):
        import os
        self.IS_WINDOWS = os.name == 'nt'
        self.IS_UNIX = os.name == 'posix'

        if self.IS_UNIX:
            import termios
            import tty
            import sys
            # Store the imported modules as instance variables
            self.termios = termios # termios module for terminal I/O
            self.tty = tty # tty module for terminal control
            self.sys = sys # sys module for system operations

        elif self.IS_WINDOWS:
            import msvcrt
            self.msvcrt = msvcrt # msvcrt module for Windows console I/O
        else:
            raise EnvironmentError("Unsupported OS for KeyHandler. Only Windows and Unix-like systems are supported.")
        
        self.typed = "" # Store typed characters

    def get_key(self):
        """
        Wait for a keypress and return the interpreted key.
        PARAM selected_key: Optional currently selected key (for context)
        """
        
        # Call the appropriate method based on the OS
        if self.IS_WINDOWS:
            return self.__get_windows_key()
        elif self.IS_UNIX:
            return self.__get_unix_key()
        else:
            raise EnvironmentError("Unsupported OS for KeyHandler. Only Windows and Unix-like systems are supported.")
        
    def __get_unix_key(self):
        """
        Handle keypresses specifically for Unix-like systems using termios and tty.
        """
        logger.debug("Unix-like system detected for keypress handling. Waiting for key...")
        # Get the file descriptor for stdin
        fd = self.sys.stdin.fileno()

        # Save the current terminal settings
        old = self.termios.tcgetattr(fd)

        # Set terminal to raw mode
        try:
            self.tty.setraw(fd)
            
            # Read a single character
            ch1 = self.sys.stdin.read(1)
            
            # Handle escape sequences for special keys
            if ch1 == '\x1b':
                ch2 = self.sys.stdin.read(2)
                return ch1 + ch2
            
            # Return the single character for regular keys
            return ch1
        
        # Restore the original terminal settings
        finally:
            self.termios.tcsetattr(fd, self.termios.TCSADRAIN, old)

    def interpret(self, raw_key):
        """
        Interpret the raw key input and return a standardized representation.
        PARAM raw_key: The raw key input from get_key()
        """
        logger.debug(f"Interpreting raw key: {raw_key}")

        mapping = self.mapping

        # Full alphabet mapping - passthrough
        if len(raw_key) == 1 and raw_key.isalpha():
            logger.debug(f"Alphabetic key detected: {raw_key}")
            return raw_key.upper()

        # Digit passthrough
        if len(raw_key) == 1 and raw_key.isdigit():
            logger.debug(f"Digit key detected: {raw_key}")
            return raw_key

        # Return mapped value or the raw key if not found
        mapped_key = mapping.get(raw_key, None)

        # Log if no mapping found
        if mapped_key is None:
            logger.warning(f"Unrecognized key input: {raw_key}. Returning raw key.")
            return raw_key

        if mapped_key == raw_key:
            logger.error(f"Seem to be in a loop with key: {raw_key}. Check calls.")
        else:
            logger.debug(f"Mapped key: {raw_key} -> {mapped_key}")
        return mapped_key

    def __get_windows_key(self):
        """
        Handle keypresses specifically for Windows using msvcrt.
        """

        logger.debug("Windows system detected for keypress handling. Waiting for key... ")
        
        first = self.msvcrt.getch()
        if first in {b'\x00', b'\xe0'}:
            logger.debug(f"Special key prefix detected: {first}. Waiting for second byte...")
            second = self.msvcrt.getch()
            # Set a break if in debug mode
            if logger.debug:
                pass
                # input(f"DEBUG -- Special key detected: {first + second}. Press Enter to continue...")
            return self.interpret(first + second)
        else:
            if logger.debug:
                pass
                # input(f"DEBUG -- Regular key detected: {first}. Press Enter to continue...")
            logger.debug(f"Regular key detected: {first}. ")
            
            # Append to typed buffer if alphanumeric - need to keep ENTER, BACKSPACE, etc out
            if first.decode(errors='ignore').isalnum():
                first = first.decode()
            return self.interpret(first)

    def reset(self):
        self.typed = ""

    def get_typed(self):
        return self.typed
    
    def glyph(self, key: str) -> str:
        """
        Return the Unicode glyph for a given key name.
        """
        return self.glyph_map.get(key, key)