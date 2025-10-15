from mchnpkg._core import hello_from_bin
from mchnpkg.model import LinearRegression

from .model import LinearRegression
__all__ = ["LinearRegression"]


def hello() -> str:
    return hello_from_bin()
