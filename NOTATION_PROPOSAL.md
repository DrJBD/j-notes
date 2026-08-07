# `.j` Notation — First Draft Proposal

Status: **draft, not implemented, not agreed** — written for Judah to react
to, cut, or redirect. Nothing below is locked. No parser exists yet.

## 1. File shape

Same family as the existing `.i` convention (Title/STATUS header,
`====`-delimited sections, `BEGIN CONTEXT`/`END CONTEXT` block), extension
`.j` instead of `.i` to mark that this BODY compiles into a real program
rather than describing something:

```
<Title>
STATUS: <OPEN | CLOSED | ...>

============================================================
Header
============================================================

<free-text metadata: purpose, target (native/WASM), notes>

============================================================
Body
============================================================

<the actual .j program, in the notation below>

============================================================
Context
============================================================

BEGIN CONTEXT
END CONTEXT
```

## 2. What's actually verified vs. what's still a guess

Pulled directly from `ktye/i`'s root `k` file (confirmed by fetching it,
not assumed):

**Dyadic verbs — symbol-to-word table, confirmed by direct source read:**

| symbol | `+` | `-` | `*` | `%` | `!` | `&` | `\|` | `<` | `>` | `=` | `~` | `,` | `^` | `#` | `_` | `$` | `?` | `@` | `.` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| word | add | sub | mul | div | mod | min | max | les | mor | eql | neq | cat | cut | tak | drp | fmt | fnd | atx | cal |

**Monadic verbs and adverbs — word lists confirmed present in the source,
but their exact glyph-by-glyph alignment (which word binds to which symbol
in monadic position) was *not* independently verified against the real
dispatch table** — the comment layout strongly implies a 1:1 order match to
the same 19 symbols above, but I only confirmed 6 of the monadic bodies
(`Abs`, `Sqt`, `Not`, `Flp`, `Neg`, `Sqr`) directly in the snippet you
pasted, not all 19 against their symbols. Treat this list as vocabulary,
not yet as a confirmed glyph map:

`abs neg sqr sqt til flp rev asc dsc grp not enl srt cnt flr str unq fst val`

**Adverbs (the things that turn a verb into each/over/scan/etc.), word list
confirmed present:**

`ech pri bot bin ovr fix ecr jon scn fxs ecl spl` — each, prior, both,
binary(?), over, fix, each-right, join, scan, fix-scan, each-left, split.

Before any compiler code gets written, this table needs a real
verification pass against `ktye/i`'s dispatch source (not the `k` file
alone) — same discipline as everywhere else in this system: don't build on
an unconfirmed mapping.

## 3. Draft syntax sketch

Two open forks below (§4) — this section shows the shape assuming the
"spell out anything that isn't already unambiguous to a human" principle.

**Arithmetic stays as familiar symbols** — `+ - * /` for add/sub/mul/div.
These are already unambiguous to a human reader; spelling them out would
add friction without buying clarity. (`/` maps to K's `%`, a straight
substitution at compile time.)

**Everything else K overloads onto a single glyph gets a word** — this is
the actual point of the exercise, since these are exactly the ones a human
can't guess without memorizing K's table:

```
total = sum over prices
biggest = max over scores
sorted = ascend prices
first_three = take 3 from prices
without_first = drop 1 from prices
doubled = each prices (multiply by 2)
```

**Assignment**: `name = expr` (compiles to K's `:`).

**Comments**: `# like this`, stripped before compilation, distinct from a
`.j` file's own HEADER/CONTEXT metadata.

## 4. Open questions — real forks, not decided here

1. **Verb+adverb word order.** K itself is right-to-left, postfix-adverb
   (`+/prices` = sum). Two readable options, both defensible:
   - **Adverb-first, prefix:** `over add prices` — mirrors K's own
     adverb-after-verb relationship, reads like a sentence.
   - **Verb-first, infix `over`:** `add over prices` — reads more like
     English ("add, applied over prices"), shown in §3 above as the
     working example, but not committed.
2. **Function/block definitions.** K functions are `{...}` with implicit
   `x`/`y`/`z` args. Does `.j` keep that, or require named parameters
   (`define add_tax(price): price * 1.08`)? Named params read better;
   implicit args are closer to K's own idiom and cheaper to compile.
3. **Types.** K has a real type system (int/float/char/symbol/list/dict,
   vectors vs. atoms). How much of that surfaces in `.j` syntax vs. staying
   inferred/hidden the way Python hides most of it?
4. **Whitespace/indentation.** Significant (Python-style blocks) or not
   (K has none)? Significant whitespace is more familiar to you; K has no
   native block concept to map it onto cleanly.
5. **Error handling.** K's `Q` (quote/error) appears throughout the source
   for malformed input. Does `.j` need its own error vocabulary, or does
   this stay invisible until it's actually needed?

## 5. What I'd suggest as next step

Pick a small, real target program (even something trivial — e.g., the
`Sum` function already visible in `ktye/i`'s own source) and hand-translate
it into candidate `.j` syntax under both options in §4.1, side by side.
Concrete example beats further abstract spec-writing.
