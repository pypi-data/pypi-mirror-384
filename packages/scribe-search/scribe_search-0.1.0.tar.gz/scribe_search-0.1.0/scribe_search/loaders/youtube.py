import re
from typing import Iterable

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter

from scribe_search.data import Sub
from scribe_search.exceptions import InvalidSource

from .srt import Loader as SrtLoader


class Loader:

    @staticmethod
    def extract_video_id(url: str) -> str:

        if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
            return url

        patterns = [
            r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise InvalidSource(f"Could not extract video ID from URL: {url}")

    @staticmethod
    def load(sources: list[str]) -> Iterable[Sub] | None:
        api = YouTubeTranscriptApi()
        formatter = SRTFormatter()

        for source in sources:
            video_id = Loader.extract_video_id(source)
            try:
                caption = api.fetch(video_id)
            except Exception as e:
                raise InvalidSource(f"Could not fetch transcripts for video {source}: {str(e)}")

            caption = formatter.format_transcript(caption)
            return SrtLoader.load([caption], source_type="youtube", source_override=source)
