# Atomic-mass basis audit — CIAAW 2024 cross-reference
Date: 2026-11-22

## Key finding
The 118-row mass column is not one uniform type of mass. CIAAW publishes standard atomic weights for normal materials where appropriate; for many radioactive elements it publishes no standard atomic weight. In those cases a periodic-table mass entry generally represents a selected nuclide or mass number and must not be described as a standard atomic weight.

CIAAW's current table is the 2024 table, incorporating revisions for Gd, Lu, and Zr. It explicitly lists intervals for elements whose natural isotopic variation warrants interval notation. Source: https://ciaaw.org/atomic-weights.htm

## Row-level availability
The audit overlay records the 84 elements for which CIAAW currently publishes a standard atomic weight:
- Z 1–42
- Z 44–60
- Z 62–83
- Z 90–92

CIAAW does not publish standard atomic weights for Tc (43), Pm (61), Po–Ac (84–89), and elements 93–118. These 34 rows require an isotope/nuclide-specific mass basis, not an invented standard atomic weight.

## Important intervals
The overlay marks the following 14 interval-style CIAAW entries for exact-value follow-up: H, Li, B, C, N, O, Mg, Si, S, Cl, Ar, Br, Tl, Pb. The exact interval endpoints and any uncertainty notation must be preserved from CIAAW; do not collapse an interval to a midpoint for the source record.

## Decision
- Keep the original PubChem mass column unchanged as source data.
- Do not overwrite it with rounded CIAAW values.
- Add a separate authoritative mass-reference overlay and preserve CIAAW intervals.
- For the 34 elements without CIAAW standard atomic weights, identify the exact isotope used by the PubChem periodic-table mass before calculating a final molar-volume property.
- For standard-weight elements, compare against CIAAW 2024 and record any rounding/source differences before deciding which mass definition the experiment uses.

## File
`ELEMENTS_118_CIAAW_MASS_BASIS_AUDIT_2026-11-22.csv`

No element triangles or angle coordinates were calculated.
