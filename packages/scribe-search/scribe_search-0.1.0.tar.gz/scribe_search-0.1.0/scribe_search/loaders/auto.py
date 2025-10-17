import mimetypes
import os
import re

from scribe_search.exceptions import InvalidSource
from scribe_search.loaders import LoaderInterface

from .srt import Loader as SRTLoader
from .video import Loader as VideoLoader
from .youtube import Loader as YTLoader


class Loader(LoaderInterface):

    @staticmethod
    def get_loader(source: str) -> type:
        if re.search(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", source):
            # Youtube link
            return YTLoader

        if os.path.exists(source):
            mime_type, _ = mimetypes.guess_type(source)
            if mime_type:
                if mime_type.startswith("video/"):
                    return VideoLoader
                return SRTLoader

        raise InvalidSource(f"Can't infer the source type from `{source}`")

    @staticmethod
    def load(sources: list[str]):
        for source in sources:
            loader_class = Loader.get_loader(source)
            return loader_class.load([source])
