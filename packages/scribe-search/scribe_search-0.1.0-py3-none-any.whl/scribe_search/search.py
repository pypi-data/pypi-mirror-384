from typing import Iterable

import nltk
from numpy import ndarray

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab")

import faiss
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

from scribe_search.data import Chunk, Result, Sub

model = SentenceTransformer("all-MiniLM-L6-v2")


def _flush_sentences(buffer_text: str) -> tuple[list, str]:
    sentences = sent_tokenize(buffer_text)

    # If only one sentence, it might still be incomplete → keep buffering
    if len(sentences) == 1:
        return [], buffer_text

    return sentences[:-1], sentences[-1]


def make_sentence_chunks(subs: Iterable[Sub]) -> list[Chunk]:
    """
    From a list of Subs, return a list of Chunks. A chunk is a group of
    sentences in a time interval
    """

    chunks = []

    buffer_text = ""
    buffer_start = None
    end_sub = None

    for sub in subs:
        text = sub.text.replace("\n", " ").strip()

        # Initialize start timestamp if buffer is empty
        if buffer_start is None:
            buffer_start = sub.start

        buffer_text += " " + text if buffer_text else text

        sentences, flushed = _flush_sentences(buffer_text)

        for sentence in sentences:
            chunks.append(
                Chunk(
                    text=sentence.strip(),
                    start=buffer_start,
                    end=sub.end,
                    source=sub.source,
                    source_type=sub.source_type,
                )
            )

        if flushed:
            buffer_text = flushed
            buffer_start = sub.end
        end_sub = sub

    # Catch leftover text (in case transcript ends without punctuation)
    if buffer_text and buffer_start:
        chunks.append(
            Chunk(
                text=buffer_text.strip(),
                start=buffer_start,
                end=end_sub.end,
                source=end_sub.source,
                source_type=end_sub.source_type,
            )
        )

    return chunks


def build_faiss_index(chunks: Iterable[Chunk]) -> tuple[faiss.Index, ndarray, list]:
    """
    Takes list of sentence chunks (with text, start, end)
    and builds a FAISS index.
    """
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity if normalized
    index.add(embeddings)

    return index, embeddings, texts


def semantic_search(query: str, index: faiss.Index, texts: list[str], chunks: list[Chunk], top_k: int = 5):
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], idxs[0]):
        c = chunks[idx]
        results.append(
            Result(
                chunk=c,
                score=score,
                index=idx,
            )
        )

    return results
