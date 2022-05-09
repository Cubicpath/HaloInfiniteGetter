###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Entrypoint that is called when using Python's -m switch."""

__all__ = (
    'exit_code',
    'main',
)

import sys

from .run import main

# Allow running from import, as __name__ should be __main__
exit_code = main(*sys.argv)

# If imported, do not exit
if '__main__' != __name__:
    sys.exit(exit_code)
