"""Uses Solution and Master Solution parsers to compile tables from multiple databases"""
import re
import click
from typing import Optional, Tuple, Literal
import importlib.resources as pkg_resources
import numpy as np
import pandas as pd
from . import parser_dat
from . import utils


def compile_master_solution_table(
    list_of_databases: list, analysis=False
) -> pd.DataFrame:
    """
    Compile the master solution table by merging data from multiple databases.

    Parameters:
    - list_of_databases (list): A list of databases to merge.


    Returns:
    - pd.DataFrame: The compiled master solution table.

    Raises:
    - None

    Examples:
    >>> compile_master_solution_table(['db1', 'db2'])
    Returns the compiled master solution table by merging data from 'db1' and 'db2' databases.
    """
    result = parser_dat.MasterSolutionParser()
    for database in list_of_databases:
        result += parser_dat.MasterSolutionParser(database)
    result.data_frame = result.data_frame.dropna(
        axis=0, subset=["element", "species", "gfw_formula"]
    )
    result.data_frame["element"] = result.data_frame["element"].apply(replace_elements)
    result.data_frame["alk"] = result.data_frame["alk"].astype(float)

    if not analysis:
        result.data_frame = result.data_frame.drop_duplicates(
            subset=["element", "species"]
        )
    result.data_frame["source"] = result.data_frame["source"].apply(lambda x: f"#{x}")
    return result.data_frame


def compile_solution_species_table(list_of_databases: list) -> pd.DataFrame:
    """
    Compile the solution species table from a list of databases.

    Parameters:
        list_of_databases (list): A list of database file paths.

    Returns:
        pd.DataFrame: The compiled solution species table.

    """
    # init result
    result = parser_dat.SolutionParser(list_of_databases[0]).parse_file()

    # loop through all databases
    for database in list_of_databases[1:]:
        result = pd.concat([result, parser_dat.SolutionParser(database).parse_file()])

    # convert log_k to float
    result["log_k"] = result["log_k"].apply(log_k_to_float)

    # convert llnl_gamma to float
    result["llnl_gamma"] = result["llnl_gamma"].apply(lambda x: float(x[0]) if x else None)

    # remove 1.0000 from equations
    result["equation"] = remove_ones(result["equation"])

    # Change mulitple ---- to -4, --- to -3, -- to -2
    result["equation"] = result["equation"].apply(replace_charges)

    # remove decimals from equations where possible
    result["equation"] = strfloat_to_stringint(result["equation"])

    # clean vm column
    if "v_m" in result.columns:
        result["v_m"] = result["v_m"].apply(lambda x: clean_tuple(x, "vm"))

    # clean dw column
    if "d_w" in result.columns:
        result["d_w"] = result["d_w"].apply(lambda x: clean_tuple(x, "dw"))

    # convert no_check to boolean
    result["no_check"] = result["no_check"].apply(
        lambda x: True if isinstance(x, tuple) else False
    )

    # reset index and drop index column
    result = result.reset_index().drop("index", axis=1)

    return result


# This function is not implemented yet, skip in testing
def compile_phase_table(list_of_databases: list) -> pd.DataFrame:  # pragma: no cover
    """
    Compile phase table from a list of databases.

    Parameters:
        list_of_databases (list): A list of database file paths.

    Returns:
        pd.DataFrame: The compiled phase table.

    Raises:
        IndexError: If the 'SURFACE_SPECIES' phase is not found in the result.

    """
    # init result
    result = parser_dat.PhaseParser(list_of_databases[0]).parse_file()

    # loop through all databases
    for database in list_of_databases[1:]:
        result = pd.concat([result, parser_dat.PhaseParser(database).parse_file()])

    # drop empty rows
    result = result.dropna(axis=0, thresh=3)

    # drop duplicate rows
    result = result.drop_duplicates(subset=["phase_name", "dissolution_reaction"])

    # convert dissolution_reaction to string
    result["dissolution_reaction"] = result["dissolution_reaction"].apply(
        tuple_to_string
    )

    # clean up vm column
    if "v_m" in result.columns:
        result["v_m"] = result["v_m"].apply(lambda x: clean_tuple(x, "vm"))

    # breakup tc column
    result = result.apply(expand_tc, axis=1)

    tupe_to_float_columns = ["t_c", "p_c", "omega"]
    for column in tupe_to_float_columns:
        result[column] = result[column].apply(tuple_to_float)

    # remove 1.0000 from equations
    result["dissolution_reaction"] = remove_ones(result["dissolution_reaction"])

    # remove decimals from equations where possible
    result["dissolution_reaction"] = strfloat_to_stringint(
        result["dissolution_reaction"]
    )

    # Change ---- to -4, --- to -3, -- to -2
    result["dissolution_reaction"] = result["dissolution_reaction"].apply(
        replace_charges
    )

    # Seperate log_k and delta_h
    result[["log_k", "delta_h"]] = result.apply(expand_logk, axis=1)

    # convert log_k tuple to float
    result["log_k"] = result["log_k"].apply(tuple_to_float)

    # replace all np.nan with None
    result = result.replace({np.nan: None})

    # remove surface master species row
    try:
        surface_species_index = result[result["phase_name"] == "SURFACE_SPECIES"].index[
            0
        ]
        result = result.drop(index=surface_species_index)
    except IndexError:
        pass

    # reset index and drop index column
    result = result.reset_index().drop("index", axis=1)
    return result


