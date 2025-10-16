"""`suricata_check` is a module and command line utility to provide feedback on Suricata rules."""

from suricata_check_design_principles import checkers
from suricata_check_design_principles._version import (
    SURICATA_CHECK_DIR,
    __version__,
)

__all__ = (
    "SURICATA_CHECK_DIR",
    "__version__",
    "checkers",
)
