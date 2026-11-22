# Mass and density source-audited draft — 118 elements
Date: 2026-11-22
Status: draft input table; not yet approved for geometry calculations.

## Retrieval
Primary machine-readable source: PubChem PUG-REST Periodic Table CSV
https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV
The dataset contains atomic number, symbol, name, atomic weight, standard state and density.

Secondary density source used only where PubChem density was blank:
- PSE Info density table: https://pse-info.de/en/scale/density
- ChemicalAid density chart: https://periodictable.chemicalaid.com/charts.php/density?lang=en

## Verified coverage
- 118 rows and 118 unique atomic numbers (Z=1..118).
- Atomic mass: 118/118 present in PubChem extract.
- Density: 118/118 populated in the draft.
- Density values sourced from PubChem: 96.
- Density values sourced from secondary tables: 22.
- Predicted/estimated status: 15 rows marked predicted/estimated in this draft.
- Four ChemicalAid secondary values (Fm, Md, No, Lr) explicitly flagged for provenance review.

## Important limitations
1. The 22 secondary values are not all equally reliable. Some are theoretical estimates, especially superheavy elements. Their source and status are retained; do not treat them as measured.
2. PubChem's source CSV does not itself provide a uniform temperature/pressure condition for every density. PSE Info includes some per-value temperatures and phases; where absent, conditions remain unspecified.
3. PubChem mass values for radioactive/synthetic elements are representative isotope masses, not standard atomic weights in the CIAAW sense. Do not interpret them as naturally occurring standard atomic weights.
4. The data table is a traceable working draft, not a homogeneous thermodynamic dataset. Gas, liquid, solid, and predicted densities must be handled as distinct categories in the experiment.
5. The source CSV is not a license to calculate all molar volumes indiscriminately. A later audit must define the comparable population and flag exceptions.
6. No old triangle angles, side lengths, centers, or normalization boundaries were used.

## Unified image deliverable
The target deliverable remains one combined image containing all 118 element-specific triangles and their in-triangle points, with clear visual status for measured, estimated, missing, and exceptional data. The image is intentionally deferred until the new rebalance transformation and valid geometric construction rules are specified and tested. No triangle calculations were performed in this data-ingestion step.

## GitHub paths
- `ELEMENTS_118_MASS_DENSITY_SOURCE_AUDITED_DRAFT_2026-11-22.csv`
- `DATA_SOURCE_HIERARCHY_2026-11-22.md`
