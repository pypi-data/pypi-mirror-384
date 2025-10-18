''' private helper package for `eda --version`'''

import sys

NAME = 'opencos-eda'

# Use standard library metadata module starting Python 3.8
if sys.version_info >= (3, 8):

    from importlib import metadata
    try:
        ver = metadata.version(NAME)
    except metadata.PackageNotFoundError:
        # Handle case where the package is not installed (e.g., running from source checkout)
        ver = "0.0.0"

else:
    # This package only supports >= 3.8, so not doing the importlib_metadata method.
    ver = "unknown" # Or raise an error, or handle differently


VERSION = ver # pylint: disable=invalid-name
