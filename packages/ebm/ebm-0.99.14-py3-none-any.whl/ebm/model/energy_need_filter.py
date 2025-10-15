from typing import Optional

import pandas as pd

from ebm.model.building_category import BuildingCategory
from ebm.model.building_condition import BuildingCondition
from ebm.model.column_operations import replace_column_alias
from ebm.model.energy_purpose import EnergyPurpose


def filter_original_condition(df: pd.DataFrame, building_category: BuildingCategory|str, tek:str, purpose: str) -> pd.DataFrame:
    """
    Explode and deduplicates DataFrame df and returns rows matching building_category, tek, and purpose

    Convenience function that does

    ```python

    exploded = explode_dataframe(df)
    de_duped = de_dupe_dataframe(exploded)
    filtered = de_duped[(de_duped.building_category==building_category) & (de_duped.building_code==tek) & (de_duped.purpose == purpose)]

    ```

    Parameters
    ----------
    df : pd.DataFrame
    building_category : BuildingCategory | str
    tek : str
    purpose : str

    Returns
    -------
    pd.DataFrame

    """
    exploded = explode_dataframe(df)
    de_duped = de_dupe_dataframe(exploded)
    return de_duped[(de_duped.building_category==building_category) & (de_duped.building_code==tek) & (de_duped.purpose == purpose)]


def filter_improvement_building_upgrade(df: pd.DataFrame, building_category: BuildingCategory|str, tek:str, purpose: str) -> pd.DataFrame:
    """
    Explode and deduplicates DataFrame df and returns rows matching building_category, tek, and purpose

    Convenience function that does

    ```python

    exploded = explode_dataframe(df)
    de_duped = de_dupe_dataframe(exploded)
    filtered = de_duped[(de_duped.building_category==building_category) & (de_duped.building_code==tek) & (de_duped.purpose == purpose)]

    ```

    Parameters
    ----------
    df : pd.DataFrame
    building_category : BuildingCategory | str
    tek : str
    purpose : str

    Returns
    -------
    pd.DataFrame

    """
    exploded = explode_dataframe(df)
    de_duped = de_dupe_dataframe(exploded, unique_columns=['building_category', 'building_code', 'purpose', 'building_condition'])
    filtered=de_duped[(de_duped.building_category==building_category) & (de_duped.building_code==tek) & (de_duped.purpose == purpose)]

    filler_frame = pd.DataFrame([(building_category, tek, purpose, bc, 0.0) for bc in BuildingCondition.existing_conditions()],
                                columns=['building_category', 'building_code', 'purpose', 'building_condition', 'reduction_share'])

    return pd.concat([filtered, filler_frame]).drop_duplicates(['building_category', 'building_code', 'purpose', 'building_condition'], keep='first')


def de_dupe_dataframe(df: pd.DataFrame, unique_columns: Optional[list[str]]=None) -> pd.DataFrame:
    """
    Drops duplicate rows in df based on building_category, TEK and purpose
    same as
        df.drop_duplicates(unique_columns)
    Parameters
    ----------
    df : pd.DataFrame
    unique_columns : list[str], optional
                     default= ['building_category', 'building_code', 'purpose']

    Returns
    -------
    pd.DataFrame

    """
    de_dupe_by = unique_columns if unique_columns else ['building_category', 'building_code', 'purpose']

    de_duped = df.drop_duplicates(de_dupe_by)
    return de_duped


def explode_dataframe(df: pd.DataFrame, building_code_list:Optional[list[str]]=None) -> pd.DataFrame:
    """
    Explode column aliases for building_category, TEK, purpose in dataframe.

    default in building_category is replaced with all options from BuildingCategory enum
    default in TEK is replaced with all elements in optional building_code_list parameter
    default in purpose is replaced with all options from EnergyPurpose enum

    Parameters
    ----------
    df : pd.DataFrame
    building_code_list : list of TEK to replace default, Optional
               default TEK49 PRE_TEK49 PRE_TEK49_RES_1950 TEK69 TEK87 TEK97 TEK07 TEK10 TEK17

    Returns
    -------
    pd.DataFrame

    """
    if not building_code_list:
        building_code_list = 'TEK49 PRE_TEK49 PRE_TEK49_RES_1950 TEK69 TEK87 TEK97 TEK07 TEK10 TEK17 TEK21 TEK01'.split(' ')
    # expand building_category
    df = replace_column_alias(df,
                              column='building_category',
                              values={'default': [b for b in BuildingCategory],
                                      'residential': [b for b in BuildingCategory if b.is_residential()],
                                      'non_residential': [b for b in BuildingCategory if not b.is_residential()]})
    # expand tek
    df = replace_column_alias(df, 'building_code', values=building_code_list, alias='default')

    # expand purpose
    df = replace_column_alias(df, 'purpose', values=[p for p in EnergyPurpose], alias='default')

    # Add priorty column and sort
    df['bc_priority'] = df.building_category.apply(lambda x: 0 if '+' not in x else len(x.split('+')))
    df['t_priority'] = df.building_code.apply(lambda x: 0 if '+' not in x else len(x.split('+')))
    df['p_priority'] = df.purpose.apply(lambda x: 0 if '+' not in x else len(x.split('+')))

    if not 'priority' in df.columns:
        df['priority'] = 0
    df['priority'] = df.bc_priority + df.t_priority + df.p_priority

    # Explode
    df = df.assign(**{'building_category': df['building_category'].str.split('+'), }).explode('building_category')
    df = df.assign(**{'building_code': df['building_code'].str.split('+')}).explode('building_code')
    df = df.assign(**{'purpose': df['purpose'].str.split('+'), }).explode('purpose')
    # dedupe
    deduped = df.sort_values(by=['building_category', 'building_code', 'purpose', 'priority'])
    deduped['dupe'] = deduped.duplicated(['building_category', 'building_code', 'purpose'], keep=False)
    return deduped


def main():
    """
    Explode and prints all files listed in command line arguments. Default is reading files from input/

    """
    import pathlib
    import sys
    def _load_file(infile):
        df = pd.read_csv(infile)
        building_code_list = 'TEK49 PRE_TEK49 TEK69 TEK87 TEK97 TEK07 TEK10 TEK17'.split(' ')

        return explode_dataframe(df, building_code_list=building_code_list).sort_values(
            by=['dupe', 'building_category', 'building_code', 'purpose', 'priority'])
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    if len(sys.argv) < 2:
        files = list(pathlib.Path('input').glob('*.csv'))
    else:
        files = [pathlib.Path(f) for f in sys.argv[1:]]
    for filename in files:
        print(f'# {filename}')
        try:
            df = _load_file(filename)
            print(df)
        except KeyError as key_error:
            print('KeyError: missing ', str(key_error), sys.stderr)


if __name__ == '__main__':
    main()