def replace_charges(value: str) -> str:
    """
    Replace charges in a string with their corresponding values.

    Parameters:
        value (str): The input string containing charges to be replaced.

    Returns:
        str: The modified string with charges replaced.

    Examples:
        >>> replace_charges("HO----")
        "HO-4"
    """
    value = re.sub(r"----", "-4", value)
    value = re.sub(r"---", "-3", value)
    value = re.sub(r"--", "-2", value)
    return value


def replace_elements(value):
    """
    Replace elements in the format 'Element(Number)' with 'Element(+Number)'.

    Parameters:
    value (str): The input string to be processed.

    Returns:
    str: The processed string with replaced elements.

    Example:
    >>> replace_elements("H(2)O + Na(1)Cl")
    'H(+2)O + Na(+1)Cl'
    """
    matches = re.findall(r"([A-Za-z]+)\((?!0\b)(\d+)\)", value)
    for match in matches:
        element, number = match
        # Replace the matched pattern with 'Element(+Number)'
        value = value.replace(f"{element}({number})", f"{element}(+{number})")
    return value


def remove_ones(equation: pd.Series) -> pd.Series:
    """Changes 1.0000 to 1 in the equation column"""
    ones = re.compile(r"\b1\.0000?\b\s?")
    return equation.str.replace(ones, "", regex=True)


def strfloat_to_stringint(equation: pd.Series) -> pd.Series:
    """Removes decimals from equation when representing integers"""
    decimals = re.compile(r"\.0000?[ ]?")
    return equation.str.replace(decimals, "", regex=True)


def clean_tuple(
    tup: tuple, filter_str: Literal["vm", "dw"]
) -> Optional[Tuple[float, ...]]:
    """
    Clean the input tuple by removing elements that contain a specified substring ('vm' or 'dw')
    and converting numeric strings to floats. Retains numeric elements as they are.

    Parameters:
        tup (tuple): The input tuple to be cleaned.
        filter_str (Literal['vm', 'dw']): The substring to filter out from the tuple. Only 'vm' or 'dw' are allowed.

    Returns:
        tuple: The cleaned tuple, or None if the input tuple is empty or contains no valid elements.
    """
    result = []
    if tup:
        for entry in tup:
            if isinstance(entry, (float)):
                result.append(float(entry))
            elif isinstance(entry, str) and filter_str not in entry:
                try:
                    entry = float(entry)
                    result.append(entry)
                except ValueError:
                    pass
        return tuple(result) if result else None
    return None


def expand_tc(row: pd.Series) -> pd.Series:
    """
    Expand the 't_c' column in the given row by extracting 'p_c' and 'omega' values.

    Parameters
    ----------
    row : dict
        A dictionary representing a row of data.

    Returns
    -------
    dict
        The modified row dictionary with 'p_c' and 'omega' values extracted from 't_c'.

    Notes
    -----
    This function assumes that the 't_c' column in the given row contains a list of values.
    The first value in the list is considered as the 't_c' value, followed by optional 'p_c' and 'omega' values.
    The 'p_c' value is identified by the presence of 'P_c' or 'p_c' in the list.
    The 'omega' value is identified by the presence of 'Omega' or 'omega' in the list.

    If the 't_c' column is empty or contains only one value, the 'p_c' and 'omega' values will be set to 0.0.
    These are the default values listing in PHREEQC documentation.

    """
    pc_ex = re.compile(r"\W?[Pp]_?[Cc]")
    omega_ex = re.compile(r"\s?\W?[Oo]mega")
    t_c_combined = row["t_c"]
    t_c, p_c, omega = np.nan, np.nan, np.nan
    if t_c_combined and len(t_c_combined) > 1:
        for i, entry in enumerate(t_c_combined):
            if i == 0:
                t_c = float(entry.strip(";"))
            elif pc_ex.search(entry):
                p_c = float(t_c_combined[i + 1].strip(";"))
            elif omega_ex.search(entry):
                omega = float(t_c_combined[i + 1].strip(";"))
    row["p_c"] = p_c
    row["omega"] = omega
    row["t_c"] = t_c
    return row


