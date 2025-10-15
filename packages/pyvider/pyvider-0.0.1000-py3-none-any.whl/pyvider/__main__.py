"""
Makes the 'pyvider' package executable using 'python -m pyvider'.

This file serves as a simple, robust entry point that delegates to the
canonical CLI main function, avoiding logic duplication.
"""

from pyvider.cli.__main__ import main

if __name__ == "__main__":
    main()
