import logging
import os
import io
import warnings
import pandas as pd
from . import clean_tables as ct
from . import write_dataframes as cf
from . import blocks as blocks


def compile_and_rank_mst(db_list: str, rank: dict) -> pd.DataFrame:
    """
    Compile and rank the master solution table.
    Parameters
    ----------
    db_list : list
        A list of database names.
    Returns
    -------
    pandas.DataFrame
        The compiled and ranked master solution table.
    Notes
    -----
    This function compiles the master solution table using the given list of database names.
    It assigns a priority to each row in the table based on the 'source' column.
    The priority is determined by looking up the 'source' value in the RANK dictionary.
    If the 'source' value is not found in the RANK dictionary, a default priority of 5 is assigned.
    The resulting table is then sorted by the 'priority' column.
    """
    mst = ct.compile_master_solution_table(db_list)
    mst['priority'] = mst['source'].apply(lambda x: rank[x] if x in rank else 5)
    return mst.sort_values(by=['priority'])


def add_hash_to_source(source: str) -> str:
    """
    Add a hash symbol to the beginning of the source if it is not already present.

    Parameters:
    source (str): The source string to add a hash symbol to.

    Returns:
    str: The modified source string with a hash symbol added.

    """
    if source[0] == '#':
        return source
    return '#' + source


def remove_hash_from_source(source: str) -> str:
    """
    Remove the hash symbol from the beginning of the source string.

    Parameters:
    source (str): The source string.

    Returns:
    str: The source string without the hash symbol at the beginning.

    """
    if source[0] == '#':
        return source[1:]
    return source


def get_missing_species(mst: pd.DataFrame, result_mst: pd.DataFrame, add: str = '#minteq.v4.dat') -> pd.DataFrame:
    """
    Get the missing species from the master database.

    Parameters:
        mst (pd.DataFrame): The master database.
        result_mst (pd.DataFrame): The result master database.
        add (str, optional): The source to add. Defaults to '#minteq.v4.dat'.

    Returns:
        pd.DataFrame: The missing species from the master database.
    """
    add = add_hash_to_source(add)
    temp = mst[mst['source'] == add]
    missing = ~temp['element'].isin(result_mst['element'])
    return temp[missing]


def process_missing_species(missing_species: pd.DataFrame) -> pd.DataFrame:
    """
    Process missing species data by removing rows with species in TO_DROP.

    Parameters
    ----------
    missing_species : pandas.DataFrame
        DataFrame containing missing species data.

    Returns
    -------
    pandas.DataFrame
        DataFrame with rows removed where species is in TO_DROP.
    """
    to_drop = ['Hg', 'Sb(OH)6-']
    missing_species = missing_species[~missing_species['species'].isin(to_drop)]
    return missing_species


def find_and_collect_matches(series: pd.Series, entry: str, all_match_indexes: list) -> None:
    """
    Find and collect matches in a series based on a given entry.

    Parameters:
    -----------
    series : pandas.Series
        The series to search for matches.
    entry : str
        The entry to search for in the series.
    all_match_indexes : list
        The list to collect all the match indexes.

    Returns:
    --------
    None

    Raises:
    -------
    None

    Notes:
    ------
    - If the entry is 'Sb(OH)6-', a warning message will be logged.
    - The function searches for matches in the series based on the entry.
    - The match indexes are collected in the all_match_indexes list.
    """
    if entry == 'Sb(OH)6-':
        logging.warning('Unexpected species Sb(OH)6- found')
    match_indexes = series[series.str.contains(entry, regex=False)].index.tolist()
    if match_indexes:
        all_match_indexes.extend(match_indexes)


def reorder_file_list(file_list: str, rank_dict: dict) -> list:
    """
    Reorders a list of file paths based on a ranking dictionary.

    Parameters:
    - file_list (list): A list of file paths.
    - rank_dict (dict): A dictionary containing the ranking information.

    Returns:
    - sorted_file_paths (list): A list of file paths sorted according to the ranking dictionary.

    Example:
    >>> file_list = ['/path/to/file1.txt', '/path/to/file2.txt', '/path/to/file3.txt']
    >>> rank_dict = {'#file1.txt': 3, '#file2.txt': 1, '#file3.txt': 2}
    >>> reorder_file_list(file_list, rank_dict)
    ['#file2.txt', '#file3.txt', '#file1.txt']
    """
    filenames = [path.split('/')[-1] for path in file_list]
    ranked_files = [file for file in filenames if f'#{file}' in rank_dict]
    unranked_files = [file for file in filenames if f'#{file}' not in rank_dict]
    ranked_files.sort(key=lambda x: rank_dict[f'#{x}'])
    sorted_filenames = ranked_files + unranked_files
    sorted_file_paths = [f'#{filename}' for filename in sorted_filenames]

    return sorted_file_paths


def save_master_database(output_file=None, result_mst: pd.DataFrame = None, result_sp: pd.DataFrame = None) -> str:
    """
    Save the master database to a file or return the file content as a string.

    Parameters:
        output_file (str, optional): The path to the output file. If provided,
        the master database will be saved to this file. Defaults to None.
        result_mst (pd.DataFrame, optional): The DataFrame containing the solution master species data.
        Defaults to None.
        result_sp (pd.DataFrame, optional): The DataFrame containing the solution species data. Defaults to None.

    Returns:
        str: The content of the master database file if output_file is not provided.

    Raises:
        ValueError: If both result_mst and result_sp are None.
        UserWarning: If either result_mst or result_sp is None.

    Notes:
        - If output_file is provided, the master database will be saved to the specified file.
        - If output_file is not provided, the content of the master database file will be returned as a string.
        - If either result_mst or result_sp is None, a warning will be raised.

    """
    if result_mst is None and result_sp is None:
        raise ValueError("At least one of result_mst or result_sp must be provided.")

    if result_mst is None or result_sp is None:
        warnings.warn("Either solution master species or solution species is missing.", UserWarning)

    with io.StringIO() as file:
        file.write(blocks.NAMED_EXPRESSIONS)
        file.write("\n"+blocks.LLNL_AQUEOUS_MODEL_PARAMETERS+"\n")

        if result_mst is not None:
            file.write(
                "SOLUTION_MASTER_SPECIES\n#element\tmaster species\talkalinity\tgfw|formula\tgfw of element\tsource\n"
            )
            result_mst.apply(lambda row: cf.write_mst(row, file), axis=1)

        if result_sp is not None:
            file.write("\nSOLUTION_SPECIES\n")
            result_sp.apply(lambda row: cf.write_sp(row, file), axis=1)

        logging.info("File processing complete.")
        file_content = file.getvalue()

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(file_content)

    else:
        return file_content


def phreeqc_database_list(database_directory: str, ignore=None) -> list:
    """Returns a list of phreeqc database file paths"""
    database_file_paths = []
    for file in os.listdir(database_directory):
        if file.endswith(".dat") and not ignore:
            database_file_paths.append(os.path.join(database_directory, file))
        elif file.endswith(".txt"):
            warnings.warn(
                f"File {file} is not a database file and will be ignored", UserWarning
            )

    return database_file_paths
