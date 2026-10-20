# Data audit — "Le sport pour tous ?" (licences & clubs, France 2023)

Phase 1 output. Every number below is printed by `python -m src.audit` (reads `data/raw/` only, ~4 s).
Raw files were downloaded on 2026-10-20 and are not committed (`data/raw/` is gitignored).

## 1. Sources

| # | File in `data/raw/` | Origin | Licence | SHA-256 (first 12) |
|---|---|---|---|---|
| S1 | `lic-data-2023.csv` (256 MB) | data.gouv.fr dataset `53699ebba3a729239d205f58`, resource uploaded 2025-12-29 | Licence Ouverte | `ea75f2c22cc1` |
| S2 | `clubs-data-2023.csv` (16 MB) | same dataset | Licence Ouverte | `9972eb7ade24` |
| S3 | `liste-federations.xlsx`, `licences-dictionnaire-des-variables.xlsx`, `clubs-dictionnaire-des-variables.xlsx` | same dataset | Licence Ouverte | `3aa27b6b7120`, `2e03932526f5`, `5d2c93bfb903` |
| R1 | `geoapi_communes.json` | `https://geo.api.gouv.fr/communes?fields=code,nom,population,codeDepartement,codeRegion&format=json` | Licence Ouverte | `0d053d0f2916` |
| R1b | `geoapi_arrondissements.json` | same API, `type=arrondissement-municipal` (Paris / Lyon / Marseille districts) | Licence Ouverte | — |
| R1c | `DS_POPULATIONS_REFERENCE_2023_data.csv` | INSEE, populations de référence 2023 (supplied by the student) | Licence Ouverte | `a905cebb258a` |
| R2 | `departements-version-simplifiee.geojson` | github.com/gregoiredavid/france-geojson (IGN Admin Express 2018, simplified) | Licence Ouverte (IGN Admin Express) | `c08a1ad48299` |
| R3 | `communes_contours/{dep}.geojson` | `https://geo.api.gouv.fr/departements/{code}/communes?format=geojson&geometry=contour` | Licence Ouverte | 100 files |
| R4 | `geoapi_departements.json`, `geoapi_regions.json` | geo.api.gouv.fr (names, region codes) | Licence Ouverte | — |
| G1 | `v_mvt_commune_2026.csv` | INSEE COG 2026, commune events since 1943 | Licence Ouverte | — |
| V1 | `injep_2023/` (licences, clubs, federation families) | injep.fr, 2023 census results, data at 11/07/2024 | Licence Ouverte | — |
| V2 | `injep_2024/` (history 2002–2024) | injep.fr, 2024 census results (July 2025) with **revised 2023 figures** | Licence Ouverte | — |

Producer: INJEP-MEDES (census of licences and clubs of approved federations); geocoding, zoning and commune-code
correction by INSEE. The local S1/S2 files match the published resource sizes byte for byte.

## 2. S1 — licences 2023

- 1,014,746 rows × 46 columns; one row = commune × QPV zone × federation. 117 federations.
- Columns: 9 identifiers + 18 female + 18 male age-band columns (`F - 1 à 4 ans` … `F - 80 à 99 ans`, `F - NR`) + `Total`.
- **Total licences: 16,535,056.**
- **Sex is always reported.** `Total = ΣF + ΣH` on every row. There is no sex-NR column: the `NR` in `F - NR` / `H - NR`
  means **age** not reported. Female licences: 6,390,363, i.e. **38.65 %** of F + H.
- Age not reported: 1,857 licences (0.01 %). No negative values.
- `Statut géo`:

  | Status | Licences | Share |
  |---|---|---|
  | 1.Champ geoc (mainland + DROM excl. Mayotte) | 16,329,138 | 98.75 % |
  | 2.Hors Champ geoc (abroad 83,993; Mayotte 42,235; COM) | 205,630 | 1.24 % |
  | 3.NR (not allocated) | 288 | 0.00 % |

  National totals compared with published figures must use all 16,535,056; maps use the geocoded 16,329,138.
- **Federations given at département level only** (`n.r.` in the federation list): 406 Défense, 409 Maccabi, 411 Police.
  Their 160,151 geocoded licences have `Code Commune = "NR - Non réparti"` and `Code QPV = "NR - Non réparti"`.
  They count in département totals but cannot appear in commune views or the QPV split.
- **School federations located at the club, not the home** (`Adr. Club` in the federation list): 604 UNSS (1,160,829)
  and 605 USEP (767,689), **11.66 % of all licences**. For these two, "home commune" is really the school's commune.
  → **Decision needed (see §8).**
- Top federations: Football 2,215,848; UNSS 1,160,829; UGSEL 1,133,522; Tennis 1,106,989; USEP 767,689.
  106 of 117 federations have ≥ 1,000 licences (threshold proposed for Q3).
