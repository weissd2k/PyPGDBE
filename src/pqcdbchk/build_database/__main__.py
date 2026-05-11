"""Compile multiple databases into a single master database."""
import re
import logging
import os
import argparse
import importlib.resources as pkg_resources
import pandas as pd
import build_database.clean_tables as ct
from build_database import utils

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main(verbose=False):
    """Main function to compile the master database. """
    data_b = pkg_resources.files('build_database').joinpath('databases')
    data_b = utils.phreeqc_database_list(data_b)
    rank = {
        '#llnl.dat': 1,
        '#minteq.v4.dat': 2,
        '#phreeqc.dat': 3,
        '#Tipping_Hurley.dat': 4,
    }

    # Compile source and result tables
    mst = utils.compile_and_rank_mst(data_b, rank)
    soln_species = ct.compile_solution_species_table(data_b)
    db_list = utils.reorder_file_list(data_b, rank)
    result_mst = mst[mst['source'] == db_list[0]]
    result_sp = soln_species[soln_species['source'] == utils.remove_hash_from_source(db_list[0])]

    all_match_indexes = []
    for i in range(1, len(db_list)):
        missing_species = utils.get_missing_species(mst, result_mst, db_list[i])
        if missing_species.empty:
            logging.info("No missing species found in %s", db_list[i])
            continue

        if db_list[i] == '#minteq.v4.dat':
            missing_species = utils.process_missing_species(missing_species)

        equations = soln_species[soln_species['source'] == utils.remove_hash_from_source(db_list[i])]['equation']
        missing_species['species'].apply(
            lambda entry: utils.find_and_collect_matches(
                equations,
                entry,
                all_match_indexes,
                )
            )
        result_mst = pd.concat([result_mst, missing_species], ignore_index=True)

    all_match_indexes = list(set(all_match_indexes))
    equations_add = soln_species.loc[all_match_indexes]
    drop_re = re.compile('Hg[(]OH[)]2|Sb[(]OH[)]6-|H4[(]SiO4[)]|H2[(]PO4[)]-|H3BO3|H4SiO4')
    drop_index = equations_add[equations_add['equation'].str.contains(drop_re)].index
    equations_add = equations_add.drop(index=drop_index)
    result_sp = pd.concat([result_sp, equations_add], ignore_index=True)
    result_mst = result_mst.sort_values(by=['element'])

    # Display information by source
    if verbose:
        logging.info(f"Master database compiled with {len(result_mst)} elements and {len(result_sp)} equations.")
        num_of_species_by_source = result_sp['source'].value_counts()
        logging.info("Number of elements by source:")
        for source, num in num_of_species_by_source.items():
            logging.info(f"{source}: {num}")

    # Handle user input
    current_dir = os.path.dirname(os.path.realpath(__file__))
    default_output = os.path.join(current_dir, 'master_database.dat')
    parser = argparse.ArgumentParser(description='Compile multiple databases into a single master database.')
    parser.add_argument('--output', '-o', type=str, default=default_output, help='Output file path')
    args = parser.parse_args()

    utils.save_master_database(args.output, result_mst, result_sp)


if __name__ == "__main__":
    main()
