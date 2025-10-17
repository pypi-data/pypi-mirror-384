__version__ = "1.0.1"
__modified__ = "2025-10-16"
__timestamp__ = "2025-10-16T21:23:00+01:00"
__author__ = "LuxForge"
__status__ = "Production"

__changelog__ = [
    "Initial release with modular logging, file I/O, and CLI menu",
    "Added JokeEngine and LotteryEngine modules",
    "Scaffolded interactive PublishMenu for PyPI workflow",
    "Centralized versioning and metadata in version.py",
]

__audit_tags__ = [
    f"release:{__version__}",
    f"timestamp:{__timestamp__}",
    "packaging:twine",
    "build:python -m build",
    "push:rasputin_push.py",
]