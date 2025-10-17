from dataclasses import dataclass
from datetime import time

TIME_FORMAT = "%H:%M:%S"


@dataclass
class Chunk:
    start: time
    end: time
    text: str
    source: str
    source_type: str

    @property
    def start_h(self):
        return self.start.strftime(TIME_FORMAT)

    @property
    def end_h(self):
        return self.end.strftime(TIME_FORMAT)

    def __str__(self):
        return f"{self.start_h} - {self.end_h}: {self.text}"


@dataclass
class Sub(Chunk): ...


@dataclass
class Result:
    chunk: Chunk
    score: float
    index: int

    def __str__(self):
        return f"{self.chunk} x {self.score:.3f}"
