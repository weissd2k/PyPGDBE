import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from src.PyPGDBE.utils import (
    alk_gfw_duplicates,
    equation_duplicates,
    plot_source_hist,
    remove_ones_full,
)


matplotlib.use("Agg")


def test_alk_gfw_duplicates_raises_for_missing_column():
    df = pd.DataFrame({"element": ["La"], "species": ["La+3"], "source": ["db1"]})

    with pytest.raises(ValueError, match="target not in DataFrame columns"):
        alk_gfw_duplicates(df, "target")


def test_alk_gfw_duplicates_returns_conflicting_pairs():
    df = pd.DataFrame(
        {
            "element": ["La", "La", "Yb"],
            "species": ["La+3", "La+3", "Yb+3"],
            "gfw": [1.0, 2.0, 3.0],
            "source": ["db1", "db2", "db3"],
        }
    )

    count, dups = alk_gfw_duplicates(df, "gfw")

    assert count == 1
    assert len(dups) == 2
    assert set(dups["element"]) == {"La"}


def test_remove_ones_full_removes_decimal_one_coefficients():
    equations = pd.Series(["1.0000 H+ + 1.0 OH-", "10 H+", "1 H2O"])

    cleaned = remove_ones_full(equations)

    assert cleaned.iloc[0] == "H+ + OH-"
    assert cleaned.iloc[1] == "10 H+"
    assert cleaned.iloc[2] == "1 H2O"


def test_equation_duplicates_raises_for_missing_column():
    df = pd.DataFrame({"equation": ["A = B"]})

    with pytest.raises(ValueError, match="log_k not in DataFrame columns"):
        equation_duplicates(df, "log_k")


def test_equation_duplicates_finds_rows_with_same_equation():
    df = pd.DataFrame(
        {
            "equation": ["A = B", "A = B", "C = D"],
            "log_k": [1.0, 2.0, 3.0],
            "source": ["db1", "db2", "db3"],
        }
    )

    count, dups = equation_duplicates(df, "log_k")

    assert count == 1
    assert len(dups) == 2
    assert set(dups["equation"]) == {"A = B"}


def test_plot_source_hist_draws_on_existing_axes():
    df = pd.DataFrame({"source": ["alpha.dat", "alpha.dat", "beta#db"]})
    fig, ax = plt.subplots()

    plot_source_hist(df=df, title="Source Distribution", ax=ax, label="demo")

    assert ax.get_title() == "Source Distribution"
    assert ax.get_xlabel() == "Source"
    assert ax.get_ylabel() == "Count"
    assert len(ax.patches) > 0

    plt.close(fig)
