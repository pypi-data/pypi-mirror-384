"""A python implementation of the hackmud chat API, using the requests module."""

from .package_data import PACKAGE_VERSION

__version__ = PACKAGE_VERSION

from .hackmudChatAPI import ChatAPI

__all__ = ["ChatAPI"]
