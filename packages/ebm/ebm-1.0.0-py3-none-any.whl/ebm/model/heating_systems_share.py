import pandas as pd

from ebm.model.bema import BUILDING_CATEGORY_ORDER


def transform_heating_systems_share_long(heating_systems_projection: pd.DataFrame) -> pd.DataFrame:
    df = heating_systems_projection.copy()

    fane2_columns = ['building_category', 'heating_systems', 'year', 'heating_system_share']

    df.loc[~df['building_category'].isin(['house', 'apartment_block']), 'building_category'] = 'non_residential'

    mean_heating_system_shares_yearly = df[fane2_columns].groupby(by=['year', 'building_category', 'heating_systems']).mean()
    return mean_heating_system_shares_yearly


def transform_heating_systems_share_wide(heating_systems_share_long: pd.DataFrame) -> pd.DataFrame:
    value_column = 'heating_system_share'
    df = heating_systems_share_long.copy().reset_index()
    df = df.pivot(columns=['year'], index=['building_category', 'heating_systems'], values=[value_column]).reset_index()

    df = df.sort_values(by=['building_category', 'heating_systems'],
                        key=lambda x: x.map(BUILDING_CATEGORY_ORDER) if x.name == 'building_category' else x)
    df.insert(2, 'U', value_column)
    df['U'] = '%'

    df.columns = ['building_category', 'heating_systems', 'U'] + [y for y in range(2020, 2051)]
    return df
