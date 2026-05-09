import pandas as pd

from src.PyPGDBE.PHREEQC_databasehelper import DatabaseSearcher


def make_searcher() -> DatabaseSearcher:
    solution_species = pd.DataFrame(
        {
            "equation": ["La+3+H2O=LaOH+2+H+", "YbF2+ = Yb+3 + 2F-", "Ca+2+CO3-2=CaCO3"],
            "log_k": [1.0, 2.0, 3.0],
        }
    )
    sms = pd.DataFrame(
        {
            "species": ["La", "Yb", "Ca"],
            "element": ["La", "Yb", "Ca"],
        }
    )
    phases = pd.DataFrame(
        {
            "phase_name": ["Quartz", "Calcite", "Fluorite"],
            "equation": ["SiO2 = SiO2", "CaCO3 = Ca+2 + CO3-2", "CaF2 = Ca+2 + 2F-"],
        }
    )
    return DatabaseSearcher(solution_species, sms, phases)


def test_empty_query_returns_empty_dataframe():
    searcher = make_searcher()

    result = searcher.search("species", "")

    assert result.empty


def test_unknown_category_returns_empty_dataframe():
    searcher = make_searcher()

    result = searcher.search("unknown", "La")

    assert result.empty


def test_species_partial_search_is_case_insensitive():
    searcher = make_searcher()

    result = searcher.search("species", "la")

    assert len(result) == 1
    assert result.iloc[0]["species"] == "La"


def test_species_exact_match():
    searcher = make_searcher()

    result = searcher.search("species", "La", exact=True)

    assert len(result) == 1
    assert result.iloc[0]["species"] == "La"


def test_equation_partial_search_by_text():
    searcher = make_searcher()

    result = searcher.search("equation", "CaCO3")

    assert len(result) == 1
    assert result.iloc[0]["equation"] == "Ca+2+CO3-2=CaCO3"


def test_phase_partial_search():
    searcher = make_searcher()

    result = searcher.search("phase", "quart")

    assert len(result) == 1
    assert result.iloc[0]["phase_name"] == "Quartz"
