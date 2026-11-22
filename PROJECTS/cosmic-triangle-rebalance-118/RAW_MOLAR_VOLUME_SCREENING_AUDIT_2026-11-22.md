# Raw elemental molar-volume screening — not for normalization
Date: 2026-11-22

## Purpose
This file computes the arithmetic ratio M/rho for all 118 rows using the current draft inputs. It is an audit/diagnostic derivative only. It is NOT a harmonized physical dataset and must not be used to establish global minima/maxima, normalization bounds, or final triangle coordinates.

## Definition
For an elemental mass M in u (numerically equivalent to g/mol for ordinary chemical calculations at the precision used here) and density rho in g/cm³:
V_atom = M/rho
reported as cm³ per mole of atoms.

For the elemental diatomic gases H₂, N₂, O₂, F₂, and Cl₂, the molecular molar volume is twice V_atom. Br₂ is also diatomic in its ordinary liquid elemental form; its molecular volume would likewise be 2× the per-mole-of-atoms value, but it is a liquid and is not placed in the gas cohort. The CSV includes a molecular volume column only for the five diatomic gases; Br₂ molecular volume should be interpreted as 2× its V_atom if that separate basis is needed.

## Restrictions
- The 118 raw ratios inherit every source, phase, allotrope, temperature, pressure, and estimation limitation of their input rows.
- The secondary-source rows are flagged as held.
- The explicitly predicted/estimated rows remain flagged and are not treated as measurements.
- Even PubChem-listed values remain on hold for common-condition comparison where the row-specific state conditions or allotrope are not recorded.
- No values have been averaged, imputed, rescaled, or silently substituted.
- This file does not authorize use of the ratio as a third independent physical input: it is mathematically derived from M and rho.

## File
`ELEMENTS_118_RAW_MOLAR_VOLUME_SCREENING_NOT_FOR_NORMALIZATION_2026-11-22.csv`
