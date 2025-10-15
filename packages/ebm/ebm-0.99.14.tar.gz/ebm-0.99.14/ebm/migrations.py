import pathlib
from typing import Callable

import pandas as pd
from loguru import logger


def drop_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove columns starting with 'Unnamed:' from a DataFrame, and log a warning if any are not sequential.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame from which to drop 'Unnamed:' columns.

    Returns
    -------
    pandas.DataFrame
        A copy of the input DataFrame with 'Unnamed:' columns removed.

    Notes
    -----
    A column is considered sequential if the difference between consecutive values is constant.
    If any 'Unnamed:' columns are found to be non-sequential, a warning is logged.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'Unnamed: 0': [0, 1, 2],
    ...     'Unnamed: 1': [5, 7, 9],
    ...     'data': [10, 20, 30]
    ... })
    >>> drop_unnamed(df)
       data
    0    10
    1    20
    2    30
    """

    unnamed = [c for c in df.columns if c.startswith('Unnamed:')]
    if unnamed:
        drop_df = df.copy()
        not_sequential = [s for s in unnamed if drop_df[s].diff().dropna().nunique() != 1]
        if not_sequential:
            msg=f'Columns {not_sequential} {"was" if len(not_sequential)==1 else "were"} not sequential'
            logger.warning(msg)
        return drop_df.drop(columns=unnamed)
    return df


def rename_columns(df: pd.DataFrame, translation: dict[str:str]) -> pd.DataFrame:

    """
    Rename columns in a DataFrame using a translation dictionary.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame whose columns are to be renamed.
    translation : dict of str
        A dictionary mapping existing column names (keys) to new column names (values).

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with columns renamed according to the translation dictionary.
        If the translation dictionary is empty, the original DataFrame is returned unchanged.

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    >>> rename_columns(data, {'A': 'Alpha', 'B': 'Beta'})
       Alpha  Beta
    0      1     3
    1      2     4
    """
    if not translation:
        logger.debug('No translation dictionary provided')
        return df
    columns_to_rename = {k:v for k,v in translation.items() if k in df.columns}
    if not columns_to_rename:
        logger.debug(f'None of columns {translation.keys()} found in the dataframe')
        return df
    logger.debug(f'Renaming columns: {", ".join(columns_to_rename.keys())}')
    return df.copy().rename(columns=columns_to_rename)


def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Drop specified columns from a DataFrame with logging and validation.

    Parameters
    ----------
    df : pandas.DataFrame
        The input DataFrame from which columns will be dropped.
    columns : list of str
        A list of column names to drop from the DataFrame.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with the specified columns removed. If none of the columns
        are found, the original DataFrame is returned unchanged.

    Logs
    ----
    - Logs a debug message if no columns are provided.
    - Logs a warning if any specified columns are not found in the DataFrame.
    - Logs a debug message listing the columns that will be dropped.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'A': [1], 'B': [2], 'C': [3]})
    >>> drop_columns(df, ['B', 'D'])
    WARNING: Column ['D'] missing from dataframe
       A  C
    0  1  3
    """

    if not columns:
        logger.debug('No columns to drop')
        return df
    logger.debug(f'drop columns {columns}')
    not_found = [c for c in columns if c not in df.columns]
    found = [c for c in columns if c in df.columns]

    if not_found:
        plural = 's' if len(not_found) == 1 else ''
        msg = f'Column{plural} {not_found} missing from dataframe'
        logger.warning(msg)
    if not found:
        logger.debug('No columns to drop')
        return df
    return df.copy().drop(columns=found)


def translate_heating_system_efficiencies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Translate and drop columns in heating_system_efficiencies.csv

     - Translate column names from norwegian to english
     - Drop redundant columns

    """

    tr_df = df.copy()
    translation = {"Grunnlast energivare": "base_load_energy_product",
                   "Grunnlast virkningsgrad": "base_load_efficiency",
                   "Grunnlast andel": "base_load_coverage",
                   "Spisslast andel": "peak_load_coverage",
                   "Spisslast energivare": "peak_load_energy_product",
                   "Spisslast virkningsgrad": "peak_load_efficiency",
                   "Ekstralast energivare": "tertiary_load_energy_product",
                   "Ekstralast andel": "tertiary_load_coverage",
                   "Ekstralast virkningsgrad": "tertiary_load_efficiency",
                   "Tappevann energivare": "domestic_hot_water_energy_product",
                   "Tappevann virkningsgrad": "domestic_hot_water_efficiency",
                   "Kjoling virkningsgrad": "cooling_efficiency",
                   }
    tr_df = rename_columns(tr_df, translation)

    delete_columns = ['Grunnlast', 'Spisslast', 'Ekstralast', 'Tappevann']
    tr_df = drop_columns(tr_df, delete_columns)

    return tr_df


def migrate_input_directory(directory: pathlib.Path, migration: Callable) -> None:
    """
    Migrates heating system efficiency data in a given directory using a specified transformation function.

    This function renames legacy input files if necessary, validates the presence of the expected input file,
    reads the data, applies a migration/transformation function, and writes the result back to the same file.

    Parameters
    ----------
    directory : pathlib.Path
        The path to the directory containing the input CSV file.
    migration : Callable[[pd.DataFrame], pd.DataFrame]
        A function that takes a pandas DataFrame and returns a transformed DataFrame.

    Raises
    ------
    FileNotFoundError
        If the expected input file does not exist or is not a file.
    Exception
        If reading, transforming, or writing the file fails.

    Notes
    -----
    - If a legacy file named 'heating_systems_efficiencies.csv' exists and the target file
      'heating_system_efficiencies.csv' does not, the legacy file will be renamed.
    - The transformation is applied in-place and overwrites the original file.

    Examples
    --------
    >>> from pathlib import Path
    >>> migrate_input_directory(Path("data"), translate_heating_system_efficiencies)
    """

    logger.info(f'Migrating {directory} using {migration}')
    old_name = directory / 'heating_systems_efficiencies.csv'
    input_file = directory / 'heating_system_efficiencies.csv'
    if old_name.is_file():
        if input_file.is_file():
            logger.info(f'Found existing {input_file}')
        else:
            logger.debug(f'Rename {old_name.name} to {input_file.name}')
            old_name.rename(input_file)
            logger.success(f'Renamed {old_name.name} to {input_file.name}')

    if not input_file.exists():
        raise FileNotFoundError(f'{input_file} not found')
    if not input_file.is_file():
        raise FileNotFoundError(f'{input_file} is not a file')

    df = pd.read_csv(input_file)
    tr_df = migration(df)
    tr_df.to_csv(input_file, index=False)
    logger.success(f'Migrated {input_file}')
