from .games import GamesMenu
from .lottery import LotteryMenu  # exposed via lottery/__init__.py

# Often modified metadata
__version__ = "1.0.0"
__modified__ = "2025-10-16"

__all__ = ["GamesMenu", "LotteryMenu"]

# Metadata
__author__ = "LuxForge"
__maintainer__ = "LuxForge"
__email__ = "lab@luxforge.dev"
__license__ = "MIT"
__status__ = "Development"
__copyright__ = "© 2025 LuxForge"
__credits__ = ["LuxForge"]
__description__ = "Interactive game module for Foundry tools, featuring a joke engine and modular lottery system. Designed for expansion into trivia, puzzles, and lore-based mini-games."
__created__ = "2025-10-16"
__module__ = "foundry.games"
__tags__ = ["games", "lottery", "jokes", "interactive", "foundry"]
__interface__ = "console,cli"
__features__ = ["randomized lottery", "joke generation", "modular game logic"]
__dependencies__ = ["random", "datetime", "json"]
__compatibility__ = ["Python 3.8+", "Foundry VTT 0.8+"]
__repository__ = "https://github.com/LuxForge/LuxForge-Foundry"