###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Entrypoint that is called when using Python's -m switch."""
import sys

from .run import main

exit_code = main(*sys.argv)