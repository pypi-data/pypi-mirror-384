import pathlib
from typing import List, Optional

import pandas as pd
from pandera.typing.common import DataFrameBase

from ebm.model.building_category import BuildingCategory


def explode_building_category_column(df: pd.DataFrame, unique_columns: List[str]) -> pd.DataFrame:
    """
        Explodes the 'building_category' column in the DataFrame into multiple columns based on residential and non-residential categories.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame containing the 'building_category' column.
        unique_columns : List[str]
            List of columns to use for de-duplication.

        Returns
        -------
        pd.DataFrame
            The DataFrame with exploded 'building_category' columns.
    """
    df = explode_column_alias(df=df, column='building_category',
                              values=[bc for bc in BuildingCategory if bc.is_residential()],
                              alias='residential',
                              de_dup_by=unique_columns)
    df = explode_column_alias(df=df, column='building_category',
                              values=[bc for bc in BuildingCategory if not bc.is_residential()],
                              alias='non_residential',
                              de_dup_by=unique_columns)
    df = explode_column_alias(df=df, column='building_category',
                              values=[bc for bc in BuildingCategory],
                              alias='default',
                              de_dup_by=unique_columns)
    return df


def explode_building_code_column(df: pd.DataFrame, unique_columns: List[str],
                       default_building_code: None | pd.DataFrame = None) -> pd.DataFrame:
    """
        Explodes the 'building_code' column in the DataFrame into multiple columns based on the provided building_codelist.

        Parameters
        ----------
        df : pd.DataFrame
            The input DataFrame containing the 'building_code' column.
        unique_columns : List[str]
            List of columns to use for de-duplication.
        default_building_code : Optional[pd.DataFrame], optional
            DataFrame containing default building_codevalues. If not provided, building_codevalues are read from 'input/building_codes.csv'.

        Returns
        -------
        pd.DataFrame
            The DataFrame with exploded 'building_code' columns.
        """
    # Hvor skal building_code_list hentes fra?
    building_code_list = pd.read_csv(pathlib.Path(__file__).parent.parent / 'data' / 'original' /'building_code_parameters.csv')['building_code'].unique() if default_building_code is None else default_building_code
    df = explode_column_alias(df=df,
                              column='building_code',
                              values=building_code_list,
                              de_dup_by=unique_columns)
    return df


def explode_unique_columns(df: pd.DataFrame| DataFrameBase,
                           unique_columns: List[str],
                           default_building_code: List[str]|None = None) -> pd.DataFrame:
    """
    Explodes 'building_code' and 'building_category' columns in df.


    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame containing the columns to be exploded.
    unique_columns : List[str]
        List of columns to use for de-duplication.
    default_building_code : List[str], optional
        List of TEKs to replace default

    Returns
    -------
    pd.DataFrame
        The DataFrame with exploded columns.
    """

    df = explode_building_code_column(df, unique_columns, default_building_code=default_building_code)
    df = explode_building_category_column(df, unique_columns)
    return df


def explode_column_alias(df, column, values: list|dict=None, alias='default', de_dup_by: list[str]=None):
    """
    Explodes a specified column in the DataFrame into multiple rows based on provided values and alias.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame containing the column to be exploded.
    column : str
        The name of the column to be exploded.
    values : Optional[List[str], dict[str, list[str]], optional
        List or dict of values to explode the column by. If not provided, unique values from the column excluding the
        alias are used.
    alias : str, optional
        The alias to be used for default values. Default is 'default'.
        When values is a dict the parameter alias is ignored
    de_dup_by : Optional[List[str]], optional
        List of columns to use for de-duplication. If not provided, no de-duplication is performed.

    Returns
    -------
    pd.DataFrame
        The DataFrame with the exploded column.

    Examples
    --------
    >>> d_f = pd.DataFrame({'category': ['A', 'B', 'default']})
    >>> explode_column_alias(d_f, column='category', values=['A', 'B'], alias='default')
       category
    0         A
    1         B
    2         A
    2         B
    """
    if column not in df.columns:
        raise ValueError(f"The DataFrame (df) must contain the column: {column}")

    df = replace_column_alias(df, column=column, values=values, alias=alias, de_dup_by=None)

    df = df.assign(**{column: df[column].str.split('+')}).explode(column)
    if de_dup_by:
        df = df.sort_values(by='_explode_column_alias_default', ascending=True)
        df = df.drop_duplicates(de_dup_by)
    return df.drop(columns=['_explode_column_alias_default'], errors='ignore')


def replace_column_alias(df: pd.DataFrame, column: str, values: Optional[list|dict]=None, alias: Optional[str]='default',
                         de_dup_by=None) -> pd.DataFrame:
    values = values if values is not None else [c for c in df[column].unique().tolist() if c != alias]
    aliases = {alias: values} if not isinstance(values, dict) else values
    df = df.copy()
    for k, v in aliases.items():
        df['_explode_column_alias_default'] = df[column] == k
        df.loc[df[df[column] == k].index, column] = '+'.join(v)
    if not de_dup_by:
        return df
    return df.drop(columns=['_explode_column_alias_default'], errors='ignore')


def explode_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.assign(**{column: df[column].str.split('+')}).explode(column)
    return df
