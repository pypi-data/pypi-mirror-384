"""
SFData CLI Launcher (standalone)

This is a standalone launcher script that sits outside the sfdata package
to avoid PyArmor import issues with console_scripts entry points.

This file is intentionally not obfuscated and not in the sfdata package.
"""

import sys
import subprocess


def main():
    """Launch sfdata CLI via python -m."""
    # Call: python -m sfdata <args>
    cmd = [sys.executable, "-m", "sfdata"] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()

