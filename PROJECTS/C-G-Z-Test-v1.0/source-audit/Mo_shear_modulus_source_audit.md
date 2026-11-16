# Mo (Molybdenum) — Shear Modulus Source Audit

Date: 2026-11-16
Project: C-G-Z Test v1.0
Status: Source audit only; no C-G-Z calculation or statistical analysis performed.

## Question
The initial 60-value G dataset contains a conflict for molybdenum:
- ChemReference aggregation: 120 GPa
- WebElements: 20 GPa

## Evidence located

### 1. NASA, Solar Cell Array Design Handbook, Volume II (October 1976)
Table 7.5-8, "Elastic and Shear Moduli and Poisson's Ratio of Molybdenum":
- 25 °C: E = 320 GN/m², G = 120 GN/m², Poisson's ratio = 0.324
- 100 °C: G = 117 GN/m²
- 500 °C: G = 110 GN/m²

Source:
https://ntrs.nasa.gov/api/citations/19770007251/downloads/19770007251.pdf

### 2. NASA, Space Nuclear Propulsion Material Property Handbook
SNP-HDBK-0008, Revision 3.1, effective 2024-08-05; Mo section, shear modulus with temperature:
- At 293 K: minimum trend G = 117.80 GPa
- At 293 K: high trend G = 121.08 GPa
- At 300 K: minimum trend G = 117.68 GPa
- At 300 K: high trend G = 120.98 GPa

The handbook explains that the shear-modulus trends are calculated from Young's-modulus and Poisson-ratio trends; the minimum and high curves arise from the two Young's-modulus trends. The displayed trend data are for 100% theoretical density.

Source:
https://ntrs.nasa.gov/api/citations/20240004217/downloads/SNP-HDBK-0008_SNP-Material-Handbook.pdf

### 3. WebElements
WebElements lists molybdenum rigidity modulus as 20 GPa.

Source:
https://winter.group.shef.ac.uk/webelements/molybdenum/physics.html

WebElements identifies its broad literature basis as:
- A.M. James and M.P. Lord, Macmillan's Chemical and Physical Data (1992)
- G.W.C. Kaye and T.H. Laby, Tables of Physical and Chemical Constants, 15th ed. (1993)
- G.V. Samsonov (Ed.), Handbook of the Physicochemical Properties of the Elements (1968)
- D.R. Lide (Ed.), CRC Handbook of Chemistry and Physics, 79th ed. (1998), for lanthanides
- H. Ellis (Ed.), Nuffield Advanced Science Book of Data (1972)

WebElements does not identify the specific underlying reference for its Mo value on the element page.

## Assessment
The value 120 GPa is supported by the NASA 1976 handbook at 25 °C and is consistent with the NASA 2024 handbook's room-temperature range (approximately 117.7–121.1 GPa, depending on the trend curve). The WebElements value of 20 GPa is inconsistent with both NASA sources and is likely a transcription or display error, possibly a dropped leading digit. That proposed explanation is not proven.

## Dataset handling recommendation
- Do not silently replace the existing CSV value.
- Keep the original source conflict recorded.
- For a future curated room-temperature reference value, 120 GPa has substantially stronger documentary support than 20 GPa.
- Record the NASA evidence and the condition caveat (NASA 2024 trend assumes 100% theoretical density).
- Do not treat 120 GPa as a fully condition-matched experimental datum without checking the underlying references and sample details.

## Scope boundary
This document records source evidence only. It does not alter the 118-element CSV, the C equation, calibration bounds, or any engine. No C-G-Z recalculation or statistical analysis was performed.
