"""j-notes command line: jmd, md, build."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import jmd, md


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="jnotes", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, help_ in (
        ("jmd", "convert a .j source into a .jmd working file"),
        ("md", "convert an answered .jmd into final CommonMark"),
        ("build", "run both stages, stopping if anything needs asking"),
    ):
        s = sub.add_parser(name, help=help_)
        s.add_argument("path", type=Path)
        s.add_argument("-o", "--out", type=Path, default=None)

    a = p.parse_args(argv)
    text = a.path.read_text(encoding="utf-8")

    if a.cmd == "jmd":
        doc = jmd.from_j(text, source=a.path.name)
        return _write(jmd.render(doc), a.out or a.path.with_suffix(".jmd"), doc)

    if a.cmd == "md":
        try:
            doc = jmd.parse(text)
            out = md.render(doc)
        except md.Unresolved as e:
            print(f"jnotes: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"jnotes: {e}", file=sys.stderr)
            return 2
        return _write(out, a.out or a.path.with_suffix(".md"), doc)

    doc = jmd.from_j(text, source=a.path.name)
    work = a.path.with_suffix(".jmd")
    work.write_text(jmd.render(doc), encoding="utf-8")
    try:
        out = md.render(doc)
    except md.Unresolved as e:
        print(f"jnotes: {e}", file=sys.stderr)
        print(f"jnotes: wrote {work} with the questions to answer.", file=sys.stderr)
        return 2
    return _write(out, a.out or a.path.with_suffix(".md"), doc)


def _write(text: str, dest: Path, doc) -> int:
    dest.write_text(text, encoding="utf-8")
    n = len(doc.open_questions)
    note = f" ({n} question(s) for Judah)" if n else ""
    print(f"jnotes: wrote {dest}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
