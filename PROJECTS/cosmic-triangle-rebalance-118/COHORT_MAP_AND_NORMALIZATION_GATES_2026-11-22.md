# Cohort map and data-use gates — 118-element rebalance
Date: 2026-11-22
Status: exploratory policy; does not approve the density table or any geometry equation.

## 1. Reconciled source/phase counts
The row-by-row phase register was programmatically re-read from GitHub and contains 118 unique elements:

| Density source | Phase label | Rows | Use status |
|---|---:|---:|---|
| PubChem | Solid | 83 | Primary-source cohort; conditions/allotrope audit still required |
| PubChem | Liquid | 2 | Separate liquid cohort; do not pool with solids |
| PubChem | Gas | 11 | Separate gas cohort; PubChem density data reference STP 0 °C, 1 atm |
| PSE Info | Solid | 17 | Secondary-source cohort; preserve estimates and provenance caveats |
| PSE Info | Expected Gas | 1 | Og; predicted/expected phase and density, separate |
| ChemicalAid | Solid | 4 | Secondary-source cohort; upstream provenance review required |
| **Total** |  | **118** |  |

Note: PSE Info solid count includes Fr, Cf, Es, and Rf–Ts. Og is separately labelled Expected to be Gas. The 15 explicit predicted/estimated entries Rf–Og are not the only values that may be uncertain; At also has a source-level estimate conflict.

## 2. Data gates before normalization
1. Preserve the original density draft and its source values.
2. Keep density values with source-specific provenance; never average conflicting values.
3. Calculate an elemental molar volume only when the mole basis and phase/condition basis are stated.
4. Use (V_{m,atom}=M_{atomic}/\rho) for volume per mole of atoms. For a diatomic gas, the volume per mole of molecules is twice that value.
5. Keep primary solid, liquid, gas, and secondary/predicted cohorts separately identifiable.
6. A missing or uncertain value remains NA/flagged; do not fabricate a density to force a triangle.

## 3. Candidate normalization tracks (not selected)
- Track A — pooled log-value empirical ranks: useful for visual exploration across the full dataset, but phase differences and unequal condition bases can dominate the ranking. Not suitable as the final physical comparison until condition harmonization is justified.
- Track B — phase-specific empirical ranks: compares elements within solid, liquid, and gas cohorts. This avoids pretending that unlike phases were measured under identical conditions, but the resulting normalized coordinates are cohort-relative and cannot be interpreted as one common absolute scale.
- Track C — harmonized-condition physical values: convert documented source values to a declared reference condition where the required physical model and inputs are available; keep measured, calculated, and estimated values distinct. This is the preferred path if a defensible 118-element common scale can be assembled, but it requires more source-level work and may leave some entries unavailable.

No track is adopted in this file. Any eventual angle map must be a separate experimental specification and must guarantee positive angles summing to 180° without borrowing old model constants.

## 4. Geometric design constraint
A triangle's three interior angles have two independent degrees of freedom because their sum is fixed at 180°. The currently proposed physical inputs (M), ρ, and (V_m=M/ρ) contain only two independent quantities; (V_m) is derived, not a third independent measurement. Therefore the design must not claim three independent physical drivers. A two-coordinate transformation can define the triangle shape; any third weight must be explicitly described as a mathematical balancing term, not a third measured property.

## 5. What remains blocked
- No final common-condition density table yet.
- No agreed normalization track.
- No adopted angle transformation or sensitivity parameter.
- No adopted definition of the plotted in-triangle point.
- No triangle calculations or 118-element image have been produced.

This cohort map is an audit/control document only. It does not alter the frozen reference model.
