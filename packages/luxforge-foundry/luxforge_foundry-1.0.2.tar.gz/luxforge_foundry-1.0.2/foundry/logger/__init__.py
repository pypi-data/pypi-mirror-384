from .logger import Logger


# Often modified metadata
__version__ = "1.0.0"
__modified__ = "2025-10-16"


__all__ = ["Logger"]

# Metadata
__author__ = "LuxForge"
__maintainer__ = "LuxForge"
__email__ = "lab@luxforge.dev"
__license__ = "MIT"
__status__ = "Development"
__copyright__ = "© 2025 LuxForge"
__credits__ = ["LuxForge"]
__description__ = "Audit-grade logging module for Foundry tools, supporting timestamped output to console, file, and (eventually) database and API endpoints."
__created__ = "2025-10-16"
__module__ = "foundry.logger"
__tags__ = ["logging", "audit", "rasputin", "foundry", "timestamp"]
__interface__ = "console,file,api"
__features__ = ["timestamped output", "file rotation", "milestone tagging"]
__dependencies__ = ["os", "logging", "logging.handlers", "datetime", "threading"]
__compatibility__ = ["Python 3.8+", "Foundry VTT 0.8+"]
__repository__ = "https://github.com/LuxForge/LuxForge-Foundry"