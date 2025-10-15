# myapp/__init__.py

from .app2 import main  # Exposes main() so you can do: import myapp; myapp.main()

__all__ = ["main"]  # Only main() is exported when using: from myapp import *
