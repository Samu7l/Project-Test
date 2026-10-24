# Sport for all? Territorial and social inequalities in organised sport in France (2023)

A data-storytelling Streamlit app built on the 2023 census of sports licences and clubs (Ministry of Sports,
INJEP-MEDES, data.gouv.fr). Individual project, EFREI Data & AI — Samuel Mollière.

## What the app answers

| Page | Question |
|---|---|
| Hook | How many licences in 2023, and how unequal are they between départements? |
| Territories | Licences per 10 000 inhabitants by département (map, Île-de-France zoom, overseas), top and bottom 5, commune drill-down |
| Priority neighbourhoods | Share of licences held by QPV residents and of clubs located in QPV, against the share of the population living in QPV |
| Women | Federations ranked by women's share; football's women's share by département |
| Seniors | Licences of people aged 60+ per 10 000 inhabitants aged 60+, by département |
| Disability | Handisport + Sport Adapté licences per 10 000 inhabitants (a lower bound) |
| Explore | Age pyramid (counts or licences per 100 people of that age and sex) and women's / men's licences per 10 000 women / men by département, for any federation |
| Implications | Five takeaways, where public effort could be targeted, what the data cannot say |
| Data & Limits | Sources, pipeline, validation results (33 checks), full list of limits |

Every number in the text is computed from the data. Sidebar filters (département, federation) are shared by all
pages; a filter that does not apply to a page is shown as "not applied". Maps are clickable.

## Install

Python **3.12**.

```bash
conda create -n stapp26 python=3.12 -y
conda activate stapp26
pip install -r requirements.txt
```

## Run

```bash
python -m streamlit run app.py
```

The app reads only `data/processed/` (shipped with the code, ~43 MB): no download, no API call at run time.

## Rebuild the data (optional)

```bash
python -m src.build      # downloads the raw files into data/raw/ (~600 MB, once) and rebuilds data/processed/
python -m src.validate   # 33 checks against INJEP published figures, sums and joins; saves the results for the app
pytest                   # unit tests + saved validation results (the full re-run needs data/raw/)
```

`python -m src.audit` prints the raw-data audit summarised in `docs/data_audit.md`.

## Sources

Full table with versions: [DATA_SOURCES.md](DATA_SOURCES.md) (also shown on the Data & Limits page).

- Licences and clubs 2023, federation list — INJEP-MEDES, geocoded by INSEE: [data.gouv.fr](https://www.data.gouv.fr/datasets/donnees-geocodees-issues-du-recensement-des-licences-et-clubs-aupres-des-federations-sportives-agreees-par-le-ministere-charge-des-sports) (Licence Ouverte)
- Legal population 2023 and commune outlines — INSEE / IGN via [geo.api.gouv.fr](https://geo.api.gouv.fr)
- Population by sex and age, census 2023 — [INSEE](https://www.insee.fr/fr/statistiques/9006235)
- Département outlines — IGN Admin Express via [france-geojson](https://github.com/gregoiredavid/france-geojson)
- Population of the 2024 QPV — [INSEE](https://www.insee.fr/fr/statistiques/8210600?sommaire=8186144)
- Commune events (COG 2026) — [INSEE](https://www.insee.fr/fr/information/8740222)
- Places for disabled adults by département — [DREES, Panorama statistique 2024](https://data.drees.solidarites-sante.gouv.fr/explore/dataset/panorama-statistique-handicap-et-invalidite/)
- Validation: INJEP results [2023](https://injep.fr/donnee/recensement-des-licences-et-clubs-sportifs-2023/) and [2024](https://injep.fr/donnee/recensement-des-licences-et-clubs-sportifs-2024/) (revised 2023 figures)

**Definitions.** *Club*: non-profit association (loi 1901) affiliated to a federation. *EPA* (établissement
professionnel agréé): private or commercial structure approved by a federation. *Active*: at least one annual
licence. *QPV*: priority neighbourhood of urban policy (2024 list).

## Deliverable

`bash make_zip.sh` builds `StApp26_20230845_MOLLIERE_DAI.zip` (code, README, processed data, DATA_SOURCES.md; no raw
data, no .git).

## Structure

```
app.py                 entry point: navigation, shared sidebar
app_pages/             one file per page (1_Hook … 9_Data_and_Limits)
src/
  sources/             readers for each raw source + registry.py (list of datasets)
  geo.py               commune codes (COG 2024) -> current communes (COG 2026)
  build.py             raw -> processed tables
  indicators.py        rates, shares, rankings (pure pandas)
  validate.py          33 checks (published figures, sums, joins)
  limits.py            limits shown on the Data & Limits page
  viz.py, ui.py        Plotly figures; Streamlit components, number formatting, sidebar
  data.py              cached loaders (st.cache_data)
data/processed/        parquet tables + simplified GeoJSON (the only data the app reads)
docs/data_audit.md     audit of every source
tests/                 pytest
```

## Architecture

How our structure maps to the course's recommended layout. The roles are the same; only the names differ.

| Course layout | This project | Role |
|---|---|---|
| `app.py` | `app.py` | Entry point: page config, `st.navigation`, shared sidebar filters |
| `sections/` | `app_pages/` (`1_Hook.py` … `9_Data_and_Limits.py`) | One file per story section. Not named `pages/`: Streamlit would auto-discover that folder and bypass `st.navigation` on direct links |
| `utils/io.py` | `src/data.py` (app: cached loaders of the processed files, `st.cache_data`) and `src/sources/` (build: one reader per raw source, plus `registry.py`, the list of datasets) | Loading data |
| `utils/prep.py` | `src/build.py` (raw → processed tables), `src/geo.py` (commune code harmonisation), `src/indicators.py` (rates, shares, rankings), `src/validate.py` (33 checks), `src/limits.py` | Cleaning, feature engineering, validation |
| `utils/viz.py` | `src/viz.py` (Plotly figures) and `src/ui.py` (Streamlit components: maps block, tables, number formatting, sidebar) | Charts and reusable UI |
| `data/` | `data/raw/` (downloaded by the build, not shipped) and `data/processed/` (parquet + simplified GeoJSON, the only data the app reads) | Data |
| `assets/` | none | No static assets: map outlines are data, in `data/processed/geo/` |
| — | `tests/`, `docs/data_audit.md`, `make_zip.sh` | Tests, source audit, deliverable script |

## Main limits

- A **licence is not a person**: one person can hold several licences.
- School sport (UNSS, USEP) is recorded at the school's address: excluded from territorial views, kept in national totals.
- Rates by sex and age use census 2023 estimates; disability counts are a lower bound.
- The QPV benchmark uses QPV populations from 2020/2021; QPV residents are younger, so the gap is probably understated.
- 2023 only: no trends. Full list on the Data & Limits page.


##

- Lien de la démo : https://youtu.be/UZ9jN3MVxK0


Developed with AI assistance (Claude Code). All data choices, validation and conclusions were reviewed by the author.