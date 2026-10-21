"""Validation checks: re-run them when the raw data is available, and check the saved results in every case."""
import pandas as pd
import pytest

from src import validate

RAW_READY = (validate.RAW / "lic-data-2023.csv").exists() and (validate.PROCESSED / "federations.parquet").exists()


@pytest.mark.skipif(not RAW_READY, reason="raw data not downloaded: run `python -m src.build` first")
def test_all_validation_checks_pass():
    res = validate.run_all()
    failed = res.loc[~res["passed"], ["check", "observed", "expected"]]
    assert failed.empty, failed.to_string()


def test_saved_validation_results_all_pass():
    """The table shown on the Data & Limits page (shipped in data/processed/) has no failed check."""
    res = pd.read_parquet(validate.PROCESSED / "validation.parquet")
    assert len(res) > 0
    assert res["passed"].all(), res.loc[~res["passed"], "check"].tolist()