# function is only used in compile_phase_table, which is not implemented yet, skip in testing
def tuple_to_string(tup: tuple) -> str:  # pragma: no cover
    """Converts a tuple to a string by joining all elements with a space"""
    return " ".join(tup)


# function is only used in compile_phase_table, which is not implemented yet, skip in testing
def tuple_to_float(tup: tuple) -> Optional[float]:  # pragma: no cover
    """Converts a tuple to a float by taking the first element"""
    if tup and not isinstance(tup, float):
        try:
            return float(tup[0])
        except ValueError:
            result = tup[0].split(";")
            return float(result[0])
    return None


# function is only used in compile_phase_table, which is not implemented yet, skip in testing
def expand_logk(row: pd.Series) -> pd.Series:  # pragma: no cover
    """
    Expand the log_k value in the given row.

    Parameters:
    - row (pandas.Series): A row of data containing 'log_k' and 'delta_h' columns.

    Returns:
    - pandas.Series: A new series with expanded 'log_k' value and corrected 'delta_h' value.

    Notes:
    - The 'log_k' value is expanded by separating the first element from the rest of the elements.
    - The 'delta_h' value is corrected by removing any entries that do not contain 'delta_h' in their lowercase form.
    """
    log_k_value = row["log_k"]
    if log_k_value and len(log_k_value) > 1:
        log_k_corrected = (log_k_value[0],)
        delta_h_corrected = []
        for i, entry in enumerate(log_k_value):
            if i == 0:
                continue
            if "delta_h" not in entry.lower():
                delta_h_corrected.append(entry)
        delta_h_corrected = tuple(delta_h_corrected)
        return pd.Series([log_k_corrected, delta_h_corrected])

    return pd.Series([log_k_value, row["delta_h"]])


def log_k_to_float(entry):
    """Convert log_k value to float"""
    if entry is not None:
        return float(entry[0].strip(";")) if ";" in entry[0] else float(entry[0])
    return 0.0


@click.command()
@click.option(
    "--function",
    type=click.Choice(["master_solution", "solution_species"], case_sensitive=False),
    required=True,
    help="The function to run: compile_master_solution_table (master_solution)"
    " or compile_solution_species_table (solution_species).",
)
# @click.option('--databases', multiple=True, required=True, help='List of database file paths.')
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=False,
    default="result",
    help="Output file path.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json"], case_sensitive=False),
    default="csv",
    help="Output file format: csv or json.",
)
@click.option(
    "--analysis",
    "-a",
    is_flag=True,
    default=False,
    help="Flag to include additional analysis in the master solution table.",
)
def main(function, format, analysis, output):
    """
    A CLI tool to compile tables from multiple databases and save as CSV or JSON.

    Example usage:
    python script.py --function master_solution --databases db1 db2 --output output.csv --format csv
    """
    data_b = pkg_resources.files('build_database').joinpath('databases')
    data_b = utils.phreeqc_database_list(data_b)
    if function == "master_solution":
        df = compile_master_solution_table(
            list_of_databases=data_b, analysis=analysis
        )
    elif function == "solution_species":
        df = compile_solution_species_table(list_of_databases=data_b)

    # Save the DataFrame to the specified format
    if format == "csv":
        output += ".csv" if not output.endswith(".csv") else ""
        df.to_csv(output, index=False)
        click.echo(f"Data saved to {output} in CSV format.")
    elif format == "json":
        output += ".json" if not output.endswith(".json") else ""
        df.to_json(output, orient="records", lines=True)
        click.echo(f"Data saved to {output} in JSON format.")


if __name__ == "__main__":
    main()
