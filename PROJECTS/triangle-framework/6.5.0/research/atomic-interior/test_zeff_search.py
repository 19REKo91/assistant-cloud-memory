import math
import unittest

from zeff_search import parse_configuration, slater_zeff, hydrogenic_zeff

class EffectiveNuclearChargeTests(unittest.TestCase):
    def test_hydrogen_slater_limit(self):
        config = parse_configuration("1s1")
        zeff, shielding, subshell, n = slater_zeff(config)
        self.assertEqual(subshell, "1s")
        self.assertEqual(n, 1.0)
        self.assertAlmostEqual(shielding, 0.0)
        self.assertAlmostEqual(zeff, 1.0)

    def test_lithium_slater_screening(self):
        config = parse_configuration("1s2 2s1")
        zeff, shielding, subshell, n = slater_zeff(config)
        self.assertEqual(subshell, "2s")
        self.assertAlmostEqual(shielding, 1.70)
        self.assertAlmostEqual(zeff, 1.30)

    def test_noble_gas_core_expansion(self):
        config = parse_configuration("[Ne] 3s2 3p5")
        self.assertEqual(sum(config.values()), 17)
        zeff, shielding, subshell, n = slater_zeff(config)
        self.assertEqual(subshell, "3p")
        self.assertEqual(n, 3.0)
        self.assertGreater(zeff, 0)

    def test_same_principal_shell_sp_group(self):
        config = parse_configuration("1s2 2s2 2p6 3s2 3p5")
        zeff, shielding, subshell, n = slater_zeff(config)
        self.assertEqual(subshell, "3p")
        self.assertAlmostEqual(shielding, 10.90)
        self.assertAlmostEqual(zeff, 6.10)

    def test_transition_metal_configuration(self):
        config = parse_configuration("[Ar] 3d6 4s2")
        self.assertEqual(sum(config.values()), 26)
        zeff, shielding, subshell, n = slater_zeff(config)
        self.assertEqual(subshell, "4s")
        self.assertEqual(n, 4.0)
        self.assertAlmostEqual(shielding, 22.25)
        self.assertAlmostEqual(zeff, 3.75)

    def test_hydrogenic_estimate(self):
        value = hydrogenic_zeff(13.605693122994, 1)
        self.assertAlmostEqual(value, 1.0)
        self.assertTrue(math.isnan(hydrogenic_zeff(float("nan"), 1)))

if __name__ == "__main__":
    unittest.main()
