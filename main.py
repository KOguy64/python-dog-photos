import sys

if sys.version_info < (3, 12):  # noqa: UP036 (pip ignores requires-python)
    sys.exit(
        f"python-fox-photos needs Python 3.12 or newer, but this is "
        f"{sys.version.split()[0]}. See the Requirements section of README.md."
    )

from python_fox_photos.terminal_interface import Session

session = Session()
session.start()
