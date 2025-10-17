"""Imgflip toolkit models and data structures"""

from typing_extensions import TypedDict


class TextBox(TypedDict, total=False):
    """Text box configuration for meme creation"""

    text: str
    x: int | None
    y: int | None
    width: int | None
    height: int | None
    color: str | None
    outline_color: str | None


class MemeTemplate(TypedDict):
    """Meme template information"""

    id: str
    name: str
    url: str
    width: int
    height: int
    box_count: int


class MemeTemplateWithCaptions(MemeTemplate):
    """Meme template with caption count information"""

    captions: int


class MemeResult(TypedDict):
    """Result of getting a single meme by ID"""

    success: bool
    meme: MemeTemplateWithCaptions | None
    error_message: str | None


class MemeCreationResult(TypedDict):
    """Result of meme creation"""

    success: bool
    url: str | None
    page_url: str | None
    template_id: int | None
    texts: list[str] | None
    error_message: str | None


class MemeSearchResult(TypedDict):
    """Result of meme search"""

    success: bool
    memes: list[MemeTemplateWithCaptions]
    error_message: str | None


class PopularMemesResult(TypedDict):
    """Result of getting popular memes"""

    success: bool
    memes: list[MemeTemplate]
    error_message: str | None
