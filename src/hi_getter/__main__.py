###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Entrypoint that is called when using Python's -m switch."""
import sys

from .run import main

# Allow running from import, as __name__ should be __main__
exit_code = main(*sys.argv)
sys.exit(exit_code)
