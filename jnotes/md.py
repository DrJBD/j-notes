"""The .md stage: valid CommonMark with nothing visible left over.

spec.yaml -> pipeline.final, and meta_keyword.output_encoding: whatever
sits inside a marked section is passed through unmodified as raw HTML.
CommonMark parses raw HTML natively and a renderer hides a comment on
its own, so there is no custom escaping scheme here by design.

The one place that rule cannot hold on its own is content containing
"-->", which would close the comment early and leave the remainder
VISIBLE -- breaking pipeline.final. Unmodified passthrough and "nothing
visible left over" genuinely collide there, so that case is raised as a
question rather than resolved by inventing an escape.
"""

from __future__ import annotations

from .model import Document, Kind, Line, Question

#: Sequences that terminate an HTML comment (HTML5 tokenizer).
CLOSERS = ("-->", "--!>")


class Unresolved(Exception):
    """Raised rather than emit a .md that passes a guess off as settled."""

    def __init__(self, questions: list[Question]) -> None:
        self.questions = questions
        lines = [f"  {q.qid} (line {q.line_no}): {q.reason}" for q in questions]
        super().__init__(
            f"{len(questions)} question(s) still open; answer them in the .jmd "
            "before building .md:\n" + "\n".join(lines)
        )


def comment_hazards(doc: Document) -> list[Line]:
    return [
        l for l in doc.lines
        if l.kind is Kind.META and l.meta and any(c in l.meta.body for c in CLOSERS)
    ]


def render(doc: Document) -> str:
    """Document -> final .md. Refuses while anything is still open."""
    if doc.open_questions:
        raise Unresolved(doc.open_questions)

    hazards = comment_hazards(doc)
    if hazards:
        raise Unresolved([
            Question(
                qid=f"h{l.no}",
                line_no=l.no,
                reason='marked content contains "-->", which would close the HTML '
                       "comment early and leave the rest visible in the final .md",
                answers=("drop", "keep-visible"),
                excerpt=l.meta.body if l.meta else "",
            )
            for l in hazards
        ])

    out = [_emit(l) for l in doc.lines]
    text = "\n".join(out)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip("\n") + "\n"


def _emit(line: Line) -> str:
    if line.kind is not Kind.META or line.meta is None:
        return line.raw
    m = line.meta
    payload = f"j-notes {m.state.value}"
    if m.body:
        payload += f" {m.body}"
    comment = f"<!-- {payload} -->"
    before = line.before
    return f"{before} {comment}" if before else comment
