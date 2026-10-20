"""Every Phase 3 validation check must pass on the processed data (run `python -m src.build` first)."""
import pytest

from src import validate

pytestmark = pytest.mark.skipif(not (validate.PROCESSED / "federations.parquet").exists(),
                                reason="processed data not built")


def test_all_validation_checks_pass():
    res = validate.run_all()
    failed = res.loc[~res["passed"], ["check", "observed", "expected"]]
    assert failed.empty, failed.to_string()
