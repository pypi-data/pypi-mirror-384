import os
from datetime import time
from typing import Iterable

import webvtt
import webvtt.srt
from webvtt.errors import MalformedCaptionError

from scribe_search.data import Sub
from scribe_search.exceptions import InvalidSource
from scribe_search.loaders import LoaderInterface


class Loader(LoaderInterface):

    @staticmethod
    def load(sources: list[str], source_type="srt", source_override=None) -> Iterable[Sub]:
        for source in sources:
            try:
                if os.path.isfile(source):
                    captions = webvtt.from_srt(source)
                else:
                    captions = webvtt.srt.parse(source.splitlines())
            except MalformedCaptionError as e:
                raise InvalidSource from e

        for source in sources:
            for caption in captions:
                yield Sub(
                    start=time(*caption.start_time.to_tuple()),
                    end=time(*caption.end_time.to_tuple()),
                    text=caption.text,
                    source=source_override or source,
                    source_type=source_type,
                )
