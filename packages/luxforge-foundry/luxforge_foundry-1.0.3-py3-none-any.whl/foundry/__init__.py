"""
LuxForge Foundry Core Package
Modular components for logging, file I/O, CLI menus, and branded utilities.
"""
from .version import __version__, __modified__, __author__, __status__, __changelog__, __audit_tags__

__all__ = [
    "logger",
    "files",
    "menu",
    "games",
    "colours",
]
