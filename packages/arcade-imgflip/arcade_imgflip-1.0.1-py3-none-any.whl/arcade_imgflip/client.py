"""Client for interacting with Imgflip API"""

from typing import Any

import httpx
from arcade_tdk.errors import ToolExecutionError

from arcade_imgflip.constants import IMGFLIP_API_URL
from arcade_imgflip.models import (
    MemeCreationResult,
    MemeResult,
    MemeSearchResult,
    PopularMemesResult,
    TextBox,
)


class ImgflipClient:
    """Client for interacting with Imgflip's REST API"""

    def __init__(
        self,
        username: str,
        password: str,
        api_url: str = IMGFLIP_API_URL,
    ) -> None:
        """Initialize Imgflip client"""
        self.username = username
        self.password = password
        self.api_url = api_url

    def _build_error_message(self, response: httpx.Response) -> tuple[str, str]:
        """Build user-friendly and developer error messages from response"""
        try:
            data = response.json()
            if not data.get("success", True):
                error_message = data.get("error_message", "Unknown Imgflip API error")
                user_message = f"Imgflip API error: {error_message}"
                dev_message = f"Imgflip API error: {error_message} (HTTP {response.status_code})"
            else:
                user_message = f"HTTP {response.status_code}: {response.reason_phrase}"
                dev_message = f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            user_message = "Failed to parse Imgflip API error response"
            dev_message = (
                f"Failed to parse error response: {type(e).__name__}: {e!s} | "
                f"Raw response: {response.text}"
            )

        return user_message, dev_message

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate errors for non-200 responses"""
        if response.status_code < 300:
            # Check for API errors in successful HTTP responses
            try:
                data = response.json()
                if not data.get("success", True):
                    user_message, dev_message = self._build_error_message(response)
                    raise ToolExecutionError(user_message, developer_message=dev_message)
            except (ValueError, KeyError):
                # Response isn't JSON or doesn't have expected structure
                pass
            return

        user_message, dev_message = self._build_error_message(response)
        raise ToolExecutionError(user_message, developer_message=dev_message)

    async def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> Any:
        """Make HTTP request to Imgflip API"""
        url = f"{self.api_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, data=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            self._raise_for_status(response)
            return response.json()

    def _build_meme_request_data(
        self,
        template_id: str,
        text0: str | None = None,
        text1: str | None = None,
        font: str | None = None,
        max_font_size: int | None = None,
        boxes: list[TextBox] | None = None,
        no_watermark: bool = False,
    ) -> dict[str, Any]:
        """Build request data for meme creation"""
        request_data: dict[str, Any] = {
            "template_id": template_id,
            "username": self.username,
            "password": self.password,
        }

        if boxes:
            # Use boxes format for advanced text positioning
            for i, box in enumerate(boxes):
                for key, value in box.items():
                    if value is not None:
                        request_data[f"boxes[{i}][{key}]"] = str(value)
        else:
            # Use simple text0/text1 format
            if text0:
                request_data["text0"] = text0
            if text1:
                request_data["text1"] = text1

        if font:
            request_data["font"] = font
        if max_font_size:
            request_data["max_font_size"] = str(max_font_size)
        if no_watermark:
            request_data["no_watermark"] = "1"

        return request_data

    async def get_popular_memes(self) -> PopularMemesResult:
        """Get popular meme templates"""
        try:
            data = await self._make_request("GET", "/get_memes")
            return PopularMemesResult(
                success=data.get("success", False),
                memes=data.get("data", {}).get("memes", []),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            return PopularMemesResult(
                success=False,
                memes=[],
                error_message=str(e),
            )

    async def get_meme(self, template_id: str) -> MemeResult:
        """Get a meme by ID"""
        try:
            request_data = {
                "username": self.username,
                "password": self.password,
                "template_id": template_id,
            }

            # Make the request without using _raise_for_status to handle API errors gracefully
            url = f"{self.api_url}/get_meme"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=request_data)
                data = response.json()

            return MemeResult(
                success=data.get("success", False),
                meme=data.get("data", {}).get("meme"),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            return MemeResult(
                success=False,
                meme=None,
                error_message=str(e),
            )

    async def create_meme(
        self,
        template_id: str,
        text0: str | None = None,
        text1: str | None = None,
        font: str | None = None,
        max_font_size: int | None = None,
        boxes: list[TextBox] | None = None,
        no_watermark: bool = False,
    ) -> MemeCreationResult:
        """Create a meme with custom text"""
        try:
            request_data = self._build_meme_request_data(
                template_id, text0, text1, font, max_font_size, boxes, no_watermark
            )
            data = await self._make_request("POST", "/caption_image", request_data)

            return MemeCreationResult(
                success=data.get("success", False),
                url=data.get("data", {}).get("url"),
                page_url=data.get("data", {}).get("page_url"),
                template_id=data.get("data", {}).get("template_id"),
                texts=data.get("data", {}).get("texts"),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            return MemeCreationResult(
                success=False,
                url=None,
                page_url=None,
                template_id=None,
                texts=None,
                error_message=str(e),
            )

    async def search_memes(self, query: str, include_nsfw: bool = False) -> MemeSearchResult:
        """Search for meme templates"""
        try:
            request_data = {
                "username": self.username,
                "password": self.password,
                "query": query,
            }

            if include_nsfw:
                request_data["include_nsfw"] = "1"

            data = await self._make_request("POST", "/search_memes", request_data)

            return MemeSearchResult(
                success=data.get("success", False),
                memes=data.get("data", {}).get("memes", []),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            return MemeSearchResult(
                success=False,
                memes=[],
                error_message=str(e),
            )

    async def create_ai_meme(
        self,
        text: str,
        model: str | None = None,
        template_id: str | None = None,
        prefix_text: str | None = None,
        no_watermark: bool = False,
    ) -> MemeCreationResult:
        """Generate AI-powered meme"""
        try:
            request_data = {
                "username": self.username,
                "password": self.password,
                "text": text,
            }

            if model:
                request_data["model"] = model
            if template_id:
                request_data["template_id"] = template_id
            if prefix_text:
                request_data["prefix_text"] = prefix_text
            if no_watermark:
                request_data["no_watermark"] = "1"

            data = await self._make_request("POST", "/ai_meme", request_data)

            return MemeCreationResult(
                success=data.get("success", False),
                url=data.get("data", {}).get("url"),
                page_url=data.get("data", {}).get("page_url"),
                template_id=data.get("data", {}).get("template_id"),
                texts=data.get("data", {}).get("texts"),
                error_message=data.get("error_message"),
            )
        except Exception as e:
            return MemeCreationResult(
                success=False,
                url=None,
                page_url=None,
                template_id=None,
                texts=None,
                error_message=str(e),
            )
