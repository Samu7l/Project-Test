"""S3: federation list (codes, names, data notes) and INJEP federation groups."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LIST_URL = (
    "https://static.data.gouv.fr/resources/donnees-geocodees-issues-du-recensement-des-licences-et-clubs-aupres-"
    "des-federations-sportives-agreees-par-le-ministere-charge-des-sports/20251229-163349/liste-federations.xlsx"
)
FAMILIES_URL = "https://injep.fr/wp-content/uploads/2024/07/Familles-federations-2023.xlsx"

DISABILITY_CODES = ["501", "503"]  # FF Handisport, FF du Sport Adapté = INJEP group "4. Para-sport"
NOTE_CLUB_ADDRESS = "Adr. Club"    # licences located at the club / school, not at the holder's home
NOTE_DEPT_ONLY = "n.r."            # licences given by département only (no commune, no QPV)
NOTE_NO_LICENCES = "Pas de licences"


def read_federations(list_path: Path, families_path: Path) -> pd.DataFrame:
    """One row per federation: code, name, INJEP group/family and the flags that drive the app's scope rules."""
    fed = pd.read_excel(list_path, sheet_name="2023", header=1, dtype=str).iloc[:, 1:]
    fed.columns = ["name", "code", "note_licences", "note_clubs"]
    fed = fed.dropna(subset=["code"])
    fed = fed[fed["code"].str.fullmatch(r"\d{3}")]

    fam = pd.read_excel(families_path, dtype=str)
    fam = fam.rename(columns={"Code 2023": "code", "Famille fédérations": "family",
                              "Sous-famille fédérations": "subfamily", "Groupe fédérations": "group"})
    fed = fed.merge(fam[["code", "group", "family", "subfamily"]], on="code", how="left")

    return fed.assign(
        is_disability=fed["code"].isin(DISABILITY_CODES),
        is_club_address=fed["note_licences"].eq(NOTE_CLUB_ADDRESS),
        is_dept_only=fed["note_licences"].eq(NOTE_DEPT_ONLY),
        has_licences=fed["note_licences"].ne(NOTE_NO_LICENCES),
        # Geographic views (maps, rates, QPV, seniors by département) leave out school sport located at the school.
        in_geo_views=~fed["note_licences"].eq(NOTE_CLUB_ADDRESS),
    ).reset_index(drop=True)
