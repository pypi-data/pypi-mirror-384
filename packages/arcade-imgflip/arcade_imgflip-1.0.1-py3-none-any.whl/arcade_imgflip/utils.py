"""Utility functions for Imgflip toolkit"""

import re

from arcade_tdk.errors import ToolExecutionError

from arcade_imgflip.client import ImgflipClient
from arcade_imgflip.constants import Font
from arcade_imgflip.models import MemeTemplate, MemeTemplateWithCaptions, TextBox


def validate_font(font: Font) -> str:
    """Validate and return a valid font name string"""
    # Since we're using an enum, we can directly return the value
    # The enum ensures we only have valid fonts
    return font.value


def sanitize_text(text: str, max_length: int = 100) -> str:
    """Sanitize text for meme creation"""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Truncate if too long
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text


def create_simple_text_boxes(
    image_width: int,
    image_height: int,
    top_text: str | None = None,
    bottom_text: str | None = None,
) -> list[TextBox]:
    """Create simple top/bottom text boxes for meme creation

    Args:
        image_width: Width of the meme template image
        image_height: Height of the meme template image
        top_text: Text to display at the top of the meme
        bottom_text: Text to display at the bottom of the meme

    Returns:
        List of TextBox objects positioned at top and/or bottom, centered horizontally
    """
    boxes = []

    # Calculate text box dimensions based on image size
    text_box_width = int(image_width * 0.8)  # 80% of image width for proper centering
    text_box_height = min(60, int(image_height * 0.15))  # 15% of image height, min 60px

    # Calculate center X position for text boxes
    center_x = (image_width - text_box_width) // 2

    if top_text:
        # Position top text at the top with some margin
        top_y = 20  # Small margin from top
        boxes.append(
            TextBox(
                text=sanitize_text(top_text),
                x=center_x,
                y=top_y,
                width=text_box_width,
                height=text_box_height,
            )
        )

    if bottom_text:
        # Position bottom text at the bottom with some margin
        bottom_y = image_height - text_box_height - 20  # Small margin from bottom
        boxes.append(
            TextBox(
                text=sanitize_text(bottom_text),
                x=center_x,
                y=bottom_y,
                width=text_box_width,
                height=text_box_height,
            )
        )

    return boxes


def format_meme_url(url: str) -> str:
    """Format meme URL for display"""
    if not url:
        return ""

    # Ensure URL is properly formatted
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    return url


def extract_template_id_from_url(url: str) -> str | None:
    """Extract template ID from Imgflip URL"""
    if not url:
        return None

    # Match patterns like /memegenerator/14859329/ or /i/123abc
    patterns = [
        r"/memegenerator/(\d+)/",
        r"/i/([a-zA-Z0-9]+)",
        r"template_id=(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def validate_template_id(template_id: str) -> bool:
    """Validate template ID format"""
    if not template_id:
        return False

    # Template IDs can be numeric or alphanumeric
    return bool(re.match(r"^[a-zA-Z0-9]+$", str(template_id)))


def format_error_message(error: str) -> str:
    """Format error message for user display"""
    if not error:
        return "An unknown error occurred"

    # Clean up common error messages
    error = error.strip()

    # Remove technical prefixes
    if error.startswith("Imgflip API error:"):
        error = error.replace("Imgflip API error:", "").strip()

    return error


def get_meme_preview_info(meme_data: dict | MemeTemplate | MemeTemplateWithCaptions) -> dict:
    """Extract preview information from meme data"""
    return {
        "id": meme_data.get("id"),
        "name": meme_data.get("name"),
        "url": meme_data.get("url"),
        "width": meme_data.get("width"),
        "height": meme_data.get("height"),
        "box_count": meme_data.get("box_count"),
        "captions": meme_data.get("captions", 0),
    }


def validate_custom_boxes(boxes: list[TextBox]) -> str | None:
    """Validate custom text boxes"""
    for i, box in enumerate(boxes):
        if not isinstance(box, dict) or "text" not in box:
            return f"Box {i} must be a dictionary with a 'text' field"
        if not box["text"]:
            return f"Box {i} text cannot be empty"
    return None


async def get_template_dimensions(client: ImgflipClient, template_id: str) -> tuple[int, int]:
    """Get template dimensions for better text positioning"""
    meme_result = await client.get_meme(template_id)
    if meme_result["success"] and meme_result["meme"]:
        return meme_result["meme"]["width"], meme_result["meme"]["height"]
    raise ToolExecutionError(
        "Failed to get meme dimensions",
        developer_message=f"Template {template_id} not found or invalid",
    )
