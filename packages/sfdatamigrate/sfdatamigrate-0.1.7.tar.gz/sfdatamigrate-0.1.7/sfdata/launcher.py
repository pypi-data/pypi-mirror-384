"""
SFData Launcher

Simple launcher that calls the main CLI via python -m to avoid
PyArmor runtime import issues with console_scripts entry points.

This file is intentionally not obfuscated.
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

