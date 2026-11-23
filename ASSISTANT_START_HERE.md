# ASSISTANT START HERE — External Memory Protocol

**Repository:** `19REKo91/assistant-cloud-memory`  
**Working branch:** `work/triangle-geometry-role-map-v0.1`  
**Updated:** 2026-11-23  
**Purpose:** Make continuity depend on the repository, not on temporary chat memory.

## Important limitation

GitHub files are durable external memory, but they are not automatically injected into every new ChatGPT conversation. At the beginning of each session, the assistant must open this entry point and follow the procedures below. If repository access is unavailable, say so; do not pretend to remember the complete archive.

## Current development baseline — IMPORTANT

The user's explicit clarification on 2026-11-23: the current development line returned to **6.5.0** and proceeded from it to the present state. Treat 6.5.0 as the current line's starting baseline. Keep 6.5.1/6.5.2 as comparison handovers, not automatically adopted current baselines. The 6.2.1 Erratum priority applies only to the historical 6.0–6.2.1 data-audit lineage. Read `PROJECTS/triangle-framework/continuity/CURRENT_DEVELOPMENT_LINEAGE_6.5.0_ONWARD_2026-11-23.md` and `PROJECTS/triangle-framework/continuity/VISUAL_ASSET_REVIEW_2026-11-23.md` before interpreting version history or visual archives. Do not run engines or transfer later corrections into 6.5.0 without explicit authorization.

## Mandatory entry procedure — Triangle Framework

1. Read `PROJECTS/triangle-framework/continuity/START_HERE.md`.
2. Read `CURRENT_STATE_AND_DECISIONS.md`, `PROJECT_HISTORY_AND_CONCEPT_MAP.md`, and `OPEN_CONFLICTS_AND_EVIDENCE.md`.
3. Check `SOURCE_READING_REGISTER.csv`. A source is fully reviewed only if its status is `READ_FULL`.
4. For connected work, read `CONNECTED_PROJECTS_AND_VERSION_BOUNDARIES_2026-11-23.md` and `CONNECTED_PROJECTS_READING_REGISTER.csv`. Do not confuse a connected project with the framework itself.
5. Open original source files relevant to the current question. Summaries and handover notes are navigation aids, not substitutes when originals exist.
6. Check the latest commit and Git tree on the working branch. Do not assume the branch or files are unchanged.
7. Search the repository and available prior context before asking the user where a file is or asking them to repeat information.
8. If a needed source is absent, say exactly what was searched and what is missing. Never fill gaps by guessing or rebuilding a lost table from an older CSV.
9. Update the appropriate reading register and continuity records after actual reading or work.

## User's terminology for discoveries inside the framework

The user clarified on 2026-11-23 that statements such as **"we discovered"** refer to a discovery local to this framework and its internal work. They do not claim a globally new discovery or an externally established scientific fact. Use this local meaning naturally. Separate internal framework findings from external scientific claims.

## Repository status at this checkpoint

- Working tree: **790 entries** — 654 files and 136 directories; complete, not truncated.
- `PROJECTS/triangle-framework/`: **108 files**.
- Core reading register: **108 READ_FULL**, 0 READ_PARTIAL, 0 NOT_YET_READ.
- Connected-project register: **182 files** — 173 READ_FULL and 9 READ_PARTIAL. The remaining partial items are the rendered page images 2–10 of the archived atlas; all nine appear in the reviewed contact sheet but have not yet been opened individually at full resolution.
- `MANIFEST.work-branch.json` is the current branch snapshot. It excludes itself to avoid a self-hash cycle; its current snapshot must be regenerated after the latest review commits; the current branch tree has 790 entries. The framework contains 108 files.
- The continuity checks passed:
  - Core framework: run `45160135295` — 108/108 files, all READ_FULL, fingerprints match.
  - Connected projects: the expanded 182-file check is pending a new run after the register update.
- All work remains on this working branch. No merge into `main` has been performed.

## Automated continuity gates

- `.github/workflows/check-triangle-continuity.yml` runs manually and automatically when `PROJECTS/triangle-framework/**` changes. It verifies complete registration and Git blob fingerprints.
- `.github/workflows/check-connected-projects.yml` runs manually and automatically when any registered connected project changes. It verifies path coverage, file sizes, and Git blob fingerprints.
- These gates verify inventory and source integrity, not semantic understanding or scientific validity. The 2 partial sources remain explicitly marked partial.

## Non-negotiable project safeguards

- Never overwrite historical or approved source files merely to make versions consistent.
- Keep each version, engine, dataset, and experiment separate.
- Preserve conflicts; record both sides, source paths, and version dates.
- Separate user decisions, source values, derived values, local discoveries, hypotheses, test results, and assistant analysis.
- Do not run scientific calculations, Prism engines, or experimental models as a side effect of reading or organizing. Dedicated inventory/continuity checks are allowed.
- Do not say a GitHub Action passed unless its actual run log confirms it.
- Keep all changes on the working branch unless the user explicitly authorizes a merge.

## 60-degree experiment continuity

The user wants each element's cycle count `n` retained as an independent value, not discarded or collapsed after correction, for later study (including possible relationships to gas/liquid behavior). When a raw angle is negative, the correction direction must be studied in relation to that sign and position. Do not assume the minimum-|n| policy used in one experiment is the general rule. Keep every 60-degree experiment separate from historical 6.2.1 rescue, B/C-cycle variants, and 6.5.0 modulo rules.

## Navigation

- [Triangle Framework continuity entry](PROJECTS/triangle-framework/continuity/START_HERE.md)
- [Current state and decisions](PROJECTS/triangle-framework/continuity/CURRENT_STATE_AND_DECISIONS.md)
- [Project history and concept map](PROJECTS/triangle-framework/continuity/PROJECT_HISTORY_AND_CONCEPT_MAP.md)
- [Core source reading register](PROJECTS/triangle-framework/continuity/SOURCE_READING_REGISTER.csv)
- [Connected projects and version boundaries](PROJECTS/triangle-framework/continuity/CONNECTED_PROJECTS_AND_VERSION_BOUNDARIES_2026-11-23.md)
- [Connected project reading register](PROJECTS/triangle-framework/continuity/CONNECTED_PROJECTS_READING_REGISTER.csv)
- [Unresolved conflicts and evidence](PROJECTS/triangle-framework/continuity/OPEN_CONFLICTS_AND_EVIDENCE.md)
- [Core continuity checker](PROJECTS/triangle-framework/continuity/check_continuity.py)
- [Connected project checker](PROJECTS/triangle-framework/continuity/check_connected_projects.py)
- [Current branch manifest](MANIFEST.work-branch.json)
