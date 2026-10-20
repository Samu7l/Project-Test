# CLAUDE.md — "Le sport pour tous ? Inégalités territoriales et sociales de la pratique sportive en France (2023)"

## Project
Individual student project (EFREI, Data & AI). Build a **data-storytelling Streamlit app** on territorial and
social inequalities in organised sport in France in **2023**, from the Ministry of Sports licence and club census
(data.gouv.fr, Licence Ouverte). Deliverables: deployable app, README, Python code, dataset links, 2–4 min demo
video. Final zip name: `StApp26_20230845_MOLLIERE_DAI.zip`.

**THIS TOPIC IS FINAL.** Previous topics (road accidents, cycling / Tour de France) are abandoned. Delete their code,
data and docs (keep only what is reused below), unless the student asks otherwise.

**The student must be able to explain every line in the demo.** Work phase by phase, explain non-obvious decisions
in plain words, never jump to a later phase without being asked.

## Grading rubric (optimise for this)
- Narrative & framing (25): audience, questions, takeaways. Hook → Context → Insights → Implications.
- Data work (25): sourcing, cleaning, validation, feature engineering. **Make it visible in the app.**
- Visualization & UX (25): right chart types, annotations, legends, colours, interactions.
- Engineering (15): structure, `st.cache_data`, performance, reproducibility, docs.
- Communication (10): clarity, honest limitations.

## Narrative pattern
"Compare groups/regions with a map" + "rankings & distribution". Single year (2023): **no trend claims anywhere.**
Audience: general public + local decision makers (départements, sports services, city policy for priority areas).
1. **Hook** — How many licences in France in 2023, and how unequal are they between territories and groups?
2. **Territories** — licences per 10,000 inhabitants by département (map), top/bottom, distribution; commune drill-down
   inside a selected département.
3. **Priority neighbourhoods (QPV)** — licences of QPV residents and clubs located in QPV (counts and shares only,
   no QPV population needed).
4. **Women** — federations with the lowest women's share; football focus: women's share by département (map).
5. **Seniors** — share of licences held by people aged 60+ by département (no population by age needed).
6. **Disability** — licences in disability federations by département (counts and per 10,000 inhabitants).
7. **Explore** — age pyramid (sex × age band) for any federation chosen by the user.
8. **Implications & limits** — where public effort could target; what the data cannot say.

## Research questions
- **Q1 Territories** — volume and rate (per 10,000 inhabitants) of licences by département and commune; highest/lowest.
- **Q2 QPV** — share of licences held by QPV residents and share of clubs/EPA located in QPV, by département.
- **Q3 Gender** — federations ranked by women's share (minimum size threshold, e.g. ≥ 1,000 licences); football:
  women's share by département.
- **Q4 Seniors** — share of 60+ licences among all licences, by département.
- **Q5 Disability** — licences of the disability federations by département.
- **Q6 Age pyramid** — licences by sex × age band for a selected federation.

## Definitions and traps (read before coding — each one goes in the Limits page)
- **A licence is not a person.** One person can hold several licences (several federations). Always write
  "licences" / "licences pour 10 000 habitants", never "X % of people are licensed".
- **Place:** licences are counted at the licence holder's **home** commune; clubs at the **club's** commune.
  "Rate per inhabitant" uses home commune → consistent. Clubs per inhabitant compares club location with residents.
- **Geography version:** the 2023 files use the commune geography of N+1 (COG 2024); geo.api.gouv.fr returns the
  current geography. Map licence commune codes with `src/geo.py` (existing, handles old/merged codes) before joining,
  and report the join rate (target ≈ 100 %).
- **`Statut géo`:** keep geocoded licences (`1.Champ geoc`) for maps; report the non-geocoded share; national totals
  must include them when compared with published figures.
- **Sex:** columns F / H / NR (not reported). Report the NR share; shares of women = F / (F + H), documented.
- **QPV:** licences have a QPV code for residents of priority neighbourhoods. We only use counts and shares (no QPV
  population), so the QPV list version does not matter for the maths — just state it in the limits.
- **Disability:** identify the disability federations by code in `liste-federations.xlsx` (Handisport **and**
  Sport Adapté — check names). Many disabled athletes hold licences in ordinary federations → these counts are a
  **lower bound** of disabled people's sport. There is no disability population by département in our sources →
  show counts and per-10,000-inhabitants rates, **never** "share of disabled people who do sport".
- **Small numbers:** small communes give extreme rates (e.g. 40 inhabitants, 30 licences). Maps of rates are at
  **département** level; commune views apply a minimum population threshold (e.g. ≥ 2,000, documented) or show counts.
- **Single year:** 2023 only. No "rising / falling" wording.

