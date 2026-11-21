import unittest
import math
import pandas as pd

from electronic_search import (
    parse_energy_token,
    parse_shells,
    parse_nist_tsv,
    electronic_element_summary,
)
from stable_isotope_search import parse_nubase2020, build_stable_isotope_summary

class ElectronicParserTests(unittest.TestCase):
    def test_nist_provenance_qualifiers(self):
        self.assertEqual(parse_energy_token("5.391714996"), (5.391714996, "MEASURED"))
        self.assertEqual(parse_energy_token("[29.60125]"), (29.60125, "SEMIEMPIRICAL"))
        self.assertEqual(parse_energy_token("(552.06741)"), (552.06741, "THEORETICAL"))
        missing_value, missing_kind = parse_energy_token("")
        self.assertTrue(math.isnan(missing_value))
        self.assertEqual(missing_kind, "MISSING")

    def test_parse_shell_occupancy(self):
        self.assertEqual(parse_shells("1s^2 2s^2 2p^6 3s^1"), (3, 1))
        self.assertEqual(parse_shells("[Ne] 3s2 3p5"), (3, 7))

    def test_parse_nist_tabular_data(self):
        raw = (
            "At. Num.\tEl. name\tIon Charge\tGround Shells\tIonization Energy (eV)\n"
            "3\tLithium\t0\t1s^2 2s^1\t5.391714996\n"
            "3\tLithium\t1\t1s^2\t[75.6400]\n"
            "3\tLithium\t2\t1s^1\t(122.4)\n"
        )
        parsed = parse_nist_tsv(raw)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed.iloc[0]["provenance"], "MEASURED")
        self.assertEqual(parsed.iloc[1]["provenance"], "SEMIEMPIRICAL")
        self.assertEqual(parsed.iloc[2]["provenance"], "THEORETICAL")
        self.assertEqual(parsed.iloc[0]["ion_charge"], 0)

    def test_parse_nist_html_output(self):
        raw = """<html><body><table>
        <tr><th>At. Num.</th><th>El. name</th><th>Ion Charge</th>
        <th>Ground Shells</th><th>Ionization Energy (eV)</th></tr>
        <tr><td>3</td><td>Lithium</td><td>0</td><td>1s2 2s1</td><td>5.391714996</td></tr>
        </table></body></html>"""
        parsed = parse_nist_tsv(raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed.iloc[0]["Z"], 3)
        self.assertEqual(parsed.iloc[0]["energy_eV"], 5.391714996)

    def test_sequential_summary_separates_provenance(self):
        ion = pd.DataFrame([
            {"Z": 3, "ion_charge": 0, "energy_eV": 5.39, "provenance": "MEASURED",
             "ground_shells": "1s2 2s1", "occupied_principal_shell_count": 2,
             "outermost_shell_electron_count": 1},
            {"Z": 3, "ion_charge": 1, "energy_eV": 75.6, "provenance": "SEMIEMPIRICAL",
             "ground_shells": "1s2", "occupied_principal_shell_count": 1,
             "outermost_shell_electron_count": 2},
            {"Z": 3, "ion_charge": 2, "energy_eV": 122.4, "provenance": "THEORETICAL",
             "ground_shells": "1s1", "occupied_principal_shell_count": 1,
             "outermost_shell_electron_count": 1},
        ])
        binding = pd.DataFrame([
            {"Z": 3, "ion_charge": 0, "energy_eV": 203.39, "provenance": "MEASURED"}
        ])
        summary = electronic_element_summary(ion, binding).iloc[0]
        self.assertEqual(summary["IE1_measured_eV"], 5.39)
        self.assertTrue(pd.isna(summary["IE2_measured_eV"]))
        self.assertTrue(pd.isna(summary["IE1_to_IE3_sum_measured_eV"]))
        self.assertEqual(summary["total_binding_neutral_measured_eV"], 203.39)

class StableIsotopeTests(unittest.TestCase):
    def test_nubase_filters_to_stable_ground_states(self):
        def make_line(A, zstate, half_life, abundance=""):
            chars = [" "] * 209
            chars[0:3] = list(f"{A:03d}")
            chars[4:8] = list(zstate)
            chars[69:78] = list(f"{half_life:<9}"[:9])
            chars[119:119+len(abundance)] = list(abundance)
            return "".join(chars)
        raw = "\n".join([
            make_line(6, "0030", "stbl", "IS=7.59 12"),
            make_line(7, "0030", "stbl", "IS=92.41 12"),
            make_line(7, "0038", "stbl", "IS=92.41 12"),  # isomer / non-ground state
            make_line(8, "0030", "2.0 s", ""),
        ])
        parsed = parse_nubase2020(raw)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(set(parsed["A"]), {6, 7})

    def test_abundance_weighted_stable_isotope_summary(self):
        nubase = pd.DataFrame([
            {"Z": 3, "A": 6, "N": 3, "isotopic_abundance_pct": 7.5},
            {"Z": 3, "A": 7, "N": 4, "isotopic_abundance_pct": 92.5},
        ])
        ame = pd.DataFrame([
            {"Z": 3, "A": 6, "N": 3, "Sn_keV": 100.0, "Sp_keV": 200.0,
             "S2n_keV": 300.0, "S2p_keV": 400.0, "N_over_Z": 1.0,
             "neutron_excess_fraction": 0.0, "binding_energy_per_A_keV": 5000.0,
             "nearest_magic_N_distance": 1, "nearest_magic_Z_distance": 1},
            {"Z": 3, "A": 7, "N": 4, "Sn_keV": 200.0, "Sp_keV": 300.0,
             "S2n_keV": 400.0, "S2p_keV": 500.0, "N_over_Z": 4/3,
             "neutron_excess_fraction": 1/7, "binding_energy_per_A_keV": 6000.0,
             "nearest_magic_N_distance": 0, "nearest_magic_Z_distance": 1},
        ])
        _, summary = build_stable_isotope_summary(nubase, ame)
        row = summary.iloc[0]
        self.assertEqual(row["dominant_stable_A"], 7)
        self.assertAlmostEqual(row["Sn_keV_abundance_weighted"], 192.5)

if __name__ == "__main__":
    unittest.main()
