"""Marker recognition and the lone-dash typo check.

spec.yaml -> meta_keyword.syntax:
    Line-scoped, not block-scoped. Never spans multiple lines.

"Line-scoped" is taken here to mean the marked section runs from the
marker to the end of THAT line and stops. It does not mean the marker
has to start the line: the corpus in library/ uses a trailing marker
for attribution ("... -- Judah"), which is exactly the shape of
known_by_judah ("Judah has stated the answer directly").

Two readings the scanner refuses to settle by itself, per
spec.yaml -> input.ambiguity_resolution (decision_authority: Judah):

  * a line-leading marker directly under an unterminated line, which is
    what a hard-wrapped prose dash looks like, and
  * a lone "-", which is what a truncated "--" looks like.

Both become Questions instead of silent decisions.
"""

from __future__ import annotations

import re

from .model import MARKERS, Kind, Line, Meta, Question, State

FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
#: A line that is only dashes (3+) is a CommonMark thematic break or a
#: setext underline, not a two-dash marker with a dash for content.
ALL_DASH = re.compile(r"^\s*-{3,}\s*$")
LEADING_BULLET = re.compile(r"^(\s*)-(?!-)(\s+\S|\s*$)")
#: Anything that opens a block of its own. Prose cannot wrap INTO one of
#: these, so a marker underneath one is a marker, not a continuation.
BLOCK_START = re.compile(r"^\s{0,3}(#{1,6}\s|>|\||\d+[.)]\s|[-*+]\s)")
#: Sentence-final punctuation. A leading marker under a line ending this
#: way is a real marker; under anything else it may be wrapped prose.
TERMINAL = tuple(".!?:;\"')]}”")

#: A trailing marker whose remainder is longer than this is not obviously
#: an attribution, so it gets asked about rather than assumed.
ATTRIBUTION_MAX = 60


def find_marker(raw: str) -> tuple[int, str] | None:
    """First marker occurrence in `raw` as (index, spelling), else None."""
    if ALL_DASH.match(raw):
        return None
    best: tuple[int, str] | None = None
    for spelling in MARKERS:
        i = raw.find(spelling)
        while i != -1:
            # "--" inside a longer dash run is not the marker.
            if spelling == "--":
                after = i + 2
                if after < len(raw) and raw[after] == "-":
                    i = raw.find(spelling, i + 1)
                    continue
                if i > 0 and raw[i - 1] == "-":
                    i = raw.find(spelling, i + 1)
                    continue
            if best is None or i < best[0]:
                best = (i, spelling)
            break
    return best


def split_body(body: str) -> tuple[str | None, str | None, State]:
    """Read a marked section's body into (key, value, state).

    Value sigils, all of them line-scoped:
        key: value    -> known_by_judah, an answer stated outright
        key: ?        -> undecided, the key is raised but unanswered
        key: ?value   -> ai_guess, a candidate offered but unconfirmed
    A body with no colon is a keyless note and carries no value.
    """
    body = body.strip()
    if not body:
        return None, None, State.UNDECIDED
    if ":" not in body:
        return None, None, State.KNOWN_BY_JUDAH
    key, _, value = body.partition(":")
    key, value = key.strip(), value.strip()
    if not key:
        return None, None, State.KNOWN_BY_JUDAH
    if not value:
        return key, None, State.UNDECIDED
    if value.startswith("?"):
        rest = value[1:].strip()
        return (key, rest, State.AI_GUESS) if rest else (key, None, State.UNDECIDED)
    return key, value, State.KNOWN_BY_JUDAH


def _continuable(prev: Line) -> bool:
    """Could `prev` be a prose line that hard-wrapped onto the next one?

    Only ordinary, unfinished prose can. A heading, a list item, a table
    row, a quote, a thematic break, or a line already carrying a marker
    all close their own block, so a marker beneath one starts something
    new rather than continuing anything.
    """
    if prev.kind is not Kind.TEXT:
        return False
    if ALL_DASH.match(prev.raw) or BLOCK_START.match(prev.raw):
        return False
    if find_marker(prev.raw) is not None:
        return False
    return not prev.raw.rstrip().endswith(TERMINAL)


def _prev_content(lines: list[Line], idx: int) -> Line | None:
    for j in range(idx - 1, -1, -1):
        if lines[j].kind is not Kind.BLANK:
            return lines[j]
    return None


def scan(text: str) -> tuple[list[Line], list[Question]]:
    """Classify every line of a .j source and collect what must be asked."""
    lines: list[Line] = []
    questions: list[Question] = []
    in_fence = False

    for n, raw in enumerate(text.splitlines(), start=1):
        line = Line(no=n, raw=raw)
        if FENCE.match(raw):
            in_fence = not in_fence
            line.kind = Kind.CODE
        elif in_fence or raw.startswith("    "):
            line.kind = Kind.CODE           # fenced or indented code: never scanned
        elif not raw.strip():
            line.kind = Kind.BLANK
        lines.append(line)

    counter = 0

    def ask(line: Line, reason: str, answers: tuple[str, ...]) -> None:
        nonlocal counter
        counter += 1
        questions.append(
            Question(
                qid=f"q{counter}",
                line_no=line.no,
                reason=reason,
                answers=answers,
                excerpt=line.raw.strip(),
            )
        )

    for idx, line in enumerate(lines):
        if line.kind in (Kind.CODE, Kind.BLANK):
            continue

        hit = find_marker(line.raw)
        if hit is None:
            _weigh_lone_dash(lines, idx, line, ask)
            continue

        col, spelling = hit
        body = line.raw[col + len(spelling) :]
        leading = not line.raw[:col].strip()

        if leading:
            prev = _prev_content(lines, idx)
            if prev is not None and _continuable(prev):
                # Exactly the shape of a hard-wrapped prose dash. Do not guess.
                ask(
                    line,
                    'line-leading marker directly under a line with no sentence-ending '
                    'punctuation, which is also what hard-wrapped prose looks like',
                    ("marker", "prose"),
                )
                continue
        elif len(body.strip()) > ATTRIBUTION_MAX:
            ask(
                line,
                "mid-line marker with a long remainder: an attribution, or a dash used "
                "as prose punctuation?",
                ("marker", "prose"),
            )
            continue

        key, value, state = split_body(body)
        line.kind = Kind.META
        line.meta = Meta(
            marker=spelling, col=col, state=state, body=body.strip(), key=key, value=value
        )

    return lines, questions


def _weigh_lone_dash(lines: list[Line], idx: int, line: Line, ask) -> None:
    """spec.yaml -> meta_keyword.typo_check.

    A lone "-" is not a valid trigger, but it is exactly the shape a
    truncated "--" or a dropped keystroke on an em-dash would take. It is
    weighed as a possible typo before being read as ordinary text. It is
    never silently promoted to a marker: not_a_marker says "-" is not a
    trigger, so the only safe directions are "ordinary text" or "ask".
    """
    m = LEADING_BULLET.match(line.raw)
    if not m:
        return  # not line-leading; a hyphen or minus sign inside prose

    indent = len(m.group(1))

    # A run of sibling dashes is a list. Settled, no question needed.
    for j in (idx - 1, idx + 1):
        if 0 <= j < len(lines):
            sib = LEADING_BULLET.match(lines[j].raw)
            if sib and len(sib.group(1)) == indent:
                return

    # A lone bullet in a document that never uses the real marker is text.
    if not any(l.kind is Kind.META for l in lines):
        return

    ask(
        line,
        'lone "-" with no sibling list item, in a document that does use the real '
        "marker: possible truncation of \"--\"",
        ("ordinary", "marker"),
    )
