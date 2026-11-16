# C-G-Z Test v1.0 — DFT History Source Cross-Check
Date: 2026-11-16
Scope: Independent spot-check of selected user-archived ABINIT and CASTEP history groups against official DeltaCodesDFT supplementary material. No numerical data were changed and no C–G/B0 analysis was performed.

## 1. Authoritative project provenance

The DeltaCodesDFT README states that `history.tar.gz` contains input data for all investigated codes and experimental information:
- https://github.com/molmod/DeltaCodesDFT/blob/master/README.md
- Archive: https://github.com/molmod/DeltaCodesDFT/blob/master/history.tar.gz

The archive object previously inspected through GitHub API had size 53,192 bytes and SHA-256-like GitHub Git-blob SHA `d47e46bc99d7caab2c568a7a4d2611846a532318` (this is a Git object identifier, not a SHA-256 file checksum). Its contents have not yet been extracted in this audit.

DTU's Computational Materials Repository documents an independent verification path: obtain `dcdft.db`, extract calculator-specific subsets, generate formatted EOS parameter files, and compare them with the corresponding `history` sections using `diff -w`. The page gives AIMS tight as a worked example and documents calculator filters for AIMS, Quantum ESPRESSO, ABINIT, and GPAW:
- https://cmr.fysik.dtu.dk/dcdft/dcdft.html

The linked `dcdft.db` download was 15,879,168 bytes and exceeded the web retrieval tool's response limit; it has not been downloaded or queried in this audit.

## 2. Verified spot-checks against official supplementary PDFs

### A. ABINIT 7.10.2 / GPAW 0.9 PAW

User archive file:
- Path: `abinit-history.txt` (repository root)
- GitHub blob SHA: `4ebc2dc0645f41f726abf9593e21cef53dbb8427`
- Exact section header: `# Abinit version 7.10.2 with PAW GPAW 0.9 (ecut = 80 Ha) -- calculations by M. Dulak`
- Parsed section row count: 68
- First row: H = 17.4575, 10.3411, 2.6850

Official supplementary PDF:
- https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-Abinit-delta80.pdf
- Identifies ABINIT 7.10.2 with GPAW 0.9 PAW, plane-wave basis, PBE, and scalar-relativistic treatment.
- Its H result is 17.458, 10.341, 2.685, matching the archived row to the PDF's displayed precision.

**Metadata discrepancy requiring preservation:** the user-archived history header says `ecut = 80 Ha`, whereas the supplementary PDF states a plane-wave cutoff of 100 Ry. These are not equivalent (80 Ha = 160 Ry). The row-value spot-check matches after rounding, but the cutoff metadata do not. Do not silently harmonize or relabel this section.

### B. CASTEP 8.0 / legacy Vanderbilt USPP

User archive file:
- Path: `PROJECTS/C-G-Z-Test-v1.0/data/CASTEP/08_Ultrasoft_Vanderbilt.txt`
- GitHub blob SHA: `c7dd7ff350e333193489f8ffe9b544055356f983`
- Exact header: `# CASTEP with ultrasoft Vanderbilt pseudopotentials -- calculations by Chris Pickard and Keith Refson`
- Parsed row count: 62
- Selected raw rows include H = 17.56268, 10.44672, 2.825; Li = 20.37775, 13.60675, 3.298; Hf = 22.89617, 118.60717, 3.805.

Official supplementary PDF:
- https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-CASTEP-USP.pdf
- Identifies CASTEP 8.0, legacy Vanderbilt-type Materials Studio ultrasoft pseudopotentials, PBE, 700 eV cutoff.
- Its displayed H, Li, and Hf values match the user archive values to the PDF's three-decimal precision.

### C. CASTEP 9.0 / OTFG C9

User archive file:
- Path: `PROJECTS/C-G-Z-Test-v1.0/data/CASTEP/04_OTFG_9.0.txt`
- GitHub blob SHA: `92c6bf7beb04a27fc24938c618fe83ed3890d20e`
- Exact header: `# CASTEP with set of OTFG pseudopotentials of version 9.0 -- calculations by Keith Refson`
- Parsed row count: 71
- Selected raw rows include H = 17.40975, 10.29544, 2.710; Li = 20.24660, 13.77091, 3.338; Hf = 22.49516, 107.48332, 3.551.

Official supplementary PDF:
- https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-CASTEP9.pdf
- Identifies CASTEP 9.0, C9 on-the-fly Vanderbilt-type USPP, PBE, and 816 eV cutoff.
- Its displayed H and Li values match the user archive values to the PDF's three-decimal precision.

## 3. What this establishes — and what it does not

Established:
- The three checked user-archived sections correspond numerically, at the tested rows and displayed precision, to official DeltaCodesDFT supplementary results.
- The CASTEP Vanderbilt and OTFG9 sections have matching published configuration descriptions.
- The ABINIT GPAW section has matching displayed H result but a cutoff-energy metadata conflict (80 Ha in history header versus 100 Ry in the PDF).

Not established:
- A byte-for-byte identity between any user file and the original `history.tar.gz`.
- A full row-by-row comparison of these sections against the complete original archive.
- Verification of the remaining ABINIT/CASTEP groups or the other program files.
- That every program file supplied in conversation is a complete, unmodified original archive member.

## 4. Current audit status

- ABINIT file: all 13 section headers and the full 5.4.4p tail were previously inventoried; one section (7.10.2 GPAW 0.9) now has a published-PDF spot-check, with the cutoff discrepancy flagged.
- CASTEP: eight sections are inventoried in the user's repository; two sections (legacy Vanderbilt and OTFG9) now have published-PDF spot-checks.
- Original archive extraction and comprehensive matching remain pending.
- The 17-file user list remains an inventory from the conversation; it is not yet a verified list of 17 exact archive members.
- The 58/58 count from the earlier provisional grouping remains unfinalized and must not be treated as a verified count.

## 5. Source links

1. DeltaCodesDFT README and archive: https://github.com/molmod/DeltaCodesDFT
2. DTU CMR independent extraction and comparison instructions: https://cmr.fysik.dtu.dk/dcdft/dcdft.html
3. ABINIT/GPAW 0.9 supplementary PDF: https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-Abinit-delta80.pdf
4. CASTEP legacy Vanderbilt supplementary PDF: https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-CASTEP-USP.pdf
5. CASTEP OTFG9 supplementary PDF: https://molmod.ugent.be/sites/default/files/deltadftcodes/supplmat/SupplMat-CASTEP9.pdf