## Data sources (verify each in Phase 1)
| # | Source | Unit | Notes |
|---|---|---|---|
| S1 | **lic-data-2023** — data.gouv.fr dataset `53699ebba3a729239d205f58` (Licence Ouverte) | commune (× QPV) × federation × sex × age band | ~256 MB, UTF-8 BOM, `;`. Reuse `src/sources/licences.py` (already parses the 2019+ format), extended to **all** federations. |
| S2 | **club-data-2023** — same dataset (check exact resource name) | commune (× QPV) × federation | Columns `Clubs_actifs`, `EPA_actifs`, `Total_actifs`, `Clubs`, `EPA`, `Total`. Define "club" vs "EPA" in the README. |
| S3 | `liste-federations.xlsx` + `licences-dictionnaire-des-variables.xlsx` (same dataset) | federation | Federation codes, names, types (Olympic, non-Olympic, multisport). |
| R1 | **Population — one API call:** `https://geo.api.gouv.fr/communes?fields=code,nom,population,codeDepartement,codeRegion&format=json` (free, no key) | commune | Legal population currently published by INSEE. Record which millésime it is (check the geo.api docs / INSEE) in the audit. Sum to département. Save the response once to `data/raw/` (the app never calls the API). |
| R2 | **Départements contours — one file:** simplified départements GeoJSON (e.g. github.com/gregoiredavid/france-geojson, `departements-version-simplifiee.geojson`) | département | Département borders are stable, so the "year" of the file does not matter. Check licence and record it. |
| R3 | **Communes contours (drill-down only) — API:** `https://geo.api.gouv.fr/departements/{code}/communes?format=geojson&geometry=contour` | commune | Download for all départements once in the build step, simplify, save one small file per département; the app loads only the selected one. |
| Bonus | Data ES / RES (sport facilities, PMR accessibility) | facility | Only if the student asks at the end. |

**Validation:** national licence total 2023 and per-federation totals vs the published INJEP 2023 figures (quote
only); département sum = national geocoded total (tested); commune join rate with the population file.

## Tech stack
- Python 3.12, macOS + VS Code, conda env `stapp26`; pip + pinned `requirements.txt` (Streamlit 1.66.0).
- pandas, pyarrow, plotly, pydeck (built into Streamlit), pytest. No geopandas needed: GeoJSON is used as-is by plotly / pydeck.
- **Maps:** département choropleths with `st.plotly_chart` (native, supports `on_select`); commune drill-down with
  plotly or `st.pydeck_chart`. **Folium / `streamlit_folium` only if plotly/pydeck cannot do it** (it is a third-party
  component and re-renders slowly) — ask the student before adding it.

## Streamlit UI rules
- Native Streamlit only: `st.sidebar` (département, federation, sex filters stored in `st.session_state`),
  `st.metric`, `st.tabs`, `st.expander` (method notes), `st.caption` (sources), `st.plotly_chart`, `st.pydeck_chart`.
- Reusable components in `src/ui.py`. No injected JavaScript, no HTML hacks.
- App language: English (course language) unless the student decides French — be consistent.

## Project structure
```
app.py                    # entry point, st.navigation, sidebar
pages/                    # 1_Hook, 2_Territories, 3_QPV, 4_Women, 5_Seniors, 6_Disability, 7_Explore, 8_Data_and_Limits
src/
  sources/                # licences.py (reuse), clubs.py, federations.py, population.py (geo.api), geometry.py (GeoJSON)
  geo.py                  # reuse: commune codes (old/merged) → current commune → département → region
  build.py                # processed tables for the app
  indicators.py           # rates, shares, ratios, thresholds
  validate.py             # checks vs published totals, sums, joins
  viz.py, ui.py
data/raw/                 # gitignored
data/processed/           # compact parquet / simplified GeoJSON (< 100 MB each)
docs/data_audit.md        # rewritten for this topic
tests/
requirements.txt
README.md
```

## Coding rules
- Small, typed functions with docstrings. No notebooks in the deliverable.
- All geographic codes are strings ("01", "2A", "01053").
- The app loads processed files only, through `@st.cache_data`.
- Never hard-code a number in narrative text: compute and inject it.
- Every chart: takeaway title, labelled axes with units ("licences pour 10 000 habitants"), source caption.
- After each phase: run it, show the output, summarise what changed and why, then stop.

## Roadmap
- [ ] Phase 0 — Clean-up: delete previous-topic code/data/docs (keep `src/geo.py`, `src/sources/licences.py`,
      COG reference files); new `docs/data_audit.md`; update `requirements.txt`
- [ ] Phase 1 — Audit S1–S3, R1–R3: exact resources, columns, disability federation codes, NR share, non-geocoded
      share, population millésime from geo.api, commune join rate; feasibility table Q1–Q6
- [ ] Phase 2 — Build processed tables (licences all federations, clubs, population, geometries)
- [ ] Phase 3 — Validation (totals vs published, sums, join rates)
- [ ] Phase 4 — App skeleton + Hook + Territories
- [ ] Phase 5 — QPV, Women, Seniors, Disability, Explore pages
- [ ] Phase 6 — Data & Limits page, README, deployment to Streamlit Community Cloud
- [ ] Phase 7 — Bonus (only if asked): sport facilities and PMR accessibility
