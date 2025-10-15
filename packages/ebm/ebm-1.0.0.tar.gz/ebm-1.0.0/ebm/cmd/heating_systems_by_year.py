import pandas as pd

from ebm.model.calibrate_heating_systems import group_heating_systems_by_energy_carrier
from ebm.model.data_classes import YearRange


def group_heating_systems_energy_source_by_year(hs: pd.DataFrame) -> pd.DataFrame:
    df = hs.set_index(['building_category', 'building_condition', 'purpose', 'building_code', 'year', 'heating_systems'])

    return group_heating_systems_by_energy_carrier(df)




def group_heating_systems_energy_source_by_year_horizontal(hs: pd.DataFrame, year_range: YearRange=None) -> pd.DataFrame:
    df = group_heating_systems_energy_source_by_year(hs)
    return df.reset_index().pivot(columns=['year'], index=['building_category', 'energy_source'], values=['energy_use'])

