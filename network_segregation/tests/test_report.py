import numpy as np
import pandas as pd
import pytest

from netseg import report


def _idx():
    rows = []
    for k, (e, n) in enumerate([(0.10, 0.12), (0.20, 0.21), (0.15, 0.20), (0.05, 0.049)]):
        rows.append({"COD_MUNICIPIO": str(k), "NM_MUN": f"C{k}", "spec": "main", "index": "H", "euc": e, "net": n})
        rows.append({"COD_MUNICIPIO": str(k), "NM_MUN": f"C{k}", "spec": "b1000", "index": "H", "euc": e, "net": n})
    return pd.DataFrame(rows)


def test_gap_table():
    t = report.gap_table(_idx())
    assert list(t.index) == ["H_euc", "H_net", "dH", "pdH"]
    assert t.loc["dH", "count"] == 4
    assert t.loc["dH", "min"] == pytest.approx(-0.001)


def test_rank_comparison():
    r = report.rank_comparison(_idx(), top=2)
    c2 = r.set_index("NM_MUN").loc["C2"]
    assert c2.rank_euc == 2 and c2.rank_net == 2
    assert set(r["NM_MUN"]) == {"C1", "C2"}


def test_robustness_table():
    t = report.robustness_table(_idx())
    row = t.set_index(["spec", "index"]).loc[("main", "H")]
    assert row.share_positive == pytest.approx(0.75)
    assert -1 <= row.spearman <= 1


def test_write_macros(tmp_path):
    p = tmp_path / "n.tex"
    report.write_macros({"nCities": 91, "meanPdH": "12.3"}, p)
    assert p.read_bytes() == b"\\newcommand{\\nCities}{91}\n\\newcommand{\\meanPdH}{12.3}\n"
    with pytest.raises(ValueError):
        report.write_macros({"bad_name1": 1}, p)
