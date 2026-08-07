# j-notes

Converts `.j` files (raw personal notes) into `.jmd` files -- plain
Markdown that any ordinary `.md` parser can render correctly, carrying
extra metadata baked in that a plain `.md` parser won't know about or
choke on.

## What this is

In the `ijk-compilers` file taxonomy, `.j` is raw material -- not
authored to be read by anyone else, not necessarily structured at all.
`.jmd` is one step toward legibility: still just Markdown to a normal
tool, but annotated for anything that's `.jmd`-aware (built on top of
`ijk-compilers`) to read the extra layer.

This is **not** a K compiler and does not target `ktye/i`. That was an
earlier, since-corrected idea for what this repo would be -- see
`ijk-compilers` for the actual `.i`/`.j`/`.k`/`.ij`/`.ijk` compiler
suite. `j-notes` depends on `ijk-compilers`, not the other way around.

## Status

Design phase. The `.jmd` metadata format itself isn't specified yet.
`NOTATION_PROPOSAL.md` in this repo is left over from the earlier,
now-incorrect K-compiler framing -- its content (the K vocabulary table,
the arithmetic-stays/everything-else-gets-a-word principle) likely
belongs in `ijk-compilers` instead, pending a decision on where it
actually lands. Not deleted yet, not accurate to this repo's real job
either -- flagged rather than quietly kept as if still current.

## Relationship to other repos

- **Depends on `ijk-compilers`** -- the general compiler suite this
  repo builds on top of, not a sibling or a fork.
- **Not** the `Parser` repo (`.i` files, word-by-word personal-notes
  classifier). That engine is tuned to one person's private note-taking
  vocabulary; `j-notes` is scoped narrowly to one conversion (`.j` to
  `.jmd`), not general parsing.

## License

AGPL-3.0 -- see `LICENSE`.
