# 118-element lambda sensitivity sweep — exploratory only
Date: 2026-11-22

## Scope and method
Recomputed all 118 rows from the existing phase-rank inputs in the 118-element exploratory dataset. Rank_Density and Rank_MolarVolume were held fixed. Tested lambda = 0.25, 0.50, 1.00, 2.00 using:
- u = 2x - 1; v = 2y - 1
- wA = exp(lambda*u); wB = exp(lambda*v); wC = exp(-lambda*(u+v))
- angles = 180*w/sum(w)
- c = 1; a = sin(A)/sin(C); b = sin(B)/sin(C)
- vertices A=(0,0), B=(1,0), C=((b²+1-a²)/2, sqrt(b²-Cx²))
- incenter = side-length-weighted vertex average.

This compares incenter coordinates in the common base-normalized construction (c=1); it is not a physical-space position. The rank inputs remain within-phase percentiles and the liquid cohort remains n=2. Secondary and predicted rows retain their existing flags and are not promoted to measured values.

## Global sensitivity relative to lambda=0.50
- Mean per-element maximum absolute angle change across lambda alternatives: 51.673060 degrees.
- Mean per-element maximum incenter displacement: 0.253200590 base-length units.
- Largest angle sensitivity: Ti (Z=22), 71.551291 degrees.
- Largest incenter displacement: Rg (Z=111), 0.347943200.
- Smallest incenter displacement: Lu (Z=71), 0.073063070.

## Highest displacement cases
1. Rg (Z=111): max displacement 0.347943200, max angle delta 69.843357°
2. Sg (Z=106): max displacement 0.347394441, max angle delta 69.386358°
3. Ts (Z=117): max displacement 0.346660797, max angle delta 68.165100°
4. Ds (Z=110): max displacement 0.346491061, max angle delta 70.640039°
5. At (Z=85): max displacement 0.343531465, max angle delta 67.647964°
6. Db (Z=105): max displacement 0.342650002, max angle delta 67.299084°
7. Bh (Z=107): max displacement 0.342415647, max angle delta 70.130472°
8. Mt (Z=109): max displacement 0.341422228, max angle delta 70.738957°
9. Ra (Z=88): max displacement 0.341334742, max angle delta 70.028139°
10. Eu (Z=63): max displacement 0.340024378, max angle delta 66.652006°
11. Np (Z=93): max displacement 0.339344004, max angle delta 65.986486°
12. Hs (Z=108): max displacement 0.338734629, max angle delta 70.841791°

## Lowest displacement cases
1. Lu (Z=71): max displacement 0.073063070, max angle delta 22.340561°
2. In (Z=49): max displacement 0.075563115, max angle delta 20.788066°
3. Tm (Z=69): max displacement 0.084305860, max angle delta 21.127956°
4. Sn (Z=50): max displacement 0.100000626, max angle delta 20.281905°
5. Pb (Z=82): max displacement 0.108165169, max angle delta 29.255318°
6. Fl (Z=114): max displacement 0.111088456, max angle delta 29.318282°
7. Th (Z=90): max displacement 0.112275279, max angle delta 30.799059°
8. Cd (Z=48): max displacement 0.114037590, max angle delta 26.133271°
9. Ar (Z=18): max displacement 0.115002083, max angle delta 24.067184°
10. F (Z=9): max displacement 0.119075478, max angle delta 35.644144°
11. Rn (Z=86): max displacement 0.123401829, max angle delta 22.531567°
12. Er (Z=68): max displacement 0.124282185, max angle delta 24.514083°

## Interpretation limits
1. Lambda sensitivity measures response of this chosen exponential mapping, not empirical uncertainty in elemental properties.
2. The lambda=0.50 run is a comparison anchor only, not a selected optimum.
3. Since the rank coordinates are fixed, this sweep isolates lambda and does not test alternative normalization.
4. Cohort sizes and source-quality differences remain unchanged; liquid ranks are especially unstable at n=2.
5. No output here changes the frozen reference framework or any approved dataset.

## Files
- `ELEMENTS_118_LAMBDA_SENSITIVITY_SWEEP_2026-11-22.csv`: 472 rows (118 × 4 lambda values).
- `ELEMENTS_118_LAMBDA_SENSITIVITY_SUMMARY_2026-11-22.csv`: per-element displacement and angle sensitivity.
