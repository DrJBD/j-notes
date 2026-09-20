"""The .jmd stage: a working file both the AI and Judah can edit directly.

spec.yaml -> pipeline.intermediate. The .jmd deliberately keeps its open
questions VISIBLE. Nothing is hidden at this stage and nothing is
settled behind Judah's back; the answers are edited in place, by hand,
and read back by the .md stage.
"""

from __future__ import annotations

import re

from .model import Document, Kind, Line, Meta, Question, State
from .scan import find_marker, scan, split_body

HEADER = "j-notes jmd/1"
Q_RE = re.compile(r"^\?\?\s+(\S+)\s+\[([^\]]+)\]\s+line\s+(\d+)\s+·\s+(.*)$")
STATE_RE = re.compile(r"\[(known_by_judah|ai_guess|undecided)\]\s*")


def render(doc: Document) -> str:
    """Document -> .jmd text."""
    out: list[str] = [HEADER, f"source: {doc.source}", ""]

    if doc.questions:
        out += [
            "## Open questions",
            "",
            "Each line below is an ambiguity this converter refused to settle on its",
            "own (spec.yaml -> ambiguity_resolution: decision_authority is Judah).",
            "Replace [open] with one of the listed answers, then run:",
            "",
            "    python3 -m jnotes md <this file>",
            "",
        ]
        for q in doc.questions:
            tag = q.answer or "open"
            out.append(f"?? {q.qid} [{tag}] line {q.line_no} · {q.reason}")
            out.append(f"??     answers: {' | '.join(q.answers)}")
            out.append(f"??     > {q.excerpt}")
        out.append("")

    out += ["## Body", ""]
    for line in doc.lines:
        out.append(_render_line(line))
    return "\n".join(out).rstrip("\n") + "\n"


def _render_line(line: Line) -> str:
    """Keep the marker where the author put it; make the state explicit."""
    if line.kind is not Kind.META or line.meta is None:
        return line.raw
    m = line.meta
    head = line.raw[: m.col + len(m.marker)]
    return f"{head} [{m.state.value}] {m.body}".rstrip()


def parse(text: str) -> Document:
    """.jmd text -> Document, reading back any answers Judah supplied."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith(HEADER):
        raise ValueError(f"not a .jmd file: expected a {HEADER!r} header")

    source = ""
    questions: list[Question] = []
    body_at: int | None = None
    pending: Question | None = None

    for i, raw in enumerate(lines):
        if raw.startswith("source:"):
            source = raw.partition(":")[2].strip()
        elif raw == "## Body":
            body_at = i + 1
            break
        elif raw.startswith("?? "):
            m = Q_RE.match(raw)
            if m:
                qid, tag, no, reason = m.groups()
                pending = Question(
                    qid=qid,
                    line_no=int(no),
                    reason=reason.strip(),
                    answers=(),
                    excerpt="",
                    answer=None if tag == "open" else tag,
                )
                questions.append(pending)
            elif pending is not None:
                stripped = raw[2:].strip()
                if stripped.startswith("answers:"):
                    pending.answers = tuple(
                        a.strip() for a in stripped[len("answers:"):].split("|")
                    )
                elif stripped.startswith(">"):
                    pending.excerpt = stripped[1:].strip()

    if body_at is None:
        raise ValueError("not a .jmd file: no '## Body' section")

    body = "\n".join(lines[body_at:]).lstrip("\n")
    doc_lines, _ = scan(body)
    for line in doc_lines:
        _absorb_state(line)

    _validate(questions)
    _apply_answers(doc_lines, questions)
    return Document(lines=doc_lines, questions=questions, source=source)


def _absorb_state(line: Line) -> None:
    """Lift an explicit [state] tag out of a re-read .jmd marker body."""
    if line.kind is not Kind.META or line.meta is None:
        return
    m = STATE_RE.match(line.meta.body)
    if not m:
        return
    body = line.meta.body[m.end():]
    key, value, inferred = split_body(body)
    declared = State(m.group(1))
    # An explicit tag is Judah's word and outranks what the sigils imply.
    line.meta = Meta(
        marker=line.meta.marker,
        col=line.meta.col,
        state=declared,
        body=body.strip(),
        key=key,
        value=value if declared is not State.UNDECIDED else value,
    )


def _validate(questions: list[Question]) -> None:
    for q in questions:
        if q.answer is not None and q.answers and q.answer not in q.answers:
            raise ValueError(
                f"{q.qid}: {q.answer!r} is not one of {' | '.join(q.answers)}"
            )


def _apply_answers(lines: list[Line], questions: list[Question]) -> None:
    """Carry each answered question back onto the line it was asked about."""
    by_line = {q.line_no: q for q in questions if q.answer}
    for line in lines:
        q = by_line.get(line.no)
        if q is None:
            continue
        if q.answer in ("prose", "ordinary"):
            line.kind = Kind.TEXT
            line.meta = None
        elif q.answer == "marker":
            hit = find_marker(line.raw)
            if hit is None:                       # a lone "-" ruled a real marker
                col = line.raw.index("-")
                body = line.raw[col + 1 :]
                spelling = "-"
            else:
                col, spelling = hit
                body = line.raw[col + len(spelling) :]
            key, value, state = split_body(body)
            line.kind = Kind.META
            line.meta = Meta(
                marker=spelling, col=col, state=state,
                body=body.strip(), key=key, value=value,
            )


def from_j(text: str, source: str = "") -> Document:
    """.j text -> Document."""
    lines, questions = scan(text)
    return Document(lines=lines, questions=questions, source=source)
