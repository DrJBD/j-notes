# j-notes

Converts `.j` files (raw personal notes) into `.jmd` files -- plain
Markdown that any ordinary `.md` parser can render correctly, carrying
extra metadata baked in that a plain `.md` parser won't know about or
choke on. 

## What this is

`.j` is raw material -- not authored to be read by anyone else, not 
necessarily structured at all.  Writing in something similar to a .md
file will allow parsing by the AI to be as simple as possible.  That
is, .j files could already be .md files but this j-notes specification
allows an automated process to go from .j files to .md files.
`.jmd` is one step toward legibility: still just Markdown to a normal
tool, but annotated for anything that's `.jmd`-aware.

This is **not** a K compiler and does not target `ktye/i`.

## Status

The `.j`/`.jmd`/`.md` stage shape is settled (see`spec.yaml`).
The `.jmd` metadata format's exact contents beyond the
`--` meta-keyword is explictly not specified.

## Relationship to other repos

- None

## License

AGPL-3.0 -- see `LICENSE`.
