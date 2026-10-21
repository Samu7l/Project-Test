"""Every dataset used by the project, in one place: shown on the Data & Limits page, written to DATA_SOURCES.md.

Run:  python -m src.sources.registry > DATA_SOURCES.md
"""
from __future__ import annotations

DATAGOUV = ("https://www.data.gouv.fr/datasets/donnees-geocodees-issues-du-recensement-des-licences-et-clubs-aupres-"
            "des-federations-sportives-agreees-par-le-ministere-charge-des-sports")

# id, name, producer, licence, link, version / date, role in the project
SOURCES = [
    ("S1", "Licences 2023 (lic-data-2023.csv)", "INJEP-MEDES; geocoding by INSEE", "Licence Ouverte",
     DATAGOUV, "file uploaded 29/12/2025", "Licences by commune × QPV × federation × sex × age"),
    ("S2", "Clubs 2023 (clubs-data-2023.csv)", "INJEP-MEDES; geocoding by INSEE", "Licence Ouverte",
     DATAGOUV, "file uploaded 29/12/2025", "Active clubs and EPA by commune × QPV × federation"),
    ("S3", "Federation list and variable dictionaries", "INJEP-MEDES", "Licence Ouverte",
     DATAGOUV, "29/12/2025", "Federation codes, names, data notes (club address, département only)"),
    ("S4", "Federation families 2023", "INJEP", "Licence Ouverte",
     "https://injep.fr/donnee/recensement-des-licences-et-clubs-sportifs-2023/", "July 2024",
     "Federation groups (Olympic, non-Olympic, multisport, para-sport, school)"),
    ("R1", "Legal population 2023 by commune", "INSEE, via geo.api.gouv.fr", "Licence Ouverte",
     "https://geo.api.gouv.fr/communes?fields=code,nom,population,codeDepartement,codeRegion&format=json",
     "populations légales 2023 (in force 1/1/2026), COG 2026; downloaded 20/10/2026", "Denominator of all rates"),
    ("R1b", "Legal population 2023 (cross-check file)", "INSEE", "Licence Ouverte",
     "https://catalogue-donnees.insee.fr/fr/catalogue/recherche/DS_POPULATIONS_REFERENCE", "millésime 2023",
     "Checks that geo.api returns the 2023 legal population"),
    ("R2", "Département outlines (simplified) and Mayotte outline", "IGN Admin Express, via france-geojson",
     "Licence Ouverte", "https://github.com/gregoiredavid/france-geojson", "IGN edition 2018", "Mainland map"),
    ("R3", "Commune outlines", "IGN, via geo.api.gouv.fr", "Licence Ouverte",
     "https://geo.api.gouv.fr/departements/01/communes?format=geojson&geometry=contour",
     "COG 2026; downloaded 20/10/2026", "Commune drill-down; overseas outlines (merged)"),
    ("R4", "Départements and regions (names, codes)", "INSEE, via geo.api.gouv.fr", "Licence Ouverte",
     "https://geo.api.gouv.fr/departements", "COG 2026", "Names and region codes"),
    ("R5", "Population of the 2024 priority neighbourhoods (QPV)", "INSEE", "Licence Ouverte",
     "https://www.insee.fr/fr/statistiques/8210600?sommaire=8186144",
     "online 10/07/2025; pop. 1/1/2020 (mainland), 1/1/2021 (overseas)", "QPV benchmark"),
    ("R7", "Census 2023: population by sex and single year of age (POP1)", "INSEE (recensement de la population)",
     "Licence Ouverte", "https://www.insee.fr/fr/statistiques/9006235",
     "RP 2023, reference date 1/1/2023; published 25/06/2026",
     "Identified, not used yet (awaiting approval): denominators by sex and age (Seniors, Explore)"),
    ("R6", "Panorama statistique 2024 « Handicap et invalidité » (sheet 11)", "DREES (FINESS; INSEE)",
     "not stated in the dataset metadata",
     "https://data.drees.solidarites-sante.gouv.fr/explore/dataset/panorama-statistique-handicap-et-invalidite/",
     "places at 31/12/2023", "Context for the Disability page (equipment rates for disabled adults)"),
    ("G1", "Commune events since 1943 (COG 2026)", "INSEE", "Licence Ouverte",
     "https://www.insee.fr/fr/information/8740222", "COG 2026", "Maps merged communes (COG 2024 → 2026)"),
    ("V1", "Licence and club results 2023 (first publication)", "INJEP", "Licence Ouverte",
     "https://injep.fr/donnee/recensement-des-licences-et-clubs-sportifs-2023/", "data at 11/07/2024",
     "Validation"),
    ("V2", "Licence results 2024, with revised 2023 history", "INJEP", "Licence Ouverte",
     "https://injep.fr/donnee/recensement-des-licences-et-clubs-sportifs-2024/", "July 2025", "Validation"),
    ("Q1", "Insee Première n° 2008 (QPV portrait)", "INSEE", "Licence Ouverte",
     "https://www.insee.fr/fr/statistiques/8236231", "August 2024",
     "Quoted only: QPV residents are younger (Implications page)"),
]
COLUMNS = ["Id", "Dataset", "Producer", "Licence", "Link", "Version / date", "Used for"]

# Figures quoted from publications (not computed from our data). Kept here with their source.
QPV_UNDER_25 = 0.39        # share of QPV residents under 25 (Insee Première n° 2008, QPV 2024)
URBAN_UNDER_25 = 0.30      # same share in the surrounding urban units


def to_markdown() -> str:
    """DATA_SOURCES.md content."""
    lines = ["# Data sources", "",
             "Every dataset used by *Sport for all?* (raw files are downloaded by `python -m src.build`; the app "
             "only reads `data/processed/`).", "",
             "| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for s in SOURCES:
        lines.append("| " + " | ".join([s[0], s[1], s[2], s[3], f"[link]({s[4]})", s[5], s[6]]) + " |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(to_markdown(), end="")
