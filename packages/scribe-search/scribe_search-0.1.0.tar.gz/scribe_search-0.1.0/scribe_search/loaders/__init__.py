from typing import Iterable

from scribe_search.data import Sub


class LoaderInterface:

    @staticmethod
    def load(sources: list[str]) -> Iterable[Sub]:
        raise NotImplementedError
