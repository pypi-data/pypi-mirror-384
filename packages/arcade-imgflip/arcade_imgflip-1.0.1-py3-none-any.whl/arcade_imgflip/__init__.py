"""Imgflip Toolkit for Arcade AI"""

from arcade_imgflip.models import MemeTemplate, TextBox
from arcade_imgflip.tools import (
    create_meme,  # Create a meme with custom text
    get_popular_memes,  # Get popular meme templates
    search_memes,  # Search for meme templates
)

__all__ = [
    "MemeTemplate",
    "TextBox",
    "get_popular_memes",
    "create_meme",
    "search_memes",
]