- **Disability federations** (checked by name): **501 FF Handisport (30,089)** and **503 FF du Sport Adapté (47,510)**,
  together 77,599 licences (0.47 %).

### QPV codes (geocoded licences)

| `Code QPV` | Meaning (dictionary) | Licences | Share |
|---|---|---|---|
| `CSZ` | commune with no QPV | 10,615,808 | 65.01 % |
| `HZ` | commune with QPV, holder lives outside it | 4,774,571 | 29.24 % |
| `QN…` | holder lives in this QPV (**2024 QPV list**, 1,476 distinct) | 778,608 | 4.77 % |
| `NR - Non réparti` | not allocated (the département-only federations) | 160,151 | 0.98 % |

Only 2024 identifiers (`QN`) appear, so one QPV list version applies throughout the file. The QPV share should be computed
over allocated licences (CSZ + HZ + QN), excluding `NR`.

## 3. S2 — clubs 2023

- 121,700 rows, 120 federations, same identifier columns as S1.
- Totals: Clubs 154,716 + EPA 10,233 = Total 164,949; active (≥ 1 annual licence): Clubs 146,837 + EPA 9,278 = **156,115**.
- Checks: `Total = Clubs + EPA` on every row; `Total_actifs ≤ Total` on every row.
- Definitions (dictionary): **club** = non-profit association (loi 1901) affiliated to a federation; **EPA**
  (établissement professionnel agréé) = private / commercial structure approved by a federation.
- `Statut géo` (active structures): geocoded 98.07 %, out of scope 1.03 %, not allocated 0.90 %.
- Active structures located in a QPV: **6,816 (4.45 % of geocoded)**.
- Clubs are located at the **club's** commune (not comparable one-to-one with residents' licences).

## 4. R1 — population

- geo.api returns 34,969 communes on **COG 2026** (backend `@etalab/decoupage-administratif` 6.0.0), including COM
  and Mayotte, plus 45 PLM districts with `type=arrondissement-municipal` (pop. 3,508,945).
- **Millésime: legal population 2023** (published by INSEE end of 2025, in force on 1 January 2026). Proof: geo.api
  `population` equals INSEE `PMUN` 2023 (file R1c) for **34,858 / 34,858** INSEE communes. Population measure =
  *population municipale* (PMUN, no double counting).
- Same scope as geocoded licences (100 départements = mainland + 971–974, no Mayotte): **68,094,280** inhabitants,
  exactly the INSEE "France excluding Mayotte" PMUN 2023 total. Population and licences refer to the same year.
- 6 uninhabited territories have no population (TAAF, Clipperton). They are outside the scope.

## 5. Commune join (geocoded licences → R1)

| Step | Communes matched | Licences matched |
|---|---|---|
| Raw codes vs geo.api communes | 34,731 / 34,844 (99.68 %) | 96.10 % |
| + PLM districts (licences use `75101…`, `69381…`, `13201…`) | 34,776 / 34,844 | **99.91 %** |
| Remaining unmatched | 68 communes | 15,061 licences (0.09 %) |

