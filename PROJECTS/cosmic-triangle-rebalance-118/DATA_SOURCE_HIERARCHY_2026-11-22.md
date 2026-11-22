# Data source policy — Cosmic Triangle Rebalance 118
Date: 2026-11-22
Status: source hierarchy for the independent experiment; no values calculated or promoted.

## Primary source
Use PubChem Periodic Table as the first source for both fields:
- Atomic mass: https://pubchem.ncbi.nlm.nih.gov/ptable/atomic-mass/
- Density: https://pubchem.ncbi.nlm.nih.gov/ptable/density/

Keep the source URL, retrieval date, units, and displayed value for every element/property. PubChem density table is in g/cm^3. Its currently visible table has values for many elements but blank entries for Fr and the lanthanide/actinide/superheavy tail beginning at Cf, plus some other gaps; do not fill blanks with zero.

## Secondary sources for PubChem gaps
- Atomic mass / longest-lived isotope mass numbers and evaluated atomic-property cross-check: NIST Periodic Table / NIST SP 966:
  https://www.nist.gov/pml/periodic-table-elements
  https://www.nist.gov/document/nistperiodictablejuly2018nocroppdf
- Missing density only: use a second source with an explicit per-element value and stated physical phase/conditions. Candidate consolidated source: AIDb Periodic Table dataset, whose stated upstream sources are PubChem (NIH/NCBI) and Wikidata:
  https://aidb.si/d/periodic-table
  Its description says gas densities are in g/cm^3 at 0 °C. Treat it as a secondary source, not a primary authority. For any missing solid/superheavy density, record whether it is measured or predicted and the upstream reference if shown.
- Where a secondary source still has no value, retain NA. Do not estimate or infer.

## Critical comparability rules
1. Never combine gas density and solid/liquid density as if measured under identical conditions.
2. Record phase, temperature, pressure, and units wherever the source provides them. PubChem's density page expresses density in g/cm^3 but the page text alone does not specify a common temperature/pressure for every row.
3. Mark predicted/theoretical values separately from measured values; especially superheavy elements.
4. Preserve conflicts between PubChem and secondary sources in separate columns. Do not silently overwrite the primary value.
5. The source hierarchy applies only to this new experiment and does not alter the frozen reference model or old datasets.
6. Do not compute molar volume or triangle geometry until the source audit has identified the usable, comparable density records.

## Output schema to build
Z, symbol, element, atomic_mass_u, mass_source_url, mass_source_note, density_g_cm3, density_source_url, phase, temperature, pressure, measurement_status, source_conflict, audit_status.

## Current observation
The previously audited candidate file in this project contains 118 rows but includes user-supplied values without field-level citations, and its density column has at least one missing record (Rn). It is therefore only a candidate snapshot, not an approved input table.
