"""S2: clubs and EPA 2023 (same census and file layout as the licences)."""
from __future__ import annotations

import pandas as pd

from src.sources.licences import CLUBS_URL, NOT_ALLOCATED, QPV_PATTERN, read_census  # noqa: F401  (re-exported)


def add_club_features(clubs: pd.DataFrame) -> pd.DataFrame:
    """Add active structures located in a QPV and active structures with an allocated QPV code."""
    is_qpv = clubs["Code QPV"].str.match(QPV_PATTERN)
    return clubs.assign(
        actifs_qpv_in=clubs["Total_actifs"].where(is_qpv, 0),
        actifs_qpv_allocated=clubs["Total_actifs"].where(clubs["Code QPV"] != NOT_ALLOCATED, 0),
    )
