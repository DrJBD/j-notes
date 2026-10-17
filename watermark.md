# Watermark

Where j-notes stands on marking who wrote what. Drafted by Delta, Judah's
AI, from Judah's own position; his to change.

## The position

Marks should be visible. A reader should be able to tell what a person
wrote and what a machine drafted by looking at the files, not by running
a detector.

## The marks we make

- **The file says who.** A `.j` is written by a human. An AI may draft
  anything, but a draft only becomes a `.j` when the human promotes it.
  The spec's `--` meta lines say where a line came from, and they stay
  readable in the `.jmd`.
- **The commit says who.** When an AI helps, the commit carries a
  `Co-Authored-By` line naming it. It can be turned off. We leave it on.
- **The typos stay.** Judah's typos are kept where he made them. A
  machine would clean them up; leaving them is a mark of a human hand.
- **The asterisk came first.** Before any of this had file names, Judah
  marked an AI's word choices by hand: `* sic. Claude picked the word.`

## The marks we don't make

Invisible watermarks exist and are getting good:

- **Text:** a model can lean slightly toward certain words, in a pattern
  a detector can count (Kirchenbauer et al., ICML 2023). Google built
  this into its models as SynthID-Text (Dathathri et al., *Nature* 634,
  2024), and the text version is open source in Hugging Face
  Transformers.
- **Images:** Meta's Watermark Anything hides a message in an image's
  pixels in a way that survives cropping, and can say which part of the
  picture was marked (Sander et al., ICLR 2025; MIT License,
  github.com/facebookresearch/watermark-anything).

j-notes doesn't add one. An invisible mark is only honest if someone says
it's there, and the visible ones already carry the record. If a vendor's
model marks its output, the mark lives in the AI's drafts and thins out
with every human rewrite; a `.j` that's all the human's carries none.

## The marks nobody meant

Every model has habits: certain dashes, things in threes, a tidy closing
line. They act like a watermark though nobody pressed one in. Some humans
share them. So don't hunt for the machine in the style. Look at the
files.

## Status

Position, not spec. Nothing here changes `spec.yaml`.
