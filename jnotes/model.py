"""Core data model for the j-notes pipeline.

Stage shape (spec.yaml -> pipeline): .j -> .jmd -> .md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    """spec.yaml -> meta_keyword.epistemic_states.

    The marker stakes a proposition. The state records how that
    proposition stands, not how strongly anyone feels about it.
    """

    KNOWN_BY_JUDAH = "known_by_judah"   # Judah has stated the answer directly.
    AI_GUESS = "ai_guess"               # The AI has a candidate answer.
    UNDECIDED = "undecided"             # Not yet asserted at all.


#: spec.yaml -> meta_keyword.markers. One marker, two accepted spellings.
MARKERS = ("--", "—")


class Kind(str, Enum):
    TEXT = "text"        # ordinary body content, passed through
    META = "meta"        # carries a marked section
    CODE = "code"        # inside a fence; never scanned for markers
    BLANK = "blank"


@dataclass
class Meta:
    """A marked section: the marker plus everything after it on its line."""

    marker: str              # the spelling actually used ("--" or em-dash)
    col: int                 # 0-based index of the marker within the line
    state: State
    body: str                # content after the marker, stripped
    key: str | None = None   # left of ":" when the body is a key/value
    value: str | None = None # right of ":" (None when undecided)

    @property
    def is_attribution(self) -> bool:
        """A trailing marker whose body names who knows it (`-- Judah`)."""
        return self.col > 0 and self.key is None


@dataclass
class Line:
    no: int                  # 1-based line number in the ORIGINAL source
    raw: str                 # verbatim source line, no trailing newline
    kind: Kind = Kind.TEXT
    meta: Meta | None = None

    @property
    def before(self) -> str:
        """Body text to the left of the marker (empty for a leading marker)."""
        return self.raw[: self.meta.col].rstrip() if self.meta else self.raw


@dataclass
class Question:
    """An ambiguity the converter refused to settle on its own.

    spec.yaml -> input.ambiguity_resolution: anything the AI cannot
    resolve gets asked to Judah directly, rather than guessed at
    silently and passed through as if settled.
    """

    qid: str
    line_no: int
    reason: str
    answers: tuple[str, ...]
    excerpt: str
    answer: str | None = None   # None means still open

    @property
    def open(self) -> bool:
        return self.answer is None


@dataclass
class Document:
    lines: list[Line] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    source: str = ""

    @property
    def open_questions(self) -> list[Question]:
        return [q for q in self.questions if q.open]
