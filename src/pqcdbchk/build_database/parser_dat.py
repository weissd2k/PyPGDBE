"""Parses phreeqc .dat files and returns pandas dataframes"""
import re
import os
import click
from dataclasses import dataclass, asdict
from typing import List
import pandas as pd


@dataclass
class SolutionData:
    """Dataclass for solution species"""

    equation: str = None
    log_k: float = None
    delta_h: List[float] = None
    gamma: List[float] = None
    d_w: List[float] = None
    v_m: List[float] = None
    millero: List[float] = None
    activity_water: List[float] = None
    add_logk: List[float] = None
    llnl_gamma: List[float] = None
    co2_llnl_gamma: List[float] = None
    erm_ddl: List[float] = None
    no_check: List[float] = None
    mole_balance: List[float] = None


@dataclass
class PhaseData:
    """Dataclass for phase species"""

    phase_name: str = None
    dissolution_reaction: str = None
    log_k: List = None
    delta_h: List = None
    analytic: List = None
    v_m: List = None
    t_c: List = None
    p_c: List = None
    omega: List = None


class BaseParser:
    """Base class for parsing phreeqc database files"""

    def __init__(
        self, database_file_path: str, section_start: str, section_end: str
    ) -> None:
        """
        Initialize the BaseParser class.

        Parameters:
        - database_file_path (str): The path to the database file.
        - section_start (str): The starting section of the file to parse.
        - section_end (str): The ending section of the file to parse.
        """
        self.block_start = None
        self.source = file_name(database_file_path)
        self.line_list = text_selection(database_file_path, section_start, section_end)

    def parse_file(self) -> pd.DataFrame:
        """
        Parse the file and return the parsed data as a pandas DataFrame.

        Returns:
        - pd.DataFrame: The parsed data as a DataFrame.
        """
        block = []
        parsed_data_list = []
        for line in self.line_list:
            if "#" in line:
                continue
            if self.block_start.match(line):
                if block:
                    parsed_data = self.parse_block(block)
                    parsed_data_list.append(parsed_data)
                    block = []
            block.append(line.strip())
        if block:
            parsed_data = self.parse_block(block)
            parsed_data_list.append(parsed_data)

        data_dicts = [asdict(data) for data in parsed_data_list]
        result = pd.DataFrame(data_dicts)
        result["source"] = self.source
        return result

    def parse_block(self, block: List[str]):
        """
        Parse a block of lines and return the parsed data.

        Parameters:
        - block (List[str]): The block of lines to parse.

        Returns:
        - Any: The parsed data.
        """
        raise NotImplementedError

    def match_patterns(self, line: str, data_instance) -> None:
        """
        Match patterns in a line and update the data instance accordingly.

        Parameters:
        - line (str): The line to match patterns in.
        - data_instance (Any): The data instance to update.
        """
        for key, pattern in self.patterns.items():
            if pattern.match(line):
                line = line.split("#")[0]
                if key in line.split()[0].lower():
                    setattr(data_instance, key, tuple(line.split()[1:]))
                else:
                    setattr(data_instance, key, tuple(line.split()[0:]))
                break


class SolutionParser(BaseParser):
    """Class for parsing solution species in phreeqc database files"""
    def __init__(self, database_file_path) -> None:
        """
        Initialize the SolutionParser class.

        Parameters:
        - database_file_path (str): The path to the database file.
        """
        super().__init__(database_file_path, "SOLUTION_SPECIES", "PHASES")
        self.block_start = re.compile(r"^.*\s=\s.*")
        self.patterns = {
            "log_k": re.compile(r"^\s*[-]*log[ _]*k"),
            "delta_h": re.compile(r"\s*[-]*delta.*"),
            "analytic": re.compile(r"^\s*[-]*analytic"),
            "llnl_gamma": re.compile(r"^\s*[-]*llnl[ _]*gamma"),
            "gamma": re.compile(r"^\s*[-]*gamma"),
            "d_w": re.compile(r"^\s*[-]*dw"),
            "v_m": re.compile(r"^\s*[-]*Vm"),
            "millero": re.compile(r"^\s*[-]*Millero"),
            "activity_water": re.compile(r"^\s*[-]*activity[ _]*water"),
            "add_logk": re.compile(r"^\s*[-]*add[ _]*logk"),
            "co2_llnl_gamma": re.compile(r"^\s*[-]*co2[ _]*llnl[ _]*gamma"),
            "erm_ddl": re.compile(r"^\s*[-]*erm[ _]*ddl"),
            "no_check": re.compile(r"^\s*[-]*no[ _]*check"),
            "mole_balance": re.compile(r"^\s*[-]*mole[ _]*balance"),
        }

    def parse_block(self, block: List[str]) -> SolutionData:
        """
        Parse a block of lines and return the parsed data.

        Parameters:
        - block (List[str]): The block of lines to parse.

        Returns:
        - SolutionData: The parsed data.
        """
        data_instance = SolutionData()
        for line in block:
            if self.block_start.match(line):
                data_instance.equation = line.strip()
            else:
                self.match_patterns(line, data_instance)
        return data_instance


