"""Search tools for Imgflip"""

from typing import Annotated, Any

from arcade_tdk import ToolContext, tool

from arcade_imgflip.client import ImgflipClient
from arcade_imgflip.utils import get_meme_preview_info


@tool(requires_secrets=["IMGFLIP_USERNAME", "IMGFLIP_PASSWORD"])
async def search_memes(
    context: ToolContext,
    query: Annotated[str, "Search query to find meme templates. Be specific for better results."],
    include_nsfw: Annotated[
        bool, "Include not-safe-for-work memes in search results. Defaults to False."
    ] = False,
    limit: Annotated[int, "Maximum number of meme templates to return. Defaults to 20."] = 20,
) -> Annotated[dict[str, Any], "Search results for meme templates"]:
    """Search for meme templates by query

    This tool searches through Imgflip's database of over 1 million meme templates
    to find ones that match your search query.

    What this tool provides:
    - Search results matching your query
    - Template information including IDs, names, and URLs
    - Caption count to show popularity
    - Ready-to-use template IDs for meme creation

    When to use this tool:
    - When you're looking for specific meme types or themes
    - When you want to find memes related to particular topics
    - When you need a specific meme format that's not in popular memes
    - When you want to discover niche or specialized meme templates

    When NOT to use this tool:
    - Do NOT use this if you just want popular memes (use get_popular_memes instead)
    - Do NOT use this if you want to create a meme (use create_meme instead)
    """

    # Get credentials from secrets
    username = context.get_secret("IMGFLIP_USERNAME")
    password = context.get_secret("IMGFLIP_PASSWORD")

    if not username or not password:
        return {
            "error": "Imgflip credentials not configured. Please set IMGFLIP_USERNAME and IMGFLIP_PASSWORD secrets."
        }

    # Validate query
    if not query or not query.strip():
        return {"error": "Search query is required"}

    client = ImgflipClient(username, password)

    try:
        result = await client.search_memes(query.strip(), include_nsfw)

        if not result["success"]:
            return {"error": result.get("error_message", "Failed to search memes")}

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
            "query": query,
            "memes": formatted_memes,
            "total_count": len(formatted_memes),
            "include_nsfw": include_nsfw,
            "message": f"Found {len(formatted_memes)} meme templates matching '{query}'",
        }

    except Exception as e:
        return {"error": f"Failed to search memes: {e!s}"}
