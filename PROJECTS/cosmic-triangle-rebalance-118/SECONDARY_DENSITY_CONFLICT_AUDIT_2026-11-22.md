# Secondary density source-conflict audit — 2026-11-22
Status: supplemental conflict log. No conflicting value has been silently selected or averaged.

## Findings
The source comparison shows that "secondary-source density" is not one coherent dataset. The PSE Info and ChemicalAid tables disagree for several elements, most severely among predicted superheavy densities. Examples include Hs: 28.6 vs 40.7 g/cm³, Sg: 23.2 vs 35 g/cm³, and Db: 21.6 vs 29.3 g/cm³. Fr (2.9 vs 1.87) and Es (13.5 vs 8.84) also differ substantially.

There are also smaller PubChem/secondary-source differences for At, Ra, U, and Np. These are retained as source-specific values, not averaged.

## Sources inspected
- PubChem density table: https://pubchem.ncbi.nlm.nih.gov/ptable/density/
- PSE Info density table: https://pse-info.de/en/scale/density
- ChemicalAid density chart: https://periodictable.chemicalaid.com/charts.php/density?lang=en
- A separate compilation of the ChemicalAid table is not treated as an independent primary authority. The values remain secondary until upstream provenance is verified.

## Interpretation rules
1. Parenthesized PSE values in the returned table are explicitly presented as estimates/predictions for the listed elements.
2. ChemicalAid gives numeric entries for the same superheavy elements, but a numeric entry alone does not establish experimental measurement.
3. Agreement between two secondary tables is not proof of independent measurement; the tables may share upstream sources.
4. Never average conflicting density values for this experiment.
5. Keep the original draft CSV unchanged. The conflict register is an overlay, not a replacement input file.
6. All conflicting or predicted values remain excluded from any provisional normalization range until provenance and status are independently established.

## Explicit conflicts recorded
See `SECONDARY_DENSITY_SOURCE_CONFLICTS_2026-11-22.csv` for 22 row-level comparisons including PubChem, PSE Info, and ChemicalAid where values were visible. Blank PubChem values are represented as NA, not zero.

## Consequence
The existing 118-row density column must not be used as one undifferentiated numerical population. At minimum, the next data stage must keep separate:
- PubChem-listed values with source-level condition caveats;
- secondary values with source-specific provenance;
- explicitly predicted values;
- unresolved source conflicts.

No triangle angles, side lengths, centers, or geometry were calculated in this audit.
