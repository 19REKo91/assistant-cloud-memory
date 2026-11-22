# 118-element row harmonization — atomic molar-volume basis

**Status:** Separate experimental harmonization output. No frozen reference or previous source file was modified.

## Join and coverage
- Raw volume rows: 118
- Phase register rows: 118
- Previous B/C cycle rows: 118
- Joined output rows: 118
- Unique atomic numbers: 118
- Phase counts: Gas=11, Solid=96, Liquid=2, Expected to be a Solid=8, Expected to be a Gas=1

## Unified basis
- Canonical comparison basis: cm³ per mole of atoms for every element.
- Retain source Raw_Volume_cm3_per_mol_atoms unchanged.
- For elemental diatomic molecules (H2, N2, O2, F2, Cl2, Br2), convert molecular molar volume to per-mole-atoms by dividing by 2.
- For monatomic gases, no molecule-to-atom divisor is applied.
- For solids/liquids, retain the source atomic molar-volume calculation M_atomic/density.
- Both raw atomic-basis and converted molecular-basis cross-checks are retained; neither overwrites the other.

## Important limitation
This harmonizes amount basis, not thermodynamic state. Gas values are listed at 0 °C and 101.325 kPa in the phase register, while many condensed-phase rows do not carry row-specific temperature/pressure conditions. Those condition gaps remain explicit and must be resolved before interpreting all 118 volumes as a same-condition physical comparison.

## Cycle data handling
Previous raw/final angles and n are carried forward as historical columns only. They have not been recalculated from the harmonized table. This prevents a false claim that the old cycle counts are already corrected.

## Files
- ELEMENTS_118_UNIFIED_ATOMIC_MOLAR_VOLUME_BASIS_2026-11-22.csv
- ELEMENTS_118_UNIFIED_ATOMIC_MOLAR_VOLUME_BASIS_AUDIT_2026-11-22.md
