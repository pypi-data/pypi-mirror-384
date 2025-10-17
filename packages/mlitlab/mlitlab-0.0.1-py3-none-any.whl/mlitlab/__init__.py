import io
import builtins

# Force open() to always read in UTF-8 mode to handle Unicode characters
builtins.open = lambda file, mode='r', *args, **kwargs: io.open(file, mode, encoding='utf-8', errors='ignore', *args, **kwargs)

from .main import program

__all__ = ["program"]
