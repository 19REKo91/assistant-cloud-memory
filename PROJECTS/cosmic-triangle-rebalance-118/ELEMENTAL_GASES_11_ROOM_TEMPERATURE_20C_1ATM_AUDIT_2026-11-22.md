# Room-temperature gas harmonization — 11 elemental gases

**Scope:** all 11 elemental gases in the project, at 20 °C (293.15 K) and 101.325 kPa (1 atm).

## Method
- Source baseline: existing project density values at 0 °C and 101.325 kPa.
- Normalize to 20 °C at constant pressure using ideal-gas temperature scaling: rho20 = rho0 × 273.15 / 293.15.
- Atomic molar volume: Vm(atom basis) = atomic molar mass / rho20.
- Molecular-basis volume is atom-basis volume multiplied by atoms per molecule (2 for H2, N2, O2, F2, Cl2; 1 for monatomic noble gases).
- Direct 20 °C density values available from an external NTP table are retained as comparison only; they do not overwrite the consistently scaled project values.

## Completeness
- All 11/11 gases have a 20 °C value on a consistent calculation basis.
- Direct 20 °C table cross-check values were located for 7/11: H, He, N, O, F, Cl, Ar.
- No direct 20 °C table value was located in the checked source for Ne, Kr, Xe, Rn; these remain explicitly marked as ideal-gas-scaled estimates from their 0 °C source densities.

## Important limitations
- This is a standardized derived dataset, not 11 direct experimental measurements at 20 °C.
- Ideal-gas temperature scaling neglects gas-specific compressibility (Z-factor) differences. At 1 atm these are usually modest but can matter to the proposed subtle ranking.
- Radon source density is inherited from the project's prior 0 °C source table; no new direct 20 °C measurement is claimed.
- Historical 60° cycle counts are carried only as references and have not been recalculated.

## External cross-check sources
- Density table defines NTP as 20 °C and 1 atm and lists direct densities for several gases: https://www.densitiestable.com/gases
- Independent temperature/pressure table and gas density temperature dependence: https://rulesofthumb.info/materials/gas-density
- Elemental gases list confirms the 11 room-temperature elemental gases: https://www.periodictable.one/elements/gas?view=table

## Output
- ELEMENTAL_GASES_11_ROOM_TEMPERATURE_20C_1ATM_2026-11-22.csv
