from .files import FileHandler

# Often modified metadata
__version__ = "1.0.0"
__modified__ = "2025-10-16"

__all__ = ["FileHandler"]

# Metadata
__author__ = "LuxForge"
__maintainer__ = "LuxForge"
__email__ = "lab@luxforge.dev"
__license__ = "MIT"
__status__ = "Development"
__copyright__ = "© 2025 LuxForge"
__credits__ = ["LuxForge"]
__description__ = "Modular file I/O handler for Foundry tools, supporting read, write, append, export, and structured archival operations."
__created__ = "2025-10-16"
__module__ = "foundry.files"
__tags__ = ["file", "io", "read", "write", "append", "export", "foundry"]
__interface__ = "filesystem,stream"
__features__ = ["read", "write", "append", "export", "structured archival"]
__dependencies__ = ["os", "pathlib", "datetime", "json", "csv"]
__compatibility__ = ["Python 3.8+", "Foundry VTT 0.8+"]
__repository__ = "https://github.com/LuxForge/LuxForge-Foundry"