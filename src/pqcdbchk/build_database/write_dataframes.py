''' This module contains functions to write data to a file. '''
import re
import pandas as pd


def write_tuple(att: str, value: tuple, file) -> None:
    """
    Breaks a tuple into individual values and writes them to a file.

    Parameters:
    att (str): The attribute name.
    value (tuple): The tuple to be written.
    file: The file object to write to.

    Returns:
    None
    """
    if value:
        file.write(f"\t{att}\t")
        for i in value:
            file.write(f"{i} ")
        file.write('\n')


def write_mst(row: pd.Series, file) -> None:
    """
    Writes a row of data to a file.

    Args:
        row (pd.Series): The row of data to be written.
        file: The file object to write the data to.

    Returns:
        None
    """
    line = '\t'.join(str(x) for x in row)
    file.write(line + '\n')


def write_sp(row: pd.Series, file) -> None:
    """
    Writes SOLUTION_SPECIES to file.

    Parameters:
        row (pd.Series): A row of the combined SOLUTION_SPECIES dataframe.
        file (file): The file object to write the data to.

    Returns:
        None
    """
    for attribute in row.index:
        value = row[attribute]
        match attribute:
            case 'equation':
                value = re.sub(r'\s+', ' ', value)
                file.write(f"{value}\n")
            case 'log_k':
                file.write(f"\tlog_k\t{value}\n")
            case 'delta_h':
                write_tuple('-delta_h', value, file)
            case 'gamma':
                write_tuple('gamma', value, file)
            case 'd_w':
                write_tuple('dw', value, file)
            case 'v_m':
                write_tuple('Vm', value, file)
            case 'add_logk':
                write_tuple('add_logk', value, file)
            case 'llnl_gamma':
                file.write(f"\tllnl_gamma\t{value}\n")
            case 'no_check':
                if value:
                    file.write("\t-no_check\n")
            case 'source':
                file.write(f"\t# source\t{value}\n")


# PHASES block not currently implemented
def write_phase(row, file):  # pragma: no cover
    """
    Writes PHASES information to file.

    Args:
        row (pandas.Series): The row containing the phase information.
        file (file object): The file to write the information to.

    Returns:
        None
    """
    for attribute in row.index:
        value = row[attribute]
        match attribute:
            case 'phase_name':
                file.write(f"{value}\n")
            case 'dissolution_reaction':
                value = re.sub(r'\s+', ' ', value)
                file.write(f"\t{value}\n")
            case 'log_k':
                if value:
                    file.write(f"\tlog_k\t{value}\n")
            case 'delta_h':
                if value:
                    write_tuple('-delta_h', value, file)
            case 'analytic':
                write_tuple('-analytic', value, file)
            case 'v_m':
                if value:
                    write_tuple('-Vm', value, file)
            case 't_c':
                if value:
                    file.write(f"\t-T_c\t{value}\n")
            case 'p_c':
                if value:
                    file.write(f"\t-P_c\t{value}\n")
            case 'omega':
                if value:
                    file.write(f"\t-Omega\t{value}\n")
            case 'source':
                file.write(f"\t# source\t{value}\n")
