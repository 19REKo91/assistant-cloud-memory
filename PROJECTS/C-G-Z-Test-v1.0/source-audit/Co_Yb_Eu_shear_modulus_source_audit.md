# Co, Yb, Eu — Shear Modulus Source Audit

Date: 2026-11-16
Project: C-G-Z Test v1.0
Status: Source audit only. No CSV values changed; no C-G-Z calculation or statistical analysis performed.

## 1. Cobalt (Co, Z=27)

### Values located
- 75 GPa: WebElements lists rigidity modulus = 75 GPa.
  https://www.winter.group.shef.ac.uk/webelements/cobalt/physics.html
- 75 GPa: PSE-info periodic-table compilation lists Co = 75 GPa.
  https://pse-info.de/en/scale/elastic_rigidity
- 82.6 GPa: MatWeb datasheet for pure cobalt lists shear modulus = 82.6 GPa, alongside modulus of elasticity = 211 GPa and Poisson's ratio = 0.32.
  https://asia.matweb.com/search/SpecificMaterial.asp?bassnum=AMECo00

### Experimental / structural context
A paper on elastic and vibrational properties of cobalt reports measurements on hcp cobalt and discusses aggregate shear modulus using Voigt-Reuss-Hill averaging. It notes small but nonzero elastic anisotropy at ambient pressure and discusses agreement among experimental estimates.
- Goncharov, Crowhurst, Zaug, Physical Review Letters 92, 115502 (2004).
- DOI: https://doi.org/10.1103/PhysRevLett.92.115502
- Additional accessible text: https://digital.library.unt.edu/ark:/67531/metadc1409788/m1/8/

A separate published elastic-constant table reports experimental hcp cobalt single-crystal constants at 0 GPa, including C44 = 75 GPa and C66 = 71 GPa. These are single-crystal elastic constants and must not be mistaken automatically for an isotropic aggregate shear modulus.
- https://harvest.aps.org/v2/journals/articles/10.1103/PhysRevB.60.791/fulltext

### Assessment
The 75 versus 82.6 GPa discrepancy is material, not a trivial rounding difference. The 75 GPa value appears in multiple periodic-table compilations, while MatWeb reports 82.6 GPa for a pure-cobalt datasheet. Because cobalt is hcp and elastically anisotropic, the averaging convention and material state matter. Do not silently select one value. Retain the source conflict and seek the original experimental dataset / exact MatWeb reference and conditions before designating a canonical value.

## 2. Ytterbium (Yb, Z=70)

### Values located
- 9.9 GPa: Royal Society of Chemistry periodic table.
  https://periodic-table.rsc.org/element/70/ytterbium
- 9.9 GPa: WebElements.
  https://webelements.com/ytterbium/physics.html
- 9.90 GPa: MatWeb datasheet.
  https://www.matweb.com/search/datasheet_print.aspx?matguid=be5a82bdeb7a45cf80ded0bea2673a6a

The MatWeb datasheet also reports Young's modulus 23.7 GPa, bulk modulus 30.5 GPa, and Poisson's ratio 0.207. An ESPI Metals technical page reports shear modulus 9.9 GPa at 27 °C and identifies the beta phase in its material information:
https://www.espimetals.com/index.php/technical-data/269-Ytterbium

### Assessment
The available values agree at 9.9 GPa. A Wolfram/PeriodicTable.com value previously noted as 10 GPa is consistent with rounding to a whole GPa, not evidence of a substantive disagreement. However, the phase and exact test conditions are not documented uniformly across all sources. Retain 9.9 GPa as the consistent reported value, while preserving the condition caveat.

## 3. Europium (Eu, Z=63)

### Values located
- 7.9 GPa: Royal Society of Chemistry periodic table.
  https://periodic-table.rsc.org/element/63/Europium
- 7.9 GPa: WebElements.
  https://www.webelements.com/europium/physics.html
- 7.90 GPa: MatWeb.
  https://www.matweb.com/search/DataSheet.aspx?MatGUID=3bac003d0ba447e3b67b13fd48d54efd
- 7.8 GPa: PSE-info compilation.
  https://pse-info.de/en/scale/elastic_rigidity

MatWeb also lists Young's modulus 18.2 GPa, bulk modulus 8.30 GPa, and Poisson's ratio 0.152.

### Assessment
The discrepancy is 0.1 GPa (7.8 versus 7.9), plausibly due to rounding or source selection. The available sources do not establish the exact underlying measurement conditions for both values. Keep the conflict visible; do not silently overwrite either source record. For a provisional rounded dataset, 7.9 GPa has support from three sources, but this is not a claim of independent experimental replication.

## Dataset and project handling

- No values in elements_118_C_G_Z_input.csv were changed by this audit.
- No C values were recalculated.
- No correlations, regressions, or model comparisons were run.
- Existing source fields and notes should continue to distinguish compilation source from original experimental provenance.
- Co remains a material unresolved discrepancy.
- Yb is consistent at 9.9 GPa, with a rounded 10 GPa entry not treated as a substantive conflict.
- Eu retains a minor 7.8/7.9 GPa source difference.
