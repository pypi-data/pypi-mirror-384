import logging
import os
import subprocess
from importlib.metadata import PackageNotFoundError, version

SURICATA_CHECK_DIR = os.path.dirname(__file__)

_logger = logging.getLogger(__name__)


def __get_git_revision_short_hash() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )


def get_version() -> str:
    v = "unknown"

    git_dir = os.path.join(SURICATA_CHECK_DIR, "..", ".git")
    if os.path.exists(git_dir):
        try:
            import setuptools_git_versioning  # noqa: RUF100, PLC0415

            v = str(
                setuptools_git_versioning.get_version(
                    root=os.path.join(SURICATA_CHECK_DIR, "..")
                )
            )
            _logger.debug(
                "Detected suricata-check-design-principles version using setuptools_git_versioning: %s",
                v,
            )
        except:  # noqa: E722
            v = __get_git_revision_short_hash()
            _logger.debug(
                "Detected suricata-check-design-principles version using git: %s", v
            )
    else:
        try:
            v = version("suricata-check-design-principles")
            _logger.debug(
                "Detected suricata-check-design-principles version using importlib: %s",
                v,
            )
        except PackageNotFoundError:
            _logger.debug(
                "Failed to detect suricata-check-design-principles version: %s", v
            )

    return v


__version__: str = get_version()
