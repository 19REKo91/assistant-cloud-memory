import unittest
import pandas as pd

from levels_search import parse_level_value, parse_levels_ascii, summarize_levels

class LevelParserTests(unittest.TestCase):
    def test_level_provenance_and_grouped_digits(self):
        self.assertEqual(parse_level_value("15 867.862"), (15867.862, "EVALUATED"))
        self.assertEqual(parse_level_value("[15 867.862]"), (15867.862, "SEMIEMPIRICAL"))
        self.assertEqual(parse_level_value("(33 792.583)"), (33792.583, "THEORETICAL"))
        self.assertEqual(parse_level_value("12 345.6?"), (12345.6, "TENTATIVE"))
        self.assertEqual(parse_level_value("76 190a"), (76190.0, "FOOTNOTED"))

    def test_parse_nist_ascii_level_table(self):
        raw = """<html><pre>
Configuration | Term | J | Level
(cm^-1) | Reference
--------------|------|---|---------------|----------
2s^2 2p^4 | 3P | 2 | 0.000 | L7288
             |    | 1 | 158.265 |
             |    | 0 | 226.977 |
2s^2 2p^4 | 1D | 2 | 15 867.862 |
2s^2 2p^4 | 1S | 0 | (33 792.583) |
2s^2 2p^3 3s | 5S | 2 | 73 768.200 |
</pre></html>"""
        parsed = parse_levels_ascii(raw, 8, "O")
        self.assertEqual(len(parsed), 6)
        self.assertEqual(parsed.iloc[0]["provenance"], "EVALUATED")
        self.assertEqual(parsed.iloc[4]["provenance"], "THEORETICAL")

    def test_preserves_blank_group_cells_with_four_column_header(self):
        raw = """<html><pre>
Configuration | Term | J | Level
(cm^-1)
--------------|------|---|---------------
2s^2 2p^4 | 3P | 2 | 0.000
             |    | 1 | 158.265
             |    | 0 | 226.977
2s^2 2p^4 | 1D | 2 | 15 867.862
</pre></html>"""
        parsed = parse_levels_ascii(raw, 8, "O")
        self.assertAlmostEqual(parsed.iloc[1]["level_cm1"], 158.265)
        self.assertEqual(parsed.iloc[1]["term"], "3P")
        self.assertAlmostEqual(parsed.iloc[2]["level_cm1"], 226.977)
        self.assertEqual(parsed.iloc[2]["term"], "3P")

    def test_summary_extracts_excitation_and_distinct_term_gaps(self):
        raw = """<html><pre>
Configuration | Term | J | Level
(cm^-1) | Reference
--------------|------|---|---------------|----------
2s^2 2p^4 | 3P | 2 | 0.000 | L7288
             |    | 1 | 158.265 |
             |    | 0 | 226.977 |
2s^2 2p^4 | 1D | 2 | 15 867.862 |
2s^2 2p^3 3s | 5S | 2 | 73 768.200 |
</pre></html>"""
        parsed = parse_levels_ascii(raw, 8, "O")
        summary = summarize_levels(parsed).iloc[0]
        self.assertAlmostEqual(summary["first_excited_level_gap_evaluated_cm1"], 158.265)
        self.assertAlmostEqual(summary["first_distinct_term_gap_evaluated_cm1"], 15867.862)
        self.assertAlmostEqual(summary["first_distinct_configuration_gap_evaluated_cm1"], 73768.2)

if __name__ == "__main__":
    unittest.main()
