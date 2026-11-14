# 6.5.0 — 118-element input dataset audit

## Files
- `elements_input_118.csv`: 118 rows, one per element, prepared for the 6.5.0 input stage.
- This is an input-data assembly only. No 6.5.0 angle, dose, side, or coordinate calculation has been run here.

## Field sources and handling
- `R`: single-bond covalent radii from Pyykkö & Atsumi (2009), as indexed in OEIS A319914. Values are in pm and replace all previously supplied R values.
- `M`, `rho`, `mp_C`: Bluegrams periodic-table-data `ElementData.csv` as the base dataset where user-supplied values were not present.
- For the 28 user-supplied rows, `M`, `rho`, and `mp_C` were retained as supplied. Only `R` was replaced by the approved Pyykkö-Atsumi series.
- Melting points from the base dataset are converted from K to °C by subtracting 273.15.
- Gas-element densities are not copied from the gas-phase density column. Kr and Xe use solid densities at the triple point: 2.826 and 3.540 g/cm³ respectively. Rn solid density remains NOT_FOUND.
- Hs melting point uses the 126 K estimate listed by PeriodicTable.one, converted to -147.15 °C.
- Fl melting point uses the 2022 theoretical study estimate 284 ± 50 K; nominal 284 K is converted to 10.85 °C.
- The six missing melting points Db, Sg, Bh, Mt, Ds, and Rg remain NOT_FOUND. No unsupported values were inserted.

## Status after source fallback
- Rows: 118
- M missing: 0
- R missing: 0
- Solid density missing: 1 (Rn)
- Melting point missing: 6 (Db, Sg, Bh, Mt, Ds, Rg)
- Data_Quality: MEASURED 102, PREDICTED 15, NO_DATA 1
- GAS class: H, He, N, O, F, Ne, Cl, Ar, Kr, Xe, Rn, Og
- Ln and An family tags are independent of Data_Quality.

## Source links
- Pyykkö & Atsumi (2009): https://doi.org/10.1002/chem.200800987
- OEIS A319914 (118 single-bond covalent radii): https://oeis.org/A319914
- Base element data: https://github.com/Bluegrams/periodic-table-data/blob/master/Periodica.Data/Data/ElementData.csv
- Solid noble-gas densities: https://en.wikipedia.org/wiki/Noble_gas_(data_page) (solid at triple point; underlying cited reference is Hwang, Lein & Morgan, 2005, DOI 10.1002/0471238961.0701190508230114.a01)
- Hs estimate: https://www.periodictable.one/property/melting-point
- Fl theoretical melting-point study: https://pubmed.ncbi.nlm.nih.gov/35963734/

## Important limitations
- `MEASURED` here describes rows assembled from non-predicted input sources; it does not mean every property is a direct experimental measurement.
- Superheavy-element mass, density, and other properties may be model-based estimates. The CSV labels Z=104–118 as PREDICTED and records notes/source provenance.
- The user's original 6.5.0 calibration constants are unchanged. This file does not alter the 6.5.0 engine or calculate any outputs.