class PhaseParser(BaseParser):
    """Class for parsing phase species in phreeqc database files"""

    def __init__(self, database_file_path) -> None:
        """
        Initialize the PhaseParser class.

        Parameters:
        - database_file_path (str): The path to the database file.
        """
        super().__init__(database_file_path, "PHASES", "EXCHANGE")
        self.block_start = re.compile(r"^(?!\s)\S+$")
        self.patterns = {
            "dissolution_reaction": re.compile(r"^.*\s=\s.*"),
            "log_k": re.compile(r"^\s*[-]*log[ _]*k"),
            "delta_h": re.compile(r"\s*[-]*delta.*"),
            "analytic": re.compile(r"^\s*[-]*analytic"),
            "v_m": re.compile(r"^\s*[-]*Vm"),
            "t_c": re.compile(r"^\s*[-]*T_c"),
            "p_c": re.compile(r"^\s*[-]*P_c"),
            "omega": re.compile(r"^\s*[-]*Omega"),
        }

    def parse_block(self, block: List[str]) -> PhaseData:
        """
        Parse a block of lines and return the parsed data.

        Parameters:
        - block (List[str]): The block of lines to parse.

        Returns:
        - PhaseData: The parsed data.
        """
        data_instance = PhaseData()
        for line in block:
            if self.block_start.match(line):
                data_instance.phase_name = line.strip()
            else:
                self.match_patterns(line, data_instance)
        return data_instance


class MasterSolutionParser:
    """
    A parser for processing and combining master solution species data from a database file.

    This class handles the extraction of species information from a specified database file and
    converts it into a pandas DataFrame for further analysis or combination with other data sources.

    Parameters
    ----------
    database_file_path : str, optional
        The path to the database file containing the solution master species data.
        If provided, the species list will be extracted and processed.

    Attributes
    ----------
    composed_sources : list of str
        A list of source names that have been processed.
    data_frame : pandas.DataFrame or None
        The DataFrame containing the processed species data. This will be `None` until the data is processed.

    Methods
    -------
    make_dataframe
        Converts the extracted species list into a pandas DataFrame and assigns it to `data_frame`.
    """

    def __init__(self, database_file_path=None) -> None:
        """
        Initialize the MasterSolutionParser with an optional database file path.

        Parameters
        ----------
        database_file_path : str, optional
            The path to the database file to be processed. If provided, the file is parsed immediately.
        """
        self.composed_sources = []
        self.data_frame = None
        if database_file_path:
            self.source = file_name(database_file_path)
            self.composed_sources.append(self.source)
            self.species_list = text_selection(
                database_file_path, "SOLUTION_MASTER_SPECIES", "SOLUTION_SPECIES"
            )
            self.species_list = [line.split() for line in self.species_list]
            self.make_dataframe()

    def make_dataframe(self) -> None:
        """
        Convert the species list into a pandas DataFrame and store it in the `data_frame` attribute.

        The DataFrame will have columns for the element, species, alkalinity,
        gram formula weight (gfw) formula, and element gfw. The DataFrame will also
        include a column indicating the source of the data.

        Returns
        -------
        None
        """
        data_frame = pd.DataFrame(
            self.species_list,
            columns=["element", "species", "alk", "gfw_formula", "element_gfw"],
        )
        data_frame["source"] = self.source
        self.data_frame = data_frame

    def __add__(self, other: 'MasterSolutionParser') -> 'MasterSolutionParser':
        """
        Combine the data from this parser with another MasterSolutionParser instance.

        This method allows for the addition of two MasterSolutionParser objects,
        resulting in a new MasterSolutionParser instance containing the combined data.

        Parameters
        ----------
        other : MasterSolutionParser
            Another instance of MasterSolutionParser whose data will be combined with this instance.

        Returns
        -------
        MasterSolutionParser
            A new MasterSolutionParser instance containing the combined data from both sources.
        """
        result = MasterSolutionParser()
        result.composed_sources = self.composed_sources + other.composed_sources
        result.data_frame = pd.concat([self.data_frame, other.data_frame])
        return result


# Utility functions
def text_selection(text_file, start_block, end_block) -> list:
    """Selects lines from a text file between start_block and end_block"""
    equations = []
    with open(text_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
        read = False
        for line in lines:
            if line.strip() == start_block:
                read = True
                continue
            if (end_block in line.strip() or 'END' in line.strip()) and read:
                read = False
                break
            if read:
                # remove comments
                if "#" in line:
                    line = line.split("#")[0]
                # strip the line of whitespace and check if it's not empty
                cleaned_line = line.strip()
                if cleaned_line:
                    equations.append(cleaned_line)
    return equations


def file_name(file_path: str) -> str:
    """Extracts the file name from a file path"""
    if os.path.isfile(file_path):
        return os.path.basename(file_path)
    else:
        raise FileNotFoundError(f"File {file_path} not found")


@click.command()
@click.argument('database_file', type=click.Path(exists=True))
@click.option('--solution_csv', default='solution_data.csv', help='Filename for solution data CSV')
@click.option('--master_solution_csv', default='master_solution_data.csv', help='Filename for master solution data CSV')
@click.option('--save_solution', is_flag=True, help='Save solution data CSV')
@click.option('--save_master_solution', is_flag=True, help='Save master solution data CSV')
def parse_phreeqc(database_file, solution_csv, master_solution_csv, save_solution, save_master_solution):
    """
    Parses a PHREEQC database file and outputs data as CSVs.

    \b
    DATABASE_FILE: Path to the PHREEQC database file.
    """
    # Create solution parser and parse data
    solution_parser = SolutionParser(database_file)
    solution_data = solution_parser.parse_file()

    # Create master solution parser and parse data
    master_solution_parser = MasterSolutionParser(database_file)
    master_solution_data = master_solution_parser.data_frame

    # Save the data to CSV files based on the user's choices
    if save_solution or (not save_solution and not save_master_solution):
        solution_data.to_csv(solution_csv, index=False)
        click.echo(f"Solution data saved to {solution_csv}")

    if save_master_solution or (not save_solution and not save_master_solution):
        master_solution_data.to_csv(master_solution_csv, index=False)
        click.echo(f"Master solution data saved to {master_solution_csv}")


if __name__ == '__main__':
    parse_phreeqc()
