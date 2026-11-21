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
