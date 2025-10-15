import numpy as np
import pandas as pd
from zz_tools import common_io as ci

def test_p95_basic():
    arr = [0, 1, 2, 3, 4, 1000]
    v = ci.p95(arr)
    assert np.isfinite(v)
    assert 4 < v < 1000  # borne large

def test_p95_robust_nan_inf():
    arr = [np.nan, np.inf, -np.inf, 0, 10]
    v = ci.p95(arr)
    assert np.isfinite(v)
    assert 0 <= v <= 10

def test_ensure_fig02_cols_aliasing():
    df = pd.DataFrame({"f":[10,20], "phi_ref_cal":[1,2], "phi_active":[3,4]})
    out = ci.ensure_fig02_cols(df.copy())
    for col in ("f_Hz", "phi_ref", "phi_mcgt"):
        assert col in out.columns
