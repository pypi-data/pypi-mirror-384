"""
ABSFUYU
-------
COMMAND LINE INTERFACE

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
try:
    from absfuyu.cli import cli
except ImportError:  # Check for `click`, `colorama`
    from absfuyu.core.dummy_cli import cli


# Function
# ---------------------------------------------------------------------------
def main() -> None:
    cli()


# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
