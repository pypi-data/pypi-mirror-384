"""Package 'playlist2podcast' level definitions."""

from importlib.metadata import version
from typing import Final

__version__: Final[str] = version(str(__package__))

__package_name__: Final[str] = str(__package__)
__display_name__: Final[str] = "playlist2podcast"
USER_AGENT: Final[str] = f"{__display_name__}"
