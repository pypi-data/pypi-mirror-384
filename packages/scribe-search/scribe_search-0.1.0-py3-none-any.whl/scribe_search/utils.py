from importlib import import_module
from typing import Iterable, Literal

from scribe_search.data import Result, Sub


def load_source(source_type: Literal["srt", "youtube", "video"], sources: list[str]) -> Iterable[Sub]:
    Loader = getattr(import_module(f"scribe_search.loaders.{source_type}"), "Loader")
    return Loader.load(sources)


def scribe_search(
    source_type: Literal["srt", "youtube", "video"], sources: list[str], query: str, top: int = 5
) -> Iterable[Result]:

    subs = list(load_source(source_type, sources))

    # faster
    from scribe_search.search import build_faiss_index, make_sentence_chunks, semantic_search

    chunks = make_sentence_chunks(subs)
    index, _embeddings, texts = build_faiss_index(chunks)

    return semantic_search(query, index, texts, chunks, top)
