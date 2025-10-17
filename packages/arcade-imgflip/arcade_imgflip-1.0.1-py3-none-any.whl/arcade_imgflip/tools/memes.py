"""Meme-related tools for Imgflip"""

from typing import Annotated, Any

from arcade_tdk import ToolContext, tool

from arcade_imgflip.client import ImgflipClient
from arcade_imgflip.constants import Font
from arcade_imgflip.utils import (
    create_simple_text_boxes,
    format_meme_url,
    get_meme_preview_info,
    get_template_dimensions,
    validate_font,
    validate_template_id,
)


@tool(requires_secrets=["IMGFLIP_USERNAME", "IMGFLIP_PASSWORD"])
async def get_popular_memes(
    context: ToolContext,
    limit: Annotated[int, "Maximum number of meme templates to return. Defaults to 20."] = 20,
) -> Annotated[dict[str, Any], "List of popular meme templates"]:
    """Get popular meme templates from Imgflip

    This tool retrieves a list of popular meme templates that can be used
    to create custom memes. These templates are ordered by popularity
    based on how many times they've been captioned.

    """

    # Get credentials from secrets
    username = context.get_secret("IMGFLIP_USERNAME")
    password = context.get_secret("IMGFLIP_PASSWORD")

    if not username or not password:
        return {
            "error": "Imgflip credentials not configured. Please set IMGFLIP_USERNAME and IMGFLIP_PASSWORD secrets."
        }

    client = ImgflipClient(username, password)

    try:
        result = await client.get_popular_memes()

        if not result["success"]:
            return {"error": result.get("error_message", "Failed to fetch popular memes")}

        memes = result["memes"]

        # Limit results if requested
        if limit > 0:
            memes = memes[:limit]

        # Format meme information
        formatted_memes = []
        for meme in memes:
            formatted_memes.append(get_meme_preview_info(meme))

        return {
            "success": True,
            "memes": formatted_memes,
            "total_count": len(formatted_memes),
            "message": f"Successfully retrieved {len(formatted_memes)} popular meme templates",
        }

    except Exception as e:
        return {"error": f"Failed to fetch popular memes: {e!s}"}


@tool(requires_secrets=["IMGFLIP_USERNAME", "IMGFLIP_PASSWORD"])
async def create_meme(
    context: ToolContext,
    template_id: Annotated[
        str,
        "The meme template ID to use for creation. You can get this from get_popular_memes.",
    ],
    top_text: Annotated[
        str, "Text to display at the top of the meme. Leave empty if not needed."
    ] = "",
    bottom_text: Annotated[
        str, "Text to display at the bottom of the meme. Leave empty if not needed."
    ] = "",
    font: Annotated[Font, "Font family to use for the text"] = Font.IMPACT,
    max_font_size: Annotated[int, "Maximum font size for the text. Defaults to 50."] = 50,
    no_watermark: Annotated[bool, "Remove the Imgflip watermark. Defaults to False."] = False,
) -> Annotated[dict[str, Any], "Created meme information with URLs"]:
    """Create a custom meme using an Imgflip template

    This tool creates a custom meme by adding your text to an existing
    meme template. You can specify top and bottom text, choose fonts,
    and control text sizing.
    """

    username = context.get_secret("IMGFLIP_USERNAME")
    password = context.get_secret("IMGFLIP_PASSWORD")

    # Validate template ID
    if not validate_template_id(template_id):
        return {"error": "Invalid template ID format"}

    # Validate font
    font_str = validate_font(font)

    # Create client
    client = ImgflipClient(username, password)

    try:
        template_width, template_height = await get_template_dimensions(client, template_id)

        # Create simple text boxes if text is provided
        if top_text or bottom_text:
            boxes = create_simple_text_boxes(template_width, template_height, top_text, bottom_text)

        # Create the meme
        result = await client.create_meme(
            template_id=template_id,
            font=font_str,
            max_font_size=max_font_size,
            boxes=boxes,
            no_watermark=no_watermark,
        )

        if not result["success"]:
            return {"error": result.get("error_message", "Failed to create meme")}

        # Format URLs
        image_url = format_meme_url(result["url"]) if result["url"] else None
        page_url = format_meme_url(result["page_url"]) if result["page_url"] else None

        return {
            "success": True,
            "meme": {
                "image_url": image_url,
                "page_url": page_url,
                "template_id": result.get("template_id"),
                "texts": result.get("texts", []),
            },
            "message": "Meme created successfully!",
            "template_id": template_id,
            "text_mode": "simple_text",
            "text_used": {
                "top": top_text if top_text else None,
                "bottom": bottom_text if bottom_text else None,
            },
            "font_used": font.value,
            "template_dimensions": {
                "width": template_width,
                "height": template_height,
            },
        }

    except Exception as e:
        return {"error": f"Failed to create meme: {e!s}"}
