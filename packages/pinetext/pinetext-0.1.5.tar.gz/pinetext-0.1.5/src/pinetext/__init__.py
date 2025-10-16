from importlib.metadata import version

from pinetext.client import PineText


__version__ = version("pinetext")
__all__ = ["PineText"]
