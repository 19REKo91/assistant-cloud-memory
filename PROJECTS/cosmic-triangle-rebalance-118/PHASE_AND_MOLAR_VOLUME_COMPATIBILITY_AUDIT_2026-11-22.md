# Phase and molar-volume compatibility audit — 118 elements
Date: 2026-11-22
Status: supplemental audit; no geometry calculations authorized by this file.

## 1. What the current CSV establishes
The working CSV has 118 atomic-number rows and a density entry in every row. That is coverage, not proof of a homogeneous physical dataset. The file records phase labels, but it does not consistently carry per-row temperature, pressure, allotrope, uncertainty, or measured-versus-predicted provenance.

The PubChem density values are the primary-source entries where present. The IUPAC FAIR Chemistry Cookbook's PubChem periodic-table example explicitly describes the density data as measured at STP (0 °C and 1 atm), and lists the gas values in g/cm³. ISO 7504 defines gas density at specified state conditions and notes that reference temperature and pressure must be specified. Sources:
- https://iupac.github.io/WFChemCookbook/datasources/pubchem_ptable.html
- https://cdn.standards.iteh.ai/samples/24662/84b01f040e9741c593568fa46ab03902/ISO-7504-2001.pdf

## 2. Phase partition visible in the current file
The file's phase labels identify:
- Gas: H, He, N, O, F, Ne, Cl, Ar, Kr, Xe, Rn.
- Liquid: Br, Hg.
- Solid: the remaining elements, with some superheavy entries labelled "Expected to be Solid" and Og labelled "Expected to be Gas".

These are source labels, not a claim that every phase assignment or density is experimentally measured under a common condition.

## 3. Gas-density reference conditions
For the PubChem-derived gas entries, use 0 °C and 1 atm (101.325 kPa) as the dataset's stated STP basis, supported by the IUPAC PubChem data cookbook. This is not automatically transferable to secondary-source values or to all solid/liquid entries. The source CSV itself does not store those conditions row by row; the supplemental register therefore distinguishes inferred dataset-level conditions from conditions absent in the file.

## 4. Molar-volume definition — must not be ambiguous
If the intended quantity is elemental molar volume per mole of atoms, use:
V_atom = M_atomic / rho
with M_atomic in g mol⁻¹ and rho in g cm⁻³, yielding cm³ mol⁻¹ of atoms.

For diatomic gas molecules (H₂, N₂, O₂, F₂, Cl₂), the molecular molar volume per mole of molecules is twice the per-mole-of-atoms value at the same state. Noble gases are monatomic. Do not mix molecular-mole and atomic-mole conventions in one column.

This definition resolves the apparent factor-of-two issue without arbitrarily doubling atomic masses: the numerator must match the stated mole basis.

## 5. Secondary-source and estimated-value limitations
The current CSV contains 22 non-PubChem density entries:
- PSE Info: Fr, Cf, Es, Rf–Og.
- ChemicalAid: Fm, Md, No, Lr.

The 15 entries Rf–Og are explicitly marked predicted/estimated in the CSV. Fr, Cf, and Es are secondary-source entries requiring provenance/status confirmation. The four ChemicalAid entries require upstream-source confirmation. A secondary-source number is not upgraded to measured merely because it is numeric.

A general independent data reference also warns that some elemental densities are theoretical estimates where experimental data are unavailable, including several radioactive and superheavy elements: https://mendeleev.readthedocs.io/en/latest/data.html

## 6. Current decision for the experiment
- Do not calculate a single 118-element min/max range from the unfiltered density column.
- Do not treat gas, liquid, solid, and predicted values as one equivalent measurement population.
- Keep all 118 rows in the archive; use explicit eligibility flags rather than deleting difficult elements.
- Treat the 11 PubChem gas rows as having a documented STP basis at dataset level, while retaining the distinction between atomic-mole and molecular-mole volume.
- Keep solid/liquid entries on hold for condition/allotrope review where the CSV lacks per-row conditions.
- Keep all 22 secondary-source densities on hold until source provenance and measurement status are confirmed.
- Keep predicted/estimated values separate from measured values in every later normalization and plot.

## 7. Files created by this audit
- `ELEMENTS_118_PHASE_COMPATIBILITY_REGISTER_2026-11-22.csv`: row-by-row overlay; original input file remains unchanged.
- This memo: rationale, source references, and eligibility policy.

No angles, triangle dimensions, centers, or element geometry were calculated. No reference-version files were changed.
