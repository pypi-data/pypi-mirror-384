"""Commands module for the VCP CLI."""

from .config import config_command
from .data import data_command
from .data.search import search_command
from .login import login_command
from .logout import logout_command
from .model import model_command

__all__ = [
    "login_command",
    "logout_command",
    "model_command",
    "config_command",
    "search_command",
    "data_command",
]
