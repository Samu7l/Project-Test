"""R6: places in establishments for disabled adults by département (DREES, Panorama statistique 2024).

Sheet "11. Taux équipement PH adultes": places per 1 000 inhabitants aged 20-59 at 31/12/2023 (sources DREES, FINESS;
INSEE population estimates). Used only as context for the Disability page (no causal claim).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

URL = ("https://data.drees.solidarites-sante.gouv.fr/api/explore/v2.1/catalog/datasets/"
       "panorama-statistique-handicap-et-invalidite/attachments/panorama_statistique_2024_xlsx")
SHEET = "11. Taux équipement PH adultes"
ROWS = {6: "mas", 7: "fam", 8: "home", 9: "esat"}  # spreadsheet row -> indicator
LABELS = {"mas": "specialised care homes (MAS)", "fam": "medicalised care homes (FAM)",
          "home": "residential homes (foyers de vie)", "esat": "sheltered work centres (ESAT)"}
FRANCE = "FR"


def read_equipment(path: Path, departements: pd.DataFrame) -> pd.DataFrame:
    """One row per département (code from its name) plus a 'FR' row for France entière; rates as floats."""
    df = pd.read_excel(path, sheet_name=SHEET, header=None)
    names = [str(n).replace("\n", " ").strip() for n in df.iloc[4]]
    code_of = {**dict(zip(departements["dep_name"], departements["dep"])), "France entière": FRANCE}
    cols = [i for i, n in enumerate(names) if n in code_of]
    out = pd.DataFrame({"dep": [code_of[names[i]] for i in cols]})
    for row, name in ROWS.items():
        out[name] = pd.to_numeric(df.iloc[row, cols], errors="coerce").to_numpy()
    if len(out) != len(departements) + 1:
        raise ValueError(f"expected {len(departements)} départements + France, found {len(out)} columns")
    return out
