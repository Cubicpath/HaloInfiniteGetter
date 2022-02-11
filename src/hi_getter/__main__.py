###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Entrypoint that is called when using Python's -m switch."""
import sys

from .run import run

if __name__ == '__main__':
    exit_code = run(*sys.argv)
