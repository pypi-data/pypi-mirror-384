"""AII CLI entry point - enables 'python -m aii' usage"""

import sys

from .main import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
