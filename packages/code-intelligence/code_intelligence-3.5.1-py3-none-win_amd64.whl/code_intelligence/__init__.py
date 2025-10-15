from .goober import (
    Language,
    Definition_Link,
    scan_file,
    find_symbols_in_text,
    init,
    stop,
    clear,
)

# PROUD   - Bump when you are proud of the release.
# DEFAULT - Just normal/okay releases.
# SHAME   - Bump when fixing things too embarrassing to admit.
#       PROUD.DEFAULT.SHAME
#            \   |   /
__version__ = "3.5.1"
__version_info__ = tuple(int(i) for i in __version__.split('.'))

__all__ = [
    "Language",
    "Definition_Link",
    "scan_file",
    "find_symbols_in_text",
    "init",
    "stop",
    "clear",
]
