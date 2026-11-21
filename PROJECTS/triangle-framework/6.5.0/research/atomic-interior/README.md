# Atomic Interior Relationship Search — Phase 1

Research-only analysis for Cosmic Triangle Framework 6.5.0.

## Scope

- Recalculate the 6.5.0 closure angle from the approved five input properties.
- Download the official AME2020 atomic-mass table.
- Derive neutron/proton one- and two-particle separation energies from **measured mass-excess entries only**.
- Calculate nuclear composition indicators (N/Z, neutron excess fraction, binding energy per nucleon) and distances to conventional magic proton/neutron numbers.
- Summarize isotope-level values by element using medians, with isotope counts shown.
- Calculate Pearson, Spearman, and partial correlation after controlling for atomic number.
- Run an ordered atomic-number holdout: train on Z <= 60, test on Z > 60.

## Important limitations

1. This is an exploratory first phase focused on nuclear properties. It does not yet test NIST electronic spectra or sequential ionization energies.
2. An element has one framework angle but multiple nuclides. The element-level median is a transparent summary of the AME nuclides available for that element; it is **not** a claim that the median nuclide is naturally abundant or stable.
3. Estimated AME mass-excess entries marked with `#` are excluded from separation-energy calculations. Non-calculable `*` entries remain missing.
4. Derived separation energies are computed from mass-excess differences using the neutron and hydrogen-atom mass excess constants stated in `search.py`. They are not copied from the separate AME reaction tables.
5. A correlation, even if strong, is not proof of a physical law. Holdout errors and partial correlations must be considered.
6. The framework CSV and constitution are read-only inputs. No framework source file is modified.

## Run locally

```bash
python -m pip install -r PROJECTS/triangle-framework/6.5.0/research/atomic-interior/requirements.txt
python PROJECTS/triangle-framework/6.5.0/research/atomic-interior/search.py
python -m unittest discover -s PROJECTS/triangle-framework/6.5.0/research/atomic-interior -p 'test_*.py'
```

## Data source

AME2020 Atomic Mass Evaluation, official AMDC listing and files:
- https://amdc.impcas.ac.cn/web/masseval.html
- https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt

Primary AME2020 publications:
- Huang et al., *The 2020 atomic mass evaluation (I)*, Chinese Physics C 45, 030002 (2021), DOI: 10.1088/1674-1137/abddb0.
- Wang et al., *The 2020 atomic mass evaluation (II)*, Chinese Physics C 45, 030003 (2021), DOI: 10.1088/1674-1137/abddaf.

## Outputs

The GitHub Actions run uploads these files as an artifact named `atomic-interior-results`:
- `AME2020_mass_records.csv`
- `AME2020_nuclide_separation_energies.csv`
- `element_angle_nuclear_summary.csv`
- `nuclear_correlations.csv`
- `ordered_Z_holdout.csv`


The GitHub Actions workflow also starts on pushes affecting this research folder or the unchanged 6.5.0 input CSV; it remains manually runnable through `workflow_dispatch`.


## Phase 2 — isotope-aware nuclear and electronic properties

The workflow now also:

- Downloads NUBASE2020 and selects **ground-state stable nuclides only** (`stbl`); isomers and radioactive nuclides are not silently mixed into this subset.
- Uses NUBASE natural isotopic abundances to compute an abundance-weighted nuclear-property mean for each element, and reports the most abundant stable isotope separately.
- Leaves elements without stable nuclides or without a reported natural abundance missing.
- Queries NIST ASD 5.12 for sequential ionization energies across elements, plus neutral ground-state shell configurations. Total electronic binding is derived only when all Z sequential stages are present.
- Keeps NIST provenance classes separate: unmarked values (evaluated experimental data), square-bracketed values (semi-empirical/interpolated), and parenthesized values (ab-initio/theoretical).
- Tests IE1, IE2, IE3, their strict measured sum, neutral total binding energy, occupied principal-shell count, and outermost-shell electron occupancy against the 6.5.0 closure angle.
- Reports Pearson, Spearman, partial correlation after controlling for Z, and an ordered-Z holdout (train Z <= 60, test Z > 60) comparing Z-only, angle-only, and Z-plus-angle models.

### Added data-source references

- NUBASE2020 official table: https://www-nds.iaea.org/amdc/ame2020/nubase_4.mas20.txt
- NUBASE2020 publication: Kondev et al., Chinese Physics C 45, 030001 (2021), DOI: 10.1088/1674-1137/abddae.
- NIST ASD 5.12: https://www.nist.gov/pml/atomic-spectra-database (DOI: 10.18434/T4W30F).
- NIST GSIE definitions and provenance conventions: https://physics.nist.gov/PhysRefData/ASD/Html/iehelp.html

### Additional phase-2 outputs

- `NUBASE2020_stable_ground_states.csv`
- `stable_isotope_element_summary.csv`
- `element_angle_stable_isotope_summary.csv`
- `stable_isotope_weighted_correlations.csv`
- `stable_isotope_weighted_holdout.csv`
- `dominant_stable_isotope_holdout.csv`
- `dominant_stable_isotope_correlations.csv`
- `NIST_ASD_ionization_all_stages.csv`
- `NIST_ASD_fetch_errors.csv`
- `element_angle_electronic_summary.csv`
- `electronic_correlations.csv`
- `electronic_ordered_Z_holdout.csv`

NIST defines total binding energy as the sum of sequential ionization energies. This workflow derives it only when every charge stage is available, retaining three separate versions: measured-only, measured-plus-semi-empirical, and a clearly labelled mixed-provenance sum. None is treated as an independent measurement. The mixed sum can include theoretical stages and must not be interpreted as an all-experimental result. The new phase is exploratory. A correlation does not establish a causal or physical law; missing or theoretical data are not promoted to measured observations.
