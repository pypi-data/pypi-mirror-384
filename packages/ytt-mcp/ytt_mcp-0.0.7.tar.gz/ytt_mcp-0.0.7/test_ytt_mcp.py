"""Tests for YouTube Transcript MCP Server."""

import pytest
from unittest.mock import patch, AsyncMock
from fastmcp import Client
from mcp.types import TextContent
from ytt_mcp import mcp, extract_video_id


class TestExtractVideoId:
    """Test video ID extraction."""

    def test_extract_from_watch_url(self) -> None:
        """Test extracting ID from watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_short_url(self) -> None:
        """Test extracting ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_embed_url(self) -> None:
        """Test extracting ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_shorts_url(self) -> None:
        """Test extracting ID from shorts URL."""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_mobile_url(self) -> None:
        """Test extracting ID from mobile URL."""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_url_with_timestamp(self) -> None:
        """Test extracting ID from URL with timestamp."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123s"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_from_url_with_additional_params(self) -> None:
        """Test extracting ID from URL with additional parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&si=abc123"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_return_video_id_directly(self) -> None:
        """Test returning video ID when already provided."""
        video_id = "dQw4w9WgXcQ"
        assert extract_video_id(video_id) == video_id

    def test_invalid_url_raises_error(self) -> None:
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            extract_video_id("not-a-valid-url")

    def test_invalid_hostname_raises_error(self) -> None:
        """Test that invalid hostname raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube URL or video ID"):
            extract_video_id("https://invalid-domain.com/watch?v=dQw4w9WgXcQ")

    def test_missing_video_id_raises_error(self) -> None:
        """Test that URL without video ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube URL or video ID"):
            extract_video_id("https://www.youtube.com/watch")

    def test_invalid_video_id_format_raises_error(self) -> None:
        """Test that URL with invalid video ID format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid YouTube URL or video ID"):
            extract_video_id("https://www.youtube.com/watch?v=invalid-id")


async def test_youtube_transcript_mcp_server():
    """Test various scenarios for the get_youtube_transcript tool."""
    mock_transcript_en = "This is a test transcript"
    mock_transcript_fr = "Ceci est une transcription de test en français"

    def mock_fetch_side_effect(video_id: str, lang: str | None = None) -> str:
        if lang is None or lang == "en":
            return mock_transcript_en
        elif lang == "fr":
            return mock_transcript_fr
        else:
            raise ValueError(f"Unsupported language: {lang}")

    async with Client(mcp) as client:
        # Verify available tools
        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "get_youtube_transcript"

        with patch(
            "ytt_mcp.fetch_youtube_transcript", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = mock_fetch_side_effect

            # Test default case (no lang parameter)
            result = await client.call_tool(
                "get_youtube_transcript",
                {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
            )
            assert isinstance(result.content[0], TextContent)
            assert result.content[0].text == mock_transcript_en
            mock_fetch.assert_called_with("dQw4w9WgXcQ", "en")

            # Test explicit English language
            result = await client.call_tool(
                "get_youtube_transcript",
                {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "lang": "en"},
            )
            assert isinstance(result.content[0], TextContent)
            assert result.content[0].text == mock_transcript_en
            mock_fetch.assert_called_with("dQw4w9WgXcQ", "en")

            # Test French transcript
            result = await client.call_tool(
                "get_youtube_transcript",
                {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "lang": "fr"},
            )
            assert isinstance(result.content[0], TextContent)
            assert result.content[0].text == mock_transcript_fr
            mock_fetch.assert_called_with("dQw4w9WgXcQ", "fr")

        # Test invalid language code (Pydantic validation)
        with pytest.raises(Exception, match="validation error"):
            await client.call_tool(
                "get_youtube_transcript",
                {
                    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                    "lang": "invalid-lang",
                },
            )
