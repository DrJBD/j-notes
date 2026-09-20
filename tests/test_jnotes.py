"""Tests for the j-notes pipeline, written against spec.yaml."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jnotes import jmd, md
from jnotes.model import Kind, State
from jnotes.scan import find_marker, scan, split_body


def metas(doc):
    return [l for l in doc.lines if l.kind is Kind.META]


class TestMarker(unittest.TestCase):
    """spec.yaml -> meta_keyword.markers: one marker, two spellings."""

    def test_both_spellings_trigger(self):
        for spelling in ("--", "—"):
            self.assertIsNotNone(find_marker(f"done {spelling} Judah"))

    def test_thematic_break_is_not_a_marker(self):
        for rule in ("---", "----", "  ---  "):
            self.assertIsNone(find_marker(rule))

    def test_lone_dash_is_not_a_marker(self):
        self.assertIsNone(find_marker("- a bullet"))

    def test_marker_never_spans_lines(self):
        doc = jmd.from_j("-- key: value\nordinary next line\n")
        self.assertEqual(len(metas(doc)), 1)
        self.assertEqual(doc.lines[1].kind, Kind.TEXT)


class TestEpistemicStates(unittest.TestCase):
    """spec.yaml -> meta_keyword.epistemic_states, all three reachable."""

    def test_stated_outright_is_known_by_judah(self):
        self.assertEqual(split_body("title: The River")[2], State.KNOWN_BY_JUDAH)

    def test_bare_question_mark_is_undecided(self):
        self.assertEqual(split_body("editor: ?")[2], State.UNDECIDED)

    def test_empty_value_is_undecided(self):
        self.assertEqual(split_body("editor:")[2], State.UNDECIDED)

    def test_offered_candidate_is_ai_guess(self):
        key, value, state = split_body("year: ?2026")
        self.assertEqual((key, value, state), ("year", "2026", State.AI_GUESS))

    def test_attribution_is_known_by_judah(self):
        doc = jmd.from_j("Back channels are where the real work get done -- Judah\n")
        m = metas(doc)[0].meta
        self.assertEqual(m.state, State.KNOWN_BY_JUDAH)
        self.assertTrue(m.is_attribution)


class TestAmbiguityIsAsked(unittest.TestCase):
    """spec.yaml -> ambiguity_resolution: ask Judah, never guess silently."""

    def test_wrapped_prose_dash_is_asked_not_assumed(self):
        # The real shape from library/the-river-v2.2.md line 913.
        src = (
            "A database that answered questions has to handle information \n"
            "-- not the same failure. A system that only has room for true\n"
        )
        doc = jmd.from_j(src)
        self.assertEqual(len(doc.open_questions), 1)
        self.assertIn("hard-wrapped prose", doc.open_questions[0].reason)
        self.assertEqual(metas(doc), [])

    def test_leading_marker_after_finished_sentence_is_a_marker(self):
        doc = jmd.from_j("A sentence that ends properly.\n-- key: value\n")
        self.assertEqual(doc.open_questions, [])
        self.assertEqual(len(metas(doc)), 1)

    def test_bullet_run_is_settled_as_ordinary_text(self):
        src = "-- k: v\n\n- first item\n- second item\n- third item\n"
        doc = jmd.from_j(src)
        self.assertEqual(doc.open_questions, [])

    def test_lone_bullet_beside_real_markers_is_asked(self):
        doc = jmd.from_j("-- k: v\n\n- an only child\n\nmore prose.\n")
        self.assertEqual(len(doc.open_questions), 1)
        self.assertIn("truncation", doc.open_questions[0].reason)

    def test_lone_dash_never_silently_promoted(self):
        # not_a_marker: "-" is never auto-read as a marker, only asked about.
        doc = jmd.from_j("-- k: v\n\n- an only child\n")
        self.assertTrue(all(l.meta.marker != "-" for l in metas(doc)))

    def test_marker_under_a_heading_is_not_wrapped_prose(self):
        # A heading closes its own block; prose cannot wrap into a marker.
        doc = jmd.from_j("# Working notes\n\n-- title: The River\n")
        self.assertEqual(doc.open_questions, [])
        self.assertEqual(len(metas(doc)), 1)

    def test_a_run_of_markers_does_not_flag_itself(self):
        src = "# Notes\n\n-- title: The River\n-- editor: ?\n-- year: ?2026\n"
        doc = jmd.from_j(src)
        self.assertEqual(doc.open_questions, [])
        self.assertEqual(len(metas(doc)), 3)

    def test_marker_under_a_list_item_is_not_wrapped_prose(self):
        doc = jmd.from_j("- a bullet with no period\n\n-- key: value\n")
        self.assertEqual(doc.open_questions, [])

    def test_code_fences_are_never_scanned(self):
        src = "```\n-- not a marker in here\n- nor this\n```\n"
        doc = jmd.from_j(src)
        self.assertEqual(metas(doc), [])
        self.assertEqual(doc.open_questions, [])


class TestFinalMarkdown(unittest.TestCase):
    """spec.yaml -> pipeline.final and meta_keyword.output_encoding."""

    def build(self, src):
        return md.render(jmd.from_j(src))

    def test_meta_becomes_an_invisible_html_comment(self):
        out = self.build("-- title: The River\n")
        self.assertEqual(out.strip(), "<!-- j-notes known_by_judah title: The River -->")

    def test_attribution_keeps_the_prose_and_hides_the_meta(self):
        out = self.build("Back channels are where the real work get done -- Judah\n")
        self.assertTrue(out.startswith("Back channels are where the real work get done"))
        self.assertIn("<!-- j-notes known_by_judah Judah -->", out)
        self.assertNotIn(" -- Judah", out)

    def test_nothing_visible_is_left_over(self):
        out = self.build("Real prose.\n\n-- key: value\n")
        visible = [l for l in out.splitlines() if l.strip() and not l.startswith("<!--")]
        self.assertEqual(visible, ["Real prose."])

    def test_refuses_to_emit_while_a_question_is_open(self):
        src = "unterminated line\n-- ambiguous\n"
        with self.assertRaises(md.Unresolved):
            self.build(src)

    def test_comment_closer_in_content_is_raised_not_mangled(self):
        # Passthrough-unmodified and nothing-visible collide here.
        with self.assertRaises(md.Unresolved) as cm:
            self.build("-- note: careful --> here\n")
        self.assertIn("close the HTML comment early", str(cm.exception))

    def test_code_and_prose_pass_through_unchanged(self):
        src = "# Title\n\n```\n-- inert\n```\n\ntext\n"
        self.assertIn("-- inert", self.build(src))


class TestRoundTrip(unittest.TestCase):
    """The .jmd is the file both parties edit; it has to survive a round trip."""

    src = "Prose here. -- Judah\n\n-- title: The River\n-- editor: ?\n-- year: ?2026\n"

    def test_states_survive_the_round_trip(self):
        doc = jmd.parse(jmd.render(jmd.from_j(self.src, "demo.j")))
        self.assertEqual(
            [l.meta.state for l in metas(doc)],
            [State.KNOWN_BY_JUDAH, State.KNOWN_BY_JUDAH, State.UNDECIDED, State.AI_GUESS],
        )

    def test_judah_confirming_a_guess_outranks_the_sigil(self):
        text = jmd.render(jmd.from_j(self.src, "demo.j"))
        confirmed = text.replace("[ai_guess] year: ?2026", "[known_by_judah] year: 2026")
        doc = jmd.parse(confirmed)
        year = [l for l in metas(doc) if l.meta.key == "year"][0]
        self.assertEqual(year.meta.state, State.KNOWN_BY_JUDAH)
        self.assertEqual(year.meta.value, "2026")

    def test_answering_prose_demotes_the_line(self):
        src = "unterminated line\n-- not a marker after all\n"
        text = jmd.render(jmd.from_j(src, "demo.j"))
        doc = jmd.parse(text.replace("[open]", "[prose]"))
        self.assertEqual(doc.open_questions, [])
        self.assertEqual(metas(doc), [])
        self.assertIn("-- not a marker after all", md.render(doc))

    def test_an_answer_outside_the_offered_set_is_refused(self):
        text = jmd.render(jmd.from_j("unterminated\n-- maybe\n", "d.j"))
        with self.assertRaises(ValueError):
            jmd.parse(text.replace("[open]", "[banana]"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
