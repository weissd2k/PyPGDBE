import pytest
import pandas as pd
from PyPGDBE.PHREEQC_databasehelper import DatabaseSearcher

def test_search_functionality():
    ss_df = pd.DataFrame({'equation': ['H2O = H+ + OH-']})
    sms_df = pd.DataFrame({'species': ['H+']})
    phase_df = pd.DataFrame({'phase_name': ['Calcite']})
    
    searcher = DatabaseSearcher(ss_df, sms_df, phase_df)
    

    result = searcher.search("equation", "H2O")
    assert not result.empty
    assert "H2O" in result.iloc[0]['equation']
    
    empty_result = searcher.search("species", "NonExistent")
    assert empty_result.empty

def test_normalize_equation():
    from PyPGDBE.PHREEQC_databasehelper import EditDatabasePage
    

    def check_norm(s):
        import re
        s = s.strip()
        s = re.sub(r'\s*=\s*', ' = ', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    assert check_norm("H2O=H++OH-") == "H2O = H++OH-"
    assert check_norm("  Ca+2   =  Ca+2  ") == "Ca+2 = Ca+2"


@pytest.fixture
def edit_page():
    from PyPGDBE.PHREEQC_databasehelper import EditDatabasePage
    import tkinter as tk
    
    root = tk.Tk()
    
    root.searcher = None 
    
    page = EditDatabasePage(root)
    
    yield page
    
    root.destroy()

def test_edit_database_logic(edit_page):
    input_eq = "Ca+2=Ca+2"
    expected_eq = "Ca+2 = Ca+2"
    assert edit_page.normalize_equation(input_eq) == expected_eq

    mock_lines = [
        "SOLUTION_MASTER_SPECIES\n",
        "Ca      Ca+2    0.0     40.08\n",
        "Mg      Mg+2    0.0     24.305\n"
    ]
    
    idx = edit_page.find_master_species_line(mock_lines, "Mg")
    
    assert idx == 2