The 68 remaining codes are communes that merged between COG 2024 (the file's geography) and COG 2026, e.g.
Orée d'Anjou 49069 (5,056 licences), Pierrefitte-sur-Seine 93059 (2,892, merged into Saint-Denis in 2025),
Porte des Pierres Dorées 69159 (1,086).
→ Phase 2: `src/geo.py` maps PLM districts to their city and old → current codes with the INSEE events file (G1):
**join rate 100 %** for licences and clubs (see §10).
(`src/geo.py` and `src/sources/licences.py` named in CLAUDE.md did not exist in this folder; they were written from
scratch in Phase 2.)

Département codes: 100 in geocoded licences (`01`–`95` with `2A`/`2B`, `971`–`974`), all strings.

## 6. R2 / R3 — geometry

- R2: 96 features (mainland incl. `2A`/`2B`), properties `code`, `nom`. **DROM 971–974 are missing**, so a mainland
  map leaves out 4 of 100 départements. Options in Phase 2: show DROM as small inset maps / a side table, or use the
  same repo's `departements-avec-outre-mer.geojson` (DROM moved next to the mainland; 3.7 MB, not simplified).
- R3: département 01 = 391 commune polygons, 2.6 MB raw → it needs simplification (coordinate rounding) in Phase 2.

## 7. Feasibility Q1–Q6

| Q | Feasible? | Data | Caveats |
|---|---|---|---|
| Q1 Territories | **Yes** | S1 geocoded + R1 (same year) | UNSS/USEP club-address licences (§8); PLM districts; merged communes; commune views need population ≥ 2,000; DROM shapes |
| Q2 QPV | **Yes** | S1 `Code QPV` (QN), S2 `Code QPV` | Shares only; exclude `NR` from the denominator; QPV list 2024 |
| Q3 Gender | **Yes** | S1 F/H columns | No sex NR; ≥ 1,000 licences → 106 federations; football 2.2 M licences |
| Q4 Seniors | **Yes** | S1 bands 60-64 … 80-99 | Age NR 0.01 %, excluded from denominator |
| Q5 Disability | **Yes** | S1 codes 501 + 503 | 77,599 licences = lower bound; counts and per 10,000 inhabitants only |
| Q6 Age pyramid | **Yes** | S1 sex × 17 age bands | Bands are 5 years, except 1–4 and 80–99 |

## 8. Scope decisions (taken by the student after Phase 1)

| Topic | Decision | Implemented as |
|---|---|---|
| School sport UNSS 604 / USEP 605 (located at the school) | Excluded from **all geographic views** (maps, rates per 10,000, QPV shares, senior shares by département). Kept in the Hook national total, the women's-share ranking of federations and the age pyramid. | `federations.in_geo_views = False` (derived from the `Adr. Club` note) |
| Overseas départements 971–974 | Map = mainland France only; DROM in a small table under the map with the same indicators. | `population_dep.is_overseas` |
| Défense 406, Maccabi 409, Police 411 (département only) | Kept in département figures; excluded from commune and QPV views. | `federations.is_dept_only`; rows with no commune are dropped from `lic_com_fed`, and their QPV code `NR` is outside `qpv_allocated` |

## 9. Processed tables (Phase 2, `python -m src.build`)

| File in `data/processed/` | Grain | Content |
|---|---|---|
| `federations.parquet` (120 rows) | federation | name, INJEP group/family, flags (`is_disability`, `is_club_address`, `is_dept_only`, `in_geo_views`), national licences total/F/H, by geocoding status, clubs |
| `lic_dep_fed.parquet` (10,046) | département × federation | geocoded licences, F, H, 60+, known age, QPV residents, QPV-allocated |
| `lic_com_fed.parquet` (952,478) | current commune (COG 2026) × federation | licences, F, H (département-only federations excluded) |
| `pyramid.parquet` (4,212) | federation × sex × age band | all licences (national, all statuses) |
| `clubs_dep_fed.parquet` / `clubs_com_fed.parquet` | département / commune × federation | active clubs, EPA, total; located in QPV |
| `population_dep.parquet` (100) / `population_com.parquet` (34,858) | département / commune | legal population 2023, names, region, `is_overseas` |
| `geo/departements_metro.geojson` | 96 mainland départements | as downloaded (570 KB) |
| `geo/communes/{dep}.geojson` (100 files, 37 MB) | commune | Douglas-Peucker 0.0005° + 4 decimals (e.g. dép. 01: 2.6 MB → 411 KB) |
| `validation.parquet`, `build_report.json` | — | Phase 3 results and build facts, for the Data page |

## 10. Validation (Phase 3, `python -m src.validate`, also run by `pytest`)

**26 / 26 checks pass.** Highlights:
- **Published figures:** total 16,535,056, women 6,390,363 and men 10,144,693 equal INJEP's **revised 2023 figures**
  (published July 2025) exactly, for all 120 federations. The first publication (July 2024) said 16,499,141. The
  +35,915 gap comes only from Aviron (102) and Voile (128), which INJEP revised upwards later. The same two
  federations explain the 1-structure gap in clubs (156,115 vs 156,114).
- **Départements vs INJEP:** median gap 0.24 %, max 1.55 % (Hautes-Alpes). INJEP re-allocates non-response to
  départements; we keep geocoded licences only.
- **Sums:** Σ départements = geocoded total (16,329,138); Σ communes = geocoded − département-only federations
  (16,168,987); pyramid = national total; licences = F + H on every row; QPV counts are consistent.
- **Joins:** commune join 100 % (licences and clubs), départements rebuilt from communes = file départements (100/100),
  96/96 mainland shapes, 34,858/34,858 commune shapes.
- **Population:** geo.api = INSEE PMUN 2023 for every commune and département; total 68,094,280 = INSEE France
  excluding Mayotte.

## 11. Lines for the Data & Limits page (Phase 6)

- A licence is not a person: one person can hold several licences.
- School sport (UNSS, USEP) is left out of maps and territorial indicators: their licences are recorded at the
  school's address, not where the pupil lives, so they would distort comparisons between places.
- Défense, Maccabi and Police federations only report by département: included in département figures, absent from
  commune and QPV views (160,151 licences).
- Maps use geocoded licences (98.75 %); abroad, Mayotte, COM and unallocated licences (1.25 %) are in the national total only.
- Overseas départements 971–974 are shown in a table, not on the map.
- Disability: Handisport + Sport Adapté only; a lower bound, as many disabled athletes hold ordinary licences.
- QPV: 2024 QPV list; shares only (no QPV population).
- Population: INSEE legal population 2023 (population municipale), COG 2026; licence communes mapped from COG 2024.
- Our national total uses INJEP's revised 2023 figures (2 federations differ from the first publication).
- Single year (2023): no trends.
