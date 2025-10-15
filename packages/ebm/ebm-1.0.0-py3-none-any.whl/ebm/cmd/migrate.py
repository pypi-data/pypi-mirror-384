import argparse
import os
import pathlib
import sys
import typing

from loguru import logger
from ebm.cmd.helpers import load_environment_from_dotenv, configure_loglevel
from ebm.migrations import migrate_input_directory, translate_heating_system_efficiencies
from ebm.model.file_handler import FileHandler


def migrate_directories(directories: typing.Iterable[pathlib.Path|str]) -> None:
    """
    Migrates and validates a list of input directories.

    Parameters
    ----------
    directories : Iterable[pathlib.Path or str]
        A list of directory paths to be migrated and validated.

    Returns
    -------
    None
    """

    for directory in map(pathlib.Path, directories):
        migrate_directory(directory)


def migrate_directory(directory: pathlib.Path):
    """
    Migrates and validates a single input directory.

    Applies the `translate_heating_system_efficiencies` migration and validates
    the input files using `FileHandler`.

    Parameters
    ----------
    directory : pathlib.Path
        The path to the directory to be migrated and validated.

    Returns
    -------
    None
    """

    logger.debug(f'Open {directory} {type(directory)}')
    migrate_input_directory(directory=directory, migration=translate_heating_system_efficiencies)
    FileHandler(directory=directory).validate_input_files()


def main() -> None:
    """
    Main entry point for the migration script.

    Loads environment variables, configures logging, creates missing input files,
    and performs migration and validation on a set of predefined directories.

    Returns
    -------
    None
    """

    load_environment_from_dotenv()
    configure_loglevel(log_format=os.environ.get('LOG_FORMAT', None))

    logger.debug(f'Starting {sys.executable} {__file__}')

    parser = argparse.ArgumentParser(description="Migrate and validate EBM input directories.")
    parser.add_argument("directories",
                        nargs="*",
                        help="List of input directories to migrate. If omitted, uses EBM_INPUT_DIRECTORY environment variable.")

    arguments = parser.parse_args()

    directories = arguments.directories or os.environ.get('EBM_INPUT_DIRECTORY', '').split(os.pathsep)
    if not directories or directories == ['']:
        logger.error('No input directories provided via CLI or EBM_INPUT_DIRECTORY.')
        sys.exit(1)

    #new_fh = FileHandler(directory='t3192_input')
    #new_fh.create_missing_input_files()

    #migration_directories = ['../Energibruksmodell/tests/ebm/data/kalibrert', 't3192_input', 't2734_input',
    #                         '../Energibruksmodell/ebm/data']

    migrate_directories(directories)


if __name__ == '__main__':
    main()
