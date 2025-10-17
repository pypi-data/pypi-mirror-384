from .menu import Menu
from .main_menu import MainMenu
from .keyhandler import KeyHandler

# Often modified metadata
__version__ = "1.0.0"
__modified__ = "2025-10-16"

__all__ = ["Menu", "MainMenu", "KeyHandler"]

# Metadata
__author__ = "LuxForge"
__maintainer__ = "LuxForge"
__email__ = "lab@luxforge.dev"
__license__ = "MIT"
__status__ = "Development"
__copyright__ = "© 2025 LuxForge"
__credits__ = ["LuxForge"]
__description__ = "Modular menu system for Foundry tools, supporting keyboard input, dynamic rendering, and contextual navigation."
__created__ = "2025-10-16"
__module__ = "foundry.menu"
__tags__ = ["menu", "navigation", "keyboard", "input", "foundry"]
__interface__ = "console,keyboard"
__features__ = ["dynamic menus", "key handling", "contextual rendering"]
__dependencies__ = ["os", "sys", "readline", "keyboard"]
__compatibility__ = ["Python 3.8+", "Foundry VTT 0.8+"]
__repository__ = "https://github.com/LuxForge/LuxForge-Foundry"