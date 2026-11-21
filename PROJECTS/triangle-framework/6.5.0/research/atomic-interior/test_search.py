import unittest
import pandas as pd

from search import (
    calculate_closure_angles,
    derive_separation_energies,
    ME_NEUTRON_KEV,
    ME_HYDROGEN_KEV,
)

class AtomicInteriorTests(unittest.TestCase):
    def test_closure_angle_uses_five_approved_inputs(self):
        source = pd.DataFrame([{
            "Z": 3, "Sym": "Li", "M": 6.94, "rho": 0.534,
            "R": 133, "mp_C": 180.54, "Data_Quality": "MEASURED"
        }])
        result = calculate_closure_angles(source)
        self.assertAlmostEqual(result.loc[0, "theta1"], 80.0)
        self.assertAlmostEqual(result.loc[0, "theta3"], 300.0 - (
            result.loc[0, "theta1"] + result.loc[0, "theta2_end"]
            + result.loc[0, "theta4"] + result.loc[0, "theta5"]
        ))

    def test_separation_energies_are_mass_differences(self):
        # Synthetic mass-excess map chosen to make the expected equations explicit.
        masses = pd.DataFrame([
            {"Z": 2, "N": 2, "A": 4, "symbol": "He", "mass_excess_keV": -25000.0},
            {"Z": 2, "N": 3, "A": 5, "symbol": "He", "mass_excess_keV": -30000.0},
            {"Z": 2, "N": 4, "A": 6, "symbol": "He", "mass_excess_keV": -35000.0},
            {"Z": 1, "N": 3, "A": 4, "symbol": "H", "mass_excess_keV": -10000.0},
        ])
        result = derive_separation_energies(masses).set_index(["Z", "N"])
        self.assertAlmostEqual(
            result.loc[(2, 4), "Sn_keV"],
            -30000.0 + ME_NEUTRON_KEV - (-35000.0)
        )
        self.assertAlmostEqual(
            result.loc[(2, 4), "S2n_keV"],
            -25000.0 + 2 * ME_NEUTRON_KEV - (-35000.0)
        )
        self.assertAlmostEqual(
            result.loc[(2, 4), "Sp_keV"],
            -10000.0 + ME_HYDROGEN_KEV - (-35000.0)
        )

    def test_estimated_mass_rows_are_not_used(self):
        masses = pd.DataFrame([
            {"Z": 2, "N": 2, "A": 4, "symbol": "He", "mass_excess_keV": -25000.0, "estimated": False},
            {"Z": 2, "N": 3, "A": 5, "symbol": "He", "mass_excess_keV": -30000.0, "estimated": True},
        ])
        result = derive_separation_energies(masses)
        self.assertTrue(result["Sn_keV"].isna().all())

if __name__ == "__main__":
    unittest.main()
