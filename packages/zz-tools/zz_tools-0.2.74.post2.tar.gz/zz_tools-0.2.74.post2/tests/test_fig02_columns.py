import importlib.util
import pathlib

import pandas as pd

# Charge le module directement depuis le script
P = pathlib.Path("zz-scripts/chapter10/plot_fig02_scatter_phi_at_fpeak.py")
spec = importlib.util.spec_from_file_location("fig02", P)
fig02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig02)


def test_detect_column_with_hint():
    df = pd.DataFrame({"XCOL": [0.1, 0.2], "y": [1, 2]})
    cands = ["x", "xcol", "phi_ref"]
    assert fig02.detect_column(df, "XCOL", cands) == "XCOL"


def test_detect_column_candidates_fallback():
    df = pd.DataFrame({"phi_ref_fpeak": [0.1, 0.2], "y": [1, 2]})
    cands = ["phi_ref_fpeak", "phi_ref", "phi_reference"]
    assert fig02.detect_column(df, None, cands) == "phi_ref_fpeak"
